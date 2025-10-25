# Migration Guide: Version 2.x to 3.x

## Overview

Version 3.x of Code Index MCP introduces significant architectural improvements that consolidate three specialized search tools into a single unified interface. This change simplifies the API, improves maintainability, and provides a more consistent user experience.

**Key Motivation:**
- **Simplified API**: One tool instead of three reduces cognitive load
- **Consistent Interface**: All search operations use the same parameter structure
- **Better Maintainability**: Single codebase for all search functionality
- **Enhanced Features**: Unified error handling and validation across all search modes

## Breaking Changes

### Removed Tools

The following MCP tools have been **removed** in version 3.x:

1. `search_code_advanced` - Replaced by `unified_search` with `mode='content'`
2. `find_files` - Replaced by `unified_search` with `mode='files'`
3. `get_file_summary` - Replaced by `unified_search` with `mode='summary'`

### New Unified Tool

All search operations now use:
- `unified_search` - Single tool with mode-based routing

## Migration Guide

### 1. Content Search (search_code_advanced → unified_search)

**Before (v2.x):**
```python
search_code_advanced(
    pattern="TODO",
    case_sensitive=True,
    context_lines=3,
    file_pattern="*.py",
    fuzzy=False,
    regex=True,
    max_line_length=500
)
```

**After (v3.x):**
```python
unified_search(
    mode="content",          # NEW: Required mode parameter
    pattern="TODO",
    case_sensitive=True,
    context_lines=3,
    file_pattern="*.py",
    fuzzy=False,
    regex=True,
    max_line_length=500
)
```

**Key Changes:**
- Add `mode='content'` parameter
- All other parameters remain identical
- Return format unchanged

---

### 2. File Discovery (find_files → unified_search)

**Before (v2.x):**
```python
find_files(pattern="*.py")
# Returns: ["src/main.py", "tests/test_main.py", ...]
```

**After (v3.x):**
```python
unified_search(
    mode="files",           # NEW: Required mode parameter
    pattern="*.py"
)
# Returns: {
#   "files": ["src/main.py", "tests/test_main.py", ...],
#   "total_count": 42
# }
```

**Key Changes:**
- Add `mode='files'` parameter
- Return format changed from `List[str]` to `Dict` with `files` and `total_count` keys
- Pattern matching behavior unchanged

---

### 3. File Summary (get_file_summary → unified_search)

**Before (v2.x):**
```python
get_file_summary(file_path="src/main.py")
# Returns: {
#   "file_path": "src/main.py",
#   "line_count": 150,
#   "functions": [...],
#   "classes": [...]
# }
```

**After (v3.x):**
```python
unified_search(
    mode="summary",         # NEW: Required mode parameter
    file_path="src/main.py"
)
# Returns: {
#   "file_path": "src/main.py",
#   "line_count": 150,
#   "functions": [...],
#   "classes": [...]
# }
```

**Key Changes:**
- Add `mode='summary'` parameter
- Use `file_path` parameter (not `pattern`)
- Return format unchanged

## Parameter Mapping Table

| Old Tool | Old Parameter | New Tool | New Parameter | Notes |
|----------|--------------|----------|---------------|-------|
| `search_code_advanced` | `pattern` | `unified_search` | `mode='content'` + `pattern` | Add mode parameter |
| `search_code_advanced` | `case_sensitive` | `unified_search` | `case_sensitive` | No change |
| `search_code_advanced` | `context_lines` | `unified_search` | `context_lines` | No change |
| `search_code_advanced` | `file_pattern` | `unified_search` | `file_pattern` | No change |
| `search_code_advanced` | `fuzzy` | `unified_search` | `fuzzy` | No change |
| `search_code_advanced` | `regex` | `unified_search` | `regex` | No change |
| `search_code_advanced` | `max_line_length` | `unified_search` | `max_line_length` | No change |
| `find_files` | `pattern` | `unified_search` | `mode='files'` + `pattern` | Add mode, return format changes |
| `get_file_summary` | `file_path` | `unified_search` | `mode='summary'` + `file_path` | Add mode parameter |

## Version Compatibility Matrix

| Feature | v2.x | v3.x | Migration Action |
|---------|------|------|------------------|
| `search_code_advanced` | Available | **Removed** | Use `unified_search(mode='content', ...)` |
| `find_files` | Available | **Removed** | Use `unified_search(mode='files', ...)` |
| `get_file_summary` | Available | **Removed** | Use `unified_search(mode='summary', ...)` |
| `unified_search` | Not available | **New** | Single tool for all search operations |
| Auto-refresh | FileWatcher only | On-demand + Optional FileWatcher | Install `watchdog` if needed |
| Config storage | `config.json` | MCP Config | Auto-migrated on first startup |
| LayeredIndexManager | Not available | **New** | Improved caching architecture |

