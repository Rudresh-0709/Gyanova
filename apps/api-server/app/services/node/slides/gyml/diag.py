import os
import sys
from pathlib import Path

print(f"Current Working Directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not Set')}")
print(f"sys.path: {sys.path}")

# Try to find the root
root = Path("d:/DATA/Desktop/AI_TUTOR/ai-teacher-app")
print(f"Root exists: {root.exists()}")

# Try to list apps
apps_dir = root / "apps"
if apps_dir.exists():
    print(f"Apps dir: {[p.name for p in apps_dir.iterdir() if p.is_dir()]}")
else:
    print("Apps dir not found at root.")

# Try import
try:
    import apps.api_server.app.services.node.slides.gyml.definitions as definitions

    print("Import successful!")
except Exception as e:
    print(f"Import failed: {e}")
