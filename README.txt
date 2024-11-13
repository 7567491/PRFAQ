# PRFAQ Pro

## 程序功能
这是一个基于 Streamlit 的 PRFAQ (Press Release/FAQ) 生成工具，主要用于生成以下内容：
1. 虚拟新闻稿
2. 客户 FAQ
3. 内部 FAQ
4. MLP 开发文档
5. 复盘六步法报告
6. PRFAQ 一键生成

## 目录结构

### 主要目录
- /                 # 根目录
  - app.py         # 主程序入口
  - .streamlit/    # Streamlit 配置目录
  - assets/        # 静态资源目录
  - config/        # 配置文件目录
  - db/            # 数据库相关
  - modules/       # 核心功能模块
  - user/          # 用户管理相关

### 文件说明和调用关系

1. 程序入口
- app.py: 主程序入口，负责初始化界面和路由管理
  - 调用 modules/ 下的各个生成器
  - 调用 user/ 下的用户管理功能
  - 调用 db/ 下的数据库管理功能

2. 数据库管理 (db/)
- db_admin.py: 数据库管理界面
- init_db.py: 数据库初始化
- backup_db.py: 数据库备份
- db_restore.py: 数据库恢复
- db_upgrade.py: 数据库升级
- db_table.py: 表结构管理
- read_db.py: 数据库读取
- migrate_data.py: 数据迁移

3. 用户管理 (user/)
- user_process.py: 用户认证和管理
- admin.py: 管理员面板
- bill.py: 账单管理
- chat.py: AI 聊天测试
- logger.py: 日志管理
- scheduler.py: 定时任务
- user.py: 用户界面

4. 核心功能模块 (modules/)
- pr_generator.py: 新闻稿生成器
- faq_generator.py: FAQ 生成器
- faq_in.py: 内部 FAQ 生成器
- mlp_generator.py: MLP 开发文档生成器
- aar_generator.py: 复盘报告生成器
- all_in_one_generator.py: 一键生成器
- api.py: API 客户端
- utils.py: 工具函数

5. 配置文件
- .streamlit/config.toml: Streamlit 配置
- config/letters.json: 模板配置
- config/prfaqs.json: PRFAQ 配置

## 数据流向
1. 用户通过 app.py 进入系统
2. user_process.py 处理用户认证
3. 认证成功后可以访问各个功能模块
4. 各模块通过 api.py 调用 AI 接口
5. 使用记录存储在数据库中
6. 账单和日志实时更新

## 数据库结构
主数据库文件：db/users.db
包含以下表：
1. users: 用户信息
2. bills: 账单记录

## 详细数据库表结构

### users 表
用户信息表，存储用户账户和使用统计
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| username | TEXT | 用户名，唯一 |
| password | TEXT | 密码哈希值 |
| email | TEXT | 电子邮件 |
| role | TEXT | 用户角色(admin/user) |
| created_at | TIMESTAMP | 创建时间 |
| last_login | TIMESTAMP | 最后登录时间 |
| status | INTEGER | 账户状态(0:禁用,1:正常) |
| tokens | INTEGER | 剩余令牌数 |

### bills 表
账单记录表，记录用户消费
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 用户ID，外键 |
| amount | DECIMAL | 消费金额 |
| tokens | INTEGER | 消费令牌数 |
| type | TEXT | 消费类型 |
| created_at | TIMESTAMP | 创建时间 |
| status | INTEGER | 支付状态(0:未支付,1:已支付) |

### logs 表
系统日志表，记录用户操作
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 用户ID，外键 |
| action | TEXT | 操作类型 |
| details | TEXT | 操作详情 |
| ip | TEXT | IP地址 |
| created_at | TIMESTAMP | 创建时间 |

### prfaqs 表
PRFAQ记录表，存储生成的内容
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 用户ID，外键 |
| title | TEXT | 标题 |
| content | TEXT | 内容 |
| type | TEXT | 类型(pr/faq/mlp/aar) |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| status | INTEGER | 状态(0:草稿,1:完成) |

### api_keys 表
API密钥管理表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| user_id | INTEGER | 用户ID，外键 |
| api_key | TEXT | API密钥 |
| provider | TEXT | 提供商(openai/azure) |
| created_at | TIMESTAMP | 创建时间 |
| expired_at | TIMESTAMP | 过期时间 |
| status | INTEGER | 状态(0:禁用,1:正常) |

### settings 表
系统设置表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| key | TEXT | 设置键名 |
| value | TEXT | 设置值 |
| type | TEXT | 值类型 |
| description | TEXT | 描述 |
| updated_at | TIMESTAMP | 更新时间 |

### templates 表
模板管理表
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| name | TEXT | 模板名称 |
| content | TEXT | 模板内容 |
| type | TEXT | 模板类型 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |
| status | INTEGER | 状态(0:禁用,1:正常) |

## 部署说明
1. 确保安装所有依赖
2. 初始化数据库：python db/init_db.py
3. 运行程序：streamlit run app.py

## 注意事项
1. 首次运行需要初始化数据库
2. 建议定期备份数据库
3. 管理员账户默认用户名和密码都是 admin 
