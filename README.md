# ArxivDigest - 智能论文推荐系统

基于 AI 的 arXiv 论文个性化推荐与推送系统。通过大模型（Qwen / DeepSeek）分析论文与您研究兴趣的相关性，每日自动推送最相关的论文到邮箱，并支持收藏整理。

## 功能特性

- **智能推荐**：基于 LLM 语义分析（非关键词匹配），精准匹配研究兴趣
- **双引擎支持**：支持 Qwen（通义千问）和 DeepSeek 两种大模型
- **邮件推送**：包含标题、作者、摘要中文翻译、相关性分析说明
- **定时推送**：支持每日自动抓取并推送
- **研究库**：通过邮件一键收藏论文，在 Web 端管理研究笔记和标签
- **优雅界面**：现代化 Vue 3 前端，支持深色/浅色主题

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + SQLite + APScheduler |
| 前端 | Vue 3 + Vite + TypeScript + Tailwind CSS |
| LLM | Qwen (DashScope) / DeepSeek (OpenAI 兼容) |
| 邮件 | SMTP (QQ邮箱 / Gmail / Outlook) |

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+

### 2. 后端

```bash
cd backend
pip install -r requirements.txt

# 复制并编辑环境变量
cp ../.env.example .env
# 编辑 .env 填入 SMTP 配置和 JWT 密钥

# 启动
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev        # 开发模式
# 或
npm run build      # 生产构建（输出到 dist/）
```

前端支持通过环境变量指定后端地址：

```bash
# 生产环境（示例）
cp .env.production.example .env.production
# 编辑 VITE_API_BASE_URL=https://your-backend.onrender.com/api
```

### 4. 访问

- 前端: http://localhost:5173
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 公网部署（推荐）

推荐方案：**Render（后端 + Postgres）+ Vercel（前端）**

详细逐步教程见：`DEPLOYMENT_GUIDE.md`

### 1) 部署后端到 Render

1. 将仓库连接到 Render，选择使用根目录 `render.yaml`。
2. 在 Render 控制台补齐环境变量：
   - `BASE_URL=https://<your-backend>.onrender.com`
   - `FRONTEND_URL=https://<your-frontend>.vercel.app`
   - `CORS_ORIGINS=https://<your-frontend>.vercel.app`
   - `SMTP_*` 全部变量
3. 首次部署成功后，检查：
   - `https://<your-backend>.onrender.com/healthz`
   - `https://<your-backend>.onrender.com/docs`

### 2) 部署前端到 Vercel

1. 将同一仓库导入 Vercel，Root Directory 选择 `frontend`。
2. 设置环境变量：
   - `VITE_API_BASE_URL=https://<your-backend>.onrender.com/api`
3. 触发部署并访问 `https://<your-frontend>.vercel.app`。

### 3) 上线验收

1. 前端注册并登录。
2. 创建订阅并手动触发推送。
3. 检查邮件送达并点击收藏链接。
4. 在研究库验证标签、搜索、笔记编辑。

## 使用流程

1. **注册/登录** — 使用邮箱注册账号
2. **创建订阅** — 填写研究兴趣、选择 LLM 和 arXiv 分类
3. **获取推送** — 手动触发或设置每日自动推送
4. **邮件收藏** — 在推送邮件中点击「收藏到研究库」
5. **管理研究库** — 在 Web 端添加笔记、标签，整理研究文献

## 项目结构

```
ArxivDigest/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── database.py          # 数据库
│   │   ├── models.py            # ORM 模型
│   │   ├── schemas.py           # API 数据模型
│   │   ├── auth.py              # JWT 认证
│   │   ├── routers/             # API 路由
│   │   ├── services/            # 业务逻辑
│   │   └── templates/           # 邮件模板
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/               # 页面组件
│   │   ├── components/          # 通用组件
│   │   ├── stores/              # Pinia 状态
│   │   ├── api/                 # API 封装
│   │   └── router/              # 路由
│   └── package.json
└── .env.example
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 注册 |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 当前用户 |
| GET/POST | /api/subscriptions | 订阅列表/创建 |
| PUT/DELETE | /api/subscriptions/:id | 更新/删除订阅 |
| POST | /api/subscriptions/:id/trigger | 手动触发推送 |
| GET/POST | /api/stars | 收藏列表/添加收藏 |
| PUT/DELETE | /api/stars/:id | 更新/取消收藏 |

## License

MIT
