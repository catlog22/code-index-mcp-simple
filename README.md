# Code Index MCP Simple

<div align="center">

[![MCP Server](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Intelligent code indexing and analysis for Large Language Models**
**为大型语言模型提供智能代码索引和分析**

Transform how AI understands your codebase with advanced search, analysis, and navigation capabilities.
通过高级搜索、分析和导航功能，改变 AI 理解代码库的方式。

</div>

---

> **🔔 Project Notice / 项目说明**
>
> This is a fork of [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) by johnhuang316, with enhanced features and improvements.
> 本项目是 [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) 的分支版本，由 johnhuang316 创建，包含功能增强和改进。

---

> **⚠️ BREAKING CHANGES IN v3.x / v3.x 版本重大变更**
>
> Version 3.x consolidates three search tools (`search_code_advanced`, `find_files`, `get_file_summary`) into a single `unified_search` tool. See [MIGRATION.md](MIGRATION.md) for upgrade guide.
> v3.x 版本将三个搜索工具（`search_code_advanced`、`find_files`、`get_file_summary`）整合为单一的 `unified_search` 工具。升级指南请参见 [MIGRATION.md](MIGRATION.md)。

---

## Overview / 概述

**English:**

Code Index MCP Simple is a [Model Context Protocol](https://modelcontextprotocol.io) server that bridges the gap between AI models and complex codebases. It provides intelligent indexing, advanced search capabilities, and detailed code analysis to help AI assistants understand and navigate your projects effectively.

**Perfect for:** Code review, refactoring, documentation generation, debugging assistance, and architectural analysis.

**中文：**

Code Index MCP Simple 是一个 [模型上下文协议（MCP）](https://modelcontextprotocol.io) 服务器，弥合了 AI 模型与复杂代码库之间的差距。它提供智能索引、高级搜索功能和详细的代码分析，帮助 AI 助手有效地理解和导航你的项目。

**适用于：** 代码审查、重构、文档生成、调试辅助和架构分析。

---

## Quick Start / 快速开始

### 🚀 Installation / 安装

#### Prerequisites / 前置要求
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended / 推荐)

#### Method 1: Using uvx (Recommended) / 方法 1：使用 uvx（推荐）

**English:** The easiest way to get started with any MCP-compatible application:

**中文：** 使用 MCP 兼容应用程序最简单的方式：

1. **Clone the repository / 克隆仓库:**
   ```bash
   git clone https://github.com/catlog22/code-index-mcp-simple.git
   cd code-index-mcp-simple
   ```

2. **Add to your MCP configuration / 添加到 MCP 配置** (e.g., `claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "code-index-simple": {
         "command": "uv",
         "args": [
           "--directory",
           "G:\\github_lib\\code-index-mcp-simple",
           "run",
           "code-index-mcp-simple"
         ]
       }
     }
   }
   ```

3. **Restart your application / 重启应用程序** – Changes will take effect / 更改将生效

4. **Start using / 开始使用** (give these prompts to your AI assistant / 向 AI 助手发送以下提示):
   ```
   Set the project path to G:\my-project
   设置项目路径为 G:\my-project

   Find all TypeScript files in this project
   查找项目中所有的 TypeScript 文件

   Search for "authentication" functions
   搜索 "authentication" 相关函数

   Analyze the main App.tsx file
   分析 App.tsx 主文件
   ```

#### Method 2: Local Development / 方法 2：本地开发

**English:** For contributing or local development:

**中文：** 用于贡献代码或本地开发：

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

**Debug with MCP Inspector / 使用 MCP Inspector 调试:**
```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

---

## Typical Use Cases / 典型使用场景

**English:**
- **Code Review**: "Find all places using the old API"
- **Refactoring Help**: "Where is this function called?"
- **Learning Projects**: "Show me the main components of this React project"
- **Debugging**: "Search for all error handling related code"

**中文：**
- **代码审查**: "查找所有使用旧 API 的地方"
- **重构帮助**: "这个函数在哪里被调用？"
- **学习项目**: "展示这个 React 项目的主要组件"
- **调试**: "搜索所有错误处理相关的代码"

---

## Key Features / 核心特性

### 🔍 Intelligent Search & Analysis / 智能搜索与分析

**English:**
- **Dual-Strategy Architecture**: Specialized tree-sitter parsing for 7 core languages, fallback strategy for 50+ file types
- **Direct Tree-sitter Integration**: No regex fallbacks for specialized languages - fail fast with clear errors
- **Advanced Search**: Auto-detects and uses the best available tool (ugrep, ripgrep, ag, or grep)
- **Universal File Support**: Comprehensive coverage from advanced AST parsing to basic file indexing
- **File Analysis**: Deep insights into structure, imports, classes, methods, and complexity metrics

**中文：**
- **双策略架构**: 7 种核心语言使用专业的 tree-sitter 解析，50+ 种文件类型使用回退策略
- **直接 Tree-sitter 集成**: 专业语言无正则表达式回退 - 快速失败并提供清晰错误
- **高级搜索**: 自动检测并使用最佳可用工具（ugrep、ripgrep、ag 或 grep）
- **通用文件支持**: 从高级 AST 解析到基础文件索引的全面覆盖
- **文件分析**: 深入了解结构、导入、类、方法和复杂度指标

### 🗂️ Multi-Language Support / 多语言支持

**Languages with Tree-sitter AST Parsing / 支持 Tree-sitter AST 解析的语言 (7):**
- Python, JavaScript, TypeScript, Java, Go, Objective-C, Zig

**Languages with Fallback Strategy / 使用回退策略的语言 (50+):**
- C/C++, Rust, Ruby, PHP, C#, Kotlin, Scala, Swift, Shell, and more / 及更多
- Vue, React, Svelte, HTML, CSS, SCSS
- SQL, JSON, YAML, XML, Markdown

### ⚡ Real-time Monitoring & Auto-refresh / 实时监控与自动刷新

**English:**
- **File Watcher**: Automatic index updates when files change
- **Cross-platform**: Native OS file system monitoring
- **Smart Processing**: Batches rapid changes to prevent excessive rebuilds
- **Shallow Index Refresh**: Watches file changes and keeps the file list current

**中文：**
- **文件监控**: 文件变化时自动更新索引
- **跨平台**: 原生操作系统文件系统监控
- **智能处理**: 批量处理快速变化以防止过度重建
- **浅层索引刷新**: 监控文件变化并保持文件列表最新

### ⚡ Performance & Efficiency / 性能与效率

**English:**
- **Tree-sitter AST Parsing**: Native syntax parsing for accurate symbol extraction
- **Persistent Caching**: Stores indexes for lightning-fast subsequent access
- **Smart Filtering**: Intelligent exclusion of build directories and temporary files
- **Memory Efficient**: Optimized for large codebases

**中文：**
- **Tree-sitter AST 解析**: 原生语法解析，准确提取符号
- **持久化缓存**: 存储索引以实现闪电般的后续访问
- **智能过滤**: 智能排除构建目录和临时文件
- **内存高效**: 为大型代码库优化

---

## Available Tools / 可用工具

### 🏗️ Project Management / 项目管理

| Tool / 工具 | Description / 描述 |
|-------------|-------------------|
| **`set_project_path`** | Initialize indexing for a project directory / 为项目目录初始化索引 |
| **`refresh_index`** | Rebuild the shallow file index after file changes / 文件更改后重建浅层索引 |
| **`build_deep_index`** | Generate the full symbol index used by deep analysis / 生成深度分析使用的完整符号索引 |
| **`get_settings_info`** | View current project configuration and status / 查看当前项目配置和状态 |

### 🔍 Search & Discovery / 搜索与发现

| Tool / 工具 | Description / 描述 |
|-------------|-------------------|
| **`unified_search`** | Single unified interface for all search operations (3 modes) / 所有搜索操作的统一接口（3 种模式） |

#### Search Modes / 搜索模式

**1. Content Mode / 内容模式 (`mode='content'`)**

**English:** Search code patterns with regex, fuzzy matching, and file filtering

**中文：** 使用正则表达式、模糊匹配和文件过滤搜索代码模式

- **Parameters / 参数**: `pattern` (required / 必需), `case_sensitive`, `context_lines`, `file_pattern`, `fuzzy`, `regex`, `max_line_length`
- **Returns / 返回**: Dictionary with search results, file paths, and match details / 包含搜索结果、文件路径和匹配详情的字典

**Example / 示例:**
```python
# Content search with regex / 正则表达式内容搜索
unified_search(mode='content', pattern='TODO|FIXME', regex=True, file_pattern='*.py')

# Fuzzy search / 模糊搜索
unified_search(mode='content', pattern='authUser', fuzzy=True)
```

**2. Files Mode / 文件模式 (`mode='files'`)**

**English:** Locate files using glob patterns (e.g., `*.py`, `test_*.js`)

**中文：** 使用 glob 模式定位文件（例如 `*.py`、`test_*.js`）

- **Parameters / 参数**: `pattern` (required / 必需)
- **Returns / 返回**: Dictionary with `files` array and `total_count` / 包含 `files` 数组和 `total_count` 的字典

**Example / 示例:**
```python
# Find TypeScript components / 查找 TypeScript 组件
unified_search(mode='files', pattern='**/*.tsx')

# Find test files / 查找测试文件
unified_search(mode='files', pattern='test_*.py')
```

**3. Summary Mode / 摘要模式 (`mode='summary'`)**

**English:** Analyze file structure, functions, imports, and complexity (requires deep index)

**中文：** 分析文件结构、函数、导入和复杂度（需要深度索引）

- **Parameters / 参数**: `file_path` (required / 必需)
- **Returns / 返回**: Dictionary with line count, functions, classes, imports, and complexity metrics / 包含行数、函数、类、导入和复杂度指标的字典

**Example / 示例:**
```python
# File analysis / 文件分析
unified_search(mode='summary', file_path='src/main.py')
```

> **Note / 注意:** For v2.x users, see [MIGRATION.md](MIGRATION.md) for upgrading guide.
> v2.x 用户请参见 [MIGRATION.md](MIGRATION.md) 获取升级指南。

### 🔄 Monitoring & Auto-refresh / 监控与自动刷新

| Tool / 工具 | Description / 描述 |
|-------------|-------------------|
| **`get_file_watcher_status`** | Check file watcher status and configuration / 检查文件监控状态和配置 |
| **`configure_file_watcher`** | Enable/disable auto-refresh and configure settings / 启用/禁用自动刷新并配置设置 |

### 🛠️ System & Maintenance / 系统与维护

| Tool / 工具 | Description / 描述 |
|-------------|-------------------|
| **`create_temp_directory`** | Set up storage directory for index data / 设置索引数据的存储目录 |
| **`check_temp_directory`** | Verify index storage location and permissions / 验证索引存储位置和权限 |
| **`clear_settings`** | Reset all cached data and configurations / 重置所有缓存数据和配置 |
| **`refresh_search_tools`** | Re-detect available search tools (ugrep, ripgrep, etc.) / 重新检测可用的搜索工具 |

---

## Usage Examples / 使用示例

### 🎯 Quick Start Workflow / 快速入门工作流

**Step 1: Initialize Your Project / 步骤 1：初始化项目**

**English:** Set the project path to start indexing
```
Set the project path to G:\my-react-app
```

**中文：** 设置项目路径以开始索引
```
设置项目路径为 G:\my-react-app
```

**Step 2: Explore Project Structure / 步骤 2：探索项目结构**

**English:** Find files by pattern
```
Find all TypeScript component files in src/components
```

**中文：** 按模式查找文件
```
查找 src/components 目录下所有 TypeScript 组件文件
```

**Step 3: Analyze Key Files / 步骤 3：分析关键文件**

**English:** Get detailed file analysis (run `build_deep_index` first if needed)
```
Give me a summary of src/api/userService.ts
```

**中文：** 获取详细文件分析（如需要请先运行 `build_deep_index`）
```
给我分析一下 src/api/userService.ts 文件
```

### 🔍 Advanced Search Examples / 高级搜索示例

#### Code Pattern Search / 代码模式搜索

**English:**
```
Search for all function calls matching "get.*Data" using regex
```
*Finds: `getData()`, `getUserData()`, `getFormData()`, etc.*

**中文：**
```
使用正则表达式搜索所有匹配 "get.*Data" 的函数调用
```
*查找: `getData()`、`getUserData()`、`getFormData()` 等*

#### Fuzzy Function Search / 模糊函数搜索

**English:**
```
Find authentication-related functions with fuzzy search for 'authUser'
```
*Matches: `authenticateUser`, `authUserToken`, `userAuthCheck`, etc.*

**中文：**
```
使用模糊搜索查找 'authUser' 相关的身份验证函数
```
*匹配: `authenticateUser`、`authUserToken`、`userAuthCheck` 等*

#### Language-Specific Search / 特定语言搜索

**English:**
```
Search for "API_ENDPOINT" only in Python files
```

**中文：**
```
仅在 Python 文件中搜索 "API_ENDPOINT"
```

#### Auto-refresh Configuration / 自动刷新配置

**English:**
```
Configure automatic index updates when files change
```

**中文：**
```
配置文件更改时自动更新索引
```

#### Project Maintenance / 项目维护

**English:**
```
I added new components, please refresh the project index
```

**中文：**
```
我添加了新组件，请刷新项目索引
```

---

## Troubleshooting / 故障排除

### 🔄 Auto-refresh Not Working / 自动刷新不工作

**English:**

If automatic index updates aren't working when files change, try:
- `pip install watchdog` (may resolve environment isolation issues)
- Use manual refresh: Call the `refresh_index` tool after making file changes
- Check file watcher status: Use `get_file_watcher_status` to verify monitoring is active

**中文：**

如果文件更改时自动索引更新不工作，请尝试：
- `pip install watchdog`（可能解决环境隔离问题）
- 使用手动刷新：文件更改后调用 `refresh_index` 工具
- 检查文件监控状态：使用 `get_file_watcher_status` 验证监控是否激活

---

## Development & Contributing / 开发与贡献

### 🔧 Building from Source / 从源码构建

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

### 🐛 Debugging / 调试

```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

### 🤝 Contributing / 贡献

**English:** Contributions are welcome! Please feel free to submit a Pull Request.

**中文：** 欢迎贡献！请随时提交 Pull Request。

---

## Credits / 致谢

**English:**

This project is a fork of [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) by [johnhuang316](https://github.com/johnhuang316). Special thanks to the original author for creating this excellent MCP server.

**中文：**

本项目是 [johnhuang316](https://github.com/johnhuang316) 创建的 [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) 的分支版本。特别感谢原作者创建了这个优秀的 MCP 服务器。

---

## License / 许可证

[MIT License](LICENSE)

---

## Contact / 联系方式

- **GitHub Issues**: [https://github.com/catlog22/code-index-mcp-simple/issues](https://github.com/catlog22/code-index-mcp-simple/issues)
- **Original Project**: [https://github.com/johnhuang316/code-index-mcp](https://github.com/johnhuang316/code-index-mcp)
