import sys
import importlib.util
from pathlib import Path

# Target: f:\Courses\Hamza\Hackathon-3\backend\triage-service\src\main.py
backend_dir = Path(__file__).parent
triage_main_path = backend_dir / "triage-service" / "src" / "main.py"

if not triage_main_path.exists():
    raise FileNotFoundError(
        f"Could not find triage service at {triage_main_path}")

# Add the src directory to sys.path so the module's internal imports work
triage_src_dir = triage_main_path.parent
if str(triage_src_dir) not in sys.path:
    sys.path.insert(0, str(triage_src_dir))

# Load the module using its absolute path to avoid shadowing "main"
spec = importlib.util.spec_from_file_location(
    "triage_service_main", str(triage_main_path))
triage_service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(triage_service)

# Expose the app object for uvicorn
app = triage_service.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
