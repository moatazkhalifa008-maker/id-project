# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path

from plyer import camera

try:
    from android.storage import app_storage_path
except Exception:
    app_storage_path = None

try:
    from android.permissions import request_permissions, Permission, check_permission
except Exception:
    request_permissions = None
    Permission = None
    check_permission = None


def get_default_capture_dir() -> Path:
    if app_storage_path is not None:
        base = Path(app_storage_path())
    else:
        base = Path.cwd()
    path = base / 'captured_cards'
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_camera_permissions(on_ready, on_denied):
    if request_permissions is None or Permission is None or check_permission is None:
        on_ready()
        return
    needed = [Permission.CAMERA]
    if all(check_permission(p) for p in needed):
        on_ready()
        return

    def _callback(permissions, grants):
        granted = bool(grants) and all(bool(x) for x in grants)
        if granted:
            on_ready()
        else:
            on_denied()

    request_permissions(needed, _callback)


def take_picture(target_file: str, on_complete):
    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    def _done(path):
        try:
            normalized = path if path and os.path.exists(path) else None
        except Exception:
            normalized = None
        return on_complete(normalized)

    camera.take_picture(filename=str(target_path), on_complete=_done)
