"""Invoke the already-built compiler without executing generated Python."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import dependency, JAR

if __name__ == "__main__":
    try:
        dependency(offline=True)
        if not JAR.is_file():
            raise RuntimeError("Compiler is not built; run python tools/build.py first")
        raise SystemExit(subprocess.call(["java", "-jar", str(JAR), *sys.argv[1:]]))
    except (OSError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2)
