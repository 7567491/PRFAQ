PRFAQ Pro 使用说明文档
==================

项目概述
--------
PRFAQ Pro是一个基于Streamlit开发的PRFAQ(Press Release/FAQ)生成工具，用于帮助产品经理生成产品相关的新闻稿和FAQ文档。该工具使用AIGC技术，能够自动生成高质量的产品文案。

主要功能
--------
1. PR生成
   - 支持输入客户、场景、需求、痛点等关键信息
   - 自动生成包含标题、副标题、时间、媒体名称等完整新闻稿
   - 包含行业大咖证言和客户证言
   - 自动生成产品价值主张和客户召唤

2. 客户FAQ (外部FAQ)
   - 市场规模分析
   - 三年盈利预测
   - 合规风险分析
   - 供应商依赖分析
   - 竞品分析

3. 内部FAQ
   - 产品独特性分析
   - 售后服务流程
   - 产品定价策略
   - 购买渠道分析
   - 促销活动策略

UI布局说明
---------
1. 侧边栏
   - PRFAQ Pro标题
   - 功能选择菜单（PR生成/客户FAQ/内部FAQ）

2. 主内容区
   - PR生成页面：包含表单输入区和生成结果显示区
   - FAQ页面：包含问题列表和答案生成区
   - 所有生成的内容都支持Markdown格式显示

文件结构
--------
project_root/
├── app.py                 # 主程序入口，包含UI布局和路由控制
├── modules/               # 模块目录
│   ├── __init__.py       # 模块初始化文件
│   ├── api.py            # API客户端封装，处理与AI服务的通信
│   ├── faq_generator.py  # 客户FAQ生成器
│   ├── faq_in.py         # 内部FAQ生成器
│   └── utils.py          # 工具函数集合
├── config/               # 配置文件目录
│   ├── config.json       # 主配置文件
│   └── prompts.json      # 提示词模板配置
└── README.txt            # 本说明文档

文件用途说明
-----------
1. app.py
   - 程序主入口
   - 实现Streamlit界面布局
   - 处理用户交互和路由
   - 初始化API客户端

2. modules/api.py
   - 封装与AI服务的通信
   - 处理API认证
   - 实现内容生成流式传输
   - 错误处理和重试机制

3. modules/faq_generator.py
   - 实现客户FAQ生成功能
   - 包含5个核心问题的处理逻辑
   - 处理提示词构建和内容生成

4. modules/faq_in.py
   - 实现内部FAQ生成功能
   - 包含5个核心问题的处理逻辑
   - 处理提示词构建和内容生成

5. modules/utils.py
   - 提供配置文件加载功能
   - 实现通用工具函数
   - 处理错误和异常

6. config/config.json
   - 存储API密钥和配置
   - 服务器配置信息
   - 其他系统参数

7. config/prompts.json
   - 存储各类提示词模板
   - FAQ问题模板
   - PR生成模板

配置说明
--------
1. API配置
   - API_KEY: AI服务的访问密钥
   - API_URL: AI服务的接口地址
   - MAX_RETRIES: 最大重试次数

2. 系统配置
   - STREAM_TIMEOUT: 流式传输超时时间
   - CHUNK_SIZE: 数据块大小
   - DEBUG_MODE: 调试模式开关

使用说明
--------
1. 安装依赖   ```
   pip install -r requirements.txt   ```

2. 配置文件
   - 复制 config.json.example 为 config.json
   - 填入必要的配置信息

3. 运行程序   ```
   streamlit run app.py   ```

注意事项
--------
1. 确保API密钥配置正确
2. 保持网络连接稳定
3. 大量生成内容时注意API使用限制
4. 定期备份重要生成内容

错误处理
--------
1. API错误
   - 检查配置文件
   - 确认API密钥有效性
   - 查看错误日志

2. 生成错误
   - 检查提示词格式
   - 确认输入内容完整
   - 尝试重新生成

维护支持
--------
如遇问题请联系：
- 技术支持：support@example.com
- 问题反馈：feedback@example.com

版本信息
--------
当前版本：1.0.0
更新日期：2024-03-21

Python代码收集结果:


================================================================================
文件: app.py
================================================================================

import streamlit as st
import json
from pathlib import Path
from modules.api import APIClient
from modules.utils import (
    load_config, 
    load_templates, 
    load_history, 
    save_history, 
    load_letters,
    add_log
)
from modules.pr_generator import PRGenerator
from modules.faq_generator import FAQGenerator
from modules.faq_in import InternalFAQGenerator
from modules.mlp_generator import MLPGenerator
from datetime import datetime
import pandas as pd
from modules.all_in_one_generator import AllInOneGenerator

def clear_main_content():
    """Clear all content in the main area except core sentence and logs"""
    preserved_keys = ['current_section', 'logs', 'product_core_sentence']
    for key in list(st.session_state.keys()):
        if key not in preserved_keys:
            del st.session_state[key]

def show_customer_faq():
    # 创建API客户端实例
    config = load_config()
    api_client = APIClient(config)
    
    # 创建FAQ生成器并传入api_client
    faq_generator = FAQGenerator(api_client)
    faq_generator.generate_customer_faq()

