"""Load one repo's abi3 wheels on every CPython 3.7-3.15, both architectures.

Usage: python C:/path/to/verify_abi3.py <repo> <module> <distribution> <dist-dir>

The point is the claim the abi3 tag makes: one wheel per platform, installable
on every interpreter from 3.7 up. A tag that nothing exercises is a guess, so
each interpreter is asked to import the grammar and parse a snippet.

Python 3.8's bundled pip cannot reach PyPI on this machine (its vendored urllib3
fails TLS with "check_hostname requires server_hostname"), so when the pip path
fails and the interpreter already has tree-sitter, the wheel is unpacked onto
PYTHONPATH instead. That still exercises the compiled extension, which is the
thing under test.
"""

import glob
import os
import shutil
import subprocess
import sys
import zipfile

VERSIONS = ["37", "38", "39", "310", "311", "312", "313", "314", "315"]
ARCHES = [("win_amd64", ""), ("win32", "-32")]

# A kernel that exercises the qualifiers and a vector type, so the parse does
# more than prove the module loaded.
SNIPPET = {
    "tree_sitter_opencl": b"__kernel void k(__global const float4* x){ float4 v = x[0]; }",
    "tree_sitter_cuda37": b"__global__ void k(const float* x){ float v = x[0]; }",
    "tree_sitter_metal": b"kernel void k(device const float* x [[buffer(0)]]){ float v = x[0]; }",
}


def check_source(module: str) -> str:
    return (
        "import sys, struct, tree_sitter as ts, %(m)s as g;"
        "l = g.language();"
        "p = ts.Parser() if hasattr(ts.Parser, 'set_language') else ts.Parser(l);"
        "p.set_language(l) if hasattr(ts.Parser, 'set_language') else None;"
        "t = p.parse(%(src)r);"
        "assert t.root_node.has_error == False, 'parse error';"
        "print(sys.version.split()[0], struct.calcsize('P')*8, 'bits', 'v'+g.__version__)"
        % {"m": module, "src": SNIPPET[module]}
    )


def wheel_for(dist: str, arch: str) -> str | None:
    matches = glob.glob(os.path.join(dist, "*-abi3-%s.whl" % arch))
    if not matches:
        return None

    def version_key(path: str) -> tuple:
        name = os.path.basename(path)
        version = name.split("-", 1)[1].rsplit("-", 3)[0]
        return tuple(int(p) for p in version.split(".") if p.isdigit())

    return sorted(matches, key=version_key)[-1]


def main() -> int:
    repo, module, distribution, dist = sys.argv[1:5]
    code = check_source(module)
    workdir = os.path.join(repo, "build", "abi3-verify")
    shutil.rmtree(workdir, ignore_errors=True)
    os.makedirs(workdir)
    failures = []

    for arch, suffix in ARCHES:
        wheel = wheel_for(dist, arch)
        if wheel is None:
            failures.append((arch, "no abi3 wheel"))
            continue
        print("=== %s -> %s ===" % (arch, os.path.basename(wheel)))

        for version in VERSIONS:
            interpreter = r"D:\Python\%s%s\python.exe" % (version, suffix)
            if not os.path.exists(interpreter):
                failures.append((interpreter, "missing interpreter"))
                continue

            venv = os.path.join(workdir, "%s-v%s" % (arch, version))
            subprocess.check_call([interpreter, "-m", "venv", venv])
            python = os.path.join(venv, "Scripts", "python.exe")

            pin = "tree-sitter==0.20.4" if version == "37" else "tree-sitter>=0.23"
            installed = subprocess.run(
                [python, "-m", "pip", "install", "--quiet",
                 "--disable-pip-version-check", pin],
                capture_output=True, text=True,
            )

            pythonpath = None
            if installed.returncode != 0:
                already = subprocess.run([interpreter, "-c", "import tree_sitter"],
                                         capture_output=True, text=True)
                if already.returncode != 0:
                    failures.append((interpreter, installed.stderr.strip()[-200:]))
                    continue
                print("    (pip unusable; using the interpreter directly)")
                python = interpreter
                pythonpath = os.path.join(workdir, "unpacked-%s" % arch)
                shutil.rmtree(pythonpath, ignore_errors=True)
                os.makedirs(pythonpath)
                with zipfile.ZipFile(wheel) as archive:
                    archive.extractall(pythonpath)
            else:
                installed = subprocess.run(
                    [python, "-m", "pip", "install", "--quiet",
                     "--disable-pip-version-check", "--force-reinstall",
                     "--no-deps", wheel],
                    capture_output=True, text=True,
                )
                if installed.returncode != 0:
                    failures.append((interpreter, installed.stderr.strip()[-200:]))
                    continue

            environment = dict(os.environ)
            if pythonpath:
                environment["PYTHONPATH"] = pythonpath
            result = subprocess.run([python, "-c", code], capture_output=True,
                                    text=True, env=environment)
            if result.returncode != 0:
                failures.append((interpreter, (result.stderr or result.stdout).strip()[-200:]))
                print("  %-34s FAIL" % interpreter)
            else:
                print("  ok  %-34s %s" % (interpreter, result.stdout.strip()))

    if failures:
        print("\n=== failures ===")
        for interpreter, message in failures:
            print(interpreter, "->", message)
        return 1
    print("\nevery interpreter loaded the same wheel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
