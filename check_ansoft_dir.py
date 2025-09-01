#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查Ansoft目录内容
"""

import os
from datetime import datetime

def check_ansoft_directory():
    """检查Ansoft目录的详细内容"""
    aedt_projects_path = os.path.join(os.path.expanduser("~"), "Documents", "Ansoft")
    
    print("=" * 80)
    print(f"检查目录: {aedt_projects_path}")
    print("=" * 80)
    
    if not os.path.exists(aedt_projects_path):
        print("❌ 目录不存在")
        return
    
    try:
        items = os.listdir(aedt_projects_path)
        print(f"\n目录中共有 {len(items)} 个项目")
        print("\n详细列表:")
        print("-" * 80)
        
        for i, item in enumerate(items, 1):
            item_path = os.path.join(aedt_projects_path, item)
            is_dir = os.path.isdir(item_path)
            is_file = os.path.isfile(item_path)
            
            # 获取修改时间
            try:
                mtime = os.path.getmtime(item_path)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
            except:
                mtime_str = "未知"
            
            # 获取大小信息
            size_info = ""
            if is_file:
                try:
                    size = os.path.getsize(item_path)
                    if size < 1024:
                        size_info = f"{size} B"
                    elif size < 1024*1024:
                        size_info = f"{size/1024:.1f} KB"
                    else:
                        size_info = f"{size/(1024*1024):.1f} MB"
                except:
                    size_info = "未知大小"
            
            type_str = "📁 文件夹" if is_dir else "📄 文件"
            
            print(f"{i:3d}. {type_str} {item}")
            print(f"     修改时间: {mtime_str}")
            if size_info:
                print(f"     大小: {size_info}")
            
            # 检查是否是HFSS相关的项目
            if item.endswith(".aedt"):
                print(f"     ✅ 这是一个AEDT项目！")
            elif "hfss" in item.lower() or "csrr" in item.lower() or "srr" in item.lower():
                print(f"     🔍 可能是HFSS相关项目")
            
            print()
        
        # 专门查找.aedt结尾的项目
        aedt_items = [item for item in items if item.endswith(".aedt")]
        print("=" * 80)
        print(f"找到 {len(aedt_items)} 个 .aedt 项目:")
        for item in aedt_items:
            item_path = os.path.join(aedt_projects_path, item)
            is_dir = os.path.isdir(item_path)
            print(f"  - {item} ({'文件夹' if is_dir else '文件'})")
        
        # 查找可能的HFSS项目（不一定以.aedt结尾）
        possible_hfss = [item for item in items if any(keyword in item.lower() for keyword in ['hfss', 'csrr', 'srr', 'antenna', 'filter'])]
        print(f"\n找到 {len(possible_hfss)} 个可能的HFSS相关项目:")
        for item in possible_hfss:
            item_path = os.path.join(aedt_projects_path, item)
            is_dir = os.path.isdir(item_path)
            print(f"  - {item} ({'文件夹' if is_dir else '文件'})")
            
    except Exception as e:
        print(f"❌ 访问目录时出错: {e}")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    check_ansoft_directory()