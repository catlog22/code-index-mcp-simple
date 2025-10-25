# Testing Guide / 测试指南

## 🧪 How to Test Code Index MCP Simple / 如何测试 Code Index MCP Simple

This guide shows you how to test the search functionality on your project.
本指南展示如何在你的项目上测试搜索功能。

---

## Method 1: Using MCP Inspector (Recommended) / 方法 1：使用 MCP Inspector（推荐）

**English:** The MCP Inspector provides a web-based interface to test all tools interactively.

**中文：** MCP Inspector 提供基于 Web 的界面来交互式测试所有工具。

### Step 1: Start MCP Inspector / 步骤 1：启动 MCP Inspector

```bash
cd G:\github_lib\code-index-mcp-simple
npx @modelcontextprotocol/inspector uv run code-index-mcp-simple
```

**Expected Output / 预期输出:**
```
🚀 MCP Inspector is up and running at:
   http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=...
```

### Step 2: Open in Browser / 步骤 2：在浏览器中打开

The URL will automatically open in your browser. If not, copy the URL from the terminal.
URL 会自动在浏览器中打开。如果没有，从终端复制 URL。

### Step 3: Set Project Path / 步骤 3：设置项目路径

**English:**
1. In the MCP Inspector interface, find the **"set_project_path"** tool
2. Click on it to expand
3. Enter your project path in the `path` field:
   ```
   D:\dongdiankaifa9\multiphysics_network
   ```
4. Click **"Run"** or **"Execute"**

**中文：**
1. 在 MCP Inspector 界面中，找到 **"set_project_path"** 工具
2. 点击展开
3. 在 `path` 字段中输入你的项目路径：
   ```
   D:\dongdiankaifa9\multiphysics_network
   ```
4. 点击 **"Run"** 或 **"Execute"**

**Expected Result / 预期结果:**
```json
{
  "message": "Project path set successfully",
  "path": "D:\\dongdiankaifa9\\multiphysics_network",
  "file_count": <number of files>
}
```

### Step 4: Search for "fluid" / 步骤 4：搜索 "fluid"

**English:**
1. Find the **"unified_search"** tool
2. Set the parameters:
   - **mode**: `content`
   - **pattern**: `fluid`
   - **case_sensitive**: `false` (optional)
   - **regex**: `false` (optional)
3. Click **"Run"**

**中文：**
1. 找到 **"unified_search"** 工具
2. 设置参数：
   - **mode**: `content`
   - **pattern**: `fluid`
   - **case_sensitive**: `false`（可选）
   - **regex**: `false`（可选）
3. 点击 **"Run"**

**Expected Result / 预期结果:**
```json
{
  "results": [
    {
      "file": "path/to/file.py",
      "line_number": 123,
      "line": "fluid_density = 1000.0",
      "column": 5
    },
    ...
  ],
  "total_results": <number>,
  "search_info": {
    "pattern": "fluid",
    "case_sensitive": false,
    ...
  }
}
```

### Step 5: Advanced Searches / 步骤 5：高级搜索

#### Search 1: Find Python files with "fluid" / 搜索 1：查找包含 "fluid" 的 Python 文件

**Parameters / 参数:**
- **mode**: `content`
- **pattern**: `fluid`
- **file_pattern**: `*.py`

#### Search 2: Regex search for fluid variables / 搜索 2：正则搜索流体变量

**Parameters / 参数:**
- **mode**: `content`
- **pattern**: `fluid[_\w]*`
- **regex**: `true`

#### Search 3: Find all Python files / 搜索 3：查找所有 Python 文件

**Parameters / 参数:**
- **mode**: `files`
- **pattern**: `**/*.py`

---

## Method 2: Using Claude Desktop / 方法 2：使用 Claude Desktop

**English:** Configure Claude Desktop to use the MCP server for natural language testing.

**中文：** 配置 Claude Desktop 使用 MCP 服务器进行自然语言测试。

### Step 1: Configure Claude Desktop / 步骤 1：配置 Claude Desktop

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/.config/Claude/claude_desktop_config.json` (Mac/Linux):

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

**Note / 注意:** Replace the path with your actual project path / 将路径替换为你的实际项目路径

### Step 2: Restart Claude Desktop / 步骤 2：重启 Claude Desktop

Close and reopen Claude Desktop for the configuration to take effect.
关闭并重新打开 Claude Desktop 以使配置生效。

### Step 3: Test with Natural Language / 步骤 3：使用自然语言测试

**English:** Now you can use natural language prompts:

```
Set the project path to D:\dongdiankaifa9\multiphysics_network

