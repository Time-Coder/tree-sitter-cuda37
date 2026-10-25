from __future__ import annotations

from os import name, path
from sysconfig import get_config_var

from setuptools import Extension, find_packages, setup
from setuptools.command.build import build
from setuptools.command.egg_info import egg_info
from wheel.bdist_wheel import bdist_wheel

sources = [
    "bindings/python/tree_sitter_cuda37/binding.c",
    "src/parser.c",
]
if path.exists("src/scanner.c"):
    sources.append("src/scanner.c")

macros = [
    ("PY_SSIZE_T_CLEAN", None),
    ("TREE_SITTER_HIDE_SYMBOLS", None),
]
limited_api = not get_config_var("Py_GIL_DISABLED")
if limited_api:
    # The limited API floor is set to 3.7 (0x03070000) so the built abi3 wheel
    # works on every Python from 3.7 upward, matching the grammar's ABI-13
    # parser that tree-sitter 0.20.x (the last line shipping 3.7 wheels) consumes.
    macros.append(("Py_LIMITED_API", "0x03070000"))

if name != "nt":
    cflags = ["-std=c11", "-fvisibility=hidden"]
else:
    cflags = ["/std:c11", "/utf-8"]


class Build(build):
    def run(self):
        if path.isdir("queries"):
            dest = path.join(self.build_lib, "tree_sitter_cuda37", "queries")
            self.copy_tree("queries", dest)
        super().run()


class BdistWheel(bdist_wheel):
    def get_tag(self):
        python, abi, platform = super().get_tag()
        if python.startswith("cp"):
            python, abi = "cp37", "abi3"
        return python, abi, platform


class EggInfo(egg_info):
    def find_sources(self):
        super().find_sources()
        self.filelist.recursive_include("queries", "*.scm")
        self.filelist.include("src/tree_sitter/*.h")


setup(
    packages=find_packages("bindings/python"),
    package_dir={"": "bindings/python"},
    package_data={
        "tree_sitter_cuda37": ["*.pyi", "py.typed"],
        "tree_sitter_cuda37.queries": ["*.scm"],
    },
    ext_package="tree_sitter_cuda37",
    ext_modules=[
        Extension(
            name="_binding",
            sources=sources,
            extra_compile_args=cflags,
            define_macros=macros,
            include_dirs=["src"],
            py_limited_api=limited_api,
        )
    ],
    cmdclass={
        "build": Build,
        "bdist_wheel": BdistWheel,
        "egg_info": EggInfo,
    },
    zip_safe=False,
)