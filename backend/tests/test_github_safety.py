"""No live GitHub calls: validate URLs, bounded transports and hostile archive handling."""
import io
import stat
import zipfile
import httpx
import pytest
from test_ai_transactions import app
from fastapi import HTTPException
from backend.services import github_client as github


@pytest.mark.parametrize("value",["https://evil.example/a/b","http://github.com/a/b","https://github.com@localhost/a/b",
    "https://github.com/a/b?token=secret","https://github.com/a/b#x","https://github.com/a/b/tree/main",
    "a/..","a/%2e%2e","a/b/c","a/b\\c","https://github.com:443/a/b","git@github.com:a/b.git"])
def test_only_canonical_public_identifiers(value):
    with pytest.raises(HTTPException):github.canonical(value)


def test_canonical_names():
    assert github.canonical("https://github.com/Octo/Hello.git/")=="octo/hello"
    assert github.canonical("Octo/Hello")=="octo/hello"


def archive(entries):
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w",zipfile.ZIP_DEFLATED) as z:
        for path,content in entries:z.writestr(path,content)
    return stream.getvalue()


@pytest.mark.parametrize("path",["../evil.py","root/../evil.py","/root/evil.py","root/C:evil.py","root/a\\evil.py","root//evil.py"])
def test_rejects_archive_traversal(path):
    data=archive([(path,"bad")])
    # Windows' ZIP writer normalizes backslashes; restore the hostile raw member name.
    if "\\" in path:data=data.replace(path.replace("\\","/").encode(),path.encode())
    with pytest.raises(HTTPException) as exc:github.inspect_archive(data)
    assert exc.value.headers["X-Error-Code"]=="repository_unsafe_archive"


def test_archive_links_duplicates_sizes_and_manifest(monkeypatch):
    link=zipfile.ZipInfo("root/link")
    link.create_system=3
    link.external_attr=(stat.S_IFLNK|0o777)<<16
    for entries in [[(link,"/etc/passwd")],[("root/A.py","x"),("root/a.py","x")],[("one/a.py","x"),("two/b.py","y")]]:
        with pytest.raises(HTTPException):github.inspect_archive(archive(entries))
    data=archive([("root/main.py","print(1)"),("root/image.png",b"\x00binary")])
    manifest,prose,code=github.inspect_archive(data)
    assert code=={"main.py":"print(1)"} and prose==""
    assert manifest[0]["included"] and not manifest[1]["included"]
    assert len(manifest[0]["sha256"])==64
    monkeypatch.setattr(github,"EXPANDED",4)
    with pytest.raises(HTTPException) as exc:github.inspect_archive(data)
    assert exc.value.status_code==413
    monkeypatch.setattr(github,"EXPANDED",1000)
    monkeypatch.setattr(github,"MAX_FILES",1)
    with pytest.raises(HTTPException):github.inspect_archive(data)
    monkeypatch.setattr(github,"COMPRESSED",1)
    with pytest.raises(HTTPException):github.inspect_archive(data)


@pytest.mark.asyncio
async def test_transport_rejects_redirect_before_any_untrusted_request(monkeypatch):
    monkeypatch.setenv("GITHUB_FIXTURE_MODE","false")
    original=httpx.AsyncClient
    called=[]
    def handler(request):
        called.append(str(request.url))
        return httpx.Response(302,headers={"location":"https://localhost/secret"})
    def client(**kwargs):
        kwargs["transport"]=httpx.MockTransport(handler)
        return original(**kwargs)
    monkeypatch.setattr(github.httpx,"AsyncClient",client)
    with pytest.raises(HTTPException) as exc:
        await github.read("https://api.github.com/repos/a/b/zipball/"+"a"*40,1000,True,"a/b","a"*40)
    assert exc.value.headers["X-Error-Code"]=="github_unsafe_redirect" and len(called)==1


@pytest.mark.asyncio
async def test_transport_limits_errors_and_public_identity(monkeypatch):
    monkeypatch.setenv("GITHUB_FIXTURE_MODE","false")
    original=httpx.AsyncClient
    reply=httpx.Response(200,content=b"x"*101)
    def client(**kwargs):
        kwargs["transport"]=httpx.MockTransport(lambda request:reply)
        return original(**kwargs)
    monkeypatch.setattr(github.httpx,"AsyncClient",client)
    with pytest.raises(HTTPException) as exc:await github.read("https://api.github.com/repos/a/b",100)
    assert exc.value.status_code==413
    reply=httpx.Response(429)
    with pytest.raises(HTTPException) as exc:await github.metadata("a/b")
    assert exc.value.headers["X-Error-Code"]=="github_rate_limit"
    reply=httpx.Response(200,json={"id":3,"full_name":"a/b","private":True})
    with pytest.raises(HTTPException):await github.metadata("a/b")
    reply=httpx.Response(200,json={"id":3,"full_name":"a/b","private":False})
    with pytest.raises(HTTPException) as exc:await github.metadata("a/b",4)
    assert exc.value.headers["X-Error-Code"]=="repository_identity"


@pytest.mark.asyncio
async def test_explicit_fixture_has_safe_archive(monkeypatch):
    monkeypatch.setenv("GITHUB_FIXTURE_MODE","true")
    monkeypatch.setenv("MOCK_MODE","true")
    assert (await github.metadata("uniassist-fixtures/demo"))["id"]==999001
    rows,partial=await github.recent("uniassist-fixtures/demo")
    assert len(rows)==1 and not partial
    data=await github.archive("uniassist-fixtures/demo","a"*40)
    assert github.inspect_archive(data)[2]["main.py"]
