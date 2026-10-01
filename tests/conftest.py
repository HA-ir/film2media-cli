import os
from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Helper fixture to read an offline fixture file by filename."""
    def _loader(filename: str) -> str:
        filepath = FIXTURES_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture file not found: {filepath}")
        return filepath.read_text(encoding="utf-8")
    return _loader


@pytest.fixture
def block_network(monkeypatch):
    """Safeguard fixture to ensure tests run completely offline."""
    import socket

    def _guarded_connect(*args, **kwargs):
        raise RuntimeError("Network access attempted during offline test execution!")

    monkeypatch.setattr(socket, "create_connection", _guarded_connect)
