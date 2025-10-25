"""
Base service class providing common functionality for all services.

This module defines the base service pattern that all domain services inherit from,
ensuring consistent behavior and shared functionality across the service layer.
"""

import logging
import time
from abc import ABC
from typing import Optional, Dict, Tuple
from mcp.server.fastmcp import Context

from ..utils import ContextHelper, ValidationHelper

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """
    Base class for all MCP services.

    This class provides common functionality that all services need:
    - Context management through ContextHelper
    - Common validation patterns
    - Shared error checking methods
    - Auto-refresh mechanism for index freshness

    All domain services should inherit from this class to ensure
    consistent behavior and access to shared utilities.
    """

    # Class-level mtime cache with TTL (shared across instances)
    _mtime_cache: Dict[str, Tuple[float, float]] = {}
    _mtime_cache_ttl: float = 5.0  # 5 seconds TTL

    def __init__(self, ctx: Context):
        """
        Initialize the base service.

        Args:
            ctx: The MCP Context object containing request and lifespan context
        """
        self.ctx = ctx
        self.helper = ContextHelper(ctx)

    def _validate_project_setup(self) -> Optional[str]:
        """
        Validate that the project is properly set up.

        This method checks if the base path is set and valid, which is
        required for most operations.

        Returns:
            Error message if project is not set up properly, None if valid
        """
        return self.helper.get_base_path_error()

    def _require_project_setup(self) -> None:
        """
        Ensure project is set up, raising an exception if not.

        This is a convenience method for operations that absolutely
        require a valid project setup.

        Raises:
            ValueError: If project is not properly set up
        """
        error = self._validate_project_setup()
        if error:
            raise ValueError(error)

    def _validate_file_path(self, file_path: str) -> Optional[str]:
        """
        Validate a file path for security and accessibility.

        Args:
            file_path: The file path to validate

        Returns:
            Error message if validation fails, None if valid
        """
        return ValidationHelper.validate_file_path(file_path, self.helper.base_path)

    def _require_valid_file_path(self, file_path: str) -> None:
        """
        Ensure file path is valid, raising an exception if not.

        Args:
            file_path: The file path to validate

        Raises:
            ValueError: If file path is invalid
        """
        error = self._validate_file_path(file_path)
        if error:
            raise ValueError(error)

    @property
    def base_path(self) -> str:
        """
        Convenient access to the base project path.

        Returns:
            The base project path
        """
        return self.helper.base_path

    @property
    def settings(self):
        """
        Convenient access to the project settings.

        Returns:
            The ProjectSettings instance
        """
        return self.helper.settings

    @property
    def file_count(self) -> int:
        """
        Convenient access to the current file count.

        Returns:
            The number of indexed files
        """
        return self.helper.file_count

    @property
    def index_provider(self):
        """
        Convenient access to the unified index provider.

        Returns:
            The current IIndexProvider instance, or None if not available
        """
        if self.helper.index_manager:
            return self.helper.index_manager.get_provider()
        return None
    
    @property
    def index_manager(self):
        """
        Convenient access to the index manager.

        Returns:
            The index manager instance, or None if not available
        """
        return self.helper.index_manager

    def _ensure_index_fresh(self, target_path: Optional[str] = None, shallow: bool = False) -> bool:
        """
        Ensure index is fresh by checking mtime and rebuilding if stale.

        This method implements auto-refresh mechanism with:
        - mtime-based staleness detection
        - Cached mtime results (5-second TTL)
        - Automatic index rebuild when stale
        - Performance monitoring and logging

        Args:
            target_path: Optional specific path to check (defaults to project root)
            shallow: Whether to check shallow or deep index

        Returns:
            True if index was fresh or successfully rebuilt, False on error
        """
        start_time = time.time()

        try:
            # Import LayeredIndexManager here to avoid circular imports
            from ..indexing import get_layered_index_manager

            index_manager = get_layered_index_manager()

            # Ensure project path is set
            if not index_manager.project_path:
                if not self.base_path:
                    logger.debug("Cannot check index freshness: no project path set")
                    return False
                index_manager.set_project_path(self.base_path)

            # Determine which index path to check
            if shallow:
                index_path = index_manager.global_shallow_path
            else:
                index_path = index_manager.global_index_path

            # Check if index exists
            import os
            if not index_path or not os.path.exists(index_path):
                logger.info(f"Index does not exist, triggering rebuild (shallow={shallow})")
                return self._rebuild_index_if_needed(index_manager, target_path, shallow, start_time)

            # Get index mtime
            index_mtime = os.path.getmtime(index_path)

            # Get max source mtime with caching
            check_path = target_path if target_path else index_manager.project_path
            max_source_mtime = self._get_cached_max_mtime(check_path)

            # Compare mtimes
            if max_source_mtime > index_mtime:
                logger.info(
                    f"Index is stale (source_mtime={max_source_mtime:.2f} > "
                    f"index_mtime={index_mtime:.2f}), triggering rebuild"
                )
                return self._rebuild_index_if_needed(index_manager, target_path, shallow, start_time)

            # Index is fresh
            duration_ms = (time.time() - start_time) * 1000
            logger.debug(f"Index freshness check completed in {duration_ms:.2f}ms (index is fresh)")

            if duration_ms > 100:
                logger.warning(f"Slow freshness check detected: {duration_ms:.2f}ms")

            return True

        except Exception as e:
            logger.error(f"Error checking index freshness: {e}")
            return False

    def _rebuild_index_if_needed(
        self,
        index_manager,
        target_path: Optional[str],
        shallow: bool,
        start_time: float
    ) -> bool:
        """
        Rebuild index and log performance metrics.

        Args:
            index_manager: LayeredIndexManager instance
            target_path: Optional specific path to rebuild
            shallow: Whether to rebuild shallow or deep index
            start_time: Start time for performance tracking

        Returns:
            True if rebuild succeeded, False otherwise
        """
        try:
            # Rebuild index
            if target_path:
                success = index_manager.refresh_index(target_path, shallow=shallow)
            else:
                index_manager.get_global_index(shallow=shallow, force_rebuild=True)
                success = True

            # Log performance metrics
            duration_ms = (time.time() - start_time) * 1000
            logger.info(
                f"Index rebuild completed in {duration_ms:.2f}ms "
                f"(shallow={shallow}, target={target_path or 'global'})"
            )

            if duration_ms > 100:
                logger.warning(f"Slow index rebuild detected: {duration_ms:.2f}ms")

            return success

        except Exception as e:
            logger.error(f"Failed to rebuild index: {e}")
            return False

    def _get_cached_max_mtime(self, path: str) -> float:
        """
        Get maximum source file mtime with caching.

        Uses class-level cache with 5-second TTL to avoid repeated stat calls.

        Args:
            path: Directory path to check

        Returns:
            Maximum mtime of source files under path
        """
        current_time = time.time()

        # Check cache
        cache_key = path
        if cache_key in BaseService._mtime_cache:
            cached_mtime, cached_time = BaseService._mtime_cache[cache_key]
            if current_time - cached_time < BaseService._mtime_cache_ttl:
                logger.debug(f"Using cached mtime for {path}")
                return cached_mtime

        # Calculate max mtime
        from ..indexing import get_layered_index_manager
        index_manager = get_layered_index_manager()
        max_mtime = index_manager._get_max_source_mtime(path)

        # Update cache
        BaseService._mtime_cache[cache_key] = (max_mtime, current_time)
        logger.debug(f"Cached mtime for {path}: {max_mtime}")

        return max_mtime
