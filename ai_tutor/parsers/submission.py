import os
import zipfile
from typing import Dict, List, Tuple
import pypdf
import docx


# Path segments to skip when extracting student submissions (dependencies, tooling, VCS).
SKIP_PATH_SEGMENTS = frozenset({
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "build",
    "dist",
    "target",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "site-packages",
})

CODE_EXTENSIONS = {
    ".py", ".cpp", ".hpp", ".c", ".h", ".java", ".js", ".ts",
    ".html", ".css", ".sql", ".sh",
}


def _should_skip_path(rel_path: str) -> bool:
    """Return True if the relative path is under a skipped directory segment."""
    normalized = rel_path.replace("\\", "/").lower().strip("/")
    if not normalized:
        return True
    return any(part in SKIP_PATH_SEGMENTS for part in normalized.split("/"))


def extract_text_from_file(file_path: str) -> str:
    """Extract readable text content from PDF, DOCX, TXT, or code files."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        text_parts = []
        reader = pypdf.PdfReader(file_path)
        for page_idx, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(f"--- Page {page_idx} ---\n{page_text}")
        return "\n".join(text_parts)

    if ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    if ext in [".txt", ".md", ".py", ".cpp", ".hpp", ".c", ".h", ".java", ".js", ".ts", ".json", ".xml", ".html", ".csv"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        raise ValueError(f"Unsupported file format '{ext}' for file {file_path}: {e}") from e


def extract_submission_content(path: str) -> Tuple[str, Dict[str, str]]:
    """
    Extract text and source code files from a submission path (file, directory, or .zip).
    Returns: (submission_text, code_files_dict)
    """
    code_files: Dict[str, str] = {}
    general_text_parts: List[str] = []

    if os.path.isfile(path) and path.lower().endswith(".zip"):
        with zipfile.ZipFile(path, "r") as z:
            for zip_info in z.infolist():
                if zip_info.is_dir():
                    continue
                filename = zip_info.filename
                if _should_skip_path(filename):
                    continue
                ext = os.path.splitext(filename)[1].lower()
                try:
                    content = z.read(zip_info).decode("utf-8", errors="ignore")
                    if ext in CODE_EXTENSIONS:
                        code_files[filename] = content
                    else:
                        general_text_parts.append(f"--- FILE: {filename} ---\n{content}")
                except Exception:
                    pass
        submission_text = "\n".join(general_text_parts) or f"ZIP submission containing {len(code_files)} code files."
        return submission_text, code_files

    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d.lower() not in SKIP_PATH_SEGMENTS]
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, path)
                if _should_skip_path(rel_path):
                    continue
                ext = os.path.splitext(file)[1].lower()
                try:
                    content = extract_text_from_file(full_path)
                    if ext in CODE_EXTENSIONS:
                        code_files[rel_path] = content
                    else:
                        general_text_parts.append(f"--- FILE: {rel_path} ---\n{content}")
                except Exception:
                    pass
        submission_text = "\n".join(general_text_parts) or f"Directory submission containing {len(code_files)} files."
        return submission_text, code_files

    if os.path.isfile(path):
        ext = os.path.splitext(path)[1].lower()
        content = extract_text_from_file(path)
        if ext in CODE_EXTENSIONS:
            code_files[os.path.basename(path)] = content
            submission_text = f"Single source code file submission: {os.path.basename(path)}"
        else:
            submission_text = content
        return submission_text, code_files

    raise FileNotFoundError(f"Submission path '{path}' does not exist.")


def prepare_submission_for_grading(
    submission_text: str = "",
    code_files: Dict[str, str] | None = None,
) -> Tuple[str, Dict[str, str], List[str]]:
    """
    Normalize submission input before grading.
    Backend should call this (via AIService) after file extraction.
    Returns: (submission_text, code_files, warnings)
    """
    warnings: List[str] = []
    text = (submission_text or "").strip()
    files = dict(code_files or {})

    if not text and not any(v.strip() for v in files.values()):
        return text, files, warnings

    empty_files = [name for name, content in files.items() if not content.strip()]
    for name in empty_files:
        del files[name]
        warnings.append(f"Removed empty code file '{name}' from submission.")

    return text, files, warnings
