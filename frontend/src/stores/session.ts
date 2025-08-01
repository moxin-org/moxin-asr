import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

// 定义会话中单个节点的结构 (如果比纯文本更复杂)
export interface SessionNode {
    id: string; // 或者其他唯一标识符
    text: string;
    translatedText?: string; // 可选的翻译文本
    timestamp: number; // 时间戳
    // 可以添加其他元数据，如语言、说话人等
}

// 定义存储在 Pinia 和用于 Modal 列表的会话摘要结构
export interface SessionSummary {
    startTime: number; // 作为唯一 ID 和排序依据
    title: string;     // 第一句话的前10个字
    outline: string[];   // 前两行内容
    nodeCount: number; // 会话中的节点总数
}

const LOCAL_STORAGE_SESSION_PREFIX = 'rt_session_'; // 本地存储键前缀

export const useSessionStore = defineStore('session', () => {
    // --- State ---

    // 会话摘要列表，将由 pinia-plugin-persistedstate 自动持久化
    const sessionSummaries = ref<SessionSummary[]>([]);

    // 当前活动会话的节点 (不持久化)
    const currentSessionNodes = ref<SessionNode[]>([]);
    // 当前活动会话的开始时间 (不持久化)
    const currentSessionStartTime = ref<number | null>(null);
    // 标记会话是否正在进行中 (不持久化)
    const isSessionActive = ref(false);

    // --- Getters ---

    // 按开始时间降序排列的会话摘要
    const sortedSessionSummaries = computed(() => {
        // 创建副本进行排序，避免直接修改响应式 ref
        return [...sessionSummaries.value].sort((a, b) => b.startTime - a.startTime);
    });

    // --- Actions ---

    /**
     * 开始一个新的会话
     */
    function startSession() {
        if (isSessionActive.value) {
            console.warn("尝试在已有活动会话时开始新会话。");
            // 可以选择结束旧会话或直接返回
            // endSession(); // 如果需要自动结束旧会话
            return;
        }
        currentSessionStartTime.value = Date.now();
        currentSessionNodes.value = [];
        isSessionActive.value = true;
        console.log(`新会话开始于: ${new Date(currentSessionStartTime.value).toLocaleString()}`);
    }

    /**
     * 向当前活动会话添加一个节点
     * @param node - 要添加的会话节点
     */
    function addNode(node: SessionNode) {
        if (!isSessionActive.value || !currentSessionStartTime.value) {
            console.warn("没有活动的会话来添加节点。");
            return;
        }
        currentSessionNodes.value.push(node);
        // 可选：如果需要更强的容错性，可以在这里进行增量保存到 localStorage
        // saveCurrentSessionToLocalStorage();
    }

    /**
     * 结束当前活动会话，保存完整内容到 localStorage，并更新摘要列表
     */
    function endSession() {
        if (!isSessionActive.value || !currentSessionStartTime.value) {
            console.log("没有活动的会话可以结束。");
            // 确保状态被重置
            isSessionActive.value = false;
            currentSessionStartTime.value = null;
            currentSessionNodes.value = [];
            return;
        }

        const startTime = currentSessionStartTime.value;
        const nodes = [...currentSessionNodes.value]; // 创建副本

        // 重置当前会话状态
        isSessionActive.value = false;
        currentSessionStartTime.value = null;
        currentSessionNodes.value = [];

        if (nodes.length === 0) {
            console.log("会话结束，但没有节点需要保存。");
            return;
        }

        // 1. 生成摘要信息
        const title = nodes[0]?.text.substring(0, 10) || '无标题会话';
        const n1 = nodes[0];
        const outline = [
            `${n1?.text.substring(0, 56)}...\n`,
            `${n1?.translatedText?.substring(0, 56)}...\n`,
        ]
            // `${n1?.text.substring(0, 56)}\n${'-'.repeat(60)}\n${n1.translatedText?.substring(0, 56)}\n`
        const summary: SessionSummary = {
            startTime,
            title,
            outline,
            nodeCount: nodes.length,
        };

        // 2. 保存完整会话内容到 Local Storage
        try {
            const storageKey = `${LOCAL_STORAGE_SESSION_PREFIX}${startTime}`;
            localStorage.setItem(storageKey, JSON.stringify(nodes));
            console.log(`完整会话 ${startTime} 已保存到 localStorage.`);

            // 3. 更新 Pinia 中的摘要列表
            // 检查是否已存在相同 startTime 的摘要 (理论上不应发生，除非手动操作或错误)
            const existingIndex = sessionSummaries.value.findIndex(s => s.startTime === startTime);
            if (existingIndex === -1) {
                sessionSummaries.value.push(summary);
            } else {
                console.warn(`会话摘要 ${startTime} 已存在，将进行覆盖。`);
                sessionSummaries.value[existingIndex] = summary;
            }
            // pinia-plugin-persistedstate 会自动处理 sessionSummaries 的持久化

            console.log(`会话 ${startTime} 结束并已处理。`);

        } catch (error) {
            console.error("保存会话到 localStorage 时出错:", error);
            // 这里可以添加用户反馈，例如提示存储空间不足
            // 也许需要决定是否回滚摘要列表的添加
        }
    }

    /**
     * 从 Local Storage 加载指定会话的完整内容
     * @param startTime - 会话的开始时间戳 (作为 ID)
     * @returns SessionNode[] | null - 会话节点数组或在未找到/出错时返回 null
     */
    function loadSessionContent(startTime: number): SessionNode[] | null {
        try {
            const storageKey = `${LOCAL_STORAGE_SESSION_PREFIX}${startTime}`;
            const storedData = localStorage.getItem(storageKey);
            if (storedData) {
                const nodes = JSON.parse(storedData) as SessionNode[];
                console.log(`从 localStorage 加载了会话 ${startTime} 的内容 (${nodes.length} 个节点)`);
                return nodes;
            }
            console.warn(`在 localStorage 中未找到键为 ${storageKey} 的会话数据。`);
            return null;
        } catch (error) {
            console.error(`从 localStorage 加载会话 ${startTime} 时出错:`, error);
            return null;
        }
    }

    /**
    * 删除指定的会话 (包括摘要和本地存储的完整内容)
    * @param startTime - 要删除的会话的开始时间戳
    */
    function deleteSession(startTime: number) {
        try {
            // 1. 从摘要列表中移除
            const index = sessionSummaries.value.findIndex(s => s.startTime === startTime);
            if (index > -1) {
                sessionSummaries.value.splice(index, 1);
                console.log(`会话摘要 ${startTime} 已从 Pinia store 中移除。`);
                // pinia-plugin-persistedstate 会自动更新持久化的摘要列表
            } else {
                console.warn(`尝试删除一个不存在的会话摘要: ${startTime}`);
            }

            // 2. 从 Local Storage 中移除完整内容
            const storageKey = `${LOCAL_STORAGE_SESSION_PREFIX}${startTime}`;
            localStorage.removeItem(storageKey);
            console.log(`会话 ${startTime} 的完整内容已从 localStorage 中移除。`);

        } catch (error) {
            console.error(`删除会话 ${startTime} 时出错:`, error);
        }
    }

    // --- 返回 State, Getters, Actions ---
    return {
        // State
        sessionSummaries, // 摘要列表 (将被持久化)
        currentSessionNodes, // 当前活动会话的节点 (用于可能的实时显示)
        currentSessionStartTime, // 当前活动会话的开始时间
        isSessionActive, // 会话是否活动

        // Getters
        sortedSessionSummaries, // 排序后的摘要列表

        // Actions
        startSession,
        addNode,
        endSession,
        loadSessionContent, // 用于下载按钮点击时加载数据
        deleteSession,
    };
}, {
    // Pinia 持久化配置
    persist: {
        // 只持久化 sessionSummaries 状态
        paths: ['sessionSummaries'],
        // 默认使用 localStorage，如果需要可以指定
        // storage: localStorage,
    },
});