def main():
    try:
        # Load configurations
        config = load_config()
        templates = load_templates()
        
        st.set_page_config(
            page_title=templates["page_title"],
            layout="wide"
        )
        
        # Initialize session state
        if 'current_section' not in st.session_state:
            st.session_state.current_section = 'pr'
        if 'logs' not in st.session_state:
            st.session_state.logs = []
        
        # Create main content and log columns
        main_col, log_col = st.columns([5, 1])
        
        with st.sidebar:
            st.title("PRFAQ Pro")
            
            # Navigation buttons
            st.header("功能导航")
            if st.button("📝 PR 生成", use_container_width=True, type="secondary"):
                clear_main_content()
                st.session_state.current_section = 'pr'
                add_log("info", "切换到PR生成模式")
            if st.button("❓ 客户 FAQ", use_container_width=True, type="secondary"):
                clear_main_content()
                st.session_state.current_section = 'faq'
                add_log("info", "切换到客户FAQ模式")
            if st.button("📋 内部 FAQ", use_container_width=True, type="secondary"):
                clear_main_content()
                st.session_state.current_section = 'internal_faq'
                add_log("info", "切换到内部FAQ模式")
            if st.button("🚀 MLP开发", use_container_width=True, type="secondary"):
                clear_main_content()
                st.session_state.current_section = 'mlp'
                add_log("info", "切换到MLP开发模式")
            if st.button("✨ PRFAQ一键生成", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'all_in_one'
                add_log("info", "切换到PRFAQ一键生成模式")
            if st.button("🧪 账单测试", use_container_width=True):
                clear_main_content()
                st.session_state.current_section = 'bill_test'
                add_log("info", "切换到账单测试模式")
            if st.button("💰 账单", use_container_width=True):
                clear_main_content()
                st.session_state.show_bill_detail = True
                add_log("info", "查看账单明细")
            
            # History section
            st.header("历史记录")
            history = load_history()
            for idx, item in enumerate(reversed(history)):
                if st.button(
                    f"#{len(history)-idx} {item['timestamp'][:16]}",
                    key=f"history_{idx}",
                    help="点击查看详情",
                    use_container_width=True,
                    type="secondary"
                ):
                    # 清空主屏幕内容
                    clear_main_content()
                    # 设置当前部分为历史记录
                    st.session_state.current_section = 'history'
                    # 保存选中的历史记录
                    st.session_state.selected_history = item
                    st.session_state.show_history_detail = True
                    add_log("info", f"查看历史记录 #{len(history)-idx}")
        
        # Main content area
        with main_col:
            if hasattr(st.session_state, 'show_bill_detail') and st.session_state.show_bill_detail:
                st.markdown("### 账单明细")
                letters_data = load_letters()  # 加载字符统计数据
                
                # 显示总账单
                total = letters_data["total"]
                st.markdown("#### 总消费")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总消费(人民币)", f"{total['cost_rmb']:.6f} 元")
                with col2:
                    st.metric("总输入字符数", f"{total['input_letters']:,}")
                with col3:
                    st.metric("总输出字符数", f"{total['output_letters']:,}")
                
                st.markdown("#### 消费记录")
                # 创建账单明细表格
                records_df = pd.DataFrame(letters_data["records"])
                if not records_df.empty:
                    records_df['timestamp'] = pd.to_datetime(records_df['timestamp'])
                    records_df = records_df.sort_values('timestamp', ascending=False)
                    
                    # 格式化显示的列
                    st.dataframe(
                        records_df[[
                            'timestamp', 'api_name', 'operation',
                            'input_letters', 'output_letters',
                            'total_cost_rmb', 'total_cost_usd'
                        ]].style.format({
                            'total_cost_rmb': '{:.6f}',
                            'total_cost_usd': '{:.6f}'
                        }),
                        use_container_width=True
                    )
                else:
                    st.info("暂无账单记录")
            
            elif st.session_state.current_section == 'history' and hasattr(st.session_state, 'show_history_detail') and st.session_state.show_history_detail:
                st.markdown(f"### 生成记录 - {st.session_state.selected_history['timestamp']}")
                st.markdown(st.session_state.selected_history['content'])
            
            elif st.session_state.current_section == 'all_in_one':
                # 创建API客户端实例
                api_client = APIClient(config)
                all_in_one_generator = AllInOneGenerator(api_client)
                all_in_one_generator.render()
            elif st.session_state.current_section == 'pr':
                # 创建API客户端实例
                api_client = APIClient(config)
                pr_generator = PRGenerator(api_client)
                pr_generator.render()
            elif st.session_state.current_section == 'faq':
                # 创建API客户端实例
                api_client = APIClient(config)
                faq_generator = FAQGenerator(api_client)
                faq_generator.generate_customer_faq()
            elif st.session_state.current_section == 'internal_faq':
                # 创建API客户端实例
                api_client = APIClient(config)
                faq_generator = InternalFAQGenerator(api_client)
                faq_generator.generate_internal_faq()
            elif st.session_state.current_section == 'bill_test':
                st.markdown("### 账单测试")
                
                # 创建一个聊天历史容器
                chat_container = st.container()
                
                # 创建输入框和发送按钮
                with st.form("chat_form", clear_on_submit=True):
                    user_input = st.text_area("请输入您的问题:", height=100)
                    submitted = st.form_submit_button("发送")
                
                # 初始化聊天历史
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []
                
                # 处理用户输入
                if submitted and user_input:
                    # 添加用户消息到历史
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    
                    # 创建API客户端
                    api_client = APIClient(config)
                    
                    # 创建一个空白占位符用于显示AI回复
                    response_placeholder = st.empty()
                    content = ""
                    
                    # 流式生成回复
                    for chunk in api_client.generate_content_stream(user_input):
                        content += chunk
                        response_placeholder.markdown(content)
                    
                    # 添加AI回复到历史
                    st.session_state.chat_history.append({"role": "assistant", "content": content})
                
                # 在聊天容器中显示历史消息
                with chat_container:
                    for message in st.session_state.chat_history:
                        if message["role"] == "user":
                            st.markdown(f"**👤 您:** {message['content']}")
                        else:
                            st.markdown(f"**🤖 AI:** {message['content']}")
                            st.markdown("---")
            elif st.session_state.current_section == 'mlp':
                # 创建API客户端实例
                api_client = APIClient(config)
                mlp_generator = MLPGenerator(api_client)
                mlp_generator.generate_mlp()
            else:
                st.info(f"{templates['sections'][st.session_state.current_section]['title']}能正在开发中...")
            
            # Log panel
            with log_col:
                st.markdown("### 系统日志")
                
                # 直接显示日志内容,不使用容器
                for log in st.session_state.logs:
                    # 根据日志类型选择不同的CSS类
                    if log['level'] == 'error':
                        color = "#FF0000"  # 错误信息用红色
                    elif log['level'] == 'user':
                        color = "#FFB700"  # 用户操作用黄色
                    elif log['level'] == 'warning':
                        color = "#FFFF00"  # 警告信息用亮黄色
                    else:
                        color = "#00FF00"  # 程序步骤用绿色
                        
                    st.markdown(f'<span style="color: {color};">[{log["timestamp"]}] {log["message"]}</span>', 
                              unsafe_allow_html=True)
                
                # Add clear logs button
                if st.button("清除日志", key="clear_logs"):
                    st.session_state.logs = []
                    add_log("info", "日志已清除")
        
    except Exception as e:
        error_msg = f"程序运行出错: {str(e)}"
        add_log("error", error_msg)
        st.error(error_msg)
        st.error("请检查配置文件是否正确，或联系管理员")

if __name__ == "__main__":
    main()

================================================================================
文件: convert_to_utf8.py
================================================================================

import json
from pathlib import Path

def convert_file_to_utf8(file_path):
    try:
        # 尝试以 UTF-8 读取
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # 如果失败，尝试以 GBK 读取
        with open(file_path, 'r', encoding='gbk') as f:
            data = json.load(f)
    
    # 以 UTF-8 写入
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 转换所有 JSON 文件
json_files = ['config.json', 'templates.json', 'prompts.json', 'metrics.json']
for file_name in json_files:
    file_path = Path(file_name)
    if file_path.exists():
        print(f"Converting {file_name} to UTF-8...")
        convert_file_to_utf8(file_path)
        print(f"Converted {file_name} successfully!") 

================================================================================
文件: run_tests.py
================================================================================

import unittest
import sys
import os

def run_tests():
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # 发现并运行所有测试
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 运行测试并收集结果
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 根据测试结果设置退出码
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 

================================================================================
文件: modules\all_in_one_generator.py
================================================================================

import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log, save_history
from datetime import datetime
import json

class AllInOneGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()
        self.all_content = []  # 存储所有生成的内容

    def render(self):
        """渲染一键生成界面"""
        st.header("PRFAQ 一键生成")
        
        # 添加按钮样式
        st.markdown("""
            <style>
            .stButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                color: #ffffff;
            }
            
            .stFormSubmitButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                width: auto;
                float: left;
            }
            
            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                border-color: #ffb84d;
                color: #ffb84d;
                background-color: rgba(255, 153, 0, 0.1);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 使用与PR生成器相同的表单布局
        with st.form("all_in_one_form"):
            # 创建两列布局
            col1, col2 = st.columns(2)
            
            # 左列
            with col1:
                customer = st.text_input("客户", value="产品经理")
                demand = st.text_input("需求", value="希望产品畅销的需求")
                company = st.text_input("公司", value="六页纸团队")
                feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿")
            
            # 右列
            with col2:
                scenario = st.text_input("场景", value="开发新产品的场景")
                pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点")
                product = st.text_input("产品", value="PRFAQ生成器")
                benefit = st.text_input("收益", value="打造以客户为中心的产品文案")
            
            # 生成按钮左对齐
            generate_all = st.form_submit_button("一键生成所有内容")
        
        if generate_all:
            add_log("user", "👉 点击一键生成所有内容")
            
            # 1. 生成中心句
            customer_needs = f"{customer}在{scenario}下，有{demand}，但他存在{pain}"
            solution = f"{company}开发了{product}，通过{feature}，帮助客户实现{benefit}"
            
            st.session_state.product_core_sentence = {
                'customer_needs': customer_needs,
                'solution': solution
            }
            
            # 显示中心句
            st.markdown("### 产品中心句")
            formatted_core_sentence = (
                f"**客户需求：**`{customer_needs}`\n\n"
                f"**解决方案：**`{solution}`"
            )
            st.markdown(formatted_core_sentence)
            self.all_content.append(("产品中心句", f"客户需求：{customer_needs}\n解决方案：{solution}"))
            add_log("info", "✅ 成功生成中心句")
            
            # 2. 生成PR
            st.markdown("### 虚拟新闻稿")
            pr_prompt = f"""你扮演一名专业的产品经理，你能够使用亚马逊prfaq的格式生成虚拟新闻稿。

客户需求：{customer_needs}
解决方案：{solution}

请生成一份虚拟新闻稿，包含标题、副标题、时间和媒体名称、摘要、客户需求和痛点、解决方案和产品价值、客户旅程，
提供一位行业大咖（使用真实名字���证言，并提供两个客户（使用虚拟名字，包含姓名、公司、职位）证言，最后号召用户购买。"""
            
            pr_content = self._generate_content("新闻稿", pr_prompt)
            if pr_content:
                self.all_content.append(("虚拟新闻稿", pr_content))
            
            # 3. 生成客户FAQ
            st.markdown("### 客户FAQ")
            try:
                customer_faqs = self.prompts.get("customer_faq", {})
                for question_id, faq_data in customer_faqs.items():
                    st.subheader(faq_data['title'])
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        f"客户需求：{customer_needs}\n解决方案：{solution}"
                    )
                    content = self._generate_content(f"客户FAQ-{faq_data['title']}", prompt)
                    if content:
                        self.all_content.append((f"客户FAQ-{faq_data['title']}", content))
            except Exception as e:
                add_log("error", f"❌ 生成客户FAQ时发生错误: {str(e)}")
            
            # 4. 生成内部FAQ
            st.markdown("### 内部FAQ")
            try:
                internal_faqs = self.prompts.get("internal_faq", {})
                for question_id, faq_data in internal_faqs.items():
                    st.subheader(faq_data['title'])
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        f"客户需求：{customer_needs}\n解决方案：{solution}"
                    )
                    content = self._generate_content(f"内部FAQ-{faq_data['title']}", prompt)
                    if content:
                        self.all_content.append((f"内部FAQ-{faq_data['title']}", content))
            except Exception as e:
                add_log("error", f"❌ 生成内部FAQ时发生错误: {str(e)}")
            
            # 5. 生成MLP开发计划
            st.markdown("### MLP开发计划")
            try:
                mlp_prompt = self.prompts.get("mlp", {}).get("prompt", "").replace(
                    "${core_sentence}", 
                    f"客户需求：{customer_needs}\n解决方案：{solution}"
                )
                content = self._generate_content("MLP开发计划", mlp_prompt)
                if content:
                    self.all_content.append(("MLP开发计划", content))
            except Exception as e:
                add_log("error", f"❌ 生成MLP开发计划时发生错误: {str(e)}")
            
            # 6. 在生成完所有内容后，显示字数统计
            if self.all_content:
                st.markdown("### 内容统计")
                
                # 计算每个部分的字数
                stats = []
                total_chars = 0
                
                for section_name, content in self.all_content:
                    chars = len(content)
                    total_chars += chars
                    stats.append({
                        "部分": section_name,
                        "字数": chars,
                    })
                
                # 添加总计行
                stats.append({
                    "部分": "总计",
                    "字数": total_chars,
                })
                
                # 使用pandas创建表格
                import pandas as pd
                df = pd.DataFrame(stats)
                
                # 显示表格
                st.dataframe(
                    df.style.format({
                        "字数": "{:,}",  # 添加千位分隔符
                    }),
                    use_container_width=True
                )
                
                # 准备下载内容
                content = ""
                for section_name, section_content in self.all_content:
                    content += f"\n{'='*50}\n"
                    content += f"{section_name}\n"
                    content += f"{'='*50}\n\n"
                    content += section_content
                    content += "\n\n"
                
                # 使用 streamlit 的下载按钮
                st.download_button(
                    label="导出完整文档",
                    data=content.encode('utf-8'),
                    file_name=f"PRFAQ_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime='text/plain'
                )
                
                # 保存到历史记录
                save_history({
                    'content': content,
                    'type': 'all_in_one',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                add_log("info", "✅ 已保存到历史记录")

    def _generate_content(self, section_name: str, prompt: str) -> Optional[str]:
        """生成内容并显示"""
        try:
            add_log("info", f"🚀 开始生成{section_name}...")
            response_placeholder = st.empty()
            full_response = ""
            
            for chunk in self.api_client.generate_content_stream(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response)
            
            add_log("info", f"✨ {section_name}生成完成")
            return full_response
            
        except Exception as e:
            error_msg = f"生成{section_name}时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}")
            return None

    def _export_to_file(self):
        """导出所有内容到文件"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"PRFAQ_{timestamp}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                for section_name, content in self.all_content:
                    f.write(f"\n{'='*50}\n")
                    f.write(f"{section_name}\n")
                    f.write(f"{'='*50}\n\n")
                    f.write(content)
                    f.write("\n\n")
            
            add_log("info", f"✅ 成功导出文件: {filename}")
            st.success(f"文件已导出: {filename}")
            
        except Exception as e:
            error_msg = f"导出文件时发生错误: {str(e)}"
            st.error(error_msg)
            add_log("error", f"❌ {error_msg}") 

================================================================================
文件: modules\api.py
================================================================================

import json
import requests
from typing import Dict, Any, Generator
import streamlit as st
from .utils import add_letters_record, save_history
from flask import Blueprint, jsonify, request
from datetime import datetime

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/api/internal-faq/<int:question_id>', methods=['GET'])
def get_internal_faq(question_id):
    """获取内部FAQ答案"""
    internal_faqs = {
        1: "产品独特性分析...",
        2: "产品售后服务流程...", 
        3: "产品定价策略...",
        4: "产品购买渠道...",
        5: "产品促销活动..."
    }
    return jsonify({"answer": internal_faqs.get(question_id, "未找到答案")})

@faq_bp.route('/api/external-faq/<int:question_id>', methods=['GET'])
def get_external_faq(question_id):
    """获取客户FAQ答案"""
    external_faqs = {
        1: "市场规模分析...",
        2: "三年盈利预测...",
        3: "合规风险分析...",
        4: "供应商依赖分析...",
        5: "竞品分析..."
    }
    return jsonify({"answer": external_faqs.get(question_id, "未找到答案")})

class APIClient:
    def __init__(self, config: Dict[str, Any]):
        """初始化API客户端"""
        self.config = config
        self.full_content = ""  # 初始化为实例变量
        
    def generate_content_stream(self, prompt: str, api_name: str = "claude") -> Generator[str, None, None]:
        """生成内容的流式接口"""
        try:
            # 每次生成前清空内容
            self.full_content = ""
            input_letters = len(prompt)
            
            # 准备API请求
            if api_name == "claude":
                headers = {
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01",
                    "x-api-key": self.config['api_keys'][api_name]
                }
                data = {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 4096,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True
                }
            else:
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.config['api_keys'][api_name]}"
                }
                data = {
                    "model": self.config["models"][api_name],
                    "messages": [
                        {"role": "system", "content": "你是一个专业的产品经理..."},
                        {"role": "user", "content": prompt}
                    ],
                    "stream": True
                }
            
            # 发送请求
            response = requests.post(
                self.config["api_urls"][api_name],
                headers=headers,
                json=data,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                chunk_count = 0
                
                for line in response.iter_lines():
                    if not line:
                        continue
                        
                    line = line.decode('utf-8')
                    
                    if not line.startswith('data: '):
                        continue
                    
                    # 如果是结束标记
                    if line == 'data: [DONE]':
                        break
                    
                    # 处理内容块
                    try:
                        json_str = line[6:]
                        json_data = json.loads(json_str)
                        
                        if api_name == "claude":
                            chunk = json_data.get('delta', {}).get('text', '') or json_data.get('content', '')
                        else:
                            chunk = json_data['choices'][0]['delta'].get('content', '')
                        
                        if chunk:
                            chunk_count += 1
                            self.full_content += chunk
                            yield chunk
                            
                    except json.JSONDecodeError as e:
                        continue
                
                # 在所有内容接收完成后
                if self.full_content:
                    try:
                        # 记录字符统计
                        success = add_letters_record(
                            input_letters=input_letters,
                            output_letters=len(self.full_content),
                            api_name=api_name,
                            operation=f"生成{st.session_state.current_section}内容"
                        )
                        
                        # 保存到历史记录
                        save_history({
                            'content': self.full_content,
                            'type': st.session_state.current_section,
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        # 在内容末尾添加字符统计
                        yield f"\n\n生成内容总字符数: {len(self.full_content)}"
                        
                    except Exception as e:
                        pass
                        
            else:
                raise Exception(f"API请求失败 (状态码: {response.status_code})")
                
        except Exception as e:
            # API切换逻辑
            next_api = None
            if api_name == "claude":
                next_api = "moonshot"
            elif api_name == "moonshot":
                next_api = "zhipu"
                
            if next_api:
                # 不清空 self.full_content，继续累积内容
                yield from self.generate_content_stream(prompt, next_api)
            else:
                # 记录已生成的内容(如果有)
                if self.full_content:
                    try:
                        success = add_letters_record(
                            input_letters=input_letters,
                            output_letters=len(self.full_content),
                            api_name=api_name,
                            operation=f"生成{st.session_state.current_section}内容(部分)"
                        )
                        # 在内容末尾添加字符统计
                        yield f"\n\n生成内容总字符数: {len(self.full_content)}"
                    except Exception as e:
                        pass
                yield ""

================================================================================
文件: modules\faq_generator.py
================================================================================

import streamlit as st
import json
from typing import Optional
from .api import APIClient
from .utils import load_prompts, add_log

class FAQGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()
        
    def generate_customer_faq(self):
        """生成客户FAQ内容"""
        st.header("客户 FAQ")
        
        # 检查全局产品中心句
        if 'product_core_sentence' not in st.session_state:
            st.warning("请先在PR生成模块生成产品中心句")
            return
            
        # 显示产品中心句
        core_sentence = st.session_state.product_core_sentence
        st.markdown("### 产品中心句")
        
        # 合并显示客户需求和解决方案，并添加高亮
        if isinstance(core_sentence, dict):
            formatted_core_sentence = (
                f"**客户需求：**`{core_sentence.get('customer_needs', '')}`\n\n"
                f"**解决方案：**`{core_sentence.get('solution', '')}`"
            )
            st.markdown(formatted_core_sentence)
            
            # 合并成完整的中心句用于提示词
            full_core_sentence = (
                f"客户需求：{core_sentence.get('customer_needs', '')}\n"
                f"解决方案：{core_sentence.get('solution', '')}"
            )
        else:
            st.error("产品中心句格式错误")
            return

        # 创建生成按钮
        if st.button("一键生成客户FAQ", key="generate_all_faq"):
            add_log("user", "👉 点击一键生成客户FAQ")
            
            # 获取customer_faq提示词
            try:
                prompts = self.prompts  # 使用初始化时加载的提示词
                customer_faqs = prompts.get("customer_faq", {})
                
                if not customer_faqs:
                    st.error("未找到客户FAQ提示词配置")
                    add_log("error", "❌ 未找到客户FAQ提示词配置")
                    return
                
                # 遍历生成每个FAQ的答案
                for question_id, faq_data in customer_faqs.items():
                    st.subheader(faq_data['title'])
                    add_log("info", f"🚀 开始生成问题: {faq_data['title']}")
                    
                    # 构建完整提示词，替换${core_sentence}占位符
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        full_core_sentence
                    )
                    
                    # 创建占位符用于流式输出
                    response_placeholder = st.empty()
                    
                    try:
                        # 初始化响应文本
                        full_response = ""
                        
                        # 流式生成内容
                        for chunk in self.api_client.generate_content_stream(prompt):
                            full_response += chunk
                            # 实时更新显示的内容
                            response_placeholder.markdown(full_response)
                        
                        add_log("info", f"✨ 问题 {faq_data['title']} 生成完成")
                        
                    except Exception as e:
                        error_msg = f"生成问题 {faq_data['title']} 时发生错误: {str(e)}"
                        st.error(error_msg)
                        add_log("error", f"❌ {error_msg}")
                    
                    # 添加分隔线
                    st.markdown("---")
                
                add_log("info", "✅ 所有FAQ生成完成")
                
            except Exception as e:
                error_msg = f"读取提示词配置时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}")

    def _generate_content(self, prompt: str) -> Optional[str]:
        """调用API生成内容"""
        try:
            return "".join(self.api_client.generate_content_stream(prompt))
        except Exception as e:
            st.error(f"生成内容时发生错误: {str(e)}")
            return None

================================================================================
文件: modules\faq_in.py
================================================================================

import streamlit as st
import json
from typing import Optional
from .api import APIClient
from .utils import load_prompts, add_log

class InternalFAQGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()

    def generate_internal_faq(self):
        """生成内部FAQ内容"""
        st.header("内部 FAQ")
        
        # 检查全局产品中心句
        if 'product_core_sentence' not in st.session_state:
            st.warning("请先在PR生成模块生成产品中心句")
            return
            
        # 显示产品中心句
        core_sentence = st.session_state.product_core_sentence
        st.markdown("### 产品中心句")
        
        # 合并显示客户需求和解决方案，并添加高亮
        if isinstance(core_sentence, dict):
            formatted_core_sentence = (
                f"**客户需求：**`{core_sentence.get('customer_needs', '')}`\n\n"
                f"**解决方案：**`{core_sentence.get('solution', '')}`"
            )
            st.markdown(formatted_core_sentence)
            
            # 合并成完整的中心句用于提示词
            full_core_sentence = (
                f"客户需求：{core_sentence.get('customer_needs', '')}\n"
                f"解决方案：{core_sentence.get('solution', '')}"
            )
        else:
            st.error("产品中心句格式错误")
            return

        # 创建生成按钮
        if st.button("一键生成内部FAQ", key="generate_all_internal_faq"):
            add_log("user", "👉 点击一键生成内部FAQ")
            
            # 获取internal_faq提示词
            try:
                prompts = self.prompts  # 使用初始化时加载的提示词
                internal_faqs = prompts.get("internal_faq", {})
                
                if not internal_faqs:
                    st.error("未找到内部FAQ提示词配置")
                    add_log("error", "❌ 未找到内部FAQ提示词配置")
                    return
                
                # 遍历生成每个FAQ的答案
                for question_id, faq_data in internal_faqs.items():
                    st.subheader(faq_data['title'])
                    add_log("info", f"🚀 开始生成问题: {faq_data['title']}")
                    
                    # 构建完整提示词，替换${core_sentence}占位符
                    prompt = faq_data['prompt'].replace(
                        "${core_sentence}", 
                        full_core_sentence
                    )
                    
                    # 创建占位符用于流式输出
                    response_placeholder = st.empty()
                    
                    try:
                        # 初始化响应文本
                        full_response = ""
                        
                        # 流式生成内容
                        for chunk in self.api_client.generate_content_stream(prompt):
                            full_response += chunk
                            # 实时更新显示的内容
                            response_placeholder.markdown(full_response)
                        
                        add_log("info", f"✨ 问题 {faq_data['title']} 生成完成")
                        
                    except Exception as e:
                        error_msg = f"生成问题 {faq_data['title']} 时发生错误: {str(e)}"
                        st.error(error_msg)
                        add_log("error", f"❌ {error_msg}")
                    
                    # 添加分隔线
                    st.markdown("---")
                
                add_log("info", "✅ 所有内部FAQ生成完成")
                
            except Exception as e:
                error_msg = f"读取提示词配置时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}") 

