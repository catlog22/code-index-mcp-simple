"""
Project Settings Management

This module provides functionality for managing project settings and persistent data
for the Code Index MCP server.
"""
import os
import json
import shutil
import logging
import tempfile
import hashlib
from typing import Dict, Any
from datetime import datetime


from .constants import (
    SETTINGS_DIR, CONFIG_FILE, INDEX_FILE, DEFAULT_MCP_CONFIG
)
from .search.base import SearchStrategy
from .search.ugrep import UgrepStrategy
from .search.ripgrep import RipgrepStrategy
from .search.ag import AgStrategy
from .search.grep import GrepStrategy
from .search.basic import BasicSearchStrategy


# Prioritized list of search strategies
SEARCH_STRATEGY_CLASSES = [
    UgrepStrategy,
    RipgrepStrategy,
    AgStrategy,
    GrepStrategy,
    BasicSearchStrategy,
]

# Logger for this module
logger = logging.getLogger(__name__)


def _get_available_strategies() -> list[SearchStrategy]:
    """
    Detect and return a list of available search strategy instances,
    ordered by preference.
    """
    available = []
    for strategy_class in SEARCH_STRATEGY_CLASSES:
        try:
            strategy = strategy_class()
            if strategy.is_available():
                available.append(strategy)
        except Exception:
            pass
    return available