## Automated Migration

### Search and Replace Pattern

For codebases using the Python MCP client:

```python
# Pattern 1: search_code_advanced
# OLD:
search_code_advanced(pattern="...", ...)

# NEW:
unified_search(mode="content", pattern="...", ...)

# Pattern 2: find_files
# OLD:
files = find_files(pattern="*.py")

# NEW:
result = unified_search(mode="files", pattern="*.py")
files = result["files"]  # Extract file list from new format

# Pattern 3: get_file_summary
# OLD:
summary = get_file_summary(file_path="...")

# NEW:
summary = unified_search(mode="summary", file_path="...")
```

### Migration Script Example

```python
#!/usr/bin/env python3
"""
Automated migration script for Code Index MCP v2.x to v3.x
"""
import re
import sys
from pathlib import Path

def migrate_search_code_advanced(content):
    """Replace search_code_advanced with unified_search mode='content'"""
    pattern = r'search_code_advanced\('
    replacement = r'unified_search(mode="content", '
    return re.sub(pattern, replacement, content)

def migrate_find_files(content):
    """Replace find_files with unified_search mode='files'"""
    # Simple case: direct assignment
    pattern = r'(\w+)\s*=\s*find_files\(pattern='
    replacement = r'\1_result = unified_search(mode="files", pattern='
    content = re.sub(pattern, replacement, content)

    # Add extraction step
    pattern = r'(\w+)_result = unified_search\(mode="files"'
    def add_extraction(match):
        var_name = match.group(1)
        return f'{var_name}_result = unified_search(mode="files"'

    return content

def migrate_get_file_summary(content):
    """Replace get_file_summary with unified_search mode='summary'"""
    pattern = r'get_file_summary\('
    replacement = r'unified_search(mode="summary", '
    return re.sub(pattern, replacement, content)

def migrate_file(file_path):
    """Migrate a single Python file"""
    content = file_path.read_text()
    original = content

    content = migrate_search_code_advanced(content)
    content = migrate_find_files(content)
    content = migrate_get_file_summary(content)

    if content != original:
        file_path.write_text(content)
        print(f"Migrated: {file_path}")
        return True
    return False

def main():
    """Migrate all Python files in a directory"""
    if len(sys.argv) < 2:
        print("Usage: migrate.py <directory>")
        sys.exit(1)

    root = Path(sys.argv[1])
    migrated = 0

    for py_file in root.rglob("*.py"):
        if migrate_file(py_file):
            migrated += 1

    print(f"\nMigration complete: {migrated} files updated")

if __name__ == "__main__":
    main()
```

## Upgrade Path

### Step 1: Backup Current Configuration
```bash
# Config is auto-backed up, but manual backup recommended
cp ~/.cache/code-index-mcp/config.json ~/.cache/code-index-mcp/config.json.backup
```

### Step 2: Update Package
```bash
# Using uvx (recommended)
# No action needed - uvx automatically uses latest version

# Using pip
pip install --upgrade code-index-mcp

# Verify version
pip show code-index-mcp | grep Version
```

### Step 3: Restart MCP Server
- Restart your MCP client (Claude Desktop, etc.)
- Configuration will auto-migrate from `config.json` to MCP Config on first startup

### Step 4: Update Client Code
- Apply migration patterns from "Migration Guide" section above
- Run migration script if using Python client
- Test each search mode to ensure correct behavior

### Step 5: Optional - Install FileWatcher
```bash
# For automatic index refresh on file changes
pip install code-index-mcp[watcher]

# Or install watchdog separately
pip install watchdog
```

## Troubleshooting

### Issue: Tool not found error

**Error Message:**
```
Error: Tool 'search_code_advanced' not found
Error: Tool 'find_files' not found
Error: Tool 'get_file_summary' not found
```

**Solution:**
You're running v3.x but using v2.x tool names. Update your code to use `unified_search` with appropriate mode:
- `search_code_advanced(...)` → `unified_search(mode='content', ...)`
- `find_files(...)` → `unified_search(mode='files', ...)`
- `get_file_summary(...)` → `unified_search(mode='summary', ...)`

---

### Issue: Config migration failed

**Error Message:**
```
WARNING: Config migration error, using defaults
```

**Solution:**
1. **Option A - Manual Migration:**
   ```bash
   # Check existing config
   cat ~/.cache/code-index-mcp/config.json

   # Manually set via MCP tools after server starts
   # Use set_project_path and configure_file_watcher
   ```

2. **Option B - Start Fresh:**
   ```bash
   # Backup old config
   mv ~/.cache/code-index-mcp/config.json ~/.cache/code-index-mcp/config.json.old

   # Restart server - will create default config
   # Then reconfigure using MCP tools
   ```