================================================================================
文件: modules\mlp_generator.py
================================================================================

import streamlit as st
import json
from typing import Optional
from .api import APIClient
from .utils import load_prompts, add_log

class MLPGenerator:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
        self.prompts = load_prompts()

    def generate_mlp(self):
        """生成MLP开发计划"""
        st.header("MLP 开发")
        
        # 检查全局产品中心句
        if 'product_core_sentence' not in st.session_state:
            st.warning("请先在PR生成模块生成产品中心句")
            return
            
        # 显示产品中心句
        core_sentence = st.session_state.product_core_sentence
        st.markdown("### 产品中心句")
        
        # 合并显示客户需求和解决方案，并添加高亮
        if isinstance(core_sentence, dict):
            formatted_core_sentence = (
                f"**客户需求：**`{core_sentence.get('customer_needs', '')}`\n\n"
                f"**解决方案：**`{core_sentence.get('solution', '')}`"
            )
            st.markdown(formatted_core_sentence)
            
            # 合并成完整的中心句用于提示词
            full_core_sentence = (
                f"客户需求：{core_sentence.get('customer_needs', '')}\n"
                f"解决方案：{core_sentence.get('solution', '')}"
            )
        else:
            st.error("产品中心句格式错误")
            return

        # 创建生成按钮
        if st.button("生成MLP开发计划", key="generate_mlp"):
            add_log("user", "👉 点击生成MLP开发计划")
            
            # 获取mlp提示词
            try:
                prompts = self.prompts
                mlp_prompt = prompts.get("mlp", {}).get("prompt")
                
                if not mlp_prompt:
                    st.error("未找到MLP提示词配置")
                    add_log("error", "❌ 未找到MLP提示词配置")
                    return
                
                # 构建完整提示词，替换${core_sentence}占位符
                prompt = mlp_prompt.replace(
                    "${core_sentence}", 
                    full_core_sentence
                )
                
                add_log("info", "🚀 开始生成MLP开发计划")
                
                # 创建占位符用于流式输出
                response_placeholder = st.empty()
                
                try:
                    # 初始化响应文本
                    full_response = ""
                    
                    # 流式生成内容
                    for chunk in self.api_client.generate_content_stream(prompt):
                        full_response += chunk
                        # 实时更新显示的内容
                        response_placeholder.markdown(full_response)
                    
                    add_log("info", "✨ MLP开发计划生成完成")
                    
                except Exception as e:
                    error_msg = f"生成MLP开发计划时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")
                
            except Exception as e:
                error_msg = f"读取提示词配置时发生错误: {str(e)}"
                st.error(error_msg)
                add_log("error", f"❌ {error_msg}") 

