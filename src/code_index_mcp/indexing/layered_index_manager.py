"""
Layered Index Manager - Unified index management with global and sub-path indexing.

This manager replaces JSONIndexManager, ShallowIndexManager, and DeepIndexManager
with a single unified system that supports:
- Global index at project root level
- Sub-path indexes for directory/file-specific searches
- Intelligent cache reuse when parent index rebuilds
- Cache invalidation when source files change
"""

import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from .json_index_builder import JSONIndexBuilder
from ..constants import SETTINGS_DIR, INDEX_FILE, INDEX_FILE_SHALLOW

logger = logging.getLogger(__name__)


class LayeredIndexManager:
    """
    Manages layered code indexes with global and sub-path caching.

    This manager provides:
    - Global index for entire project
    - Sub-path indexes cached separately
    - Cache key generation based on target_path
    - Automatic cache validation and invalidation
    """

    def __init__(self):
        self.project_path: Optional[str] = None
        self.index_builder: Optional[JSONIndexBuilder] = None
        self.temp_dir: Optional[str] = None
        self.global_index_path: Optional[str] = None
        self.global_shallow_path: Optional[str] = None
        self.subpath_cache_dir: Optional[str] = None
        self._lock = threading.RLock()
        logger.info("Initialized Layered Index Manager")

    def set_project_path(self, project_path: str) -> bool:
        """Set the project path and initialize index storage."""
        with self._lock:
            try:
                # Input validation
                if not project_path or not isinstance(project_path, str):
                    logger.error(f"Invalid project path: {project_path}")
                    return False

                project_path = project_path.strip()
                if not project_path:
                    logger.error("Project path cannot be empty")
                    return False

                if not os.path.isdir(project_path):
                    logger.error(f"Project path does not exist: {project_path}")
                    return False

                self.project_path = project_path
                self.index_builder = JSONIndexBuilder(project_path)

                # Create temp directory structure
                project_hash = hashlib.md5(project_path.encode()).hexdigest()[:12]
                self.temp_dir = os.path.join(tempfile.gettempdir(), SETTINGS_DIR, project_hash)
                os.makedirs(self.temp_dir, exist_ok=True)

                # Global index paths
                self.global_index_path = os.path.join(self.temp_dir, INDEX_FILE)
                self.global_shallow_path = os.path.join(self.temp_dir, INDEX_FILE_SHALLOW)

                # Sub-path cache directory
                self.subpath_cache_dir = os.path.join(self.temp_dir, "subpath_caches")
                os.makedirs(self.subpath_cache_dir, exist_ok=True)

                logger.info(f"Set project path: {project_path}")
                logger.info(f"Global index: {self.global_index_path}")
                logger.info(f"Sub-path cache: {self.subpath_cache_dir}")
                return True

            except Exception as e:
                logger.error(f"Failed to set project path: {e}")
                return False

    def get_global_index(self, shallow: bool = False, force_rebuild: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get or build the global index for the entire project.

        Args:
            shallow: If True, build/load shallow index (file list only)
            force_rebuild: Force rebuild even if index is fresh

        Returns:
            Index data or None if failed
        """
        with self._lock:
            if not self.index_builder or not self.project_path:
                logger.error("Index builder not initialized")
                return None

            try:
                if shallow:
                    return self._get_global_shallow_index(force_rebuild)
                else:
                    return self._get_global_deep_index(force_rebuild)

            except Exception as e:
                logger.error(f"Failed to get global index: {e}")
                return None

    def _get_global_deep_index(self, force_rebuild: bool = False) -> Optional[Dict[str, Any]]:
        """Get or build global deep index (with symbols)."""
        # Check if we need to rebuild
        if not force_rebuild and os.path.exists(self.global_index_path):
            if self._is_index_fresh(self.global_index_path):
                logger.info("Global deep index is fresh, loading from cache")
                return self.index_builder.load_index(self.global_index_path)

        # Build new index
        logger.info("Building global deep index...")
        index = self.index_builder.build_index()

        # Add metadata
        index.setdefault('_metadata', {})
        index['_metadata'].update({
            'build_time': time.time(),
            'files_indexed': len(index.get('files', {})),
            'max_mtime': self._get_max_source_mtime(self.project_path)
        })

        # Save to disk
        self.index_builder.save_index(index, self.global_index_path)
        logger.info(f"Built global deep index with {len(index.get('symbols', {}))} symbols")

        return index

    def _get_global_shallow_index(self, force_rebuild: bool = False) -> Optional[List[str]]:
        """Get or build global shallow index (file list only)."""
        # Check if we need to rebuild
        if not force_rebuild and os.path.exists(self.global_shallow_path):
            if self._is_index_fresh(self.global_shallow_path):
                logger.info("Global shallow index is fresh, loading from cache")
                with open(self.global_shallow_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return self._normalize_file_list(data)

        # Build new shallow index
        logger.info("Building global shallow index...")
        file_list = self.index_builder.build_shallow_file_list()

        # Save to disk with metadata
        cache_data = {
            '_metadata': {
                'build_time': time.time(),
                'files_indexed': len(file_list),
                'max_mtime': self._get_max_source_mtime(self.project_path),
                'target_path': self.project_path
            },
            'files': file_list
        }

        with open(self.global_shallow_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False)

        logger.info(f"Built global shallow index with {len(file_list)} files")
        return file_list

    def get_subpath_index(self, target_path: str, shallow: bool = False, force_rebuild: bool = False) -> Optional[Any]:
        """
        Get or build a sub-path index for a specific directory or file.

        Args:
            target_path: Absolute or relative path to index
            shallow: If True, return file list only
            force_rebuild: Force rebuild even if cache is valid

        Returns:
            Index data or file list, or None if failed
        """
        with self._lock:
            if not self.index_builder or not self.project_path:
                logger.error("Index builder not initialized")
                return None

            try:
                # Normalize target path
                if os.path.isabs(target_path):
                    target_path = os.path.relpath(target_path, self.project_path)
                target_path = target_path.replace('\\', '/')

                # Generate cache key
                cache_key = self._generate_cache_key(target_path, shallow)
                cache_path = os.path.join(self.subpath_cache_dir, f"{cache_key}.json")

                # Check cache validity
                if not force_rebuild and os.path.exists(cache_path):
                    if self._validate_cache(cache_path, target_path):
                        logger.info(f"Loading sub-path index from cache: {target_path}")
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            cached = json.load(f)
                            return cached.get('files') if shallow else cached.get('index')

                # Build new sub-path index
                logger.info(f"Building sub-path index for: {target_path}")
                full_target_path = os.path.join(self.project_path, target_path)

                if shallow:
                    # Build shallow file list for sub-path
                    temp_builder = JSONIndexBuilder(full_target_path)
                    file_list = temp_builder.build_shallow_file_list()
                    result = file_list
                else:
                    # Build deep index for sub-path
                    temp_builder = JSONIndexBuilder(full_target_path)
                    index = temp_builder.build_index()
                    result = index

                # Get parent index reference (global index mtime)
                parent_index_mtime = None
                parent_index_path = self.global_shallow_path if shallow else self.global_index_path
                if os.path.exists(parent_index_path):
                    parent_index_mtime = os.path.getmtime(parent_index_path)

                # Store cache with metadata
                cache_data = {
                    '_metadata': {
                        'target_path': target_path,
                        'parent_index_ref': parent_index_mtime,
                        'build_time': time.time(),
                        'max_mtime': self._get_max_source_mtime(full_target_path),
                        'is_shallow': shallow
                    },
                    'files' if shallow else 'index': result
                }

                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)

                logger.info(f"Built and cached sub-path index: {target_path}")
                return result

            except Exception as e:
                logger.error(f"Failed to get sub-path index: {e}")
                return None

    def _generate_cache_key(self, target_path: str, is_shallow: bool) -> str:
        """
        Generate cache key for a target path.

        Args:
            target_path: Normalized relative path
            is_shallow: Whether this is a shallow index

        Returns:
            Cache key string
        """
        # Include path and index type in hash
        path_hash = hashlib.md5(target_path.encode()).hexdigest()[:12]
        index_type = "shallow" if is_shallow else "deep"
        return f"{path_hash}_{index_type}"

    def _validate_cache(self, cache_path: str, target_path: str) -> bool:
        """
        Validate cache file against source files and parent index.

        Args:
            cache_path: Path to cache file
            target_path: Target path being indexed

        Returns:
            True if cache is valid, False otherwise
        """
        try:
            # Load cache metadata
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            metadata = cache_data.get('_metadata', {})
            parent_index_ref = metadata.get('parent_index_ref')
            cache_build_time = metadata.get('build_time', 0)
            cache_max_mtime = metadata.get('max_mtime', 0)
            is_shallow = metadata.get('is_shallow', False)

            # Check if parent index changed
            parent_index_path = self.global_shallow_path if is_shallow else self.global_index_path
            if parent_index_ref and os.path.exists(parent_index_path):
                current_parent_mtime = os.path.getmtime(parent_index_path)
                if current_parent_mtime > parent_index_ref:
                    logger.debug(f"Cache invalid: parent index changed for {target_path}")
                    return False

            # Check if source files changed
            full_target_path = os.path.join(self.project_path, target_path)
            current_max_mtime = self._get_max_source_mtime(full_target_path)
            if current_max_mtime > cache_max_mtime:
                logger.debug(f"Cache invalid: source files changed for {target_path}")
                return False

            logger.debug(f"Cache valid for {target_path}")
            return True

        except Exception as e:
            logger.warning(f"Error validating cache: {e}")
            return False

    def invalidate_cache(self, target_path: Optional[str] = None) -> bool:
        """
        Invalidate cache for a specific path or all caches.

        Args:
            target_path: Specific path to invalidate, or None for all

        Returns:
            True if successful
        """
        with self._lock:
            try:
                if target_path:
                    # Invalidate specific cache
                    target_path = target_path.replace('\\', '/')
                    for is_shallow in [True, False]:
                        cache_key = self._generate_cache_key(target_path, is_shallow)
                        cache_path = os.path.join(self.subpath_cache_dir, f"{cache_key}.json")
                        if os.path.exists(cache_path):
                            os.remove(cache_path)
                            logger.info(f"Invalidated cache for {target_path} ({'shallow' if is_shallow else 'deep'})")
                else:
                    # Invalidate all caches
                    if os.path.exists(self.subpath_cache_dir):
                        for cache_file in os.listdir(self.subpath_cache_dir):
                            cache_path = os.path.join(self.subpath_cache_dir, cache_file)
                            os.remove(cache_path)
                        logger.info("Invalidated all sub-path caches")

                return True

            except Exception as e:
                logger.error(f"Failed to invalidate cache: {e}")
                return False

    def _is_index_fresh(self, index_path: str) -> bool:
        """Check if an index file is fresh compared to source files."""
        if not os.path.exists(index_path):
            return False

        try:
            from ..utils.file_filter import FileFilter
            file_filter = FileFilter()

            index_mtime = os.path.getmtime(index_path)
            base_path = Path(self.project_path)

            # Check if any source files are newer than index
            for root, dirs, files in os.walk(self.project_path):
                dirs[:] = [d for d in dirs if not file_filter.should_exclude_directory(d)]

                for file in files:
                    file_path = Path(root) / file
                    if file_filter.should_process_path(file_path, base_path):
                        if os.path.getmtime(str(file_path)) > index_mtime:
                            return False

            return True

        except Exception as e:
            logger.warning(f"Error checking index freshness: {e}")
            return False

    def _get_max_source_mtime(self, path: str) -> float:
        """Get the maximum modification time of source files under a path."""
        try:
            from ..utils.file_filter import FileFilter
            file_filter = FileFilter()

            max_mtime = 0.0
            base_path = Path(path)

            if os.path.isfile(path):
                return os.path.getmtime(path)

            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not file_filter.should_exclude_directory(d)]

                for file in files:
                    file_path = Path(root) / file
                    if file_filter.should_process_path(file_path, base_path):
                        file_mtime = os.path.getmtime(str(file_path))
                        max_mtime = max(max_mtime, file_mtime)

            return max_mtime

        except Exception as e:
            logger.warning(f"Error getting max source mtime: {e}")
            return 0.0

    def _normalize_file_list(self, data: Any) -> List[str]:
        """Normalize file list from various formats."""
        if isinstance(data, dict):
            file_list = data.get('files', [])
        elif isinstance(data, list):
            file_list = data
        else:
            return []

        normalized = []
        for p in file_list:
            if isinstance(p, str):
                q = p.replace('\\\\', '/').replace('\\', '/')
                if q.startswith('./'):
                    q = q[2:]
                normalized.append(q)
        return normalized

    def find_files(self, pattern: str = "*", target_path: Optional[str] = None) -> List[str]:
        """
        Find files matching a glob pattern.

        Args:
            pattern: Glob pattern to match
            target_path: Optional sub-path to search within

        Returns:
            List of matching file paths
        """
        with self._lock:
            try:
                # Get appropriate index
                if target_path:
                    file_list = self.get_subpath_index(target_path, shallow=True)
                else:
                    file_list = self.get_global_index(shallow=True)

                if not file_list:
                    return []

                # Apply pattern matching
                import re
                import os
                norm_pattern = pattern.replace('\\\\', '/').replace('\\', '/')

                if norm_pattern == "*":
                    return file_list

                # Smart matching strategy:
                # - If pattern contains '/', match against full path
                # - If pattern contains no '/', match against basename only
                match_basename_only = '/' not in norm_pattern

                regex = self._compile_glob_regex(norm_pattern)

                if match_basename_only:
                    # Match against basename for simple filename patterns
                    return [f for f in file_list if regex.match(os.path.basename(f)) is not None]
                else:
                    # Match against full path for patterns with path separators
                    return [f for f in file_list if regex.match(f) is not None]

            except Exception as e:
                logger.error(f"Error finding files: {e}")
                return []

    def get_file_summary(self, file_path: str, target_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get summary information for a file.

        Args:
            file_path: Relative path to the file
            target_path: Optional sub-path context

        Returns:
            Dictionary containing file summary information
        """
        with self._lock:
            try:
                # Get appropriate index
                if target_path:
                    index = self.get_subpath_index(target_path, shallow=False)
                else:
                    index = self.get_global_index(shallow=False)

                if not index:
                    return None

                # Normalize file path
                file_path = file_path.replace('\\', '/').lstrip('./')

                # Get file info
                file_info = index.get("files", {}).get(file_path)
                if not file_info:
                    logger.warning(f"File not found in index: {file_path}")
                    return None

                # Get symbols for file
                symbols = []
                for symbol_id, symbol_data in index.get("symbols", {}).items():
                    symbol_file = symbol_data.get("file", "").replace("\\", "/")
                    if symbol_file == file_path:
                        symbols.append(symbol_data)

                # Categorize symbols
                functions = []
                classes = []
                methods = []

                for s in symbols:
                    signature = s.get("signature", "")
                    if signature:
                        if signature.startswith("def ") and "::" in signature:
                            methods.append(s)
                        elif signature.startswith("def "):
                            functions.append(s)
                        elif signature.startswith("class "):
                            classes.append(s)

                return {
                    "file_path": file_path,
                    "language": file_info.get("language"),
                    "line_count": file_info.get("line_count"),
                    "symbol_count": len(symbols),
                    "functions": functions,
                    "classes": classes,
                    "methods": methods,
                    "imports": file_info.get("imports", []),
                    "exports": file_info.get("exports", [])
                }

            except Exception as e:
                logger.error(f"Error getting file summary: {e}")
                return None

    def refresh_index(self, target_path: Optional[str] = None, shallow: bool = False) -> bool:
        """
        Refresh index by rebuilding.

        Args:
            target_path: Optional specific path to refresh
            shallow: Whether to refresh shallow or deep index

        Returns:
            True if successful
        """
        with self._lock:
            try:
                if target_path:
                    self.get_subpath_index(target_path, shallow=shallow, force_rebuild=True)
                else:
                    self.get_global_index(shallow=shallow, force_rebuild=True)
                return True
            except Exception as e:
                logger.error(f"Failed to refresh index: {e}")
                return False

    def cleanup(self):
        """Clean up resources."""
        with self._lock:
            self.project_path = None
            self.index_builder = None
            self.temp_dir = None
            self.global_index_path = None
            self.global_shallow_path = None
            self.subpath_cache_dir = None
            logger.info("Cleaned up Layered Index Manager")

    @staticmethod
    def _compile_glob_regex(pattern: str) -> 're.Pattern':
        """Compile a glob pattern to regex (same logic as old managers)."""
        import re
        i = 0
        out = []
        special = ".^$+{}[]|()"
        while i < len(pattern):
            c = pattern[i]
            if c == '*':
                if i + 1 < len(pattern) and pattern[i + 1] == '*':
                    out.append('.*')
                    i += 2
                    continue
                else:
                    out.append('[^/]*')
            elif c == '?':
                out.append('[^/]')
            elif c in special:
                out.append('\\' + c)
            else:
                out.append(c)
            i += 1
        return re.compile('^' + ''.join(out) + '$')


# Global singleton instance
_layered_manager = LayeredIndexManager()


def get_layered_index_manager() -> LayeredIndexManager:
    """Get the global layered index manager instance."""
    return _layered_manager
