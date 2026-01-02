const UserAnalyzeApp = {
    currentUrl: '',
    conversationHistory: [],
    decisionTree: null,
    personaData: null,
    conversationId: '',

    init: function() {
        console.log('用户分析应用初始化完成');
    },

    showLoading: function(message) {
        const loadingEl = document.getElementById('loading-state');
        if (loadingEl) {
            loadingEl.classList.remove('hidden');
            loadingEl.querySelector('p').textContent = message || '正在分析用户画像，请稍候...';
        }
        document.getElementById('analyze-btn').disabled = true;
    },

    hideLoading: function() {
        const loadingEl = document.getElementById('loading-state');
        if (loadingEl) {
            loadingEl.classList.add('hidden');
        }
        document.getElementById('analyze-btn').disabled = false;
    },

    showError: function(message) {
        alert('错误: ' + message);
    },

    showSuccess: function(message) {
        alert('成功: ' + message);
    },

    resetUI: function() {
        document.getElementById('analysis-result').classList.add('hidden');
        document.getElementById('decision-tree-result').classList.add('hidden');
        document.getElementById('chat-messages').innerHTML = '';
        this.conversationHistory = [];
        this.decisionTree = null;
        this.personaData = null;
    }
};

async function startAnalysis() {
    const urlInput = document.getElementById('user-homepage');
    const depthSelect = document.getElementById('analysis-depth');
    const url = urlInput.value.trim();

    if (!url) {
        alert('请输入用户主页URL');
        return;
    }

    if (!url.includes('xiaohongshu.com')) {
        alert('请输入有效的小红书用户主页URL');
        return;
    }

    UserAnalyzeApp.resetUI();
    UserAnalyzeApp.showLoading('正在分析用户画像...');
    UserAnalyzeApp.currentUrl = url;

    try {
        const response = await fetch('/mcp/api/v1/analyze/user/persona', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_homepage_url: url,
                analysis_depth: depthSelect.value
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `请求失败: ${response.status}`);
        }

        const data = await response.json();
        UserAnalyzeApp.personaData = data;
        renderPersonaResult(data);

    } catch (error) {
        console.error('分析失败:', error);
        UserAnalyzeApp.showError(error.message);
    } finally {
        UserAnalyzeApp.hideLoading();
    }
}

function renderPersonaResult(data) {
    document.getElementById('analysis-result').classList.remove('hidden');

    document.getElementById('confidence-badge').textContent = `置信度: ${Math.round(data.confidence_score * 100)}%`;
    document.getElementById('confidence-badge').className = `status-badge status-${data.confidence_score > 0.7 ? 'success' : data.confidence_score > 0.4 ? 'warning' : 'error'}`;

    renderBasicInfo(data.basic);
    renderRelationshipInfo(data.relationship);
    renderShortTermAssessment(data.short_term);
    renderLongTermAssessment(data.long_term);
    renderIcebreakers(data.icebreakers);
    renderTopicTree(data.topic_tree);
    document.getElementById('overall-assessment').textContent = data.overall_assessment || '暂无评估';
}

function renderBasicInfo(basic) {
    const container = document.getElementById('basic-info');
    const items = [
        { label: '年龄段', value: basic.age_range || '未知' },
        { label: '性格类型', value: basic.personality_type || '未知' },
        { label: '生活方式', value: basic.lifestyle || '未知' }
    ];

    if (basic.interests && basic.interests.length > 0) {
        items.push({ label: '兴趣爱好', value: basic.interests.join('、') });
    }

    container.innerHTML = items.map(item => `
        <div class="detail-row">
            <span class="detail-label">${item.label}:</span>
            <span class="detail-value">${item.value}</span>
        </div>
    `).join('');
}

function renderRelationshipInfo(relationship) {
    const container = document.getElementById('relationship-info');
    const items = [
        { label: '关系类型', value: translateRelationshipType(relationship.relationship_type) },
        { label: '沟通风格', value: relationship.communication_style || '未知' },
        { label: '开放程度', value: translateOpennessLevel(relationship.openness_level) },
        { label: '依恋类型', value: relationship.attachment_style || '未知' }
    ];

    if (relationship.relationship_goal) {
        items.splice(1, 0, { label: '关系目标', value: relationship.relationship_goal });
    }

    container.innerHTML = items.map(item => `
        <div class="detail-row">
            <span class="detail-label">${item.label}:</span>
            <span class="detail-value">${item.value}</span>
        </div>
    `).join('');
}

