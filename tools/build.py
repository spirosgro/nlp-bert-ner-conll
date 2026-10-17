"""Build from the grammar using one SHA-256-pinned ANTLR tool/runtime."""
from pathlib import Path
import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = "4.13.1"
SHA256 = "bc13a9c57a8dd7d5196888211e5ede657cb64a3ce968608697e4f668251a8487"
URL = f"https://www.antlr.org/download/antlr-{VERSION}-complete.jar"
ANTLR = ROOT / ".cache" / f"antlr-{VERSION}-complete.jar"
JAR = ROOT / "build" / "tabloid-compiler.jar"


def dependency(offline=False):
    if not ANTLR.exists():
        if offline:
            raise RuntimeError(f"Offline build requires the verified ANTLR JAR at {ANTLR}")
        ANTLR.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(URL, timeout=60) as response:
            content = response.read(10_000_001)
        if len(content) > 10_000_000 or hashlib.sha256(content).hexdigest() != SHA256:
            raise RuntimeError("Downloaded ANTLR JAR does not match the pinned SHA-256")
        with tempfile.NamedTemporaryFile(dir=ANTLR.parent, delete=False) as temporary:
            temporary.write(content)
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, ANTLR)
        finally:
            temporary_path.unlink(missing_ok=True)
    if hashlib.sha256(ANTLR.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError("Cached ANTLR JAR failed SHA-256 verification; inspect/remove it before rebuilding")
    return ANTLR


def build(offline=False):
    for command in ("java", "javac"):
        if shutil.which(command) is None:
            raise RuntimeError(f"{command} is missing; install a JDK 17+ and configure PATH")
    antlr = dependency(offline)
    JAR.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="compile-", dir=JAR.parent) as temporary:
        work = Path(temporary)
        generated, classes = work / "generated", work / "classes"
        generated.mkdir(); classes.mkdir()
        subprocess.run(["java", "-jar", str(antlr), "-visitor", "-no-listener", "-package", "tabloid.parser",
                        "-o", str(generated), "Tabloid.g4"], cwd=ROOT / "grammar", check=True, timeout=60)
        # Generator templates can trigger new JDK lint categories; keep strict lint on our code.
        generated_sources = sorted(generated.rglob("*.java"))
        subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-Xlint:none", "-cp", str(antlr),
                        "-d", str(classes), *map(str, generated_sources)], check=True, timeout=60)
        sources = sorted((ROOT / "src/main/java").rglob("*.java"))
        subprocess.run(["javac", "--release", "17", "-encoding", "UTF-8", "-Xlint:all", "-Werror", "-cp", str(antlr) + os.pathsep + str(classes),
                        "-d", str(classes), *map(str, sources)], check=True, timeout=60)
        staged = work / JAR.name
        with zipfile.ZipFile(staged, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("META-INF/MANIFEST.MF", f"Manifest-Version: 1.0\r\nMain-Class: tabloid.Main\r\nClass-Path: ../.cache/antlr-{VERSION}-complete.jar\r\n\r\n")
            for path in sorted(classes.rglob("*.class")):
                bundle.write(path, path.relative_to(classes).as_posix())
        os.replace(staged, JAR)
    print(f"Built {JAR.name}; ANTLR {VERSION}; Java 17 target. Generated sources stay out of Git.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Require a previously cached, verified ANTLR dependency")
    options = parser.parse_args()
    try:
        build(options.offline)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Build failed: {error}\n")
