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


"""