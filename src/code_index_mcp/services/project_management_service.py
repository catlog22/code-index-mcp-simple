"""
Project Management Service - Business logic for project lifecycle management.

This service handles the business logic for project initialization, configuration,
and lifecycle management using the new JSON-based indexing system.
"""
import logging
from typing import Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

from .base_service import BaseService
from ..utils.response_formatter import ResponseFormatter
from ..constants import SUPPORTED_EXTENSIONS
from ..indexing import get_layered_index_manager

logger = logging.getLogger(__name__)


@dataclass
class ProjectInitializationResult:
    """Business result for project initialization operations."""
    project_path: str
    file_count: int
    index_source: str  # 'loaded_existing' or 'built_new'
    search_capabilities: str
    monitoring_status: str
    message: str


class ProjectManagementService(BaseService):
    """
    Business service for project lifecycle management.

    This service orchestrates project initialization workflows by composing
    technical tools to achieve business goals like setting up projects,
    managing configurations, and coordinating system components.
    """

    def __init__(self, ctx):
        super().__init__(ctx)
        # Unified layered index manager (replaces old managers)
        self._index_manager = get_layered_index_manager()
        from ..tools.config import ProjectConfigTool
        self._config_tool = ProjectConfigTool()
        # Import FileWatcherTool locally to avoid circular import
        from ..tools.monitoring import FileWatcherTool
        self._watcher_tool = FileWatcherTool(ctx)


    @contextmanager
    def _noop_operation(self, *_args, **_kwargs):
        yield

    def initialize_project(self, path: str) -> str:
        """
        Initialize a project with comprehensive business logic.

        This is the main business method that orchestrates the project
        initialization workflow, handling validation, cleanup, setup,
        and coordination of all project components.

        Args:
            path: Project directory path to initialize

        Returns:
            Success message with project information

        Raises:
            ValueError: If path is invalid or initialization fails
        """
        # Business validation
        self._validate_initialization_request(path)

        # Business workflow: Execute initialization
        result = self._execute_initialization_workflow(path)

        # Business result formatting
        return self._format_initialization_result(result)

    def _validate_initialization_request(self, path: str) -> None:
        """
        Validate the project initialization request according to business rules.

        Args:
            path: Project path to validate

        Raises:
            ValueError: If validation fails
        """
        # Business rule: Path must be valid
        error = self._config_tool.validate_project_path(path)
        if error:
            raise ValueError(error)

    def _execute_initialization_workflow(self, path: str) -> ProjectInitializationResult:
        """
        Execute the core project initialization business workflow.

        Args:
            path: Project path to initialize

        Returns:
            ProjectInitializationResult with initialization data
        """
        # Business step 1: Initialize config tool
        self._config_tool.initialize_settings(path)

        # Normalize path for consistent processing
        normalized_path = self._config_tool.normalize_project_path(path)

        # Business step 2: Cleanup existing project state
        self._cleanup_existing_project()

        # Business step 3: Initialize layered index manager (shallow by default for fast path)
        index_result = self._initialize_layered_index_manager(normalized_path)

        # Business step 3.1: Store index manager in context for other services
        self.helper.update_index_manager(self._index_manager)

        # Business step 4: Setup file monitoring
        monitoring_result = self._setup_file_monitoring(normalized_path)

        # Business step 4: Update system state
        self._update_project_state(normalized_path, index_result['file_count'])

        # Business step 6: Get search capabilities info
        search_info = self._get_search_capabilities_info()

        return ProjectInitializationResult(
            project_path=normalized_path,
            file_count=index_result['file_count'],
            index_source=index_result['source'],
            search_capabilities=search_info,
            monitoring_status=monitoring_result,
            message=f"Project initialized: {normalized_path}"
        )

    def _cleanup_existing_project(self) -> None:
        """Business logic to cleanup existing project state."""
        with self._noop_operation():
            # Stop existing file monitoring
            self._watcher_tool.stop_existing_watcher()

            # Clear existing index cache
            self.helper.clear_index_cache()

            # Clear any existing index state
            pass

    def _initialize_layered_index_manager(self, project_path: str) -> Dict[str, Any]:
        """
        Business logic to initialize the layered index manager (shallow by default).

        Args:
            project_path: Project path

        Returns:
            Dictionary with initialization results
        """
        # Set project path in layered manager
        if not self._index_manager.set_project_path(project_path):
            raise RuntimeError(f"Failed to set project path: {project_path}")

        # Update context
        self.helper.update_base_path(project_path)

        # Build or load global shallow index (fast path)
        file_list = self._index_manager.get_global_index(shallow=True, force_rebuild=False)

        if file_list:
            source = "loaded_existing"
            file_count = len(file_list) if isinstance(file_list, list) else 0
        else:
            # Force rebuild if loading failed
            file_list = self._index_manager.get_global_index(shallow=True, force_rebuild=True)
            source = "built_new"
            file_count = len(file_list) if isinstance(file_list, list) else 0

        return {
            'file_count': file_count,
            'source': source,
            'total_symbols': 0,
            'languages': []
        }


    def _is_valid_existing_index(self, index_data: Dict[str, Any]) -> bool:
        """
        Business rule to determine if existing index is valid and usable.

        Args:
            index_data: Index data to validate

        Returns:
            True if index is valid and usable, False otherwise
        """
        if not index_data or not isinstance(index_data, dict):
            return False

        # Business rule: Must have new format metadata
        if 'index_metadata' not in index_data:
            return False

        # Business rule: Must be compatible version
        version = index_data.get('index_metadata', {}).get('version', '')
        return version >= '3.0'

    def _load_existing_index(self, index_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Business logic to load and use existing index.

        Args:
            index_data: Existing index data

        Returns:
            Dictionary with loading results
        """


        # Note: Legacy index loading is now handled by UnifiedIndexManager
        # This method is kept for backward compatibility but functionality moved

        # Extract file count from metadata
        file_count = index_data.get('project_metadata', {}).get('total_files', 0)



        return {
            'file_count': file_count,
            'source': 'loaded_existing'
        }


    def _setup_file_monitoring(self, project_path: str) -> str:
        """
        Business logic to setup file monitoring for the project.

        Args:
            project_path: Project path to monitor

        Returns:
            String describing monitoring setup result
        """
        # Check if file watcher is enabled in MCP Config
        from ..services.file_watcher_service import WATCHDOG_AVAILABLE

        file_watcher_config = self.settings.get_file_watcher_config()
        file_watcher_enabled = file_watcher_config.get('enabled', False)

        if not file_watcher_enabled:
            logger.info("FileWatcher disabled in config, using on-demand index refresh")
            return "monitoring_disabled"

        if not WATCHDOG_AVAILABLE:
            logger.error("FileWatcher enabled but watchdog not installed. Install with: pip install code-index-mcp[watcher]")
            logger.info("Falling back to on-demand index refresh")
            return "monitoring_unavailable"

        try:
            # Create rebuild callback that uses the layered index manager
            def rebuild_callback():
                logger.info("File watcher triggered rebuild callback")
                try:
                    logger.debug(f"Starting shallow index rebuild for: {project_path}")
                    # Business logic: File changed, rebuild using layered index manager
                    try:
                        if not self._index_manager.set_project_path(project_path):
                            logger.warning("Index manager set_project_path failed")
                            return False

                        # Rebuild shallow index
                        file_list = self._index_manager.get_global_index(shallow=True, force_rebuild=True)
                        if file_list:
                            logger.info(f"File watcher shallow rebuild completed successfully - files {len(file_list)}")
                            return True
                        else:
                            logger.warning("File watcher shallow rebuild failed")
                            return False
                    except Exception as e:
                        import traceback
                        logger.error(f"File watcher shallow rebuild failed: {e}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        return False
                except Exception as e:
                    import traceback
                    logger.error(f"File watcher rebuild failed: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    return False

            # Start monitoring using watcher tool
            logger.info("FileWatcher enabled - starting file system monitoring")
            success = self._watcher_tool.start_monitoring(project_path, rebuild_callback)

            if success:
                # Store watcher in context for later access
                self._watcher_tool.store_in_context()
                logger.info("FileWatcher started successfully (auto-refresh enabled)")
                return "monitoring_active"
            else:
                self._watcher_tool.record_error("Failed to start file monitoring")
                logger.warning("FileWatcher failed to start, falling back to on-demand refresh")
                return "monitoring_failed"

        except ImportError as e:
            error_msg = f"FileWatcher enabled but watchdog not installed: {e}"
            logger.error(error_msg)
            logger.info("Install with: pip install code-index-mcp[watcher]")
            logger.info("Falling back to on-demand index refresh")
            self._watcher_tool.record_error(error_msg)
            return "monitoring_unavailable"
        except Exception as e:
            error_msg = f"File monitoring setup failed: {e}"
            self._watcher_tool.record_error(error_msg)
            logger.warning("FileWatcher setup failed, falling back to on-demand refresh")
            return "monitoring_error"

    def _update_project_state(self, project_path: str, file_count: int) -> None:
        """Business logic to update system state after project initialization."""


        # Update context with file count
        self.helper.update_file_count(file_count)

        # No logging

    def _get_search_capabilities_info(self) -> str:
        """Business logic to get search capabilities information."""
        search_info = self._config_tool.get_search_tool_info()

        if search_info['available']:
            return f"Advanced search enabled ({search_info['name']})"
        else:
            return "Basic search available"

    def _format_initialization_result(self, result: ProjectInitializationResult) -> str:
        """
        Format the initialization result according to business requirements.

        Args:
            result: Initialization result data

        Returns:
            Formatted result string for MCP response
        """
        if result.index_source == 'unified_manager':
            message = (f"Project path set to: {result.project_path}. "
                      f"Initialized unified index with {result.file_count} files. "
                      f"{result.search_capabilities}.")
        elif result.index_source == 'failed':
            message = (f"Project path set to: {result.project_path}. "
                      f"Index initialization failed. Some features may be limited. "
                      f"{result.search_capabilities}.")
        else:
            message = (f"Project path set to: {result.project_path}. "
                      f"Indexed {result.file_count} files. "
                      f"{result.search_capabilities}.")

        if result.monitoring_status != "monitoring_active":
            message += " (File monitoring unavailable - use manual refresh)"

        return message

    def get_project_config(self) -> str:
        """
        Get the current project configuration for MCP resource.

        Returns:
            JSON formatted configuration string
        """

        # Check if project is configured
        if not self.helper.base_path:
            config_data = {
                "status": "not_configured",
                "message": ("Project path not set. Please use set_project_path "
                           "to set a project directory first."),
                "supported_extensions": SUPPORTED_EXTENSIONS
            }
            return ResponseFormatter.config_response(config_data)

        # Get settings stats
        settings_stats = self.helper.settings.get_stats() if self.helper.settings else {}

        config_data = {
            "base_path": self.helper.base_path,
            "supported_extensions": SUPPORTED_EXTENSIONS,
            "file_count": self.helper.file_count,
            "settings_directory": self.helper.settings.settings_path if self.helper.settings else "",
            "settings_stats": settings_stats
        }

        return ResponseFormatter.config_response(config_data)

    # Removed: get_project_structure; the project structure resource is deprecated
