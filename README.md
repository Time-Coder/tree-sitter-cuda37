tree-sitter-cuda37
==================

Python 3.7 compatible build of the tree-sitter CUDA grammar.

This is a fork of [tree-sitter-cuda](https://github.com/tree-sitter-grammars/tree-sitter-cuda)
by Stephan Seitz, which is itself an extension of
[tree-sitter-cpp](https://github.com/tree-sitter/tree-sitter-cpp) (and therefore
[tree-sitter-c](https://github.com/tree-sitter/tree-sitter-c)) supporting CUDA
storage and function specifiers (`__shared__`, `__device__`) and its kernel call
syntax. The grammar rules are unmodified; only the packaging and the generated
parser differ.

Differences from upstream `tree-sitter-cuda`:

- The generated C parser targets tree-sitter **ABI 13**, so it loads under the
  legacy tree-sitter 0.20.x line (the last line that ships CPython 3.7 wheels)
  as well as newer tree-sitter 0.21+.
- The Python `language()` returns a native `tree_sitter.Language` on both the
  legacy 0.20.x two-argument form and the 0.21+ capsule form.
- Wheels are published for CPython 3.7 through 3.15 on 64-bit and 32-bit
  Windows, each compiled against its target interpreter.

It exists so projects (e.g. [PyGPGPU](https://github.com/Time-Coder/PyGPGPU))
can parse CUDA source on Python 3.7, which the upstream distribution does not
support.

License
-------

MIT, identical to upstream. The original copyright notices are preserved
unchanged in [LICENSE](LICENSE):

```
Copyright (c) 2014 Max Brunsfield
Copyright (c) 2021 Stephan Seitz
```

The grammar, the generated parser and the query files originate from
tree-sitter-cuda, tree-sitter-cpp and tree-sitter-c, all released under the MIT
license. Only the build configuration, the Python binding wrapper and the
regenerated parser are new work in this fork.
