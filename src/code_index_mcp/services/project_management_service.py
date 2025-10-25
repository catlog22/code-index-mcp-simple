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

        # Business step 4: Update system state
        self._update_project_state(normalized_path, index_result['file_count'])

        # Business step 5: Get search capabilities info
        search_info = self._get_search_capabilities_info()

        return ProjectInitializationResult(
            project_path=normalized_path,
            file_count=index_result['file_count'],
            index_source=index_result['source'],
            search_capabilities=search_info,
            message=f"Project initialized: {normalized_path}"
        )

    def _cleanup_existing_project(self) -> None:
        """Business logic to cleanup existing project state."""
        with self._noop_operation():
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
