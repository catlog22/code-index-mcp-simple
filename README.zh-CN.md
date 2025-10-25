# Code Index MCP Simple

<div align="center">

[![MCP Server](https://img.shields.io/badge/MCP-Server-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

**面向大型语言模型的智能代码索引和分析**

通过高级搜索、分析和导航功能，改变 AI 理解代码库的方式。

[English](README.md) | [简体中文](README.zh-CN.md)

</div>

---

> **🔔 项目通知**
> 
> 这是 johnhuang316 的 [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) 的简化和增强分支，专注于为核心代码智能功能提供精简的 API。

---

> **⚠️ v3.x 中的重大变更**
> 
> 版本 3.x 将所有搜索、项目设置和索引功能整合到一个 `unified_search` 工具中。请参阅 [MIGRATION.md](MIGRATION.md) 获取升级指南。

---

## 概述

Code Index MCP Simple 是一个 [Model Context Protocol](https://modelcontextprotocol.io) 服务器，旨在为 AI 模型提供智能索引、高级搜索和详细的代码分析功能。它简化了 AI 助手与复杂代码库的交互和理解方式。

**适用于：** 代码审查、重构、文档生成、调试辅助和架构分析。

---

## 快速开始

### 🚀 安装

#### 先决条件
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (推荐)

#### 方法 1：直接从 GitHub 安装（推荐）

无需克隆，直接从 GitHub 安装和运行：

**添加到您的 MCP 配置中** (例如，`claude_desktop_config.json`)：
```json
{
  "mcpServers": {
    "code-index-simple": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/catlog22/code-index-mcp-simple.git",
        "code-index-mcp-simple"
      ]
    }
  }
}
```

**重启您的应用程序** 并开始使用：
```
查找项目中所有的 TypeScript 文件
搜索 "authentication" 相关函数
分析 App.tsx 主文件
```

#### 方法 2：本地克隆

用于离线使用或开发：

1.  **克隆仓库：**
    ```bash
    git clone https://github.com/catlog22/code-index-mcp-simple.git
    cd code-index-mcp-simple
    ```

2.  **添加到您的 MCP 配置中** (例如，`claude_desktop_config.json`)：

    **Windows:**
    ```json
    {
      "mcpServers": {
        "code-index-simple": {
          "command": "uv",
          "args": [
            "--directory",
            "C:\\path\\to\\code-index-mcp-simple",
            "run",
            "code-index-mcp-simple"
          ]
        }
      }
    }
    ```

    **macOS/Linux:**
    ```json
    {
      "mcpServers": {
        "code-index-simple": {
          "command": "uv",
          "args": [
            "--directory",
            "/path/to/code-index-mcp-simple",
            "run",
            "code-index-mcp-simple"
          ]
        }
      }
    }
    ```

3.  **重启您的应用程序** – 更改将生效。

#### 方法 3：本地开发

用于贡献或本地开发：

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

**使用 MCP Inspector 调试：**
```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

---

## 主要功能

### 🔍 智能搜索与分析
-   **统一搜索 (Unified Search)**：一个 `unified_search` 工具处理所有搜索模式（内容、文件、摘要）、项目设置和索引。
-   **双策略架构 (Dual-Strategy Architecture)**：Tree-sitter 解析 7 种核心语言，并为 50 多种文件类型提供强大的回退支持。
-   **高级搜索 (Advanced Search)**：自动检测并利用最佳可用搜索工具 (ugrep, ripgrep, ag, 或 grep)。
-   **文件分析 (File Analysis)**：深入了解文件结构、函数、导入和复杂性指标。

### 🗂️ 多语言支持
-   **Tree-sitter AST 解析 (7 种语言)：** Python, JavaScript, TypeScript, Java, Go, Objective-C, Zig。
-   **回退策略 (50 多种语言)：** 全面覆盖 C/C++, Rust, Ruby, PHP, C#, Kotlin, Scala, Swift, Shell, Vue, React, Svelte, HTML, CSS, SQL, JSON, YAML, XML, Markdown 等。

### ⚡ 实时监控与效率
-   **文件监视器 (File Watcher)**：文件更改时自动更新索引，通过智能处理防止过度重建。
-   **持久缓存 (Persistent Caching)**：存储索引以实现闪电般的后续访问。
-   **内存高效 (Memory Efficient)**：通过智能排除构建目录和临时文件，针对大型代码库进行优化。

---

## `unified_search` 工具：您的单一入口点

此简化版 Code Index MCP 专注于一个强大且单一的 `unified_search` 工具。它整合了所有项目设置、索引和搜索功能，以实现最大的便利性。

### 用法

```python
unified_search(
    mode: str,             # 'content', 'files', or 'summary'
    project_path: str,     # REQUIRED: Absolute path to project. Auto-initializes and indexes.
    query: Optional[str],  # REQUIRED for 'content' and 'files' modes
    file_path: Optional[str], # REQUIRED for 'summary' mode
    # ... other optional parameters like case_sensitive, file_pattern, fuzzy, regex
)
```

### 搜索模式

1.  **内容模式 (`mode='content'`)**
    -   **目的**：使用正则表达式、模糊匹配和文件过滤搜索代码模式。
    -   **关键参数**：`query` (文本或正则表达式模式)。
    -   **示例**：`unified_search(mode='content', project_path='D:\my-project', query='TODO|FIXME', regex=True, file_pattern='*.py')`

2.  **文件模式 (`mode='files'`)**
    -   **目的**：使用 glob 模式定位文件。
    -   **关键参数**：`query` (文件名或 glob 模式)。
    -   **示例**：`unified_search(mode='files', project_path='D:\my-project', query='**/*.tsx')`

3.  **摘要模式 (`mode='summary'`)**
    -   **目的**：分析文件结构、函数、导入和复杂性。
    -   **关键参数**：`file_path` (文件的相对路径)。
    -   **示例**：`unified_search(mode='summary', project_path='D:\my-project', file_path='src/main.py')`

---

## 使用示例

### 🎯 快速启动工作流程

**超简单的 2 步流程！**

#### 步骤 1：设置项目路径 (自动索引所有内容)

```
Set the project path to G:\my-react-app
```

此单个命令：
-   ✅ 设置项目目录
-   ✅ 自动构建文件索引 (用于 `mode='content'` 和 `mode='files'`)
-   ✅ 自动构建符号索引 (用于 `mode='summary'`)
-   ✅ 使 `unified_search` 立即可用！

#### 步骤 2：开始搜索！

无需额外设置 - 立即搜索！

```
Search for "authentication" in the codebase
Find all TypeScript component files
Give me a summary of src/api/userService.ts
```

### 🔍 高级搜索示例

#### 代码模式搜索

```
Search for all function calls matching "get.*Data" using regex
```
*查找：`getData()`, `getUserData()`, `getFormData()` 等.*

#### 模糊函数搜索

```
Find authentication-related functions with fuzzy search for 'authUser'
```
*匹配：`authenticateUser`, `authUserToken`, `userAuthCheck` 等.*

#### 特定语言搜索

```
Search for "API_ENDPOINT" only in Python files
```

---

## 故障排除

### 🔄 自动刷新不工作

如果文件更改时自动索引更新不工作，请尝试：
-   `pip install watchdog` (可能解决环境隔离问题)
-   `unified_search` 工具会自动处理索引。如果您需要强制重新索引，只需使用 `project_path` 再次调用 `unified_search`。

---

## 开发与贡献

### 🔧 从源代码构建

```bash
git clone https://github.com/catlog22/code-index-mcp-simple.git
cd code-index-mcp-simple
uv sync
uv run code-index-mcp-simple
```

### 🐛 调试

```bash
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

### 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

---

## 致谢

本项目是 [johnhuang316](https://github.com/johnhuang316) 的 [code-index-mcp](https://github.com/johnhuang316/code-index-mcp) 的一个分支。特别感谢原作者创建了这个出色的 MCP 服务器。

---

## 许可证

[MIT License](LICENSE)

---

## 联系方式

-   **GitHub Issues**：[https://github.com/catlog22/code-index-mcp-simple/issues](https://github.com/catlog22/code-index-mcp-simple/issues)
-   **原始项目**：[https://github.com/johnhuang316/code-index-mcp](https://github.com/johnhuang316/code-index-mcp)