function renderShortTermAssessment(shortTerm) {
    const container = document.getElementById('short-term-assessment');
    const potentialClass = shortTerm.short_term_potential === 'high' ? 'status-success' : shortTerm.short_term_potential === 'medium' ? 'status-warning' : 'status-error';

    let html = `
        <div class="potential-indicator ${potentialClass}">
            <span class="potential-label">短期可能性:</span>
            <span class="potential-value">${translatePotential(shortTerm.short_term_potential)}</span>
        </div>
        <div class="score-bar">
            <div class="score-fill" style="width: ${shortTerm.opportunity_score}%"></div>
            <span class="score-text">机会得分: ${shortTerm.opportunity_score}</span>
        </div>
    `;

    if (shortTerm.attraction_indicators && shortTerm.attraction_indicators.length > 0) {
        html += `
            <div class="indicators-section">
                <h5>吸引指标:</h5>
                <ul class="indicator-list">
                    ${shortTerm.attraction_indicators.map(ind => `<li>${ind}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    if (shortTerm.timeline_recommendation) {
        html += `
            <div class="recommendation-section">
                <h5>时间线建议:</h5>
                <p>${shortTerm.timeline_recommendation}</p>
            </div>
        `;
    }

    container.innerHTML = html;
}

function renderLongTermAssessment(longTerm) {
    const container = document.getElementById('long-term-assessment');
    const compatibilityClass = longTerm.long_term_compatibility === 'high' ? 'status-success' : longTerm.long_term_compatibility === 'medium' ? 'status-warning' : 'status-error';

    let html = `
        <div class="potential-indicator ${compatibilityClass}">
            <span class="potential-label">长期兼容度:</span>
            <span class="potential-value">${translateCompatibility(longTerm.long_term_compatibility)}</span>
        </div>
    `;

    if (longTerm.core_value_match) {
        html += `<p><strong>核心价值观匹配:</strong> ${longTerm.core_value_match}</p>`;
    }

    if (longTerm.life_goal_alignment) {
        html += `<p><strong>人生目标一致性:</strong> ${longTerm.life_goal_alignment}</p>`;
    }

    if (longTerm.risk_factors && longTerm.risk_factors.length > 0) {
        html += `
            <div class="risk-section">
                <h5>⚠️ 风险因素:</h5>
                <ul class="risk-list">
                    ${longTerm.risk_factors.map(risk => `<li class="risk-item">${risk}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    container.innerHTML = html;
}

function renderIcebreakers(icebreakers) {
    const container = document.getElementById('icebreaker-list');

    if (!icebreakers || icebreakers.length === 0) {
        container.innerHTML = '<p class="no-data">暂无开场白建议</p>';
        return;
    }

    container.innerHTML = icebreakers.map((ib, index) => {
        const successClass = ib.success_rate > 70 ? 'status-success' : ib.success_rate > 50 ? 'status-warning' : 'status-error';
        const riskClass = ib.risk_level === 'low' ? 'status-success' : ib.risk_level === 'medium' ? 'status-warning' : 'status-error';

        return `
            <div class="icebreaker-item" onclick="copyIcebreaker('${index}')">
                <div class="icebreaker-header">
                    <span class="icebreaker-category badge badge-${ib.category}">${translateIcebreakerCategory(ib.category)}</span>
                    <span class="icebreaker-success ${successClass}">成功率: ${ib.success_rate}%</span>
                    <span class="icebreaker-risk ${riskClass}">风险: ${ib.risk_level}</span>
                </div>
                <p class="icebreaker-content">${ib.icebreaker}</p>
                <span class="copy-hint">点击复制</span>
            </div>
        `;
    }).join('');
}

function copyIcebreaker(index) {
    const icebreakers = UserAnalyzeApp.personaData.icebreakers;
    if (icebreakers && icebreakers[index]) {
        navigator.clipboard.writeText(icebreakers[index].icebreaker).then(() => {
            alert('已复制到剪贴板');
        }).catch(() => {
            const textarea = document.createElement('textarea');
            textarea.value = icebreakers[index].icebreaker;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            alert('已复制到剪贴板');
        });
    }
}

function renderTopicTree(topicTree) {
    const container = document.getElementById('topic-tree');

    if (!topicTree || topicTree.length === 0) {
        container.innerHTML = '<p class="no-data">暂无话题树</p>';
        return;
    }

    container.innerHTML = topicTree.map(node => `
        <div class="topic-node" data-priority="${node.priority}">
            <div class="topic-node-header">
                <span class="topic-category">${node.category}</span>
                <span class="topic-priority badge badge-${node.priority}">${translatePriority(node.priority)}</span>
            </div>
            <h4 class="topic-title">${node.topic}</h4>
            ${node.talking_points && node.talking_points.length > 0 ? `
                <div class="talking-points">
                    <h5>谈话要点:</h5>
                    <ul>
                        ${node.talking_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${node.follow_up_questions && node.follow_up_questions.length > 0 ? `
                <div class="follow-up-questions">
                    <h5>跟进问题:</h5>
                    <ul>
                        ${node.follow_up_questions.map(q => `<li>${q}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${node.land_zone_indicators && node.land_zone_indicators.length > 0 ? `
                <div class="land-indicators">
                    <h5>拉升关系指标:</h5>
                    <ul class="land-list">
                        ${node.land_zone_indicators.map(ind => `<li class="land-item">${ind}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `).join('');
}

async function generateDecisionTree() {
    if (!UserAnalyzeApp.currentUrl) {
        alert('请先进行用户分析');
        return;
    }

    const targetRelationship = prompt('目标关系类型 (romantic/friendship/casual):', 'romantic');
    const timeline = prompt('预期时间线 (short/medium/long):', 'medium');

    try {
        const response = await fetch('/mcp/api/v1/analyze/user/decision-tree', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_homepage_url: UserAnalyzeApp.currentUrl,
                target_relationship: targetRelationship || 'romantic',
                timeline: timeline || 'medium'
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `请求失败: ${response.status}`);
        }

        const data = await response.json();
        UserAnalyzeApp.decisionTree = data;
        renderDecisionTree(data);

    } catch (error) {
        console.error('决策树生成失败:', error);
        UserAnalyzeApp.showError(error.message);
    }
}

function renderDecisionTree(data) {
    document.getElementById('decision-tree-result').classList.remove('hidden');

    document.getElementById('feasibility-badge').textContent = `可行性: ${translateFeasibility(data.overall_feasibility)}`;
    document.getElementById('feasibility-badge').className = `status-badge status-${data.overall_feasibility === 'excellent' ? 'success' : data.overall_feasibility === 'high' || data.overall_feasibility === 'medium' ? 'warning' : 'error'}`;

    const container = document.getElementById('decision-tree-content');

    if (!data.decision_tree || data.decision_tree.length === 0) {
        container.innerHTML = '<p class="no-data">暂无决策树</p>';
        return;
    }

    let html = '';
    data.decision_tree.forEach((node, index) => {
        html += `
            <div class="decision-node">
                <div class="decision-node-header">
                    <span class="decision-number">${index + 1}</span>
                    <h4>${node.decision_point}</h4>
                </div>
                <p class="decision-situation">${node.situation}</p>
                <div class="decision-options">
                    <h5>可选方案:</h5>
                    ${node.options.map(opt => `
                        <div class="option-item">
                            <span class="option-text">${opt.option}</span>
                            <span class="option-outcome">${opt.outcome}</span>
                            <span class="option-probability">${opt.success_probability}%</span>
                        </div>
                    `).join('')}
                </div>
                <div class="recommended-action">
                    <h5>💡 推荐行动:</h5>
                    <p>${node.recommended_action}</p>
                    ${node.reasoning ? `<p class="reasoning">${node.reasoning}</p>` : ''}
                </div>
                ${node.next_steps && node.next_steps.length > 0 ? `
                    <div class="next-steps">
                        <h5>后续步骤:</h5>
                        <ul>
                            ${node.next_steps.map(step => `<li>${step}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
    });

    container.innerHTML = html;
    document.getElementById('action-plan').textContent = data.action_plan || '暂无行动计划';

    if (data.success_factors && data.success_factors.length > 0) {
        const successFactorsHtml = `
            <div class="factors-section success-factors">
                <h5>✅ 成功因素:</h5>
                <ul>
                    ${data.success_factors.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
        `;
        document.querySelector('.action-plan-section').insertAdjacentHTML('beforeend', successFactorsHtml);
    }

    if (data.warning_signals && data.warning_signals.length > 0) {
        const warningSignalsHtml = `
            <div class="factors-section warning-signals">
                <h5>⚠️ 警示信号:</h5>
                <ul>
                    ${data.warning_signals.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
        document.querySelector('.action-plan-section').insertAdjacentHTML('beforeend', warningSignalsHtml);
    }

    document.getElementById('decision-tree-result').scrollIntoView({ behavior: 'smooth' });
}

async function sendChatMessage() {
    const inputEl = document.getElementById('chat-input');
    const message = inputEl.value.trim();

    if (!message) {
        return;
    }

    if (!UserAnalyzeApp.currentUrl) {
        alert('请先进行用户分析');
        return;
    }

    appendChatMessage('user', message);
    inputEl.value = '';
    showTypingIndicator();

    try {
        const response = await fetch('/mcp/api/v1/analyze/user/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_homepage_url: UserAnalyzeApp.currentUrl,
                conversation_history: UserAnalyzeApp.conversationHistory,
                current_message: message,
                decision_tree_context: UserAnalyzeApp.decisionTree
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `请求失败: ${response.status}`);
        }

        const data = await response.json();

        removeTypingIndicator();

        if (data.response && data.response.content) {
            appendChatMessage('assistant', data.response.content);
            UserAnalyzeApp.conversationHistory.push({ role: 'user', content: message });
            UserAnalyzeApp.conversationHistory.push({ role: 'assistant', content: data.response.content });
            UserAnalyzeApp.conversationId = data.conversation_id;

            if (data.suggestions && data.suggestions.length > 0) {
                showChatSuggestions(data.suggestions);
            }
        }

    } catch (error) {
        console.error('对话发送失败:', error);
        removeTypingIndicator();
        appendChatMessage('assistant', '抱歉，处理您的消息时出错。请稍后再试。');
        UserAnalyzeApp.showError(error.message);
    }
}

function appendChatMessage(role, content) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${role}-message`;
    messageDiv.innerHTML = `
        <div class="message-avatar">${role === 'user' ? '👤' : '🤖'}</div>
        <div class="message-content">${content.replace(/\n/g, '<br>')}</div>
    `;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function showTypingIndicator() {
    const container = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message assistant-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    typingDiv.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-content">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
        </div>
    `;
    container.appendChild(typingDiv);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function showChatSuggestions(suggestions) {
    const container = document.getElementById('chat-messages');
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.className = 'chat-suggestions';
    suggestionsDiv.innerHTML = `
        <p class="suggestions-label">💡 建议话题:</p>
        <div class="suggestion-buttons">
            ${suggestions.map(s => `<button class="suggestion-btn" onclick="useSuggestion('${s.replace(/'/g, "\\'")}')">${s}</button>`).join('')}
        </div>
    `;
    container.appendChild(suggestionsDiv);
    container.scrollTop = container.scrollHeight;
}

function useSuggestion(suggestion) {
    document.getElementById('chat-input').value = suggestion;
    sendChatMessage();
}

async function resetChat() {
    if (!UserAnalyzeApp.currentUrl) {
        return;
    }

    if (!confirm('确定要重置对话吗？对话历史将被清除。')) {
        return;
    }

    try {
        const response = await fetch('/mcp/api/v1/analyze/user/conversation/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_homepage_url: UserAnalyzeApp.currentUrl
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `请求失败: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            UserAnalyzeApp.conversationHistory = [];
            document.getElementById('chat-messages').innerHTML = '';
            UserAnalyzeApp.showSuccess('对话已重置');
        }

    } catch (error) {
        console.error('重置对话失败:', error);
        UserAnalyzeApp.showError(error.message);
    }
}

function handleChatKeypress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}

function translateRelationshipType(type) {
    const typeMap = {
        'potential_romantic': '潜在恋爱对象',
        'friendship': '朋友关系',
        'casual': '随意发展',
        'unknown': '未知'
    };
    return typeMap[type] || type || '未知';
}

function translateOpennessLevel(level) {
    const levelMap = {
        'low': '低',
        'medium': '中等',
        'high': '高'
    };
    return levelMap[level] || level || '中等';
}

function translatePotential(potential) {
    const potentialMap = {
        'high': '高',
        'medium': '中等',
        'low': '低'
    };
    return potentialMap[potential] || potential || '未知';
}

function translateCompatibility(compatibility) {
    const compatibilityMap = {
        'high': '高',
        'medium': '中等',
        'low': '低'
    };
    return compatibilityMap[compatibility] || compatibility || '未知';
}

function translateIcebreakerCategory(category) {
    const categoryMap = {
        'comment': '评论式',
        'compliment': '赞美式',
        'question': '提问式'
    };
    return categoryMap[category] || category || '其他';
}

function translatePriority(priority) {
    const priorityMap = {
        'high': '高优先级',
        'medium': '中优先级',
        'low': '低优先级'
    };
    return priorityMap[priority] || priority || '中优先级';
}

function translateFeasibility(feasibility) {
    const feasibilityMap = {
        'excellent': '优秀',
        'high': '高',
        'medium': '中等',
        'low': '低',
        'unknown': '未知'
    };
    return feasibilityMap[feasibility] || feasibility || '未知';
}

document.addEventListener('DOMContentLoaded', function() {
    UserAnalyzeApp.init();
});