================================================================================
文件: modules\pr_generator.py
================================================================================

import streamlit as st
from typing import Optional, Dict
from .api import APIClient
from .utils import load_prompts, add_log  # 从utils导入add_log

class PRGenerator:
    def __init__(self, api_client: APIClient, all_in_one: bool = False):
        self.api_client = api_client
        self.all_in_one = all_in_one
        self.prompts = load_prompts()

    def render(self):
        """渲染PR生成界面"""
        st.header("PR 生成")
        
        # 自定义所有按钮样式
        st.markdown("""
            <style>
            /* 通用按钮样式 */
            .stButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                color: #ffffff;
            }
            
            /* 表单提交按钮（生成电梯谈话中心句）样式 */
            .stFormSubmitButton > button {
                border: 2px solid #ff9900;
                background-color: transparent;
                width: auto;
                float: left;
            }
            
            /* 鼠标悬停效果 */
            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                border-color: #ffb84d;
                color: #ffb84d;
                background-color: rgba(255, 153, 0, 0.1);
            }
            
            /* 点击效果 */
            .stButton > button:active,
            .stFormSubmitButton > button:active {
                border-color: #cc7a00;
                color: #cc7a00;
                background-color: rgba(255, 153, 0, 0.2);
            }
            </style>
        """, unsafe_allow_html=True)
        
        # 创建输入表单
        with st.form("pr_form"):
            # 创建两列布局
            col1, col2 = st.columns(2)
            
            # 左列
            with col1:
                customer = st.text_input("客户", value="产品经理")
                demand = st.text_input("需求", value="希望产品畅销的需求")
                company = st.text_input("公司", value="六页纸团队")
                feature = st.text_input("特色", value="使用六页纸模板和AIGC撰写虚拟新闻稿")
            
            # 右列
            with col2:
                scenario = st.text_input("场景", value="开发新产品的场景")
                pain = st.text_input("痛点", value="很难以客户为中心打造产品的痛点")
                product = st.text_input("产品", value="PRFAQ生成器")
                benefit = st.text_input("收益", value="打造以客户为中心的产品文案")
            
            # 生成按钮左对齐
            generate_core = st.form_submit_button("生成电梯谈话中心句")
            if generate_core:
                add_log("user", "👉 点击生成电梯谈话中心句")
        
        # 如果点击生成中心句按钮或已经存在中心句
        if generate_core or 'product_core_sentence' in st.session_state:
            if generate_core:
                # 初始化中心句
                customer_needs = f"{customer}在{scenario}下，有{demand}，但他存在{pain}"
                solution = f"{company}开发了{product}，通过{feature}，帮助客户实现{benefit}"
                
                st.session_state.product_core_sentence = {
                    'customer_needs': customer_needs,
                    'solution': solution
                }
                add_log("info", "✅ 成功生成中心句")
            
            # 显示可编辑的中心句（带颜色预览）
            st.markdown("### 产品中心句")
            
            # 获取当前的中心句
            current_needs = st.session_state.product_core_sentence['customer_needs']
            current_solution = st.session_state.product_core_sentence['solution']
            
            # 合并成一个完整的中心句
            combined_core_sentence = f"客户需求：{current_needs}\n解决方案：{current_solution}"
            
            # 创建单个可编辑的文本区域
            edited_text = st.text_area(
                "编辑中心句", 
                value=combined_core_sentence,
                height=100
            )
            
            # 解析编辑后的文本，分离客户需求和解决方案
            try:
                # 分割文本
                parts = edited_text.split('\n')
                edited_needs = parts[0].replace('客户需求：', '').strip()
                edited_solution = parts[1].replace('解决方案：', '').strip()
                
                # 更新session state中的中心句
                st.session_state.product_core_sentence = {
                    'customer_needs': edited_needs,
                    'solution': edited_solution
                }
            except Exception as e:
                st.error("中心句格式错误，请确保包含'客户需求：'和'解决方案：'两行")
                return

            # 生成新闻稿按钮
            if st.button("生成新闻稿", key="generate_pr"):
                add_log("user", "👉 点击生成新闻稿")
                
                # 构建完整提示词
                prompt = f"""你扮演一名专业的产品经理，你能够使用亚马逊prfaq的格式生成虚拟新闻稿。

客户需求：{edited_needs}
解决方案：{edited_solution}

请生成一份虚拟新闻稿，包含标题、副标题、时间和媒体名称、摘要、客户需求和痛点、解决方案和产品价值、客户旅程，
提供一位行业大咖（使用真实名字）证言，并提供两个客户（使用虚拟名字，包含姓名、公司、职位）证言，最后号召用户购买。"""

                # 显示提示词
                st.markdown("### 合成提示词")
                st.text_area(
                    label="",  # 移除标签
                    value=prompt,
                    height=200,  # 减小高度
                    disabled=True,  # 设置为不可编辑
                    key="prompt_display"
                )
                add_log("info", "✅ 成功生成提示词")
                
                # 生成新闻稿
                st.markdown("### 生成的虚拟新闻稿")
                
                # 创建一个空的占位符用于流式输出
                response_placeholder = st.empty()
                
                try:
                    add_log("info", "🚀 开始生成新闻稿...")
                    # 初始化响应文本
                    full_response = ""
                    
                    # 流式生成内容
                    for chunk in self.api_client.generate_content_stream(prompt):
                        full_response += chunk
                        # 实时更新显示的内容
                        response_placeholder.markdown(full_response)
                    
                    add_log("info", "✨ 新闻稿生成完成")
                    
                except Exception as e:
                    error_msg = f"生成内容时发生错误: {str(e)}"
                    st.error(error_msg)
                    add_log("error", f"❌ {error_msg}")

