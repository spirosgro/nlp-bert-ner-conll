"""Check public-source syntax, local documentation links and release contents offline."""
import ast
import json
from pathlib import Path
import re
from urllib.parse import unquote
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["README.md", "LICENSE", "CITATION.cff", "pyproject.toml", ".gitignore",
            ".github/workflows/test.yml", "docs/verification.md", "docs/github-upload.md",
            "docs/technical-report.md", "results/historical-results.json", "assets/pipeline.svg"]
SKIP_PARTS = {".git", ".venv", "__pycache__", "build", "dist", ".pytest_cache"}


def public_files():
    for path in sorted(ROOT.rglob("*")):
        if path.is_file() and not any(p in SKIP_PARTS or p.endswith(".egg-info") for p in path.relative_to(ROOT).parts):
            yield path


def main():
    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f"Missing required file: {name}")
    files = list(public_files())
    for path in files:
        relative = path.relative_to(ROOT)
        if relative.parts[0] == "runs" or relative.parts[:2] == ("data", "raw"):
            errors.append(f"Local experiment data in release: {relative}")
        if path.suffix.lower() in {".pt", ".pth", ".bin", ".safetensors", ".zip", ".docx", ".pdf"}:
            errors.append(f"Unexpected binary in this source release: {relative}")
        if path.suffix in {".py", ".md", ".json", ".toml", ".yml", ".cff", ".svg", ".conll"}:
            content = path.read_text(encoding="utf-8")
            if re.search(r"[\u0370-\u03ff\u1f00-\u1fff]", content):
                errors.append(f"Non-English Greek text: {relative}")
            if re.search(r"[A-Za-z]:[\\/]Users[\\/]", content):
                errors.append(f"Personal local path: {relative}")
            if re.search("icsd" + r"\d{5,}", content, re.I):
                errors.append(f"Student identifier: {relative}")
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
        elif path.suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        elif path.suffix == ".svg":
            ET.parse(path)
        elif path.suffix == ".md":
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                target_path = (path.parent / unquote(target.split("#", 1)[0])).resolve()
                if not target_path.is_relative_to(ROOT) or not target_path.exists():
                    errors.append(f"Broken or external local link in {relative}: {target}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"PASS: {len(files)} source files; required files, Python syntax, JSON/SVG, local Markdown links and publication checks.")
    print("This is a targeted packaging check, not a comprehensive secret or licensing audit.")


if __name__ == "__main__":
    main()