def migrate_legacy_config(settings_path: str) -> Dict[str, Any]:
    """
    Migrate legacy config.json to new MCP Config format.

    This function reads the legacy config.json file, transforms it to the new
    MCP Config schema, backs up the original file, and returns the migrated
    configuration.

    Args:
        settings_path: Path to the settings directory containing config.json

    Returns:
        Dict containing the migrated configuration or default config

    Migration strategy:
    - Idempotent: Safe to run multiple times (checks migration marker)
    - Automatic backup: Creates config.json.backup before migration
    - Fallback: Returns defaults if legacy config missing or invalid
    - Error handling: Logs errors and returns defaults on failure
    """
    import copy

    # Deep copy defaults to avoid mutations
    mcp_config = copy.deepcopy(DEFAULT_MCP_CONFIG)
    migration_status = "default"

    config_file_path = os.path.join(settings_path, CONFIG_FILE)
    backup_path = config_file_path + ".backup"

    # Check if already migrated by looking for migration marker in a separate file
    migration_marker_path = os.path.join(settings_path, ".migration_complete")
    if os.path.exists(migration_marker_path):
        try:
            with open(migration_marker_path, 'r', encoding='utf-8') as f:
                marker_data = json.load(f)
            logger.info(f"Config already migrated on {marker_data.get('timestamp', 'unknown')}")
            # Return the migrated config (already set as default above)
            mcp_config["_migration"]["completed"] = True
            mcp_config["_migration"]["timestamp"] = marker_data.get('timestamp')
            mcp_config["_migration"]["source"] = marker_data.get('source', 'legacy')
            return mcp_config
        except Exception as e:
            logger.warning(f"Failed to read migration marker: {e}")
            # Continue with migration attempt

    # Check if legacy config.json exists
    if not os.path.exists(config_file_path):
        logger.info("No legacy config.json found, using defaults")
        migration_status = "default"
        # Mark as migrated with default source
        _write_migration_marker(migration_marker_path, "default")
        mcp_config["_migration"]["completed"] = True
        mcp_config["_migration"]["timestamp"] = datetime.now().isoformat()
        mcp_config["_migration"]["source"] = "default"
        return mcp_config

    try:
        # Load legacy config
        with open(config_file_path, 'r', encoding='utf-8') as f:
            legacy_config = json.load(f)

        logger.info(f"Migrating legacy config from {config_file_path}")

        # Create backup (with timestamp if backup already exists)
        if os.path.exists(backup_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{config_file_path}.backup.{timestamp}"

        try:
            shutil.copy2(config_file_path, backup_path)
            logger.info(f"Legacy config backed up to {backup_path}")
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

        # Map legacy config to new schema
        # Legacy structure expected: { "search_tools": {...}, "file_watcher": {...}, ... }

        # Migrate search parameters
        if "search_tools" in legacy_config:
            search_tools = legacy_config["search_tools"]
            if isinstance(search_tools, dict):
                if "case_sensitive" in search_tools:
                    mcp_config["search"]["case_sensitive"] = search_tools["case_sensitive"]
                if "context_lines" in search_tools:
                    mcp_config["search"]["context_lines"] = search_tools.get("context_lines", 0)
                if "max_line_length" in search_tools:
                    mcp_config["search"]["max_line_length"] = search_tools.get("max_line_length")
                if "fuzzy" in search_tools:
                    mcp_config["search"]["fuzzy"] = search_tools.get("fuzzy", False)
                if "regex" in search_tools:
                    mcp_config["search"]["regex"] = search_tools.get("regex")

        # Migrate file watcher configuration
        if "file_watcher" in legacy_config:
            fw_config = legacy_config["file_watcher"]
            if isinstance(fw_config, dict):
                if "enabled" in fw_config:
                    mcp_config["file_watcher"]["enabled"] = fw_config["enabled"]
                if "debounce_seconds" in fw_config:
                    mcp_config["file_watcher"]["debounce_seconds"] = fw_config.get("debounce_seconds", 6.0)

        # Migrate filter patterns
        if "exclude_patterns" in legacy_config:
            exclude_patterns = legacy_config["exclude_patterns"]
            if isinstance(exclude_patterns, list):
                mcp_config["filter"]["exclude_patterns"] = exclude_patterns

        if "additional_exclude_patterns" in legacy_config.get("file_watcher", {}):
            additional = legacy_config["file_watcher"]["additional_exclude_patterns"]
            if isinstance(additional, list):
                # Merge with existing exclude patterns
                existing = set(mcp_config["filter"]["exclude_patterns"])
                existing.update(additional)
                mcp_config["filter"]["exclude_patterns"] = list(existing)

        # Mark migration as complete
        mcp_config["_migration"]["completed"] = True
        mcp_config["_migration"]["timestamp"] = datetime.now().isoformat()
        mcp_config["_migration"]["source"] = "legacy"

        # Write migration marker
        _write_migration_marker(migration_marker_path, "legacy", legacy_config)

        migration_status = "migrated"
        logger.info(f"Successfully migrated legacy config to MCP Config format")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in legacy config: {e}")
        migration_status = "failed"
        # Mark as migrated with default fallback
        _write_migration_marker(migration_marker_path, "default_fallback")
        mcp_config["_migration"]["completed"] = True
        mcp_config["_migration"]["timestamp"] = datetime.now().isoformat()
        mcp_config["_migration"]["source"] = "default_fallback"

    except KeyError as e:
        logger.warning(f"Missing key in legacy config: {e}, using partial migration")
        migration_status = "partial"
        # Mark as migrated even with partial data
        _write_migration_marker(migration_marker_path, "partial")
        mcp_config["_migration"]["completed"] = True
        mcp_config["_migration"]["timestamp"] = datetime.now().isoformat()
        mcp_config["_migration"]["source"] = "partial"

    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        migration_status = "failed"
        # Mark as migrated with default fallback
        _write_migration_marker(migration_marker_path, "default_fallback")
        mcp_config["_migration"]["completed"] = True
        mcp_config["_migration"]["timestamp"] = datetime.now().isoformat()
        mcp_config["_migration"]["source"] = "default_fallback"

    return mcp_config


def _write_migration_marker(marker_path: str, source: str, legacy_config: Dict = None) -> None:
    """
    Write migration marker file to prevent re-migration.

    Args:
        marker_path: Path to the migration marker file
        source: Migration source (legacy, default, partial, default_fallback)
        legacy_config: Optional legacy config data for reference
    """
    try:
        os.makedirs(os.path.dirname(marker_path), exist_ok=True)
        marker_data = {
            "completed": True,
            "timestamp": datetime.now().isoformat(),
            "source": source
        }
        if legacy_config and source == "legacy":
            marker_data["legacy_keys"] = list(legacy_config.keys())

        with open(marker_path, 'w', encoding='utf-8') as f:
            json.dump(marker_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to write migration marker: {e}")


class ProjectSettings:
    """Class for managing project settings and index data"""

    def __init__(self, base_path, skip_load=False):
        """Initialize project settings

        Args:
            base_path (str): Base path of the project
            skip_load (bool): Whether to skip loading files
        """
        import copy
        self.base_path = base_path
        self.skip_load = skip_load
        self.available_strategies: list[SearchStrategy] = []
        self.refresh_available_strategies()

        # Find project root to avoid creating multiple .code_indexer directories
        self.project_root = self._find_project_root(base_path)

        # Initialize in-memory MCP Config (will be populated by migration)
        self._mcp_config: Dict[str, Any] = copy.deepcopy(DEFAULT_MCP_CONFIG)

        # Store index in project root directory to avoid duplicates in subdirectories
        try:
            if self.project_root and os.path.exists(self.project_root):
                # Use .code_indexer subdirectory in project root
                temp_base_dir = os.path.join(self.project_root, f".{SETTINGS_DIR}")
            else:
                # Fallback: use system temp directory
                system_temp = tempfile.gettempdir()
                temp_base_dir = os.path.join(system_temp, SETTINGS_DIR)

            # Create the directory if it doesn't exist
            if not os.path.exists(temp_base_dir):
                os.makedirs(temp_base_dir, exist_ok=True)
        except Exception:
            # Last resort fallback: use home directory
            temp_base_dir = os.path.join(os.path.expanduser("~"), f".{SETTINGS_DIR}")
            if not os.path.exists(temp_base_dir):
                os.makedirs(temp_base_dir, exist_ok=True)

        # Use system temporary directory to store index data
        try:
            if base_path:
                # Use hash of project path as unique identifier
                path_hash = hashlib.md5(base_path.encode()).hexdigest()
                self.settings_path = os.path.join(temp_base_dir, path_hash)
            else:
                # If no base path provided, use a default directory
                self.settings_path = os.path.join(temp_base_dir, "default")

            self.ensure_settings_dir()
        except Exception:
            # If error occurs, use .code_indexer in project or home directory as fallback
            if base_path and os.path.exists(base_path):
                fallback_dir = os.path.join(base_path, ".code_indexer",
                                          hashlib.md5(base_path.encode()).hexdigest())
            else:
                fallback_dir = os.path.join(os.path.expanduser("~"), ".code_indexer",
                                          "default" if not base_path else hashlib.md5(base_path.encode()).hexdigest())
            
            self.settings_path = fallback_dir
            if not os.path.exists(fallback_dir):
                os.makedirs(fallback_dir, exist_ok=True)

    def ensure_settings_dir(self):
        """Ensure settings directory exists"""

        try:
            if not os.path.exists(self.settings_path):
                # Create directory structure
                os.makedirs(self.settings_path, exist_ok=True)
            else:
                pass

            # Check if directory is writable
            if not os.access(self.settings_path, os.W_OK):
                # If directory is not writable, use .code_indexer in project or home directory as fallback
                if self.base_path and os.path.exists(self.base_path) and os.access(self.base_path, os.W_OK):
                    fallback_dir = os.path.join(self.base_path, ".code_indexer",
                                              os.path.basename(self.settings_path))
                else:
                    fallback_dir = os.path.join(os.path.expanduser("~"), ".code_indexer",
                                              os.path.basename(self.settings_path))
                
                self.settings_path = fallback_dir
                if not os.path.exists(fallback_dir):
                    os.makedirs(fallback_dir, exist_ok=True)
        except Exception:
            # If unable to create settings directory, use .code_indexer in project or home directory
            if self.base_path and os.path.exists(self.base_path):
                fallback_dir = os.path.join(self.base_path, ".code_indexer",
                                          hashlib.md5(self.base_path.encode()).hexdigest())
            else:
                fallback_dir = os.path.join(os.path.expanduser("~"), ".code_indexer",
                                          "default" if not self.base_path else hashlib.md5(self.base_path.encode()).hexdigest())
            
            self.settings_path = fallback_dir
            if not os.path.exists(fallback_dir):
                os.makedirs(fallback_dir, exist_ok=True)

    def get_config_path(self):
        """Get the path to the configuration file"""
        try:
            path = os.path.join(self.settings_path, CONFIG_FILE)
            # Ensure directory exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            return path
        except Exception:
            # If error occurs, use file in project or home directory as fallback
            if self.base_path and os.path.exists(self.base_path):
                return os.path.join(self.base_path, CONFIG_FILE)
            else:
                return os.path.join(os.path.expanduser("~"), CONFIG_FILE)


    def _get_timestamp(self):
        """Get current timestamp"""
        return datetime.now().isoformat()

    def save_config(self, config):
        """Save configuration data

        Args:
            config (dict): Configuration data
        """
        try:
            config_path = self.get_config_path()
            # Add timestamp
            config['last_updated'] = self._get_timestamp()

            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            
            return config
        except Exception:
            return config

    def load_config(self):
        """Load configuration data

        Returns:
            dict: Configuration data, or empty dict if file doesn't exist
        """
        # If skip_load is set, return empty dict directly
        if self.skip_load:
            return {}

        try:
            config_path = self.get_config_path()
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    return config
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If file is corrupted, return empty dict
                    return {}
            else:
                pass
            return {}
        except Exception:
            return {}

    def save_index(self, index_data):
        """Save code index in JSON format

        Args:
            index_data: Index data as dictionary or JSON string
        """
        try:
            index_path = self.get_index_path()

            # Ensure directory exists
            dir_path = os.path.dirname(index_path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

            # Check if directory is writable
            if not os.access(dir_path, os.W_OK):
                # Use project or home directory as fallback
                if self.base_path and os.path.exists(self.base_path):
                    index_path = os.path.join(self.base_path, INDEX_FILE)
                else:
                    index_path = os.path.join(os.path.expanduser("~"), INDEX_FILE)
                

            # Convert to JSON string if it's an object with to_json method
            if hasattr(index_data, 'to_json'):
                json_data = index_data.to_json()
            elif isinstance(index_data, str):
                json_data = index_data
            else:
                # Assume it's a dictionary and convert to JSON
                json_data = json.dumps(index_data, indent=2, default=str)

            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(json_data)

            
        except Exception:
            # Try saving to project or home directory
            try:
                if self.base_path and os.path.exists(self.base_path):
                    fallback_path = os.path.join(self.base_path, INDEX_FILE)
                else:
                    fallback_path = os.path.join(os.path.expanduser("~"), INDEX_FILE)
                

                # Convert to JSON string if it's an object with to_json method
                if hasattr(index_data, 'to_json'):
                    json_data = index_data.to_json()
                elif isinstance(index_data, str):
                    json_data = index_data
                else:
                    json_data = json.dumps(index_data, indent=2, default=str)

                with open(fallback_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            except Exception:
                pass
    def load_index(self):
        """Load code index from JSON format

        Returns:
            dict: Index data, or None if file doesn't exist or has errors
        """
        # If skip_load is set, return None directly
        if self.skip_load:
            return None

        try:
            index_path = self.get_index_path()

            if os.path.exists(index_path):
                try:
                    with open(index_path, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                    return index_data
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # If file is corrupted, return None
                    return None
                except Exception:
                    return None
            else:
                # Try loading from project or home directory
                if self.base_path and os.path.exists(self.base_path):
                    fallback_path = os.path.join(self.base_path, INDEX_FILE)
                else:
                    fallback_path = os.path.join(os.path.expanduser("~"), INDEX_FILE)
            if os.path.exists(fallback_path):
                try:
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        index_data = json.load(f)
                    return index_data
                except Exception:
                    pass
            return None
        except Exception:
            return None



    def cleanup_legacy_files(self) -> None:
        """Clean up any legacy index files found."""
        try:
            legacy_files = [
                os.path.join(self.settings_path, "file_index.pickle"),
                os.path.join(self.settings_path, "content_cache.pickle"),
                os.path.join(self.settings_path, INDEX_FILE)  # Legacy JSON
            ]
            
            for legacy_file in legacy_files:
                if os.path.exists(legacy_file):
                    try:
                        os.remove(legacy_file)
                    except Exception:
                        pass
        except Exception:
            pass

    def clear(self):
        """Clear config and index files"""
        try:

            if os.path.exists(self.settings_path):
                # Check if directory is writable
                if not os.access(self.settings_path, os.W_OK):
                    return

                # Delete specific files only (config.json and index.json)
                files_to_delete = [CONFIG_FILE, INDEX_FILE]

                for filename in files_to_delete:
                    file_path = os.path.join(self.settings_path, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception:
                        pass

            else:
                pass
        except Exception:
            pass
    def get_stats(self):
        """Get statistics for the settings directory

        Returns:
            dict: Dictionary containing file sizes and update times
        """
        try:

            stats = {
                'settings_path': self.settings_path,
                'exists': os.path.exists(self.settings_path),
                'is_directory': os.path.isdir(self.settings_path) if os.path.exists(self.settings_path) else False,
                'writable': os.access(self.settings_path, os.W_OK) if os.path.exists(self.settings_path) else False,
                'files': {},
                'temp_dir': tempfile.gettempdir(),
                'base_path': self.base_path
            }

            if stats['exists'] and stats['is_directory']:
                try:
                    # Get all files in the directory
                    all_files = os.listdir(self.settings_path)
                    stats['all_files'] = all_files

                    # Get details for specific files
                    for filename in [CONFIG_FILE, INDEX_FILE]:
                        file_path = os.path.join(self.settings_path, filename)
                        if os.path.exists(file_path):
                            try:
                                file_stats = os.stat(file_path)
                                stats['files'][filename] = {
                                    'path': file_path,
                                    'size_bytes': file_stats.st_size,
                                    'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                                    'readable': os.access(file_path, os.R_OK),
                                    'writable': os.access(file_path, os.W_OK)
                                }
                            except Exception as e:
                                stats['files'][filename] = {
                                    'path': file_path,
                                    'error': str(e)
                                }
                except Exception as e:
                    stats['list_error'] = str(e)

            # Check fallback path
            if self.base_path and os.path.exists(self.base_path):
                fallback_dir = os.path.join(self.base_path, ".code_indexer")
            else:
                fallback_dir = os.path.join(os.path.expanduser("~"), ".code_indexer")
            stats['fallback_path'] = fallback_dir
            stats['fallback_exists'] = os.path.exists(fallback_dir)
            stats['fallback_is_directory'] = os.path.isdir(fallback_dir) if os.path.exists(fallback_dir) else False

            return stats
        except Exception as e:
            return {
                'error': str(e),
                'settings_path': self.settings_path,
                'temp_dir': tempfile.gettempdir(),
                'base_path': self.base_path
            }

    def get_search_tools_config(self):
        """Get the configuration of available search tools.

        Returns:
            dict: A dictionary containing the list of available tool names.
        """
        return {
            "available_tools": [s.name for s in self.available_strategies],
            "preferred_tool": self.get_preferred_search_tool().name if self.available_strategies else None
        }

    def get_preferred_search_tool(self) -> SearchStrategy | None:
        """Get the preferred search tool based on availability and priority.

        Returns:
            SearchStrategy: An instance of the preferred search strategy, or None.
        """
        if not self.available_strategies:
            self.refresh_available_strategies()

        return self.available_strategies[0] if self.available_strategies else None

    def _find_project_root(self, start_path):
        """
        Find existing parent index or determine where to create new one.
        Automatically cleans up redundant child indexes when parent index exists.

        Strategy:
        1. Walk up directory tree from start_path
        2. Check each parent for existing .code_indexer directory
        3. If found, use that location (prefer highest-level index)
        4. Clean up any child indexes below the parent level
        5. If not found after reaching filesystem root, use start_path

        This creates a hierarchical index system where:
        - Subdirectories automatically use parent indexes when available
        - New indexes only created when no parent index exists
        - Always prefer the highest-level (closest to root) index
        - Redundant child indexes are automatically removed

        Args:
            start_path: The starting path to search from

        Returns:
            str: Directory that should contain the .code_indexer folder
        """
        if not start_path or not os.path.exists(start_path):
            return start_path

        current = os.path.abspath(start_path)
        start_abs = os.path.abspath(start_path)
        index_dir_name = f".{SETTINGS_DIR}"  # ".code_indexer"

        # Track directories we've traversed (for cleanup later)
        traversed_dirs = []

        # Walk up the directory tree
        while True:
            # Check if .code_indexer exists in current directory
            index_path = os.path.join(current, index_dir_name)

            if os.path.exists(index_path) and os.path.isdir(index_path):
                # Found existing index at this level
                logger.info(f"Found existing parent index at: {current}")

                # Clean up any child indexes below this parent level
                if current != start_abs:
                    self._cleanup_child_indexes(start_abs, current, index_dir_name)

                return current

            # Track this directory for potential cleanup
            traversed_dirs.append(current)

            # Move to parent directory
            parent = os.path.dirname(current)

            # Stop if we've reached the filesystem root
            if parent == current:
                # No existing index found in any parent
                # Use the original start_path to create new index
                logger.info(f"No parent index found, will create at: {start_path}")
                return start_path

            current = parent

    def _cleanup_child_indexes(self, start_path, parent_index_path, index_dir_name):
        """
        Clean up redundant .code_indexer directories in child paths.

        When a parent index is found, remove any .code_indexer directories
        between start_path and parent_index_path to avoid duplication.

        Args:
            start_path: The original search starting path
            parent_index_path: The parent directory containing the index to use
            index_dir_name: Name of the index directory (e.g., ".code_indexer")
        """
        try:
            current = os.path.abspath(start_path)
            parent_abs = os.path.abspath(parent_index_path)

            # Walk from start_path up to (but not including) parent_index_path
            while current != parent_abs:
                child_index = os.path.join(current, index_dir_name)

                if os.path.exists(child_index) and os.path.isdir(child_index):
                    try:
                        # Remove the redundant child index
                        shutil.rmtree(child_index)
                        logger.info(f"Cleaned up redundant child index at: {current}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up child index at {current}: {e}")

                # Move to parent
                parent = os.path.dirname(current)
                if parent == current:  # Reached filesystem root
                    break
                current = parent

        except Exception as e:
            logger.warning(f"Error during child index cleanup: {e}")

    def refresh_available_strategies(self):
        """
        Force a refresh of the available search tools list.
        """

        self.available_strategies = _get_available_strategies()


    def get_file_watcher_config(self) -> dict:
        """
        Get file watcher specific configuration from MCP Config.

        Returns:
            dict: File watcher configuration with defaults
        """
        # Return from MCP Config
        return self._mcp_config.get("file_watcher", DEFAULT_MCP_CONFIG["file_watcher"])

    def update_file_watcher_config(self, updates: dict) -> None:
        """
        Update file watcher configuration in MCP Config.

        Args:
            updates: Dictionary of configuration updates
        """
        if "file_watcher" not in self._mcp_config:
            self._mcp_config["file_watcher"] = DEFAULT_MCP_CONFIG["file_watcher"].copy()

        self._mcp_config["file_watcher"].update(updates)
        logger.info(f"File watcher config updated: {updates}")

    def load_mcp_config(self) -> Dict[str, Any]:
        """
        Load MCP Config from in-memory storage.

        Returns:
            Dict containing the current MCP Config
        """
        return self._mcp_config

    def set_mcp_config(self, config: Dict[str, Any]) -> None:
        """
        Set MCP Config (typically called by migration function).

        Args:
            config: Complete MCP Config dictionary
        """
        import copy
        self._mcp_config = copy.deepcopy(config)
        logger.info("MCP Config updated in memory")

    def get_mcp_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a value from MCP Config using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "search.case_sensitive")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self._mcp_config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set_mcp_config_value(self, key_path: str, value: Any) -> None:
        """
        Set a value in MCP Config using dot notation.

        Args:
            key_path: Dot-separated path (e.g., "search.case_sensitive")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self._mcp_config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        logger.debug(f"MCP Config value set: {key_path} = {value}")
