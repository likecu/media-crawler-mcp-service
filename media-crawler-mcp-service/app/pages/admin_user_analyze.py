# -*- coding: utf-8 -*-
"""小红书用户分析管理页面"""

from starlette.responses import HTMLResponse

from .ui_base import (
    build_page_with_nav,
    create_page_header,
    create_button_group,
)


def render_user_analyze() -> HTMLResponse:
    """渲染用户分析页面"""
    
    header = create_page_header(
        title="小红书用户分析",
        breadcrumb="首页 / 用户分析",
        actions=create_button_group([
            ("刷新页面", "location.reload()", "secondary"),
        ])
    )

    main_content = """
    <div class="mc-user-analyze-container">
        <!-- 输入区域 -->
        <div class="mc-analyze-input-section">
            <div class="mc-card">
                <h3>输入用户主页</h3>
                <div class="mc-form-group">
                    <label for="user-homepage">小红书用户主页 URL</label>
                    <input 
                        type="url" 
                        id="user-homepage" 
                        placeholder="https://www.xiaohongshu.com/user/profile/xxxxx"
                        class="mc-input"
                    >
                    <small>请粘贴小红书用户主页链接，系统将自动分析用户画像</small>
                </div>
                <div class="mc-form-group">
                    <label for="analysis-depth">分析深度</label>
                    <select id="analysis-depth" class="mc-select">
                        <option value="basic">基础分析</option>
                        <option value="medium" selected>中等分析</option>
                        <option value="detailed">详细分析</option>
                    </select>
                </div>
                <button id="analyze-btn" class="btn btn-primary" onclick="startAnalysis()">
                    开始分析
                </button>
            </div>
        </div>

        <!-- 加载状态 -->
        <div id="loading-state" class="mc-loading hidden">
            <div class="mc-spinner"></div>
            <p>正在分析用户画像，请稍候...</p>
        </div>

        <!-- 分析结果区域 -->
        <div id="analysis-result" class="mc-result-container hidden">
            <!-- 用户基础画像 -->
            <div class="mc-card mc-persona-card">
                <div class="card-header">
                    <h3>👤 用户画像</h3>
                    <span id="confidence-badge" class="status-badge status-warning">置信度: 0%</span>
                </div>
                <div class="persona-grid">
                    <div class="persona-section">
                        <h4>基础信息</h4>
                        <div id="basic-info" class="detail-list"></div>
                    </div>
                    <div class="persona-section">
                        <h4>关系评估</h4>
                        <div id="relationship-info" class="detail-list"></div>
                    </div>
                </div>
            </div>

            <!-- 短期/长期评估 -->
            <div class="mc-card mc-assessment-card">
                <h3>📊 关系发展评估</h3>
                <div class="assessment-grid">
                    <div class="assessment-item">
                        <h4>短期发展</h4>
                        <div id="short-term-assessment" class="assessment-content"></div>
                    </div>
                    <div class="assessment-item">
                        <h4>长期兼容</h4>
                        <div id="long-term-assessment" class="assessment-content"></div>
                    </div>
                </div>
            </div>

            <!-- 开场白建议 -->
            <div class="mc-card mc-icebreaker-card">
                <h3>💬 开场白建议</h3>
                <div id="icebreaker-list" class="icebreaker-list"></div>
            </div>

            <!-- 话题树 -->
            <div class="mc-card mc-topic-card">
                <h3>🌳 话题树</h3>
                <div id="topic-tree" class="topic-tree"></div>
            </div>

            <!-- 总体评估 -->
            <div class="mc-card mc-overall-card">
                <h3>📝 总体评估</h3>
                <p id="overall-assessment" class="overall-assessment"></p>
            </div>

            <!-- 决策树按钮 -->
            <div class="mc-action-buttons">
                <button id="decision-tree-btn" class="btn btn-primary" onclick="generateDecisionTree()">
                    生成决策树
                </button>
            </div>
        </div>

        <!-- 决策树结果 -->
        <div id="decision-tree-result" class="mc-decision-container hidden">
            <div class="mc-card mc-decision-card">
                <div class="card-header">
                    <h3>🎯 决策树</h3>
                    <span id="feasibility-badge" class="status-badge status-warning">可行性: 未知</span>
                </div>
                <div id="decision-tree-content" class="decision-tree-content"></div>
                <div class="action-plan-section">
                    <h4>📋 行动计划</h4>
                    <p id="action-plan" class="action-plan"></p>
                </div>
            </div>

            <!-- 智能对话区域 -->
            <div class="mc-card mc-chat-card">
                <div class="card-header">
                    <h3>💭 智能对话</h3>
                    <button id="reset-chat-btn" class="btn btn-secondary btn-sm" onclick="resetChat()">
                        重置对话
                    </button>
                </div>
                <div id="chat-container" class="chat-container">
                    <div id="chat-messages" class="chat-messages"></div>
                </div>
                <div class="chat-input-section">
                    <input 
                        type="text" 
                        id="chat-input" 
                        placeholder="输入你的问题或情况描述..."
                        class="chat-input"
                        onkeypress="handleChatKeypress(event)"
                    >
                    <button id="send-chat-btn" class="btn btn-primary" onclick="sendChatMessage()">
                        发送
                    </button>
                </div>
            </div>
        </div>
    </div>
    <script src='/static/js/user_analyze.js'></script>
    """

    return build_page_with_nav(
        main_content=main_content,
        title="用户分析 · MediaCrawler MCP",
        current_path="/user_analyze"
    )
