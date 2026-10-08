import pytest
from unittest.mock import patch, MagicMock
from app.core.config import settings

@pytest.fixture
def mock_settings():
    with patch("scripts.backfill_doctypes.settings") as mock:
        yield mock

def test_backfill_cowardly_refuses_non_sqlite(mock_settings, monkeypatch):
    mock_settings.database_url = "postgresql://user:pass@localhost/db"
    
    with patch("sys.argv", ["backfill_doctypes.py"]):
        from scripts.backfill_doctypes import main
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code == 1

def test_backfill_runs_on_sqlite(mock_settings, monkeypatch):
    mock_settings.database_url = "sqlite:///test.db"
    
    with patch("sys.argv", ["backfill_doctypes.py"]):
        from scripts.backfill_doctypes import main
        with patch("scripts.backfill_doctypes.backfill_doctypes") as mock_backfill:
            main()
            mock_backfill.assert_called_once()
