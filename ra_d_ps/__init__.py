"""
ra_d_ps package wrapper.

This module re-exports the public API from existing top-level modules (e.g. XMLPARSE)
so callers can import from `ra_d_ps` while existing `from XMLPARSE import ...` calls still work.
"""

# Re-export common public symbols from XMLPARSE if available.
try:
    from XMLPARSE import *  # type: ignore
except Exception:
    # If XMLPARSE is not importable for some reason, expose a minimal placeholder.
    __all__ = []