================================================================================
文件: modules\utils.py
================================================================================

import os
import json
from pathlib import Path
from datetime import datetime
import streamlit as st

def load_config():
    """Load configuration with environment variable override support"""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path, encoding='utf-8') as f:
        config = json.load(f)
    
    # Override API keys with environment variables if available
    for api_name in config["api_keys"]:
        env_key = f"{api_name.upper()}_API_KEY"
        if env_key in os.environ:
            config["api_keys"][api_name] = os.environ[env_key]
            
    return config

def load_templates():
    """Load UI templates"""
    template_path = Path(__file__).parent.parent / "templates.json"
    with open(template_path, encoding='utf-8') as f:
        return json.load(f)

def load_prompts():
    """Load prompts from prompt.json"""
    try:
        with open('prompt.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("未找到 prompt.json 配置文件")
        return {}
    except json.JSONDecodeError:
        st.error("prompt.json 格式错误")
        return {}
    except Exception as e:
        st.error(f"加载提示词配置时发生错误: {str(e)}")
        return {}

def load_history():
    """Load generation history"""
    history_path = Path(__file__).parent.parent / "prfaqs.json"
    if not history_path.exists():
        return []
    with open(history_path, encoding='utf-8') as f:
        return json.load(f)

def save_history(item):
    """Save generation result to history"""
    history_path = Path(__file__).parent.parent / "prfaqs.json"
    history = load_history()
    
    # Add timestamp to item
    item['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Add to history
    history.append(item)
    
    # Keep only latest 100 items
    if len(history) > 100:
        history = history[-100:]
    
    # Save to file
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def add_letters_record(input_letters: int, output_letters: int, api_name: str, operation: str) -> bool:
    """Add a new letters record"""
    try:
        # 计算费用 (每1000字符)
        input_cost_usd = (input_letters / 1000) * 0.001  # $0.001 per 1K chars
        output_cost_usd = (output_letters / 1000) * 0.002  # $0.002 per 1K chars
        total_cost_usd = input_cost_usd + output_cost_usd
        
        input_cost_rmb = input_cost_usd * 7.2  # 汇率转换
        output_cost_rmb = output_cost_usd * 7.2
        total_cost_rmb = total_cost_usd * 7.2
        
        # 读取当前记录
        letters_path = Path(__file__).parent.parent / "letters.json"
        if not letters_path.exists():
            letters_data = {
                "total": {
                    "input_letters": 0,
                    "output_letters": 0,
                    "cost_usd": 0.0,
                    "cost_rmb": 0.0
                },
                "records": []
            }
        else:
            try:
                with open(letters_path, encoding='utf-8') as f:
                    letters_data = json.load(f)
            except Exception as e:
                return False
        
        # 更新总计
        letters_data["total"]["input_letters"] += input_letters
        letters_data["total"]["output_letters"] += output_letters
        letters_data["total"]["cost_usd"] = float(letters_data["total"]["cost_usd"]) + total_cost_usd
        letters_data["total"]["cost_rmb"] = float(letters_data["total"]["cost_rmb"]) + total_cost_rmb
        
        # 添加新记录
        record = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "api_name": api_name,
            "operation": operation,
            "input_letters": input_letters,
            "output_letters": output_letters,
            "input_cost_usd": input_cost_usd,
            "output_cost_usd": output_cost_usd,
            "total_cost_usd": total_cost_usd,
            "input_cost_rmb": input_cost_rmb,
            "output_cost_rmb": output_cost_rmb,
            "total_cost_rmb": total_cost_rmb
        }
        letters_data["records"].append(record)
        
        # 保存更新后的记录
        try:
            with open(letters_path, 'w', encoding='utf-8') as f:
                json.dump(letters_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            return False
            
    except Exception as e:
        return False

def load_letters():
    """Load letters statistics"""
    letters_path = Path(__file__).parent.parent / "letters.json"
    if not letters_path.exists():
        initial_letters = {
            "total": {
                "input_letters": 0,
                "output_letters": 0,
                "cost_usd": 0.0,
                "cost_rmb": 0.0
            },
            "records": []
        }
        with open(letters_path, 'w', encoding='utf-8') as f:
            json.dump(initial_letters, f, ensure_ascii=False, indent=2)
        return initial_letters
    
    try:
        with open(letters_path, encoding='utf-8') as f:
            letters_data = json.load(f)
            return letters_data
    except Exception as e:
        return {
            "total": {
                "input_letters": 0,
                "output_letters": 0,
                "cost_usd": 0.0,
                "cost_rmb": 0.0
            },
            "records": []
        }

def add_log(level: str, message: str):
    """Add a log entry to session state"""
    if 'logs' not in st.session_state:
        st.session_state.logs = []
    
    log_entry = {
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'level': level,
        'message': message
    }
    
    st.session_state.logs.append(log_entry)
    
    # Keep only latest 100 logs
    if len(st.session_state.logs) > 100:
        st.session_state.logs = st.session_state.logs[-100:]

================================================================================
文件: modules\__init__.py
================================================================================

# 空文件，用于标识这是一个Python包 

================================================================================
文件: tests\test_api.py
================================================================================

import unittest
from unittest.mock import Mock, patch
from modules.api import APIClient

class TestAPIClient(unittest.TestCase):
    def setUp(self):
        self.mock_config = {
            'API_KEY': 'test_key',
            'API_URL': 'http://test.api'
        }
        self.api_client = APIClient(self.mock_config)

    @patch('modules.api.requests.post')
    def test_generate_content_stream(self, mock_post):
        """测试内容生成流功能"""
        # 模拟API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.iter_lines.return_value = [
            b'data: {"choices":[{"delta":{"content":"test"}}]}',
            b'data: {"choices":[{"delta":{"content":" content"}}]}'
        ]
        mock_post.return_value = mock_response

        # 测试生成内容
        prompt = "Test prompt"
        content = list(self.api_client.generate_content_stream(prompt))
        
        # 验证结果
        self.assertEqual(len(content), 2)
        self.assertEqual(content[0], "test")
        self.assertEqual(content[1], " content")

        # 验��API调用
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], 'http://test.api')
        self.assertIn('Authorization', call_args[1]['headers']) 

