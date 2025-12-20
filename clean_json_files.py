#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理JSON文件中的敏感字段

功能：递归遍历指定目录下的所有JSON文件，删除指定的敏感字段
参数：
    - 命令行参数1：目录路径，默认当前目录
    - 命令行参数2：要删除的字段，默认 xsec_token, xsec_source

使用示例：
    python clean_json_files.py /path/to/directory
    python clean_json_files.py /path/to/directory field1,field2
"""

import os
import json
import sys
from typing import List, Dict, Any


def clean_json_file(file_path: str, fields_to_remove: List[str]) -> None:
    """
    清理单个JSON文件中的敏感字段
    
    Args:
        file_path: JSON文件路径
        fields_to_remove: 要删除的字段列表
    
    Returns:
        None
    
    Raises:
        json.JSONDecodeError: 如果JSON文件格式错误
        IOError: 如果文件读写错误
    """
    try:
        # 尝试使用UTF-8编码打开文件
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 递归删除敏感字段
        def remove_fields(obj: Any) -> Any:
            if isinstance(obj, dict):
                # 删除当前字典中的敏感字段
                for field in fields_to_remove:
                    if field in obj:
                        del obj[field]
                # 递归处理子字典
                for key, value in obj.items():
                    obj[key] = remove_fields(value)
            elif isinstance(obj, list):
                # 递归处理列表中的每个元素
                for i, item in enumerate(obj):
                    obj[i] = remove_fields(item)
            return obj
        
        cleaned_data = remove_fields(data)
        
        # 保存清理后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已清理: {file_path}")
        
    except UnicodeDecodeError as e:
        # 跳过非UTF-8编码的文件
        print(f"✗ 编码错误 {file_path}: {e}")
    except json.JSONDecodeError as e:
        print(f"✗ JSON错误 {file_path}: {e}")
    except IOError as e:
        print(f"✗ IO错误 {file_path}: {e}")
    except Exception as e:
        # 捕获其他所有异常，继续处理下一个文件
        print(f"✗ 未知错误 {file_path}: {e}")


def clean_json_files_in_directory(directory: str, fields_to_remove: List[str]) -> None:
    """
    递归清理目录下的所有JSON文件
    
    Args:
        directory: 要清理的目录路径
        fields_to_remove: 要删除的字段列表
    
    Returns:
        None
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                clean_json_file(file_path, fields_to_remove)


def main():
    """
    主函数，处理命令行参数并执行清理操作
    """
    # 默认参数
    directory = "."
    fields_to_remove = ["xsec_token", "xsec_source"]
    
    # 处理命令行参数
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    if len(sys.argv) > 2:
        fields_to_remove = sys.argv[2].split(',')
    
    print(f"开始清理目录: {directory}")
    print(f"要删除的字段: {fields_to_remove}")
    print("=" * 50)
    
    clean_json_files_in_directory(directory, fields_to_remove)
    
    print("=" * 50)
    print("清理完成！")


if __name__ == "__main__":
    main()
