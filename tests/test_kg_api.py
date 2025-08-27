import requests
import json
import pytest
from django.conf import settings

BASE_URL = getattr(settings, 'TEST_BASE_URL', 'http://localhost:8000/api')

def test_get_graph_data():
    """测试获取图谱数据接口"""
    response = requests.get(f'{BASE_URL}/kg/data') # http://localhost:8000/api/kg/data
    assert response.status_code == 200, "接口请求失败"
    data = response.json()
    assert data['ret'] == 0, "接口返回错误"
    assert 'nodes' in data['data'] and 'links' in data['data'], "数据格式错误"

def test_add_entity():
    """测试添加实体接口"""
    test_entity = {
        "id": f"test_entity_{hash(json.dumps(locals()))}",  # 确保ID唯一
        "name": "测试实体",
        "type": "测试类型"
    }

    response = requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )
    assert response.status_code == 200, "接口请求失败"
    result = response.json()
    assert result['ret'] == 0, f"添加实体失败: {result.get('msg')}"

def test_add_duplicate_entity():
    """测试添加重复ID的实体"""
    test_entity = {
        "id": "duplicate_test_id",
        "name": "重复ID实体",
        "type": "测试类型"
    }

    # 第一次添加（预期成功）
    requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )

    # 第二次添加（预期失败）
    response = requests.post(
        f'{BASE_URL}/kg/entity',
        headers={'Content-Type': 'application/json'},
        data=json.dumps(test_entity)
    )
    result = response.json()
    assert result['ret'] != 0, "重复添加实体未报错"

if __name__ == '__main__':
    pytest.main(['-v', 'test_kg_api.py'])


"""
http://localhost:8000/api/kg/data
http://localhost:8000/api/kg/entity
"""