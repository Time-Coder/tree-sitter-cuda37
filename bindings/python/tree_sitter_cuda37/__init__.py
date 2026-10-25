"""CUDA grammar for tree-sitter (Python 3.7 compatible build).

``language()`` returns a native ``tree_sitter.Language`` object that is
compatible with both the legacy tree-sitter 0.20.x line (the last line that
ships CPython 3.7+ wheels, requiring the two-argument ``Language(path, name)``
constructor) and the modern tree-sitter 0.21+ line (``Language(capsule)``).
"""

import tree_sitter


def _library():
    """Resolve the shared-extension file backing this package."""
    from . import _binding

    return _binding.__file__


def language():
    """Return a tree-sitter Language object for CUDA.

    On the legacy tree-sitter 0.20.x line the grammar capsule is not used;
    instead the shared extension is loaded directly through ``ctypes`` using the
    two-argument ``tree_sitter.Language(library_path, name)`` constructor, which
    looks up the exported ``tree_sitter_cuda`` symbol. On the modern line the
    ``_binding`` module returns a ``PyCapsule`` that ``tree_sitter.Language``
    wraps. Both paths yield the same native ``tree_sitter.Language`` so callers
    can hand it to a ``tree_sitter.Parser`` regardless of the installed
    tree-sitter version.
    """
    try:
        # Modern path: _binding.language() returns a PyCapsule.
        from ._binding import language as _lang_capsule
    except AttributeError:  # pragma: no cover - defensive
        _lang_capsule = None

    if _lang_capsule is not None:
        # 0.21+ wraps the capsule with Language(capsule).
        try:
            return tree_sitter.Language(_lang_capsule())
        except (TypeError, ValueError):
            pass

    # Legacy path: tree-sitter 0.20.x Language(library_path, name) loads the
    # dynamic library and looks up the tree_sitter_cuda symbol.
    lib = _library()
    return tree_sitter.Language(lib, "cuda")