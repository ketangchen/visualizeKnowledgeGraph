# visualizeKnowledgeGraph

知识图谱可视化系统，支持实体与关系的管理、导入导出及可视化展示。

## 技术栈
- 前端：HTML、CSS、JavaScript、D3.js
- 后端：Python、Django
- 数据库：SQLite（可扩展为PostgreSQL等）

## 部署步骤
1. 安装依赖：`pip install -r requirements.txt`
2. 创建`.env`文件配置环境变量
3. 数据库迁移：`python manage.py migrate`
4. 启动服务：`python manage.py runserver`