/**
 * 辅助函数：触发浏览器下载会话数据
 * @param startTime - 会话开始时间，用于文件名
 * @param nodes - 要下载的会话节点数据
 * @param format - 'json' 或 'txt' (默认为 'json')
 */
export function downloadSessionData(startTime: number, nodes: SessionNode[], format: 'json' | 'txt' = 'json') {
    if (!nodes || nodes.length === 0) {
        console.error("没有数据可供下载:", startTime);
        alert("没有内容可以下载。"); // 给用户反馈
        return;
    }
    try {
        const dateStr = new Date(startTime).toISOString().split('T')[0]; // YYYY-MM-DD
        let dataStr: string;
        let mimeType: string;
        let fileExtension: string;

        if (format === 'txt') {
            dataStr = nodes.map(n => `${new Date(n.timestamp).toLocaleTimeString()} - ${n.text}`).join('\n');
            mimeType = 'text/plain;charset=utf-8;';
            fileExtension = 'txt';
        } else { // 默认为 json
            dataStr = JSON.stringify(nodes, null, 2); // 美化 JSON 输出
            mimeType = 'application/json;charset=utf-8;';
            fileExtension = 'json';
        }

        const filename = `session_${dateStr}_${startTime}.${fileExtension}`;
        const blob = new Blob([dataStr], { type: mimeType });
        const link = document.createElement("a");

        // 使用 createObjectURL 创建一个临时的 URL 指向 Blob 对象
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click(); // 模拟点击下载链接

        // 清理：移除链接并释放 URL 对象
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        console.log(`已触发下载会话 ${startTime} 为 ${filename}`);

    } catch (error) {
        console.error(`下载会话 ${startTime} 时出错:`, error);
        alert("下载文件时发生错误。"); // 给用户反馈
    }
}
