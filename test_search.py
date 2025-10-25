#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Code Index MCP - Search functionality
测试 Code Index MCP 的搜索功能
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from code_index_mcp.server import mcp
from code_index_mcp.services.project_management_service import ProjectManagementService
from code_index_mcp.services.search_service import SearchService


async def test_search():
    """Test search functionality on multiphysics_network project"""

    print("=" * 80)
    print("🧪 Code Index MCP - Search Test / 搜索功能测试")
    print("=" * 80)
    print()

    # Step 1: Set project path
    project_path = r"D:\dongdiankaifa9\multiphysics_network"
    print(f"📁 Step 1: Setting project path / 步骤 1：设置项目路径")
    print(f"   Path: {project_path}")
    print()

    try:
        project_service = ProjectManagementService()
        result = await project_service.set_project_path(project_path)
        print(f"✅ Project path set successfully / 项目路径设置成功")
        print(f"   {result}")
        print()
    except Exception as e:
        print(f"❌ Error setting project path / 设置项目路径失败: {e}")
        return

    # Step 2: Build index (optional - may take time)
    print(f"📊 Step 2: Building shallow index / 步骤 2：构建浅层索引")
    try:
        await project_service.refresh_index()
        print(f"✅ Index built successfully / 索引构建成功")
        print()
    except Exception as e:
        print(f"⚠️  Warning: Index build issue / 索引构建警告: {e}")
        print()

    # Step 3: Search for "fluid" related content
    print(f"🔍 Step 3: Searching for 'fluid' / 步骤 3：搜索 'fluid'")
    print(f"   Pattern: fluid")
    print(f"   Mode: content")
    print()

    try:
        search_service = SearchService()

        # Search 1: Basic content search
        print("   Search 1: Basic content search / 基础内容搜索")
        results = await search_service.search_code(
            pattern="fluid",
            case_sensitive=False,
            regex=False,
            fuzzy=False
        )

        if results and 'results' in results:
            print(f"   ✅ Found {len(results['results'])} results / 找到 {len(results['results'])} 个结果")

            # Display first 5 results
            for i, result in enumerate(results['results'][:5], 1):
                print(f"\n   Result {i}:")
                print(f"      File: {result.get('file', 'N/A')}")
                print(f"      Line: {result.get('line_number', 'N/A')}")
                print(f"      Match: {result.get('line', 'N/A')[:100]}...")
        else:
            print(f"   ℹ️  No results found / 未找到结果")

        print()

        # Search 2: Case-sensitive search
        print("   Search 2: Case-sensitive search / 区分大小写搜索")
        results2 = await search_service.search_code(
            pattern="Fluid",
            case_sensitive=True,
            regex=False
        )

        if results2 and 'results' in results2:
            print(f"   ✅ Found {len(results2['results'])} results with 'Fluid' / 找到 {len(results2['results'])} 个 'Fluid' 结果")
        else:
            print(f"   ℹ️  No case-sensitive results / 无区分大小写结果")

        print()

        # Search 3: Regex search for fluid-related variables
        print("   Search 3: Regex search for fluid variables / 正则搜索流体变量")
        results3 = await search_service.search_code(
            pattern=r"fluid[_\w]*",
            regex=True,
            case_sensitive=False
        )

        if results3 and 'results' in results3:
            print(f"   ✅ Found {len(results3['results'])} regex matches / 找到 {len(results3['results'])} 个正则匹配")

            # Show unique matches
            unique_matches = set()
            for result in results3['results'][:20]:
                line = result.get('line', '')
                import re
                matches = re.findall(r'fluid[_\w]*', line, re.IGNORECASE)
                unique_matches.update(matches)

            print(f"   Example matches / 匹配示例: {list(unique_matches)[:10]}")

        print()

    except Exception as e:
        print(f"❌ Search error / 搜索错误: {e}")
        import traceback
        traceback.print_exc()
        return

    print("=" * 80)
    print("✅ Test completed successfully / 测试完成")
    print("=" * 80)
    print()
    print("💡 Tips / 提示:")
    print("   - MCP Inspector is running at: http://localhost:6274")
    print("   - You can also test via Claude Desktop by configuring MCP settings")
    print("   - 你也可以通过配置 Claude Desktop 的 MCP 设置来测试")
    print()


if __name__ == "__main__":
    asyncio.run(test_search())
