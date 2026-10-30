"""Stage application files without uploading local tooling or virtualenvs."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent
target = root / ".worker-src"
for relative in ["worker.py", "app.py", "08_Runtime/runtime_control.py"]:
    destination = target / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, destination)
for source in (root / "13_Implementation").glob("*.md"):
    destination = target / "13_Implementation" / source.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