================================================================================
文件: tests\test_faq_generator.py
================================================================================

import unittest
from unittest.mock import Mock, patch
import streamlit as st
from modules.faq_generator import FAQGenerator

class TestFAQGenerator(unittest.TestCase):
    def setUp(self):
        self.mock_api_client = Mock()
        self.faq_generator = FAQGenerator(self.mock_api_client)

    @patch('streamlit.button')
    def test_generate_customer_faq(self, mock_button):
        """测试客户FAQ生成功能"""
        # 模拟按钮点击
        mock_button.return_value = True
        
        # 模拟API响应
        self.mock_api_client.generate_content_stream.return_value = ["测试回答"]
        
        # 执行测试
        with patch('streamlit.markdown') as mock_markdown:
            self.faq_generator.generate_customer_faq()
            
            # 验证API调用
            self.mock_api_client.generate_content_stream.assert_called()
            
            # 验证结果显示
            mock_markdown.assert_called_with("测试回答") 

================================================================================
文件: tests\test_mmm.py
================================================================================

import unittest
from pathlib import Path
import tempfile
import shutil
import os
from mmm import collect_python_files, read_file_content, write_to_prfaq

class TestMMM(unittest.TestCase):
    def setUp(self):
        # 创建临时测试目录
        self.test_dir = Path(tempfile.mkdtemp())
        
        # 创建测试文件
        self.test_files = {
            'test1.py': 'print("Hello")',
            'test2.py': 'def test(): pass',
            'mmm.py': 'should not collect this',
            'test3.txt': 'not a python file'
        }
        
        # 创建子目录和文件
        self.sub_dir = self.test_dir / 'subdir'
        self.sub_dir.mkdir()
        self.test_files['subdir/test4.py'] = 'class Test: pass'
        
        # 写入测试文件
        for file_path, content in self.test_files.items():
            full_path = self.test_dir / file_path
            full_path.parent.mkdir(exist_ok=True)
            full_path.write_text(content, encoding='utf-8')

    def tearDown(self):
        # 清理临时测试目录
        shutil.rmtree(self.test_dir)

    def test_collect_python_files(self):
        """测试Python文件收集功能"""
        python_files = collect_python_files(self.test_dir)
        
        # 验证收集到的文件数量（应该是3个，不包括mmm.py）
        self.assertEqual(len(python_files), 3)
        
        # 验证文件名
        file_names = [f.name for f in python_files]
        self.assertIn('test1.py', file_names)
        self.assertIn('test2.py', file_names)
        self.assertIn('test4.py', file_names)
        self.assertNotIn('mmm.py', file_names)
        self.assertNotIn('test3.txt', file_names)

    def test_read_file_content(self):
        """测试文件读取功能"""
        test_file = self.test_dir / 'test1.py'
        content = read_file_content(test_file)
        self.assertEqual(content, 'print("Hello")')

    def test_write_to_mmm(self):
        """测试文件合并写入功能"""
        output_file = self.test_dir / 'mmm.txt'
        python_files = collect_python_files(self.test_dir)
        write_to_prfaq(python_files, str(output_file))
        
        # 验证输出文件存在
        self.assertTrue(output_file.exists())
        
        # 验证输出文件内容
        content = output_file.read_text(encoding='utf-8')
        self.assertIn('Python代码收集结果', content)
        self.assertIn('test1.py', content)
        self.assertIn('test2.py', content)
        self.assertIn('test4.py', content)
        self.assertIn('print("Hello")', content) 
