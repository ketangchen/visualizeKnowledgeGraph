import requests
import json
import pytest
from django.conf import settings

BASE_URL = getattr(settings, 'TEST_BASE_URL', 'http://localhost:8000/api')

def test_get_graph_data():
    """���Ի�ȡͼ�����ݽӿ�"""
    response = requests.get(f'{BASE_URL}/kg/data') # http://localhost:8000/api/kg/data
    assert response.status_code == 200, "�ӿ�����ʧ��"
    data = response.json()
    assert data['ret'] == 0, "�ӿڷ��ش���"
    assert 'nodes' in data['data'] and 'links' in data['data'], "���ݸ�ʽ����"

def test_add_entity():
    """�������ʵ��ӿ�"""
    test_entity = {
        "id": f"test_entity_{hash(json.dumps(locals()))}",  # ȷ��IDΨһ
        "name": "����ʵ��",
        "type": "��������"
    }

    response = requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )
    assert response.status_code == 200, "�ӿ�����ʧ��"
    result = response.json()
    assert result['ret'] == 0, f"���ʵ��ʧ��: {result.get('msg')}"

def test_add_duplicate_entity():
    """��������ظ�ID��ʵ��"""
    test_entity = {
        "id": "duplicate_test_id",
        "name": "�ظ�IDʵ��",
        "type": "��������"
    }

    # ��һ����ӣ�Ԥ�ڳɹ���
    requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )

    # �ڶ�����ӣ�Ԥ��ʧ�ܣ�
    response = requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )
    result = response.json()
    assert result['ret'] != 0, "�ظ����ʵ��δ����"

if __name__ == '__main__':
    pytest.main(['-v', 'test_kg_api.py'])


"""
http://localhost:8000/api/kg/data
http://localhost:8000/api/kg/entity
"""