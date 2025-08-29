/* -*- coding: utf-8 -*- */
// ȫ�ֱ���
let graphData = { nodes: [], links: [] }; // ͼ������
let svg, simulation; // D3 SVG������������ģ��

// ��ʼ��ͼ��
function initGraph() {
    const container = document.getElementById('graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // ����SVG����
    svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // �������Ź���
    svg.call(d3.zoom().on('zoom', (event) => {
        g.attr('transform', event.transform);
    }));

    const g = svg.append('g');

    // ��ʼ�������򲼾�
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

    // �Ӻ�˼�������
    loadGraphData();
}

// �Ӻ��API����ͼ������
function loadGraphData() {
    fetch('/api/kg/data')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP����${response.status}`);
            }
            return response.json();
        })
        .then(res => {
            if (res.ret === 0) {
                graphData = res.data;
                updateGraph(); // ������Ⱦͼ��
            } else {
                console.error('���ݼ���ʧ��:', res.msg);
                alert(`���ݼ���ʧ�ܣ�${res.msg}`);
            }
        })
        .catch(error => {
            console.error('����ʧ��:', error);
            alert(`��������ʱ������${error.message}`);
        });
}

// ������Ⱦͼ��
function updateGraph() {
        // �������Ԫ��
        svg.selectAll('*').remove();

        // �����µ�ͼ��
        const g = svg.append('g');

        // ���ƹ�ϵ��
        const link = g.append('g')
            .selectAll('line')
            .data(graphData.links)
            .enter().append('line')
            .attr('class', 'link')
            .attr('stroke-width', 2);

        // ����ʵ��ڵ�
        const node = g.append('g')
            .selectAll('g')
            .data(graphData.nodes)
            .enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragstarted)
                .on('drag', dragged)
                .on('end', dragended));

        // �ڵ�����Բ��
        node.append('circle')
            .attr('r', 15)
            .attr('fill', d => {
                // ����ʵ������������ɫ
                const colors = { '����': '#4285f4', '��֯': '#34a853', '�ص�': '#fbbc05' };
                return colors[d.type] || '#ea4335';
            });

    // �ڵ���������
    node.append('text')
        .attr('dx', 20)
        .attr('dy', '.3em')
        .text(d => d.name);

    // ����������ģ��
    simulation.nodes(graphData.nodes)
        .on('tick', ticked);

    simulation.force('link')
        .links(graphData.links);

    simulation.alpha(1).restart();

    // �����򲼾ָ��»ص�
    function ticked() {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    }
}

// ��ק�¼�����
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}

// ���¼�
function bindEvents() {
    // ����JSON�ļ�
    document.getElementById('import-btn').addEventListener('click', () => {
        document.getElementById('file-upload').click();
    });

    document.getElementById('file-upload').addEventListener('change', handleFileImport);

    // ������ǰ����
    document.getElementById('export-btn').addEventListener('click', exportGraphData);

    // ����ʵ��
    document.getElementById('add-entity-btn').addEventListener('click', addNewEntity);
}

// �����ļ�����
function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file || !file.name.endsWith('.json')) {
        alert('��ѡ��JSON�ļ�');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            if (data.nodes && data.links) {
                graphData = data;
                updateGraph();
                alert('����ɹ�');
            } else {
                alert('JSON��ʽ���������nodes��links');
            }
        } catch (error) {
            alert('����ʧ��: ' + error.message);
        }
    };
    reader.readAsText(file);
}

// ������ǰ����
function exportGraphData() {
    const dataStr = JSON.stringify(graphData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timestamp = `${year}${month}${day}_${hours}${minutes}${seconds}`;
    a.download = `kg_${timestamp}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// ������ʵ�嵽���
function addNewEntity() {
    const id = document.getElementById('entity-id').value;
    const name = document.getElementById('entity-name').value;
    if (!id || !name) {
        alert('����дʵ��ID������');
        return;
    }

    fetch('/api/kg/entities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, name })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP����${response.status}`);
        }
        return response.json();
    })
    .then(res => {
        if (res.ret === 0) {
            alert('ʵ�����ӳɹ�');
            loadGraphData(); // ���¼�������
        } else {
            alert('����ʧ��: ' + res.msg);
        }
    })
    .catch(error => {
        alert('����ʧ��: ' + error.message);
    });
}

// 新增：对接后端的通用操作（供简单页面或控制台使用）
async function updateEntityOnServer(entityId, payload) {
    try {
        const response = await fetch(`/api/kg/entities/${encodeURIComponent(entityId)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        return data.ret === 0;
    } catch (e) {
        console.warn('更新实体异常:', e);
        return false;
    }
}

async function deleteEntityFromServer(entityId) {
    try {
        const response = await fetch(`/api/kg/entities/${encodeURIComponent(entityId)}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        return data.ret === 0;
    } catch (e) {
        console.warn('删除实体异常:', e);
        return false;
    }
}

async function createRelationshipOnServer(sourceId, targetId, type, description = '') {
    try {
        const response = await fetch('/api/kg/relationships', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: sourceId, target: targetId, type, description })
        });
        const data = await response.json();
        if (data.ret === 0 && data.data && typeof data.data.id !== 'undefined') {
            return { ok: true, id: data.data.id };
        }
        return { ok: false };
    } catch (e) {
        console.warn('创建关系异常:', e);
        return { ok: false };
    }
}

async function deleteRelationshipFromServer(relId) {
    try {
        const response = await fetch(`/api/kg/relationships/${relId}`, { method: 'DELETE' });
        const data = await response.json();
        return data.ret === 0;
    } catch (e) {
        console.warn('删除关系异常:', e);
        return false;
    }
}

// 暴露简易API，方便在控制台或其他脚本中调用
window.KGApi = {
    updateEntityOnServer,
    deleteEntityFromServer,
    createRelationshipOnServer,
    deleteRelationshipFromServer,
};

// ҳ�������ɺ��ʼ��
window.onload = () => {
    initGraph();
    bindEvents();
};