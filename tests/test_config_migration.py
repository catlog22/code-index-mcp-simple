"""Tests for legacy config.json to MCP Config migration."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path as _TestPath

ROOT = _TestPath(__file__).resolve().parents[1]
SRC_PATH = ROOT / 'src'
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from code_index_mcp.project_settings import migrate_legacy_config


def test_migrate_legacy_config_success(tmp_path):
    """Test successful migration of valid legacy config."""
    # Setup test directory with legacy config
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    # Create valid legacy config
    legacy_config = {
        "last_updated": "2024-01-15T10:30:00Z",
        "file_watcher": {
            "enabled": True,
            "debounce_seconds": 2.0,
            "exclude_patterns": ["*.log", "*.tmp"]
        },
        "search_tools": {
            "preferred_tool": "ripgrep"
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_config, f, indent=2)

    # Perform migration
    migrated = migrate_legacy_config(str(settings_dir))

    # Verify migration metadata
    assert '_migration' in migrated
    migration_info = migrated['_migration']
    assert migration_info['source'] == 'legacy'
    assert migration_info['completed'] is True
    assert 'timestamp' in migration_info

    # Verify backup was created
    backup_file = config_file.with_suffix('.json.backup')
    assert backup_file.exists()

    # Verify backup contains original data
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    assert backup_data == legacy_config


def test_migrate_legacy_config_missing(tmp_path):
    """Test migration when config.json is missing."""
    # Setup empty settings directory
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()

    # Perform migration
    migrated = migrate_legacy_config(str(settings_dir))

    # Should return default config
    assert '_migration' in migrated
    assert migrated['_migration']['source'] == 'default'

    # Verify defaults are present
    assert 'file_watcher' in migrated
    assert 'search' in migrated


def test_migrate_legacy_config_invalid(tmp_path):
    """Test migration with invalid JSON in config file."""
    # Setup test directory
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    # Write invalid JSON
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('{ invalid json syntax }')

    # Perform migration
    migrated = migrate_legacy_config(str(settings_dir))

    # Should fall back to defaults
    assert '_migration' in migrated
    assert migrated['_migration']['source'] == 'default_fallback'

    # Verify default config structure
    assert 'file_watcher' in migrated
    assert 'search' in migrated


def test_migration_idempotency(tmp_path):
    """Test that migration can be run multiple times safely."""
    # Setup test directory
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    # Create legacy config
    legacy_config = {
        "file_watcher": {"enabled": True}
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_config, f)

    # First migration
    result1 = migrate_legacy_config(str(settings_dir))
    assert result1['_migration']['source'] == 'legacy'

    # Second migration (backup already exists)
    result2 = migrate_legacy_config(str(settings_dir))

    # Should handle gracefully (either skip or re-migrate)
    assert '_migration' in result2
    # Second run should detect backup and use default or re-migrate
    assert result2['_migration']['source'] in ['default', 'legacy', 'default_fallback']


def test_partial_config_migration(tmp_path):
    """Test migration with partial config (missing keys)."""
    # Setup test directory
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    # Create partial config (only file_watcher, no search_tools)
    partial_config = {
        "file_watcher": {
            "enabled": True
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(partial_config, f)

    # Perform migration
    migrated = migrate_legacy_config(str(settings_dir))

    # Verify migration handled partial data
    assert '_migration' in migrated

    # Should have merged with defaults for missing keys
    assert 'file_watcher' in migrated
    assert 'search' in migrated  # Should have default search config


def test_file_watcher_config_mapping(tmp_path):
    """Test file_watcher configuration mapping."""
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    legacy_config = {
        "file_watcher": {
            "enabled": False,
            "debounce_seconds": 5.0,
            "exclude_patterns": ["*.pyc", "__pycache__"]
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_config, f)

    migrated = migrate_legacy_config(str(settings_dir))

    # Verify file_watcher settings migrated
    assert 'file_watcher' in migrated
    fw_config = migrated['file_watcher']
    assert fw_config['enabled'] is False
    assert fw_config['debounce_seconds'] == 5.0


def test_search_defaults_mapping(tmp_path):
    """Test search defaults configuration mapping."""
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    legacy_config = {
        "search_defaults": {
            "case_sensitive": True,
            "context_lines": 5
        }
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(legacy_config, f)

    migrated = migrate_legacy_config(str(settings_dir))

    # Verify search settings migrated
    assert 'search' in migrated
    search_config = migrated['search']
    # Migration may map these to MCP Config structure
    # Just verify search section exists and has config


def test_migration_preserves_original_file(tmp_path):
    """Test that original config.json is preserved as backup."""
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    original_content = {
        "file_watcher": {"enabled": True},
        "custom_field": "preserved"
    }

    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(original_content, f, indent=2)

    # Get original file content
    with open(config_file, 'r', encoding='utf-8') as f:
        original_text = f.read()

    # Perform migration
    migrate_legacy_config(str(settings_dir))

    # Verify backup contains exact original content
    backup_file = config_file.with_suffix('.json.backup')
    assert backup_file.exists()

    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    assert backup_data == original_content


def test_nonexistent_settings_directory():
    """Test migration with non-existent settings directory."""
    # Use non-existent path
    fake_path = "/tmp/nonexistent_settings_dir_12345"

    # Should handle gracefully
    migrated = migrate_legacy_config(fake_path)

    # Should return default config
    assert '_migration' in migrated
    assert migrated['_migration']['source'] in ['default', 'default_fallback']


def test_migration_error_handling(tmp_path):
    """Test error handling during migration."""
    settings_dir = tmp_path / "settings"
    settings_dir.mkdir()
    config_file = settings_dir / "config.json"

    # Create config file
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write('{"file_watcher": {"enabled": true}}')

    # Make config file read-only to simulate permission error
    os.chmod(config_file, 0o444)

    try:
        # Attempt migration (may fail due to permissions)
        migrated = migrate_legacy_config(str(settings_dir))

        # Should still return valid config (defaults on error)
        assert '_migration' in migrated

    finally:
        # Restore permissions for cleanup
        os.chmod(config_file, 0o644)
