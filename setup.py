"""Build the tree-sitter-cuda37 extension.

Only the Extension lives here. Every piece of *metadata* -- name, version,
readme, dependencies, classifiers, package discovery, package data -- is in
``pyproject.toml``, which is the single source for all of it. The version is not
spelled here either: the toml reads it out of ``tree_sitter_cuda37/__init__.py``
with ``attr``, and setuptools parses that with an AST reader rather than
importing the package (which would fail: it needs ``_binding``, the very
extension this file builds).

Why the Extension cannot move into pyproject.toml as well: the declarative
``[[tool.setuptools.ext-modules]]`` table arrived in setuptools 74, and
setuptools 68 is the last release that installs on Python 3.7 -- an interpreter
this package exists for. Declaring the extension in the toml would either drop
3.7 or make every 3.7 build fail with "``tool.setuptools`` must not contain
{'ext-modules'}".

Two things are specific to this grammar. It has an **external scanner**
(``src/scanner.c``), which is added to the sources only when it exists so the
same file builds a grammar without one. And the scanner's own header
(``src/scanner.h``) plus ``src/tree_sitter/*.h`` are needed by the sdist, which
patching ``egg_info`` arranges -- setuptools' default file list carries only
the ``.c`` files, so a source install would otherwise fail looking for a header.
"""

from os import name as os_name
from os.path import exists, isdir, join
from sysconfig import get_config_var

from setuptools import Extension, setup
from setuptools.command.build import build
from setuptools.command.egg_info import egg_info

# `wheel` backs only bdist_wheel. This module is also imported for sdist,
# egg_info and a plain source install, none of which a bare venv can satisfy.
try:
    from wheel.bdist_wheel import bdist_wheel  # noqa: F401  (registers the command)
except ImportError:  # pragma: no cover - a build without wheel cannot bdist_wheel
    bdist_wheel = None

C_PACKAGE = "tree_sitter_cuda37"

sources = [
    "bindings/python/tree_sitter_cuda37/binding.c",
    "src/parser.c",
]
# The scanner is optional: a grammar either has one or it does not, and the same
# setup.py has to build both. It must be listed *after* parser.c, because the
# generated parser calls into it.
if exists("src/scanner.c"):
    sources.append("src/scanner.c")

define_macros = [
    ("PY_SSIZE_T_CLEAN", None),
    ("TREE_SITTER_HIDE_SYMBOLS", None),
]

# The limited API floor is 3.7 (0x03070000) so one abi3 wheel works on every
# CPython from 3.7 upward, matching the grammar's ABI-13 parser that
# tree-sitter 0.20.x (the last line shipping 3.7 wheels) consumes.
#
# A free-threaded build cannot target the limited API, so the macro is omitted
# there. That interpreter gets a version-specific wheel, which is correct: its
# ABI is genuinely different.
limited_api = not get_config_var("Py_GIL_DISABLED")
if limited_api:
    define_macros.append(("Py_LIMITED_API", "0x03070000"))


class Build(build):
    """Copy the query files next to the package.

    `queries/` sits at the repository root, outside `bindings/python`, so
    package-data cannot find it -- its source path is not inside the package
    directory. Copying it into the built package is the only way it ships.
    """

    def run(self):
        if isdir("queries"):
            destination = join(self.build_lib, C_PACKAGE, "queries")
            self.copy_tree("queries", destination)
        super().run()


class EggInfo(egg_info):
    """Widen the sdist file list to the generated headers and the scanner.

    setuptools' default includes only the `.c` files, so an sdist built without
    this shipped `parser.c` and no `parser.h`; `pip install` from it then failed
    with "tree_sitter/parser.h: No such file or directory". The scanner's header
    is the same problem one level down.
    """

    def find_sources(self):
        super().find_sources()
        self.filelist.recursive_include("queries", "*.scm")
        self.filelist.recursive_include("src", "*.h")


setup(
    ext_package=C_PACKAGE,
    ext_modules=[
        Extension(
            name="_binding",
            sources=sources,
            extra_compile_args=(
                # `/std:c11` for MSVC, which rejects the C11 syntax the generated
                # parser uses without it; `-std=c11` plus hidden symbols elsewhere.
                ["/std:c11", "/utf-8"] if os_name == "nt" else ["-std=c11", "-fvisibility=hidden"]
            ),
            define_macros=define_macros,
            include_dirs=["src"],
            py_limited_api=limited_api,
        )
    ],
    # The abi3 *tag* comes from this option, not from `py_limited_api` alone:
    # `py_limited_api=True` only changes how the extension is built, and a plain
    # `bdist_wheel` would still tag the wheel cp37-cp37m. Set here so every build
    # front end produces abi3 without being told to, which is what makes the
    # wheel count one per platform instead of one per interpreter.
    options={"bdist_wheel": {"py_limited_api": "cp37"}},
    cmdclass={"build": Build, "egg_info": EggInfo},
)
