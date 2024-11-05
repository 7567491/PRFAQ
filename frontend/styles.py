def load_css():
    return """
    <style>
    /* Logo样式 */
    .sidebar-logo {
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .sidebar-logo img {
        object-fit: none;  /* 保持原始尺寸 */
        margin: 0 auto;
    }
    """ + load_css_content()  # 添加原有的CSS内容

def load_css_content():
    return """
    /* 原有的CSS样式 */
    /* 主题颜色 - 亚马逊风格 */
    :root {
        --primary-color: #232F3E;
        --secondary-color: #FF9900;
        --background-color: #131921;
        --surface-color: #232F3E;
        --text-color: #FFFFFF;
        --border-color: #37475A;
        --hover-color: #485769;
        --success-color: #067D62;
    }
    
    /* 全局样式 */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* 标题样式 */
    .main-title {
        color: var(--secondary-color);
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin: 2rem 0;
        text-shadow: 0 0 10px rgba(255, 153, 0, 0.3);
    }
    
    /* 表单样式 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--surface-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 3px;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--secondary-color);
        box-shadow: 0 0 0 2px rgba(255, 153, 0, 0.2);
    }
    
    /* 按钮样式 */
    .stButton > button {
        background: var(--secondary-color);
        color: var(--primary-color);
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 3px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #FFAC31;
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(255, 153, 0, 0.2);
    }
    
    /* 标签页样式 */
    .stTabs {
        background-color: var(--surface-color);
        padding: 1rem;
        border-radius: 3px;
        margin: 1rem 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 3px;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: var(--secondary-color);
        border-color: var(--secondary-color);
        color: var(--primary-color);
    }
    
    /* 生成结果样式 */
    .generated-content {
        background-color: var(--surface-color);
        border-left: 4px solid var(--secondary-color);
        padding: 1.5rem;
        border-radius: 3px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    /* 侧边栏样式 */
    .sidebar-content {
        background-color: var(--surface-color);
        padding: 1rem;
        border-radius: 3px;
        margin-bottom: 1rem;
        border: 1px solid var(--border-color);
    }
    
    /* 表单容器样式 */
    form {
        background-color: var(--surface-color);
        padding: 1.5rem;
        border-radius: 3px;
        border: 1px solid var(--border-color);
        margin: 1rem 0;
    }
    
    /* 确保文本可见性 */
    p, h1, h2, h3, h4, h5, h6, label {
        color: var(--text-color) !important;
    }
    
    /* 链接样式 */
    a {
        color: var(--secondary-color);
        text-decoration: none;
    }
    
    a:hover {
        color: #FFAC31;
        text-decoration: underline;
    }
    
    /* 分割线样式 */
    hr {
        border-color: var(--border-color);
        margin: 2rem 0;
    }
    
    /* 输入框标签样式 */
    .stTextInput > label {
        color: var(--text-color) !important;
        font-weight: 500;
    }

    /* 成功消息样式 */
    .element-container div[data-testid="stMarkdownContainer"] > div.stSuccess {
        background-color: var(--success-color);
        color: white;
        padding: 0.75rem;
        border-radius: 3px;
    }
    </style>
    """