# Code Index MCP Simple

<div align="center">

[![MCP Server](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**Intelligent code indexing and analysis for Large Language Models**

Transform how AI understands your codebase with advanced search, analysis, and navigation capabilities.

[English](README.md) | [简体中文](README.zh-CN.md)

</div>

---

> **🔔 Project Notice**
>
> This is a simplified and enhanced fork of [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) by johnhuang316, focusing on a streamlined API for core code intelligence features.

---

> **⚠️ BREAKING CHANGES IN v3.x**
>
> Version 3.x consolidates all search, project setup, and indexing functionalities into a single `unified_search` tool. See [MIGRATION.md](MIGRATION.md) for upgrade guide.

---

## Overview

Code Index MCP Simple is a [Model Context Protocol](https://modelcontextprotocol.io) server designed to provide AI models with intelligent indexing, advanced search, and detailed code analysis capabilities. It simplifies how AI assistants interact with and understand complex codebases.

**Ideal for:** Code review, refactoring, documentation generation, debugging assistance, and architectural analysis.

---

## Quick Start

### 🚀 Installation

#### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended)

#### Method 1: Using uvx (Recommended)

The easiest way to get started with any MCP-compatible application:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/catlog22/code-index-mcp-simple.git
    cd code-index-mcp-simple
    ```

2.  **Add to your MCP configuration** (e.g., `claude_desktop_config.json`):
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

3.  **Restart your application** – Changes will take effect.

4.  **Start using** (example prompts for your AI assistant):
    ```
    Set the project path to G:\my-project
    Find all TypeScript files in this project
    Search for "authentication" functions
    Analyze the main App.tsx file
    ```

#### Method 2: Local Development

For contributing or local development:

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

**Debug with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

---

## Key Features

### 🔍 Intelligent Search & Analysis
-   **Unified Search**: A single `unified_search` tool handles all search modes (content, files, summary), project setup, and indexing.
-   **Dual-Strategy Architecture**: Tree-sitter parsing for 7 core languages, with a robust fallback for 50+ file types.
-   **Advanced Search**: Auto-detects and utilizes the best available search tools (ugrep, ripgrep, ag, or grep).
-   **File Analysis**: Provides deep insights into file structure, functions, imports, and complexity metrics.

### 🗂️ Multi-Language Support
-   **Tree-sitter AST Parsing (7 languages):** Python, JavaScript, TypeScript, Java, Go, Objective-C, Zig.
-   **Fallback Strategy (50+ languages):** Comprehensive coverage for C/C++, Rust, Ruby, PHP, C#, Kotlin, Scala, Swift, Shell, Vue, React, Svelte, HTML, CSS, SQL, JSON, YAML, XML, Markdown, and more.

### ⚡ Real-time Monitoring & Efficiency
-   **File Watcher**: Automatic index updates when files change, with smart processing to prevent excessive rebuilds.
-   **Persistent Caching**: Stores indexes for lightning-fast subsequent access.
-   **Memory Efficient**: Optimized for large codebases with intelligent exclusion of build directories and temporary files.

---

## The `unified_search` Tool: Your Single Entry Point

This simplified version of Code Index MCP focuses on a single, powerful `unified_search` tool. It consolidates all project setup, indexing, and search functionalities for maximum convenience.

### Usage

```python
unified_search(
    mode: str,             # 'content', 'files', or 'summary'
    project_path: str,     # REQUIRED: Absolute path to project. Auto-initializes and indexes.
    query: Optional[str],  # REQUIRED for 'content' and 'files' modes
    file_path: Optional[str], # REQUIRED for 'summary' mode
    # ... other optional parameters like case_sensitive, file_pattern, fuzzy, regex
)
```

### Search Modes

1.  **Content Mode (`mode='content'`)**
    -   **Purpose**: Search code patterns using regex, fuzzy matching, and file filtering.
    -   **Key Parameter**: `query` (text or regex pattern).
    -   **Example**: `unified_search(mode='content', project_path='D:\\my-project', query='TODO|FIXME', regex=True, file_pattern='*.py')`

2.  **Files Mode (`mode='files'`)**
    -   **Purpose**: Locate files using glob patterns.
    -   **Key Parameter**: `query` (file name or glob pattern).
    -   **Example**: `unified_search(mode='files', project_path='D:\\my-project', query='**/*.tsx')`

3.  **Summary Mode (`mode='summary'`)**
    -   **Purpose**: Analyze file structure, functions, imports, and complexity.
    -   **Key Parameter**: `file_path` (relative path to the file).
    -   **Example**: `unified_search(mode='summary', project_path='D:\\my-project', file_path='src/main.py')`

---

## Usage Examples

### 🎯 Quick Start Workflow

**Ultra-simple 2-step process!**

#### Step 1: Set Project Path (Auto-indexes everything)

```
Set the project path to G:\my-react-app
```

This single command:
-   ✅ Sets the project directory
-   ✅ Auto-builds file index (for `mode='content'` and `mode='files'`)
-   ✅ Auto-builds symbol index (for `mode='summary'`)
-   ✅ Makes `unified_search` immediately ready to use!

#### Step 2: Start Searching!

No additional setup needed - search immediately!

```
Search for "authentication" in the codebase
Find all TypeScript component files
Give me a summary of src/api/userService.ts
```

### 🔍 Advanced Search Examples

#### Code Pattern Search

```
Search for all function calls matching "get.*Data" using regex
```
*Finds: `getData()`, `getUserData()`, `getFormData()`, etc.*

#### Fuzzy Function Search

```
Find authentication-related functions with fuzzy search for 'authUser'
```
*Matches: `authenticateUser`, `authUserToken`, `userAuthCheck`, etc.*

#### Language-Specific Search

```
Search for "API_ENDPOINT" only in Python files
```

---

## Troubleshooting

### 🔄 Auto-refresh Not Working

If automatic index updates aren't working when files change, try:
-   `pip install watchdog` (may resolve environment isolation issues)
-   The `unified_search` tool automatically handles indexing. If you need to force a re-index, simply call `unified_search` again with the `project_path`.

---

## Development & Contributing

### 🔧 Building from Source

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

### 🐛 Debugging

```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

### 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## Credits

This project is a fork of [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) by [johnhuang316](https://github.com/johnhuang316). Special thanks to the original author for creating this excellent MCP server.

---

## License

[MIT License](LICENSE)

---

## Contact

-   **GitHub Issues**: [https://github.com/catlog22/code-index-mcp-simple/issues](https://github.com/catlog22/code-index-mcp-simple/issues)
-   **Original Project**: [https://github.com/johnhuang316/code-index-mcp](https://github.com/johnhuang316/code-index-mcp)