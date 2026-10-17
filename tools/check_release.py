"""Offline checks for the intended source upload; not a comprehensive security scan."""
from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".cache", "build", "out", "__pycache__", ".idea", ".vscode"}
REQUIRED = ["README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "SECURITY.md", "CITATION.cff",
            ".gitignore", ".gitattributes", ".github/workflows/test.yml", "grammar/Tabloid.g4",
            "src/main/java/tabloid/Main.java", "src/main/java/tabloid/PythonEmitter.java",
            "tools/build.py", "tools/tabloid.py", "tests/test_compiler.py",
            "docs/language.md", "docs/architecture.md", "docs/provenance.md",
            "docs/verification.md", "docs/github-upload.md", "examples/README.md"]


def public_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and not any(part in SKIP for part in path.relative_to(ROOT).parts):
            yield path


def main():
    errors = []
    for required in REQUIRED:
        if not (ROOT / required).is_file():
            errors.append(f"Missing required file: {required}")
    paths = list(public_files())
    for path in paths:
        relative = path.relative_to(ROOT)
        if path.suffix.lower() in {".jar", ".class", ".tokens", ".interp", ".pyc", ".zip", ".pdf", ".docx"}:
            errors.append(f"Unexpected artifact: {relative}")
            continue
        content = path.read_text(encoding="utf-8")
        if re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", content):
            errors.append(f"Greek text in the English source release: {relative}")
        if re.search(r"[A-Za-z]:[\\/]Users[\\/]", content):
            errors.append(f"Personal local path: {relative}")
        if re.search("icsd" + r"\d{5,}", content, re.I):
            errors.append(f"Student identifier: {relative}")
        if path.suffix == ".py":
            ast.parse(content, filename=str(relative))
        if path.suffix == ".md":
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                if target.startswith(("https://", "http://", "#", "mailto:")):
                    continue
                destination = (path.parent / target.split("#", 1)[0]).resolve()
                if not destination.is_relative_to(ROOT) or not destination.exists():
                    errors.append(f"Broken local link in {relative}: {target}")
    examples = sorted((ROOT / "examples").glob("*.tbd"))
    if len(examples) != 6:
        errors.append("Expected six documented source examples")
    for source in examples:
        if not (ROOT / "examples/expected" / (source.stem + ".py")).is_file():
            errors.append(f"Missing reference Python: {source.name}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(paths)} public files, Python syntax, local links and six source/output example pairs.")
    print("Generated parsers and dependency binaries are excluded; this check does not replace the compiler test suite.")


if __name__ == "__main__":
    main()
