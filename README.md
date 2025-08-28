# visualizeKnowledgeGraph

知识图谱可视化系统，支持实体与关系的管理、导入导出及可视化展示。

# visualizeKnowledgeGraph目录
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

## 技术栈
- 前端：HTML、CSS、JavaScript、D3.js
- 后端：Python、Django
- 数据库：MYSQLite（可扩展为PostgreSQL等）

## 部署步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 创建`.env`文件配置环境变量
3. 数据库迁移：`python manage.py migrate`
4. 启动服务：`python manage.py runserver`
