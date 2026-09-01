import os
import tempfile
import zipfile

from file_parser import extract_submission_content, _should_skip_path


def test_should_skip_path_common_junk_dirs():
    assert _should_skip_path("node_modules/lodash/index.js") is True
    assert _should_skip_path("project/venv/Lib/site-packages/foo.py") is True
    assert _should_skip_path("src/__pycache__/main.cpython-311.pyc") is True
    assert _should_skip_path(".git/objects/pack/pack-abc") is True
    assert _should_skip_path("src/main.py") is False
    assert _should_skip_path("Lab3/solution.cpp") is False


def test_zip_extraction_skips_node_modules_and_keeps_student_code():
    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, "submission.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("src/main.py", "def student_solution():\n    return 42\n")
            zf.writestr("node_modules/pkg/index.js", "module.exports = {};\n")
            zf.writestr("venv/lib/python3.11/site-packages/foo.py", "print('dep')\n")

        submission_text, code_files = extract_submission_content(zip_path)

        assert "src/main.py" in code_files
        assert "def student_solution" in code_files["src/main.py"]
        assert not any("node_modules" in path for path in code_files)
        assert not any("venv" in path for path in code_files)
        assert "node_modules" not in submission_text
        assert submission_text == "" or "node_modules" not in submission_text


def test_directory_extraction_skips_pycache():
    with tempfile.TemporaryDirectory() as tmp_dir:
        src_dir = os.path.join(tmp_dir, "src")
        cache_dir = os.path.join(src_dir, "__pycache__")
        os.makedirs(cache_dir)
        with open(os.path.join(src_dir, "app.py"), "w", encoding="utf-8") as f:
            f.write("print('hello')\n")
        with open(os.path.join(cache_dir, "app.cpython-311.pyc"), "w", encoding="utf-8") as f:
            f.write("bytecode\n")

        submission_text, code_files = extract_submission_content(tmp_dir)

        assert any(path.replace("\\", "/").endswith("src/app.py") for path in code_files)
        assert not any("__pycache__" in path.replace("\\", "/") for path in code_files)