---

### Issue: FileWatcher not working

**Error Message:**
```
WARNING: FileWatcher could not be started
```

**Solution:**
Install the `watchdog` package:
```bash
# Full installation with watcher support
pip install code-index-mcp[watcher]

# Or install watchdog separately
pip install watchdog

# Restart your MCP server
# Then enable file watcher
# Use: configure_file_watcher(enabled=True)
```

**Fallback:**
Use on-demand refresh instead:
```
# After making file changes, manually refresh
Call: refresh_index()
```

---

### Issue: Index not refreshing automatically

**Expected Behavior in v3.x:**
Auto-refresh requires explicit FileWatcher installation and configuration.

**Solution:**
1. Install watchdog: `pip install watchdog`
2. Enable file watcher: `configure_file_watcher(enabled=True)`
3. Check status: `get_file_watcher_status()`
4. If disabled, use manual refresh: `refresh_index()`

---

### Issue: Parameter not recognized

**Error Message:**
```
TypeError: unified_search() got an unexpected keyword argument 'pattern'
```

**Solution:**
Check that you're including the `mode` parameter:
```python
# WRONG - missing mode parameter
unified_search(pattern="*.py")

# CORRECT - mode specifies search type
unified_search(mode="files", pattern="*.py")
```

**Parameter Requirements by Mode:**
- `mode='content'`: Requires `pattern`
- `mode='files'`: Requires `pattern`
- `mode='summary'`: Requires `file_path` (not pattern)

---

### Issue: find_files return format changed

**Problem:**
Old code expects a list, but v3.x returns a dictionary.

**Before (v2.x):**
```python
files = find_files("*.py")  # Returns list directly
for f in files:
    print(f)
```

**After (v3.x):**
```python
result = unified_search(mode="files", pattern="*.py")  # Returns dict
files = result["files"]  # Extract list
total = result["total_count"]  # Bonus: get count
for f in files:
    print(f)
```

## FAQ

### Q: Why consolidate the tools?

**A:** Three main reasons:
1. **Simplicity**: One tool is easier to learn and use than three separate tools
2. **Consistency**: All search operations now share the same error handling and validation
3. **Maintainability**: Single codebase reduces bugs and makes improvements easier to implement

---

### Q: Is there a performance impact?

**A:** No, performance is improved:
- New LayeredIndexManager provides better caching
- On-demand refresh reduces unnecessary index rebuilds
- Same underlying search engines (ugrep, ripgrep, etc.)
- Mode-based routing adds negligible overhead

---

### Q: Can I still use the old tools?

**A:** No, this is a breaking change in v3.x:
- Old tools are completely removed from the codebase
- You must migrate to `unified_search`
- Use the migration script provided in this guide for automated updates

---

### Q: What if I need to roll back to v2.x?

**A:** Rollback is supported:
```bash
# Pin to last v2.x version
pip install code-index-mcp==2.4.1

# Restore backup config if needed
cp ~/.cache/code-index-mcp/config.json.backup ~/.cache/code-index-mcp/config.json

# Restart MCP server
```

**Note:** Config format is backward compatible, so v2.x can read v3.x configs.

---

### Q: Does auto-refresh still work?

**A:** Yes, but with changes:
- **v2.x**: FileWatcher was always enabled
- **v3.x**: On-demand refresh by default, FileWatcher is optional
- **To enable**: Install `watchdog` and use `configure_file_watcher(enabled=True)`
- **Alternative**: Use `refresh_index()` for manual updates

---

### Q: Are there any new features in v3.x?

**A:** Yes, several improvements:
1. **LayeredIndexManager**: Multi-tier caching architecture
2. **MCP Config Integration**: Better configuration management
3. **Unified Search**: Simplified API with mode-based routing
4. **Better Error Messages**: Consistent validation across all modes
5. **Optional FileWatcher**: Choose automatic or on-demand refresh

## Additional Resources

- [README.md](README.md) - Full documentation with examples
- [GitHub Issues](https://github.com/johnhuang316/code-index-mcp/issues) - Report problems or ask questions
- [MCP Documentation](https://modelcontextprotocol.io) - Learn more about Model Context Protocol

## Support

If you encounter issues not covered in this guide:

1. Check existing [GitHub Issues](https://github.com/johnhuang316/code-index-mcp/issues)
2. Review the [README.md](README.md) for updated examples
3. Create a new issue with:
   - Error message (full traceback)
   - Code example showing the problem
   - Version information (`pip show code-index-mcp`)
   - Steps to reproduce

---

**Last Updated:** 2025-01-25
**Version:** 3.0.0
