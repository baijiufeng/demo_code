// 英文ID到中文标签的映射（保留在HTML中，这里作为备用）
const defaultLabelMap = {};

// 从HTML中读取labelMap数据
function getLabelMap() {
    const dataElement = document.getElementById('label-map-data');
    if (dataElement) {
        try {
            return JSON.parse(dataElement.textContent);
        } catch (e) {
            console.error('解析labelMap数据失败:', e);
        }
    }
    return defaultLabelMap;
}

// 替换SVG中的英文标签为中文（支持 "Label" 或 "Label 123" 格式）
function replaceLabels() {
    const svg = document.querySelector('#sankey-diagram svg');
    if (!svg) return;

    const labelMap = getLabelMap();
    const textElements = svg.querySelectorAll('text.nodeLabel, text');
    textElements.forEach(text => {
        const originalText = text.textContent.trim();
        let newText = null;

        // 完全匹配
        if (labelMap[originalText] !== undefined) {
            newText = labelMap[originalText];
        } else {
            // 匹配 "Label 数值" 格式，保留数字
            for (const [en, zh] of Object.entries(labelMap)) {
                const regex = new RegExp('^' + en.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s+(\\d+)$');
                const match = originalText.match(regex);
                if (match) {
                    newText = zh + ' ' + match[1];
                    break;
                }
            }
        }

        if (newText !== null) {
            text.textContent = newText;
        }
    });
}

// 等待DOM加载完成后初始化
function initSankey() {
    mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        sankey: {
            nodeAlignment: 'left',
            margin: 20,
            nodeWidth: 20,
            nodePadding: 10,
            nodeLabelPadding: 10,
            linkOpacity: 0.4,
            linkShortening: true,
            linkColor: 'gradient',
            iterations: 32
        }
    });

    // 等待Mermaid渲染完成
    setTimeout(replaceLabels, 1500);
    setTimeout(replaceLabels, 3000);

    // 使用MutationObserver监听SVG变化
    const observer = new MutationObserver((mutations) => {
        replaceLabels();
    });

    const target = document.getElementById('sankey-diagram');
    if (target) {
        observer.observe(target, {
            childList: true,
            subtree: true
        });
    }
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSankey);
} else {
    initSankey();
}