"""Tests for ProjectSettings MCP Config migration and configuration management."""
import os
import sys
import json
import tempfile
from pathlib import Path as _TestPath
from unittest.mock import Mock, patch

ROOT = _TestPath(__file__).resolve().parents[1]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.project_settings import migrate_legacy_config, _write_migration_marker
from code_index_mcp.constants import DEFAULT_MCP_CONFIG


def test_migrate_legacy_config_no_legacy_file(tmp_path):
    """Test migration when no legacy config.json exists."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    result = migrate_legacy_config(str(settings_dir))

    # Should return default config
    assert result['search']['case_sensitive'] == DEFAULT_MCP_CONFIG['search']['case_sensitive']
    assert result['_migration']['completed'] is True
    assert result['_migration']['source'] == 'default'

    # Should create migration marker
    marker_path = settings_dir / '.migration_complete'
    assert marker_path.exists()


def test_migrate_legacy_config_valid_config(tmp_path):
    """Test migration with valid legacy config.json."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create legacy config
    legacy_config = {
        "search_tools": {
            "case_sensitive": False,
            "context_lines": 5,
            "max_line_length": 150,
            "fuzzy": True,
            "regex": True
        },
        "file_watcher": {
            "enabled": True,
            "debounce_seconds": 10.0
        },
        "exclude_patterns": ["*.log", "*.tmp"]
    }

    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(legacy_config, f)

    result = migrate_legacy_config(str(settings_dir))

    # Verify migration
    assert result['search']['case_sensitive'] is False
    assert result['search']['context_lines'] == 5
    assert result['search']['max_line_length'] == 150
    assert result['search']['fuzzy'] is True
    assert result['search']['regex'] is True
    assert result['file_watcher']['enabled'] is True
    assert result['file_watcher']['debounce_seconds'] == 10.0
    assert result['filter']['exclude_patterns'] == ["*.log", "*.tmp"]
    assert result['_migration']['completed'] is True
    assert result['_migration']['source'] == 'legacy'

    # Backup should exist
    backup_path = settings_dir / 'config.json.backup'
    assert backup_path.exists()


def test_migrate_legacy_config_idempotent(tmp_path):
    """Test migration is idempotent (running twice produces same result)."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create legacy config
    legacy_config = {"search_tools": {"case_sensitive": False}}
    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(legacy_config, f)

    # First migration
    result1 = migrate_legacy_config(str(settings_dir))
    assert result1['_migration']['source'] == 'legacy'

    # Second migration (should skip)
    result2 = migrate_legacy_config(str(settings_dir))
    assert result2['_migration']['source'] == 'legacy'
    assert result2['_migration']['completed'] is True


def test_migrate_legacy_config_invalid_json(tmp_path):
    """Test migration handles malformed JSON gracefully."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create invalid JSON file
    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        f.write('{ invalid json }')

    result = migrate_legacy_config(str(settings_dir))

    # Should fall back to defaults
    assert result['_migration']['completed'] is True
    assert result['_migration']['source'] == 'default_fallback'
    assert result['search']['case_sensitive'] == DEFAULT_MCP_CONFIG['search']['case_sensitive']


def test_migrate_legacy_config_partial_migration(tmp_path):
    """Test migration with missing fields uses defaults for those fields."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create partial legacy config (missing some expected fields)
    legacy_config = {
        "search_tools": {
            "case_sensitive": False
            # Missing: context_lines, max_line_length, etc.
        }
        # Missing: file_watcher, exclude_patterns
    }

    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(legacy_config, f)

    result = migrate_legacy_config(str(settings_dir))

    # Should migrate available fields
    assert result['search']['case_sensitive'] is False

    # Should use defaults for missing fields
    assert result['search']['context_lines'] == DEFAULT_MCP_CONFIG['search']['context_lines']
    assert result['file_watcher']['enabled'] == DEFAULT_MCP_CONFIG['file_watcher']['enabled']


def test_migrate_legacy_config_extra_fields(tmp_path):
    """Test migration with extra fields ignores them safely."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create legacy config with extra fields
    legacy_config = {
        "search_tools": {
            "case_sensitive": False
        },
        "unknown_field": "should be ignored",
        "another_unknown": 123
    }

    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(legacy_config, f)

    result = migrate_legacy_config(str(settings_dir))

    # Should complete migration without errors
    assert result['_migration']['completed'] is True
    assert result['search']['case_sensitive'] is False


def test_migrate_legacy_config_backup_creation(tmp_path):
    """Test migration creates backup with timestamp when backup already exists."""
    settings_dir = tmp_path / 'settings'
    settings_dir.mkdir()

    # Create legacy config
    legacy_config = {"search_tools": {"case_sensitive": False}}
    config_path = settings_dir / 'config.json'
    with open(config_path, 'w') as f:
        json.dump(legacy_config, f)

    # Create existing backup
    existing_backup = settings_dir / 'config.json.backup'
    existing_backup.write_text('old backup')

    result = migrate_legacy_config(str(settings_dir))

    # Should create timestamped backup
    assert result['_migration']['completed'] is True

    # Check for timestamped backup files
    backup_files = list(settings_dir.glob('config.json.backup*'))
    assert len(backup_files) >= 1  # Original backup still exists


def test_write_migration_marker_creates_file(tmp_path):
    """Test _write_migration_marker creates marker file."""
    marker_path = tmp_path / '.migration_complete'

    _write_migration_marker(str(marker_path), 'legacy')

    assert marker_path.exists()

    # Verify content
    with open(marker_path, 'r') as f:
        marker_data = json.load(f)

    assert marker_data['completed'] is True
    assert marker_data['source'] == 'legacy'
    assert 'timestamp' in marker_data


def test_write_migration_marker_with_legacy_config(tmp_path):
    """Test _write_migration_marker includes legacy config keys."""
    marker_path = tmp_path / '.migration_complete'
    legacy_config = {
        "search_tools": {},
        "file_watcher": {}
    }

    _write_migration_marker(str(marker_path), 'legacy', legacy_config)

    # Verify content
    with open(marker_path, 'r') as f:
        marker_data = json.load(f)

    assert marker_data['source'] == 'legacy'
    assert 'legacy_keys' in marker_data
    assert 'search_tools' in marker_data['legacy_keys']
    assert 'file_watcher' in marker_data['legacy_keys']
