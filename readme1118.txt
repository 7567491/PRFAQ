# PRFAQ Pro

## 1. 程序功能
这是一个基于 Streamlit 的 PRFAQ (Press Release/FAQ) 生成工具，主要用于以下内容生成：

### 1.1 核心功能
1. 逆向工作法（虚拟新闻稿）
   - 通过编写未来新闻稿的形式明确项目目标
   - 帮助团队从结果反推过程
   - 生成完整的项目愿景说明

2. 复盘六步法报告
   - 基于军事领域的"事后复盘"（AAR）
   - 包含：目标设定、过程回顾、结果对比、差距分析、经验总结、文档形成
   - 帮助团队持续改进

3. 领导力测评
   - 专业的领导力评估工具
   - 生成详细的评估报告
   - 提供发展建议

### 1.2 辅助功能
1. 客户 FAQ 生成
2. 内部 FAQ 生成
3. MLP 开发文档生成
4. PRFAQ 一键生成
5. AI 聊天测试（管理员功能）
6. AWS 集成（管理员功能）

## 2. 系统架构

### 2.1 目录结构
- /                 # 根目录
  - app.py         # 主程序入口
  - .streamlit/    # Streamlit 配置目录
  - assets/        # 静态资源目录（图片等）
  - config/        # 配置文件目录
  - db/            # 数据库相关
  - modules/       # 核心功能模块
  - user/          # 用户管理相关
  - test/          # 测试相关
  - aws/           # AWS集成相关
  - bill/          # 账单管理相关

### 2.2 核心模块说明

1. 数据库管理 (db/)
   - db_admin.py: 数据库管理界面
   - db_init.py: 数据库初始化
   - db_restore.py: 数据库备份和恢复
   - db_upgrade.py: 数据库升级
   - migrate_data.py: 数据迁移工具
   - read_db.py: 数据库读取工具

2. 用户管理 (user/)
   - user_base.py: 用户基础类
   - user_process.py: 用户认证和处理
   - admin.py: 管理员面板
   - user_history.py: 用户历史记录
   - logger.py: 日志管理

3. 核心生成器 (modules/)
   - pr_generator.py: 新闻稿生成器
   - faq_generator.py: FAQ生成器
   - faq_in.py: 内部FAQ生成器
   - mlp_generator.py: MLP文档生成器
   - aar_generator.py: 复盘报告生成器
   - all_in_one_generator.py: 一键生成器
   - api.py: API客户端
   - utils.py: 工具函数
   - notifier.py: 通知管理

4. 账单管理 (bill/)
   - bill.py: 积分和账单管理

## 3. 数据流向
1. 用户认证流程：
   - 用户登录/注册 -> 认证验证 -> 角色分配 -> 功能访问
   - 每日首次登录奖励5000积分
   - 新用户���册赠送20000积分

2. 功能使用流程：
   - 用户请求 -> 积分检查 -> API调用 -> 内容生成 -> 历史记录
   - 所有操作记录日志
   - 积分变动记录账单

3. 数据存储流程：
   - 生成内容保存历史记录
   - 用户操作记录日志
   - 积分变动记录账单
   - 定期数据库备份

## 4. 特色功能

### 4.1 企业微信通知
- 用户登录通知（包含IP和系统信息）
- 用户操作通知
- 系统状态通知

### 4.2 积分系统
- 新用户注册：20000积分
- 每日登录奖励：5000积分
- 使用功能消耗积分
- 积分明细查看

### 4.3 数据分析
- 用户行为分析
- 系统使用统计
- 积分消耗分析

### 4.4 AWS集成
- S3数据备份
- 其他AWS服务集成

## 5. 部署说明

### 5.1 环境要求
- Python 3.8+
- SQLite3
- 必要的Python包：
  - streamlit
  - pandas
  - plotly
  - requests
  - python-docx (用于测评报告)
  - boto3 (AWS集成)

### 5.2 安装步骤
1. 克隆代码库
2. 安装依赖：pip install -r requirements.txt
3. 初始化数据库：python db/db_init.py
4. 运行程序：streamlit run app.py

### 5.3 配置说明
1. 配置文件位置：config/
   - config.json: 主配置文件
   - templates.json: 模板配置
   - letters.json: 文案配置

2. 环境变量
   - AWS凭证配置
   - API密钥配置

## 6. 注意事项
1. 定期备份数据库
2. 监控日志记录
3. 检查积分变动
4. 注意API调用限制
5. 保护用户数据安全

## 7. 默认账户
1. 管理员账户：
   - 用户名：Jack
   - 密码：Amazon123

2. 测试用户：
   - 用户名：Rose
   - 密码：Amazon123

## 8. 联系方式
如有问题请联系管理员或查看系统日志 