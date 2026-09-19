"""Bounded public-only GitHub reads. No credentials, shell, checkout or arbitrary hosts."""
import asyncio
import datetime as dt
import hashlib
import io
import json
import os
import re
import stat
import zipfile
import zlib
from urllib.parse import urlsplit
import httpx
from backend.services.access import fail

COMPRESSED = 25 * 1024 * 1024
EXPANDED = 100 * 1024 * 1024
MAX_FILES = 1000
SHA = re.compile(r"[0-9a-f]{40}\Z")
FULL_NAME = re.compile(r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,38})/[a-zA-Z0-9_.-]{1,100}\Z")
CODE = {".py",".js",".ts",".tsx",".jsx",".java",".c",".cpp",".h",".cs",".go",".rs",".rb",".php",".html",".css",".sql",".sh",".json",".yaml",".yml"}


def canonical(value):
    value = value.strip()
    if value.startswith("https://github.com/"):
        parsed = urlsplit(value)
        if parsed.query or parsed.fragment or parsed.username or parsed.password:
            fail("repository_url", "Use a public GitHub owner/repository URL only.",422)
        value = parsed.path.removeprefix("/").removesuffix("/")
    if value.endswith(".git"):
        value = value[:-4]
    if not FULL_NAME.fullmatch(value) or value.split("/")[1] in (".",".."):
        fail("repository_url", "Use a public GitHub owner/repository URL only.",422)
    return value.lower()


def fixture_mode():
    enabled = os.getenv("GITHUB_FIXTURE_MODE", "false").lower() == "true"
    if enabled and os.getenv("MOCK_MODE", "false").lower() != "true":
        fail("github_unavailable", "GitHub fixtures require explicit mock AI mode.",503)
    return enabled


