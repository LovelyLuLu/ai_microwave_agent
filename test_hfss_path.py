#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试HFSS项目路径查找功能
"""

import os
from pathlib import Path

def test_hfss_path_detection():
    """测试HFSS项目路径检测功能"""
    print("=" * 60)
    print("HFSS项目路径检测测试")
    print("=" * 60)
    
    # 1. 测试标准HFSS项目路径
    aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    print(f"\n1. 标准HFSS项目路径: {aedt_projects_path}")
    print(f"   路径是否存在: {'✅ 是' if os.path.exists(aedt_projects_path) else '❌ 否'}")
    
    if os.path.exists(aedt_projects_path):
        try:
            # 列出所有文件和文件夹
            items = os.listdir(aedt_projects_path)
            print(f"   目录中的项目数量: {len(items)}")
            
            # 查找.aedt项目文件
            project_files = [
                f for f in items
                if f.endswith(".aedt") and os.path.isfile(os.path.join(aedt_projects_path, f))
            ]
            
            print(f"   找到的HFSS项目数量: {len(project_files)}")
            
            if project_files:
                print("   HFSS项目列表:")
                for i, project in enumerate(project_files, 1):
                    project_path = os.path.join(aedt_projects_path, project)
                    mtime = os.path.getmtime(project_path)
                    from datetime import datetime
                    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"     {i}. {project} (修改时间: {mtime_str})")
                
                # 找到最新的项目
                latest_project = max(
                    project_files,
                    key=lambda f: os.path.getmtime(os.path.join(aedt_projects_path, f))
                )
                latest_project_path = os.path.join(aedt_projects_path, latest_project)
                print(f"\n   ✅ 最新项目: {latest_project_path}")
            else:
                print("   ❌ 未找到任何HFSS项目")
                
        except Exception as e:
            print(f"   ❌ 访问目录时出错: {e}")
    
    # 2. 测试当前目录查找
    print(f"\n2. 当前工作目录: {Path.cwd()}")
    current_dir = Path.cwd()
    aedt_files = list(current_dir.rglob("*.aedt"))
    print(f"   找到的.aedt文件数量: {len(aedt_files)}")
    
    if aedt_files:
        print("   .aedt文件列表:")
        for i, file in enumerate(aedt_files, 1):
            mtime = file.stat().st_mtime
            from datetime import datetime
            mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            print(f"     {i}. {file} (修改时间: {mtime_str})")
        
        # 找到最新的文件
        latest_file = max(aedt_files, key=lambda f: f.stat().st_mtime)
        print(f"\n   ✅ 最新文件: {latest_file}")
    else:
        print("   ❌ 未找到任何.aedt文件")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_hfss_path_detection()