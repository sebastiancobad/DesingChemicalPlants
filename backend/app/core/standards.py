"""
ChemScale — Standards Reference Decorator.

Attaches industry standard references to calculation functions so that
every result can be traced back to its normative source.
"""

from __future__ import annotations

import functools
from typing import Callable


def standards_ref(*references: str) -> Callable:
    """Decorator that attaches standards references to a calculation function.

    Usage::

        @standards_ref("API 520 Part I, §4.3.2", "ASME Sec VIII Div 1, UG-125")
        def size_gas_psv(...) -> PSVResult:
            ...

    The references are stored on ``func.__standards_refs__`` and are
    automatically collected into the calculation audit trail.
    """

    def decorator(func: Callable) -> Callable:
        func.__standards_refs__ = list(references)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__standards_refs__ = func.__standards_refs__
        return wrapper

    return decorator


def get_standards_refs(func: Callable) -> list[str]:
    """Retrieve the standards references attached to a function."""
    return getattr(func, "__standards_refs__", [])
