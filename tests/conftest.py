"""Shared fixtures for exocortex-cli tests."""

import sys
from pathlib import Path

import pytest

# Make sure the src package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def tmp_dir(tmp_path):
    """Provide a clean temporary directory."""
    return tmp_path


@pytest.fixture
def mock_config_dir(tmp_path, monkeypatch):
    """Redirect config dir to a temp dir so tests don't touch real config."""
    config_dir = tmp_path / "exocortex"
    config_dir.mkdir(parents=True, exist_ok=True)
    import exocortex.config as config_mod
    monkeypatch.setattr(config_mod, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config_mod, "CONFIG_FILE", config_dir / "config.toml")
    # Also patch profiles file path
    import exocortex.profiles as profiles_mod
    monkeypatch.setattr(profiles_mod, "PROFILES_FILE", config_dir / "profiles.toml")
    return config_dir


@pytest.fixture
def mock_env_files(tmp_path, monkeypatch):
    """Redirect key lookups to temp .env files."""
    import exocortex.keys as keys_mod
    profile_env = tmp_path / "profile_env"
    profile_env.mkdir(parents=True, exist_ok=True)
    env_file = profile_env / ".env"
    monkeypatch.setattr(keys_mod, "PROFILE_ENV", env_file)
    monkeypatch.setattr(keys_mod, "GLOBAL_ENV", tmp_path / "global_env" / ".env")
    return env_file
