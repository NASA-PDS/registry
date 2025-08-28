# -*- coding: utf-8 -*-
"""PDS Registry."""
import importlib.metadata
import pathlib


try:
    # Try to get version from package metadata first (preferred method)
    __version__ = importlib.metadata.version("pds.registry")
except importlib.metadata.PackageNotFoundError:
    # Fallback to reading from VERSION.txt file
    try:
        version_file = pathlib.Path(__file__).parent / "VERSION.txt"
        __version__ = version_file.read_text().strip()
    except OSError:
        __version__ = "unknown"


# For future consideration:
#
# - Other metadata (__docformat__, __copyright__, etc.)
# - N̶a̶m̶e̶s̶p̶a̶c̶e̶ ̶p̶a̶c̶k̶a̶g̶e̶s̶ we got this