Search for "fluid" in the codebase

Find all Python files containing "fluid"

Search for fluid-related variables using regex pattern "fluid[_\w]*"

Show me all files in the src directory
```

**中文：** 现在你可以使用自然语言提示：

```
设置项目路径为 D:\dongdiankaifa9\multiphysics_network

在代码库中搜索 "fluid"

查找所有包含 "fluid" 的 Python 文件

使用正则表达式 "fluid[_\w]*" 搜索流体相关变量

显示 src 目录下的所有文件
```

---

## Method 3: Direct Python API Test / 方法 3：直接 Python API 测试

**English:** For programmatic testing, create a test script.

**中文：** 用于程序化测试，创建测试脚本。

Create `test_api.py`:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
from pathlib import Path
from code_index_mcp.indexing.layered_index_manager import LayeredIndexManager
from code_index_mcp.models.search_context import SearchContext

async def test_search():
    # Initialize index manager
    project_path = Path(r"D:\dongdiankaifa9\multiphysics_network")
    index_manager = LayeredIndexManager(project_path)

    # Build index
    print("Building index...")
    await index_manager.build_shallow_index()

    # Search for "fluid"
    print("Searching for 'fluid'...")
    results = await index_manager.search_code(
        pattern="fluid",
        case_sensitive=False,
        regex=False
    )

    print(f"Found {len(results.get('results', []))} results")

    # Display first 5 results
    for i, result in enumerate(results.get('results', [])[:5], 1):
        print(f"\n{i}. {result.get('file')}:{result.get('line_number')}")
        print(f"   {result.get('line', '')[:100]}")

if __name__ == "__main__":
    asyncio.run(test_search())
```

Run:
```bash
cd G:\github_lib\code-index-mcp-simple
uv run python test_api.py
```

---

## Example Test Workflow / 示例测试工作流

**English:**

1. **Start MCP Inspector** → Open http://localhost:6274
2. **Set project path** → `D:\dongdiankaifa9\multiphysics_network`
3. **Basic search** → Search for "fluid" in content mode
4. **File search** → Find all Python files with `**/*.py`
5. **Regex search** → Search for fluid variables with `fluid[_\w]*`
6. **Analyze file** → Use summary mode to analyze a specific file

**中文：**

1. **启动 MCP Inspector** → 打开 http://localhost:6274
2. **设置项目路径** → `D:\dongdiankaifa9\multiphysics_network`
3. **基础搜索** → 在内容模式下搜索 "fluid"
4. **文件搜索** → 使用 `**/*.py` 查找所有 Python 文件
5. **正则搜索** → 使用 `fluid[_\w]*` 搜索流体变量
6. **分析文件** → 使用摘要模式分析特定文件

---

## Troubleshooting / 故障排除

### Issue 1: MCP Inspector won't start / 问题 1：MCP Inspector 无法启动

**Solution / 解决方案:**
- Ensure Node.js is installed / 确保安装了 Node.js
- Check if port 6274 is available / 检查端口 6274 是否可用
- Try using a different port: `npx @modelcontextprotocol/inspector --port 8080 uv run code-index-mcp-simple`

### Issue 2: No search results / 问题 2：无搜索结果

**Solution / 解决方案:**
- Verify project path is set correctly / 验证项目路径设置正确
- Check if the project contains the search pattern / 检查项目是否包含搜索模式
- Try case-insensitive search / 尝试不区分大小写搜索
- Check file permissions / 检查文件权限

### Issue 3: Encoding errors / 问题 3：编码错误

**Solution / 解决方案:**
- Set `PYTHONIOENCODING=utf-8` environment variable / 设置环境变量
- Use file patterns to exclude binary files / 使用文件模式排除二进制文件

---

## Next Steps / 下一步

**English:**
- Explore other tools like `build_deep_index` for advanced analysis
- Configure file watcher for auto-refresh
- Test with different search patterns and modes

**中文：**
- 探索其他工具如 `build_deep_index` 进行高级分析
- 配置文件监控实现自动刷新
- 测试不同的搜索模式和方式
