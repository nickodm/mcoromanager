"""
Submodule with the handlers for each command of the program.
"""

__all__ = ["init", "done", "name"]

from .init import main as init
from .done import main as done
from .name import main as name