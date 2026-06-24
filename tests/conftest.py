import os
from pathlib import Path
from dotenv import load_dotenv

# Load the environment variables from app/.env before running tests
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / "app" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
