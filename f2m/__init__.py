"""
f2m package root.
Exports main CLI functions and variables for backward compatibility.
"""

__version__ = "1.1.0"
VERSION = __version__

# Re-export key legacy module members from root f2m.py if imported as `import f2m` or `from f2m import ...`
try:
    import sys
    from pathlib import Path
    root_dir = Path(__file__).resolve().parent.parent
    if str(root_dir) not in sys.path:
        sys.path.insert(0, str(root_dir))

    # Import legacy routines from f2m.py for backwards compatibility
    import importlib.util
    spec = importlib.util.spec_from_file_location("_f2m_legacy", root_dir / "f2m.py")
    if spec and spec.loader:
        _legacy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_legacy)
        clean_title = getattr(_legacy, "clean_title", None)
        parse_filename = getattr(_legacy, "parse_filename", None)
        parse_selection = getattr(_legacy, "parse_selection", None)
        parse_categories = getattr(_legacy, "parse_categories", None)
        parse_listing = getattr(_legacy, "parse_listing", None)
        parse_post = getattr(_legacy, "parse_post", None)
        main = getattr(_legacy, "main", None)
        cli = getattr(_legacy, "cli", None)
except Exception:
    pass
