"""Add the telegram-support-bot package root to sys.path so tests can import db.queries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "examples" / "telegram-support-bot"))
