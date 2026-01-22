from main import app
import sys
from pathlib import Path

# Add the triage-service/src directory to the Python path
backend_dir = Path(__file__).parent
triage_src_dir = backend_dir / "triage-service" / "src"
sys.path.append(str(triage_src_dir))

# Import the app from main.py in the triage-service/src directory
# Renamed root entry point to entry.py to avoid shadowing triage-service.src.main

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("entry:app", host="0.0.0.0", port=8000, reload=True)
