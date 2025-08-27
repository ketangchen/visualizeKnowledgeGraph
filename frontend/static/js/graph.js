// 全局变量
let graphData = { nodes: [], links: [] }; // 图谱数据
let svg, simulation; // D3 SVG容器和力导向模拟

// 初始化图谱
function initGraph() {
    const container = document.getElementById('graph-container');
    const width = container.clientWidth;
    const height = container.clientHeight;

    // 创建SVG容器
    svg = d3.select('#graph-container')
        .append('svg')
        .attr('width', width)
        .attr('height', height);

    // 添加缩放功能
    svg.call(d3.zoom().on('zoom', (event) => {
        g.attr('transform', event.transform);
    }));

    const g = svg.append('g');

    // 初始化力导向布局
    simulation = d3.forceSimulation()
        .force('link', d3.forceLink().id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2));

    // 从后端加载数据
    loadGraphData();
}

// 从后端API加载图谱数据
function loadGraphData() {
    fetch('/api/kg/data')
        .then(response => response.json())
        .then(res => {
            if (res.ret === 0) {
                graphData = res.data;
                updateGraph(); // 更新图谱渲染
            } else {
                console.error('加载数据失败:', res.msg);
            }
        })
        .catch(error => console.error('请求失败:', error));
}

// 更新图谱渲染
function updateGraph() {
    // 清除现有元素
    svg.selectAll('*').remove();

    // 重新创建图层
    const g = svg.append('g');

    // 绘制关系线
    const link = g.append('g')
        .selectAll('line')
        .data(graphData.links)
        .enter().append('line')
        .attr('class', 'link')
        .attr('stroke-width', 2);

    // 绘制实体节点
    const node = g.append('g')
        .selectAll('g')
        .data(graphData.nodes)
        .enter().append('g')
        .attr('class', 'node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    // 节点添加圆形
    node.append('circle')
        .attr('r', 15)
        .attr('fill', d => {
            // 根据实体类型设置颜色
            const colors = { '人物': '#4285f4', '组织': '#34a853', '地点': '#fbbc05' };
            return colors[d.type] || '#ea4335';
        });

    // 节点添加文字
    node.append('text')
        .attr('dx', 20)
        .attr('dy', '.3em')
        .text(d => d.name);

    // 更新力导向模拟
    simulation.nodes(graphData.nodes)
        .on('tick', ticked);

    simulation.force('link')
        .links(graphData.links);

    simulation.alpha(1).restart();

    // 力导向布局更新回调
    function ticked() {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
    }
}

// 拖拽事件处理
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

// 绑定文件导入导出事件
function bindEvents() {
    // 导入JSON文件
    document.getElementById('import-btn').addEventListener('click', () => {
        document.getElementById('file-upload').click();
    });

    document.getElementById('file-upload').addEventListener('change', handleFileImport);

    // 导出当前数据
    document.getElementById('export-btn').addEventListener('click', exportGraphData);

    // 新增实体
    document.getElementById('add-entity-btn').addEventListener('click', addNewEntity);
}

// 处理文件导入
function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file || !file.name.endsWith('.json')) {
        alert('请选择JSON文件');
        return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            if (data.nodes && data.links) {
                graphData = data;
                updateGraph();
                alert('导入成功');
            } else {
                alert('JSON格式错误，需包含nodes和links');
            }
        } catch (error) {
            alert('解析失败: ' + error.message);
        }
    };
    reader.readAsText(file);
}

// 导出当前数据
function exportGraphData() {
    const dataStr = JSON.stringify(graphData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge_graph_${new Date().getTime()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

// 新增实体到后端
function addNewEntity() {
    const id = document.getElementById('entity-id').value;
    const name = document.getElementById('entity-name').value;
    if (!id || !name) {
        alert('请输入实体ID和名称');
        return;
    }

    fetch('/api/kg/entity', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, name })
    })
    .then(response => response.json())
    .then(res => {
        if (res.ret === 0) {
            alert('实体添加成功');
            loadGraphData(); // 重新加载数据
        } else {
            alert('添加失败: ' + res.msg);
        }
    });
}

// 页面加载完成后初始化
window.onload = () => {
    initGraph();
    bindEvents();
};