# visualizeKnowledgeGraph

֪ʶͼ�׿��ӻ�ϵͳ��֧��ʵ�����ϵ�Ĺ������뵼�������ӻ�չʾ��

# visualizeKnowledgeGraphĿ¼
visualizeKnowledgeGraph/
������ frontend/               # ǰ�˴���
��   ������ index.html          # ��ҳ�棬����֪ʶͼ�׿��ӻ�����ͽ����ؼ�
��   ������ libs/               # ǰ��������
��   ������ static/             # ��̬��Դ����JS��CSS��
��       ������ js/graph.js     # ֪ʶͼ�׿��ӻ������߼�������D3.js��
������ backend/                # ��˴��루����Django��
��   ������ apps/               # Ӧ��ģ��
��   ��   ������ kg_visualize/   # ֪ʶͼ�׿��ӻ���ع��ܣ�ģ�͡�API�ȣ�
��   ������ config/             # ��Ŀ���ã������ݿ⡢·�ɡ�ȫ�����õȣ�
��   ������ ...
������ tests/                  # ���Դ��루��test_kg_api.py��
������ manage.py               # Django��Ŀ����ű�
������ ���������ļ���.gitignore��IDE���õȣ�

## ����ջ
- ǰ�ˣ�HTML��CSS��JavaScript��D3.js
- ��ˣ�Python��Django
- ���ݿ⣺SQLite������չΪPostgreSQL�ȣ�

## ������
1. ��װ������`pip install -r requirements.txt`
2. ����`.env`�ļ����û�������
3. ���ݿ�Ǩ�ƣ�`python manage.py migrate`
4. ��������`python manage.py runserver`