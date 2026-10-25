tree-sitter-cuda37
==================

[![npm][npm]](https://www.npmjs.com/package/tree-sitter-cuda)
[![crates][crates]](https://crates.io/crates/tree-sitter-cuda)

Python 3.7 compatible build of the tree-sitter CUDA grammar. It differs from
the upstream `tree-sitter-cuda` in two ways:

- The generated C parser targets tree-sitter **ABI 13**, so it loads under the
  legacy tree-sitter 0.20.x line (the last line that ships CPython 3.7 wheels)
  as well as newer tree-sitter 0.21+.
- The Python `language()` returns a native `tree_sitter.Language` on both the
  legacy 0.20.x two-argument form and the 0.21+ capsule form, and the wheel is
  built with the limited API floor set to 3.7 (`cp37-abi3`).

It is a fork intended for projects (e.g. PyGPGPU) that must parse CUDA source
on Python 3.7. The grammar itself is identical to upstream.

This is a extension of [tree-sitter-cpp](https://github.com/tree-sitter/tree-sitter-cpp) to support
CUDA storage and function specifiers (`__shared__`, `__device__`) and its kernel call syntax.

[npm]: https://img.shields.io/npm/v/tree-sitter-cuda?logo=npm
[crates]: https://img.shields.io/crates/v/tree-sitter-cuda?logo=rust
