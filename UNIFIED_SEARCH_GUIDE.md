# unified_search 详细使用指南
# Detailed Guide for unified_search

---

## 📖 目录 / Table of Contents

1. [概述 / Overview](#概述--overview)
2. [模式 1: 内容搜索 / Mode 1: Content Search](#模式-1-内容搜索--mode-1-content-search)
3. [模式 2: 文件搜索 / Mode 2: Files Search](#模式-2-文件搜索--mode-2-files-search)
4. [模式 3: 文件摘要 / Mode 3: Summary Mode](#模式-3-文件摘要--mode-3-summary-mode)
5. [完整示例 / Complete Examples](#完整示例--complete-examples)
6. [常见问题 / FAQ](#常见问题--faq)

---

## 概述 / Overview

### English

`unified_search` is the **core tool** of Code Index MCP Simple. It provides three search modes in a single interface:

- **`content`** - Search for code patterns in file contents
- **`files`** - Find files by name/path patterns
- **`summary`** - Analyze file structure and symbols

All modes share the same entry point but provide different functionality based on the `mode` parameter.

### 中文

`unified_search` 是 Code Index MCP Simple 的**核心工具**。它在单一接口中提供三种搜索模式：

- **`content`** - 在文件内容中搜索代码模式
- **`files`** - 按名称/路径模式查找文件
- **`summary`** - 分析文件结构和符号

所有模式共享相同的入口点，但根据 `mode` 参数提供不同的功能。

---

## 模式 1: 内容搜索 / Mode 1: Content Search

### 基本用法 / Basic Usage

**English:** Search for text patterns within file contents.

**中文：** 在文件内容中搜索文本模式。

```python
unified_search(
    mode='content',
    pattern='your_search_pattern'
)
```

### 完整参数列表 / Complete Parameters

| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `mode` | `str` | ✅ Yes | Must be `'content'` / 必须为 `'content'` |
| `pattern` | `str` | ✅ Yes | Search pattern / 搜索模式 |
| `case_sensitive` | `bool` | ❌ No | Case-sensitive search (default: `false`) / 区分大小写（默认：`false`） |
| `regex` | `bool` | ❌ No | Use regex pattern (default: `false`) / 使用正则表达式（默认：`false`） |
| `fuzzy` | `bool` | ❌ No | Fuzzy matching (default: `false`) / 模糊匹配（默认：`false`） |
| `file_pattern` | `str` | ❌ No | Filter by file glob pattern / 按文件 glob 模式过滤 |
| `context_lines` | `int` | ❌ No | Number of context lines (default: `2`) / 上下文行数（默认：`2`） |
| `max_line_length` | `int` | ❌ No | Maximum line length (default: `1000`) / 最大行长度（默认：`1000`） |

### 返回值 / Return Value

```json
{
  "results": [
    {
      "file": "path/to/file.py",
      "line_number": 123,
      "line": "def fluid_dynamics():",
      "column": 5,
      "context_before": ["# Previous line 1", "# Previous line 2"],
      "context_after": ["    return value", ""]
    }
  ],
  "total_results": 42,
  "search_info": {
    "pattern": "fluid",
    "case_sensitive": false,
    "regex": false,
    "fuzzy": false,
    "file_pattern": "*.py"
  }
}
```

### 使用场景 / Use Cases

#### 1. 基础文本搜索 / Basic Text Search

**English:** Find all occurrences of a simple string.

**中文：** 查找简单字符串的所有出现。

```python
# Find all TODO comments
unified_search(mode='content', pattern='TODO')

# Find specific function name
unified_search(mode='content', pattern='calculate_total')
```

#### 2. 区分大小写搜索 / Case-Sensitive Search

**English:** Search with exact case matching.

**中文：** 精确大小写匹配搜索。

```python
# Find 'Fluid' class (not 'fluid' variable)
unified_search(
    mode='content',
    pattern='Fluid',
    case_sensitive=True
)
```

#### 3. 正则表达式搜索 / Regex Search

**English:** Use regex patterns for advanced matching.

**中文：** 使用正则表达式进行高级匹配。

```python
# Find all function definitions
unified_search(
    mode='content',
    pattern=r'def\s+\w+\s*\(',
    regex=True
)

# Find all fluid-related variables (fluid_*, *_fluid, fluid*)
unified_search(
    mode='content',
    pattern=r'fluid[_\w]*',
    regex=True
)

# Find all TODO or FIXME comments
unified_search(
    mode='content',
    pattern=r'(TODO|FIXME):',
    regex=True
)
```

#### 4. 模糊搜索 / Fuzzy Search

**English:** Find approximate matches (typos, variations).

**中文：** 查找近似匹配（拼写错误、变体）。

```python
# Find 'authenticate', 'authUser', 'userAuth', etc.
unified_search(
    mode='content',
    pattern='authUser',
    fuzzy=True
)
```

#### 5. 文件类型过滤 / File Type Filtering

**English:** Limit search to specific file types.

**中文：** 限制搜索到特定文件类型。

```python
# Search only in Python files
unified_search(
    mode='content',
    pattern='import numpy',
    file_pattern='*.py'
)

# Search only in TypeScript/JavaScript files
unified_search(
    mode='content',
    pattern='useState',
    file_pattern='*.{ts,tsx,js,jsx}'
)

# Search in test files only
unified_search(
    mode='content',
    pattern='assert',
    file_pattern='test_*.py'
)
```

#### 6. 上下文行数 / Context Lines

**English:** Show surrounding code for better understanding.

**中文：** 显示周围代码以更好理解。

```python
# Show 5 lines before and after each match
unified_search(
    mode='content',
    pattern='class DatabaseConnection',
    context_lines=5
)
```

#### 7. 组合使用 / Combined Usage

**English:** Combine multiple parameters for precise searches.

**中文：** 组合多个参数进行精确搜索。

```python
# Find 'API_ENDPOINT' in Python files, case-sensitive, with context
unified_search(
    mode='content',
    pattern='API_ENDPOINT',
    case_sensitive=True,
    file_pattern='*.py',
    context_lines=3
)

# Find all error handling in JavaScript files
unified_search(
    mode='content',
    pattern=r'(try|catch|throw|Error)',
    regex=True,
    file_pattern='*.{js,ts}',
    context_lines=2
)
```

---

## 模式 2: 文件搜索 / Mode 2: Files Search

### 基本用法 / Basic Usage

**English:** Find files by name or path patterns.

**中文：** 按名称或路径模式查找文件。

```python
unified_search(
    mode='files',
    pattern='your_file_pattern'
)
```

### 完整参数列表 / Complete Parameters

| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `mode` | `str` | ✅ Yes | Must be `'files'` / 必须为 `'files'` |
| `pattern` | `str` | ✅ Yes | Glob pattern for file matching / 文件匹配的 glob 模式 |

### 返回值 / Return Value

```json
{
  "files": [
    "src/components/Auth.tsx",
    "src/components/AuthButton.tsx",
    "tests/test_auth.py"
  ],
  "total_count": 3
}
```

### Glob 模式语法 / Glob Pattern Syntax

| Pattern / 模式 | Matches / 匹配 | Example / 示例 |
|----------------|---------------|----------------|
| `*` | Any characters (single level) / 任意字符（单级） | `*.py` → `test.py` |
| `**` | Any characters (multi-level) / 任意字符（多级） | `**/*.py` → `src/utils/test.py` |
| `?` | Single character / 单个字符 | `test?.py` → `test1.py` |
| `[abc]` | Character set / 字符集 | `test[123].py` → `test1.py` |
| `{a,b}` | Alternatives / 选择项 | `*.{js,ts}` → `app.js`, `app.ts` |

### 使用场景 / Use Cases

#### 1. 按文件扩展名查找 / Find by Extension

**English:** Find all files with specific extensions.

**中文：** 查找所有具有特定扩展名的文件。

```python
# All Python files
unified_search(mode='files', pattern='**/*.py')

# All TypeScript/JavaScript files
unified_search(mode='files', pattern='**/*.{ts,tsx,js,jsx}')

# All configuration files
unified_search(mode='files', pattern='**/*.{json,yaml,yml,toml}')
```

#### 2. 按文件名模式查找 / Find by Name Pattern

**English:** Find files matching specific naming patterns.

**中文：** 查找匹配特定命名模式的文件。

```python
# All test files
unified_search(mode='files', pattern='**/test_*.py')

# All component files
unified_search(mode='files', pattern='**/Component*.tsx')

# All index files
unified_search(mode='files', pattern='**/index.{js,ts}')
```

#### 3. 按目录查找 / Find by Directory

**English:** Find files in specific directories.

**中文：** 在特定目录中查找文件。

```python
# All files in src directory
unified_search(mode='files', pattern='src/**/*')

# All files in tests directory
unified_search(mode='files', pattern='tests/**/*.py')

# All files in components subdirectory
unified_search(mode='files', pattern='**/components/*.tsx')
```

#### 4. 精确文件名 / Exact Filename

**English:** Find specific file by exact name.

**中文：** 按精确名称查找特定文件。

```python
# Find main.py anywhere in project
unified_search(mode='files', pattern='**/main.py')

# Find package.json at any level
unified_search(mode='files', pattern='**/package.json')
```

#### 5. 复杂模式 / Complex Patterns

**English:** Combine multiple patterns for specific searches.

**中文：** 组合多个模式进行特定搜索。

```python
# All Python files starting with 'test_' or 'spec_'
unified_search(mode='files', pattern='**/{test_,spec_}*.py')

# All React component files (tsx/jsx)
unified_search(mode='files', pattern='src/components/**/*.{tsx,jsx}')

# All service layer files
unified_search(mode='files', pattern='**/services/**/*Service.{ts,js}')
```

---

## 模式 3: 文件摘要 / Mode 3: Summary Mode

### 基本用法 / Basic Usage

**English:** Analyze file structure, functions, classes, and complexity.

**中文：** 分析文件结构、函数、类和复杂度。

```python
unified_search(
    mode='summary',
    file_path='path/to/file.py'
)
```

### 完整参数列表 / Complete Parameters

| Parameter / 参数 | Type / 类型 | Required / 必需 | Description / 描述 |
|------------------|-------------|-----------------|-------------------|
| `mode` | `str` | ✅ Yes | Must be `'summary'` / 必须为 `'summary'` |
| `file_path` | `str` | ✅ Yes | Path to file for analysis / 要分析的文件路径 |

### 前置条件 / Prerequisites

**English:** Requires deep index to be built first.

**中文：** 需要先构建深度索引。

```python
# Step 1: Build deep index (run once or after major changes)
build_deep_index()

# Step 2: Analyze files
unified_search(mode='summary', file_path='src/main.py')
```

### 返回值 / Return Value

```json
{
  "file_path": "src/main.py",
  "line_count": 250,
  "functions": [
    {
      "name": "calculate_total",
      "line_number": 45,
      "params": ["items", "tax_rate"],
      "return_type": "float",
      "complexity": 5
    }
  ],
  "classes": [
    {
      "name": "DatabaseConnection",
      "line_number": 10,
      "methods": ["connect", "disconnect", "query"],
      "complexity": 12
    }
  ],
  "imports": [
    {"name": "numpy", "alias": "np", "line": 1},
    {"name": "pandas", "alias": "pd", "line": 2}
  ],
  "complexity_metrics": {
    "cyclomatic_complexity": 18,
    "cognitive_complexity": 22,
    "maintainability_index": 68.5
  }
}
```

### 使用场景 / Use Cases

#### 1. 代码审查 / Code Review

**English:** Analyze file before reviewing.

**中文：** 在审查前分析文件。

```python
# Get overview of file structure
unified_search(mode='summary', file_path='src/services/user_service.py')

# Review output to understand:
# - Number of functions/classes
# - Complexity metrics
# - Import dependencies
```

#### 2. 重构决策 / Refactoring Decisions

**English:** Identify complex files needing refactoring.

**中文：** 识别需要重构的复杂文件。

```python
# Analyze file complexity
result = unified_search(mode='summary', file_path='src/legacy_code.py')

# If complexity_metrics.cyclomatic_complexity > 15:
#   → File needs refactoring
```

#### 3. 依赖分析 / Dependency Analysis

**English:** Understand file dependencies.

**中文：** 理解文件依赖关系。

```python
# Check what modules a file imports
result = unified_search(mode='summary', file_path='src/main.py')

# result['imports'] shows all dependencies
```

#### 4. API 文档生成 / API Documentation

**English:** Extract function signatures for documentation.

**中文：** 提取函数签名用于文档。

```python
# Get all public functions
result = unified_search(mode='summary', file_path='src/api.py')

# result['functions'] provides:
# - Function names
# - Parameters
# - Return types
```

---

## 完整示例 / Complete Examples

### 示例 1: 在 multiphysics_network 项目中搜索 "fluid"
### Example 1: Search for "fluid" in multiphysics_network project

```python
# Step 1: Set project path (auto-builds ALL indexes!) / 步骤 1：设置项目路径（自动构建所有索引！）
set_project_path(r"D:\dongdiankaifa9\multiphysics_network")
# ✅ This automatically builds shallow + deep indexes
# ✅ 这会自动构建浅层和深度索引

# Step 2: Search for "fluid" (ready immediately!) / 步骤 2：搜索 "fluid"（立即可用！）

# 3a. Basic search / 基础搜索
basic_results = unified_search(
    mode='content',
    pattern='fluid'
)
print(f"Found {basic_results['total_results']} matches")

# 3b. Search only in Python files / 仅在 Python 文件中搜索
python_results = unified_search(
    mode='content',
    pattern='fluid',
    file_pattern='*.py'
)

# 3c. Regex search for fluid variables / 正则搜索流体变量
regex_results = unified_search(
    mode='content',
    pattern=r'fluid[_\w]*',
    regex=True,
    file_pattern='*.py'
)

# 3d. Find all Python files / 查找所有 Python 文件
all_py_files = unified_search(
    mode='files',
    pattern='**/*.py'
)
print(f"Total Python files: {all_py_files['total_count']}")
```

### 示例 2: 代码审查工作流
### Example 2: Code Review Workflow

```python
# Step 1: Set project (auto-indexes!) / 设置项目（自动索引！）
set_project_path(r"D:\my-project")

# Step 2: Find all Python files / 查找所有 Python 文件
changed_files = unified_search(
    mode='files',
    pattern='src/**/*.py'
)

# Step 3: Analyze each file (deep index already built!) / 分析每个文件（深度索引已构建！）
for file_path in changed_files['files']:
    summary = unified_search(
        mode='summary',
        file_path=file_path
    )

    # Check complexity / 检查复杂度
    if summary['complexity_metrics']['cyclomatic_complexity'] > 15:
        print(f"⚠️ High complexity: {file_path}")

    # Check function count / 检查函数数量
    if len(summary['functions']) > 20:
        print(f"⚠️ Too many functions: {file_path}")
```

### 示例 3: 查找和分析特定模式
### Example 3: Find and Analyze Specific Patterns

```python
# Find all files with database connections / 查找所有数据库连接文件
db_files = unified_search(
    mode='content',
    pattern='DatabaseConnection',
    file_pattern='**/*.py'
)

# Analyze each file with database code / 分析每个数据库代码文件
for result in db_files['results']:
    file_path = result['file']

    # Get detailed analysis / 获取详细分析
    summary = unified_search(
        mode='summary',
        file_path=file_path
    )

    print(f"File: {file_path}")
    print(f"Functions: {len(summary['functions'])}")
    print(f"Classes: {len(summary['classes'])}")
    print(f"Complexity: {summary['complexity_metrics']['cyclomatic_complexity']}")
    print("---")
```

---

## 常见问题 / FAQ

### Q1: 如何搜索多个关键词？/ How to search for multiple keywords?

**English:**

```python
# Use regex with OR operator
unified_search(
    mode='content',
    pattern=r'(keyword1|keyword2|keyword3)',
    regex=True
)
```

**中文：**

```python
# 使用正则表达式的 OR 运算符
unified_search(
    mode='content',
    pattern=r'(关键词1|关键词2|关键词3)',
    regex=True
)
```

### Q2: 如何排除某些文件类型？/ How to exclude certain file types?

**English:** Use negative file patterns (not directly supported, filter results instead).

**中文：** 使用负文件模式（不直接支持，改为过滤结果）。

```python
# Instead of excluding, be specific with file_pattern
unified_search(
    mode='content',
    pattern='search_term',
    file_pattern='*.{py,js,ts}'  # Only include these types
)
```

### Q3: Summary 模式显示 "needs deep index"？/ Summary mode shows "needs deep index"?

**English:** This should NOT happen with the latest version! `set_project_path()` auto-builds deep index.

If you still see this error:
1. Check if you used `set_project_path(build_deep=False)`
2. Manually run `build_deep_index()` to rebuild

**中文：** 最新版本不应该出现这个问题！`set_project_path()` 会自动构建深度索引。

如果仍然看到此错误：
1. 检查是否使用了 `set_project_path(build_deep=False)`
2. 手动运行 `build_deep_index()` 重建

```python
# Normally NOT needed (auto-built by default)
# 通常不需要（默认自动构建）
build_deep_index()
```

### Q4: 如何搜索特定目录？/ How to search in specific directory?

**English:**

```python
# Content search in specific directory
unified_search(
    mode='content',
    pattern='search_term',
    file_pattern='src/components/**/*.tsx'
)

# File search in specific directory
unified_search(
    mode='files',
    pattern='src/utils/**/*.py'
)
```

**中文：**

```python
# 在特定目录中搜索内容
unified_search(
    mode='content',
    pattern='搜索词',
    file_pattern='src/components/**/*.tsx'
)

# 在特定目录中搜索文件
unified_search(
    mode='files',
    pattern='src/utils/**/*.py'
)
```

### Q5: 搜索结果太多怎么办？/ Too many search results?

**English:** Add more specific filters:

**中文：** 添加更具体的过滤器：

```python
# More specific pattern
unified_search(
    mode='content',
    pattern=r'\bexact_function_name\b',  # Word boundaries
    regex=True,
    file_pattern='src/**/*.py'  # Specific directory
)
```

### Q6: 如何区分大小写？/ How to make search case-sensitive?

**English:**

```python
unified_search(
    mode='content',
    pattern='SearchTerm',
    case_sensitive=True  # ← Add this
)
```

**中文：**

```python
unified_search(
    mode='content',
    pattern='搜索词',
    case_sensitive=True  # ← 添加这个
)
```

---

## 性能建议 / Performance Tips

### English

1. **Use specific file patterns** - Narrow down search scope
2. **Build deep index once** - Only rebuild when structure changes significantly
3. **Combine filters** - Use `file_pattern` + `case_sensitive` together
4. **Use regex wisely** - Simple string search is faster than regex

### 中文

1. **使用具体的文件模式** - 缩小搜索范围
2. **只构建一次深度索引** - 仅在结构发生重大变化时重建
3. **组合过滤器** - 同时使用 `file_pattern` + `case_sensitive`
4. **明智使用正则** - 简单字符串搜索比正则表达式快

---

## 下一步 / Next Steps

**English:**

1. Try basic searches in your project
2. Experiment with regex patterns
3. Build deep index and explore summary mode
4. Combine modes for comprehensive analysis

**中文：**

1. 在你的项目中尝试基础搜索
2. 实验正则表达式模式
3. 构建深度索引并探索摘要模式
4. 组合模式进行综合分析

---

**Need more help? / 需要更多帮助？**

See [TESTING.md](TESTING.md) for interactive testing with MCP Inspector.
查看 [TESTING.md](TESTING.md) 了解如何使用 MCP Inspector 进行交互式测试。
