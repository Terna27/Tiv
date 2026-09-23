"""Local development storage preparation and namespace management (Milestone 1).

Milestone 2 will implement the complete storage abstraction interface.
This module strictly handles directory creation and writability checks for localhost development.
"""

import os
from pathlib import Path
from typing import Dict, Any


STORAGE_NAMESPACES = ["raw/audio", "processed/audio", "quarantine", "exports/datasets"]


def ensure_local_storage_directories(base_path: str = ".storage") -> Dict[str, Any]:
    """Ensure local storage directories exist and are writable without creating production artifacts."""
    root = Path(base_path)
    created_dirs = []

    for ns in STORAGE_NAMESPACES:
        ns_path = root / ns
        ns_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(ns_path))

    # Verify writability with a temporary probe file
    probe_file = root / ".probe"
    is_writable = False
    try:
        probe_file.write_text("ok")
        if probe_file.read_text() == "ok":
            is_writable = True
        probe_file.unlink(missing_ok=True)
    except Exception:
        is_writable = False

    return {
        "backend": "local",
        "root_path": str(root.resolve()),
        "writable": is_writable,
        "namespaces": STORAGE_NAMESPACES,
    }
