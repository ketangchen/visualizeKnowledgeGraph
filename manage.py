# -*- coding: utf-8 -*-
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pathlib  # 新增：导入pathlib模块


def main():
    """Run administrative tasks."""
    # 新增：将backend目录添加到Python路径
    backend_dir = pathlib.Path(__file__).resolve().parent / "backend"
    sys.path.append(str(backend_dir))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

"""
python manage.py runserver
http://127.0.0.1:8000/api/

http://127.0.0.1:8000




visualizeKnowledgeGraph/
├── frontend/               # 前端代码
│   ├── index.html          # 主页面，包含知识图谱可视化界面和交互控件
│   ├── libs/               # 前端依赖库
│   └── static/             # 静态资源（如JS、CSS）
│       └── js/graph.js     # 知识图谱可视化核心逻辑（基于D3.js）
├── backend/                # 后端代码（基于Django）
│   ├── apps/               # 应用模块
│   │   └── kg_visualize/   # 知识图谱可视化相关功能（模型、API等）
│   ├── config/             # 项目配置（如数据库、路由、全局设置等）
│   └── ...
├── tests/                  # 测试代码（如test_kg_api.py）
├── manage.py               # Django项目管理脚本
└── 其他配置文件（.gitignore、IDE配置等）



打包依赖库
pip freeze > requirements.txt
安装依赖库
pip install -r requirements.txt


操作系统版本（uname -m）：x86_64
Python版本（python --version）:3.9
PaddlePaddle和PaddleOCR的版本（pip list | grep paddle）:

pip怎么查看一个三方库有哪些版本？
pip index versions <package>
pip index versions paddlepaddle
pip index versions paddleocr

conda创建虚拟环境
conda create -n my_env1 python=3.10
conda activate my_env1
conda deactivate
conda env list
file $(which python3)


"""