"""Client-aware installer helpers."""

from .cli import InstallResult, install
from .targets import Target

__all__ = ["InstallResult", "Target", "install"]
