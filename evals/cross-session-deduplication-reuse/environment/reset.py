"""Restore only the disposable task workspace; tool state lives outside /app."""

from pathlib import Path
import shutil

workspace = Path("/app")
if workspace.is_symlink() or workspace.resolve() != Path("/app"):
    raise RuntimeError("unexpected workspace")
workspace.mkdir(exist_ok=True)
for entry in workspace.iterdir():
    if entry.is_dir() and not entry.is_symlink():
        shutil.rmtree(entry)
    else:
        entry.unlink()
shutil.copytree("/opt/task/baseline", workspace, dirs_exist_ok=True)
shutil.chown(workspace, user="agent", group="agent")
for entry in workspace.rglob("*"):
    shutil.chown(entry, user="agent", group="agent")
