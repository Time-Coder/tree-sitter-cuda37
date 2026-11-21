"""Build one abi3 wheel per architecture, plus the sdist.

The grammar is compiled from the ABI-13 `src/parser.c` plus the external
scanner, and the extension targets the **limited API**
(`Py_LIMITED_API=0x03070000`), so one wheel per architecture serves every
CPython from 3.7 up -- `cp37-abi3-win_amd64`, not one wheel per interpreter.

This script used to run `bdist_wheel` on all eighteen interpreters and produced
eighteen per-version wheels. The tag now comes from
`options={"bdist_wheel": {"py_limited_api": "cp37"}}` in `setup.py`, so the
matrix is two builds and the artefact count is two wheels, not eighteen.

Building with the 3.7 interpreter is deliberate: it proves the limited-API floor
rather than assuming it.
"""

import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))

# (interpreter, builds the sdist too). One entry per architecture.
INTERPRETERS = [
    (r"D:\Python\37\python.exe", True),
    (r"D:\Python\37-32\python.exe", False),
]


def main() -> int:
    dist = os.path.join(ROOT, "dist")
    shutil.rmtree(dist, ignore_errors=True)
    shutil.rmtree(os.path.join(ROOT, "build"), ignore_errors=True)
    os.makedirs(dist, exist_ok=True)

    failures = []
    for python, with_sdist in INTERPRETERS:
        if not os.path.exists(python):
            failures.append((python, "missing interpreter"))
            continue
        commands = ["bdist_wheel", "--dist-dir", dist]
        if with_sdist:
            commands = ["sdist", "--dist-dir", dist] + commands
        # A stale build/ directory would leak objects compiled for the previous
        # architecture into this wheel, so it is removed before every build.
        shutil.rmtree(os.path.join(ROOT, "build"), ignore_errors=True)
        result = subprocess.run(
            [python, "setup.py"] + commands,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.returncode != 0:
            tail = result.stdout.decode("utf-8", "replace").strip().splitlines()[-6:]
            failures.append((python, "\n".join(tail)))
            print("FAILED:", python)
        else:
            print("ok:", python)

    artifacts = sorted(f for f in os.listdir(dist) if f.endswith((".whl", ".tar.gz")))
    print("\n=== %d artifacts ===" % len(artifacts))
    for name in artifacts:
        print(name)

    # Each architecture must have produced exactly one abi3 wheel. A wheel named
    # cpXXX-cpXXX means the limited-API option stopped taking effect, which would
    # quietly rebuild the eighteen-wheel matrix this replaced.
    wheels = [f for f in artifacts if f.endswith(".whl")]
    bad = [f for f in wheels if "-abi3-" not in f]
    if bad:
        failures.append(("dist/", "not abi3: %s" % ", ".join(bad)))
    if len(wheels) != len(INTERPRETERS):
        failures.append(("dist/", "%d wheels for %d architectures" % (len(wheels), len(INTERPRETERS))))

    if failures:
        print("\n=== failures ===")
        for python, message in failures:
            print(python, "->", message)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