def fixture_response(request):
    """Opt-in verification transport; unmistakable provenance, never a network failure fallback."""
    path = request.url.path
    match=re.search(r"(?:/repos)?/(uniassist-fixtures/(?:demo|replacement))(?:/|$)",path)
    if not match:
        return httpx.Response(404)
    full_name=match.group(1)
    if "/zipball/" in path:
        return httpx.Response(302,headers={"Location":f"https://codeload.github.com/{full_name}/legacy.zip/"+path.rsplit("/",1)[1]})
    if request.url.host == "codeload.github.com":
        output = io.BytesIO()
        with zipfile.ZipFile(output,"w",zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("demo-fixture/README.md","Deterministic verification repository. Not real GitHub evidence.")
            archive.writestr("demo-fixture/main.py","def search(values, target):\n    return target in values\n")
        return httpx.Response(200,content=output.getvalue())
    commit = {"sha":"a"*40,"author":{"login":"fixture-author"},"commit":{
        "author":{"name":"Fixture author","date":"2026-09-19T00:00:00Z"},"message":"Fixture commit"}}
    if "/commits/" in path:
        return httpx.Response(200,json=commit) if path.endswith("a"*40) else httpx.Response(404)
    if path.endswith("/commits"):
        return httpx.Response(200,json=[commit])
    return httpx.Response(200,json={"id":999001 if full_name.endswith("/demo") else 999002,"full_name":full_name,"private":False})


async def read(url, limit, archive=False, full_name=None, sha=None):
    # Only internally built URLs reach here; validate every redirect before issuing another request.
    transport = httpx.MockTransport(fixture_response) if fixture_mode() else None
    try:
        async with asyncio.timeout(40):
            async with httpx.AsyncClient(timeout=10,follow_redirects=False,trust_env=False,transport=transport,
                headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2026-03-10","User-Agent":"UniAssist-public-evidence"}) as client:
                for hop in range(3):
                    parsed = urlsplit(url)
                    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None,443) or parsed.fragment:
                        fail("github_unsafe_redirect","Unsafe GitHub redirect rejected.",502)
                    if hop == 0:
                        if parsed.hostname != "api.github.com" or not parsed.path.startswith("/repos/"):
                            fail("github_unsafe_redirect","Invalid GitHub endpoint.",502)
                    elif not archive or parsed.hostname != "codeload.github.com" or parsed.query or parsed.path.lower() not in (
                        f"/{full_name}/legacy.zip/{sha}",f"/{full_name}/zip/{sha}"):
                        fail("github_unsafe_redirect","Unsafe GitHub archive redirect rejected.",502)
                    async with client.stream("GET",url) as response:
                        if response.status_code in (301,302,303,307,308):
                            if not archive or hop >= 2:
                                fail("github_unavailable","Repository moved or archive redirects exceeded the limit.",503)
                            url = response.headers.get("location", "")
                            continue
                        if response.status_code in (403,429):
                            fail("github_rate_limit","GitHub denied or rate-limited the public request. Retry later.",429)
                        if response.status_code in (404,409,451):
                            fail("github_unavailable","Public repository or commit is unavailable.",503)
                        if response.status_code != 200:
                            fail("github_unavailable","GitHub is unavailable.",503)
                        chunks, size = [], 0
                        async for chunk in response.aiter_bytes(65536):
                            size += len(chunk)
                            if size > limit:
                                fail("repository_size","GitHub response exceeds the configured size limit.",413)
                            chunks.append(chunk)
                        return b"".join(chunks)
        fail("github_unavailable","Archive was not returned.",503)
    except (httpx.HTTPError, TimeoutError, ValueError):
        fail("github_unavailable","GitHub request failed or timed out.",503)


async def payload(full_name, suffix=""):
    raw = await read(f"https://api.github.com/repos/{canonical(full_name)}{suffix}",4*1024*1024)
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        fail("github_invalid_response","Invalid GitHub response.",502)


async def metadata(full_name, github_id=None):
    value = await payload(full_name)
    if not isinstance(value,dict) or value.get("private") is not False or type(value.get("id")) is not int or value["id"]<=0 or not isinstance(value.get("full_name"),str) or value["full_name"].lower() != full_name:
        fail("github_unavailable","Only the exact public repository is supported.",503)
    if github_id is not None and value["id"] != github_id:
        fail("repository_identity","The GitHub repository identity changed. Propose a new link.",409)
    return value


def commit_info(value):
    try:
        sha = value["sha"]
        author = value["commit"]["author"]
        timestamp = dt.datetime.fromisoformat(author["date"].replace("Z","+00:00"))
        if not SHA.fullmatch(sha) or timestamp.tzinfo is None:
            raise ValueError()
        return {"commit_hash":sha,"author_name":str(author["name"] or "")[:255],
            "author_github_username":str((value.get("author") or {}).get("login") or "")[:255],
            "message":str(value["commit"]["message"])[:2000],
            "committed_at":timestamp.astimezone(dt.timezone.utc).replace(tzinfo=None)}
    except (KeyError,TypeError,ValueError,AttributeError):
        fail("github_invalid_response","Invalid GitHub commit metadata.",502)


async def recent(full_name):
    rows = await payload(full_name,"/commits?per_page=100&page=1")
    if not isinstance(rows,list) or len(rows)>100:
        fail("github_invalid_response","Invalid GitHub commit list.",502)
    return [commit_info(r) for r in rows], len(rows)>=100


async def archive(full_name, sha):
    if not SHA.fullmatch(sha):
        fail("invalid_input","A full lowercase 40-character SHA is required.",422)
    info = commit_info(await payload(full_name,"/commits/"+sha))
    if info["commit_hash"] != sha:
        fail("github_invalid_response","GitHub returned a different commit.",502)
    return await read(f"https://api.github.com/repos/{full_name}/zipball/{sha}",COMPRESSED,True,full_name,sha)


def inspect_archive(data):
    """Read bounded entries in memory. Never extract or execute repository content."""
    if len(data)>COMPRESSED:
        fail("repository_size","Archive exceeds 25 MiB compressed.",413)
    manifest, code, prose, total, selected, root, seen = [], {}, [], 0, 0, None, set()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries)>2000:
                fail("repository_size","Too many archive entries.",413)
            for entry in entries:
                path = entry.filename
                parts = path.rstrip("/").split("/")
                mode = entry.external_attr >> 16
                if (entry.orig_filename!=path or not path or len(path)>600 or "\\" in path or ":" in path or any(ord(c)<32 for c in path)
                    or any(p in ("",".","..") for p in parts) or entry.flag_bits & 1
                    or stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)
                    or entry.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED)):
                    fail("repository_unsafe_archive","Unsafe archive path, link or entry rejected.",422)
                root = root or parts[0]
                if parts[0] != root or (len(parts)==1 and not entry.is_dir()):
                    fail("repository_unsafe_archive","Archive must have one repository root.",422)
                if entry.is_dir():
                    continue
                relative = "/".join(parts[1:])
                if relative.casefold() in seen:
                    fail("repository_unsafe_archive","Duplicate archive path rejected.",422)
                seen.add(relative.casefold())
                if len(seen)>MAX_FILES or total+entry.file_size>EXPANDED:
                    fail("repository_size","Archive exceeds 100 MiB expanded or 1000 files.",413)
                digest, chunks, size = hashlib.sha256(), [], 0
                with archive.open(entry) as stream:
                    while chunk := stream.read(65536):
                        size += len(chunk)
                        total += len(chunk)
                        if total>EXPANDED:
                            fail("repository_size","Archive expansion exceeds 100 MiB.",413)
                        digest.update(chunk)
                        if size<=512*1024:
                            chunks.append(chunk)
                suffix = "."+relative.rsplit(".",1)[-1].lower() if "." in relative else ""
                included = False
                if size<=512*1024 and selected+size<=4*1024*1024 and suffix in CODE | {".md",".txt"}:
                    try:
                        content = b"".join(chunks).decode("utf-8")
                        if "\x00" not in content:
                            selected += size
                            included = True
                            if suffix in CODE:
                                code[relative] = content
                            else:
                                prose.append(relative+"\n"+content)
                    except UnicodeError:
                        pass
                manifest.append({"path":relative,"size":size,"sha256":digest.hexdigest(),"included":included})
    except (zipfile.BadZipFile,RuntimeError,NotImplementedError,EOFError,OSError,zlib.error):
        fail("repository_unsafe_archive","Invalid or unsupported archive.",422)
    if not manifest:
        fail("repository_empty","Repository archive contains no files.",422)
    return manifest, "\n\n".join(prose), code
