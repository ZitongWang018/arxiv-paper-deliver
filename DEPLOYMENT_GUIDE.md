# ArxivDigest 部署实操手册（Render + Vercel）

本手册目标：让你拿到两个公网地址并完成真实用户可交互验收。

---

## 0. 你现在已有的仓库能力

- 根目录 `render.yaml`：Render 后端和 Postgres 基础编排
- 前端支持 `VITE_API_BASE_URL` 环境变量
- 健康检查接口：`/healthz`
- 变量模板：
  - `backend/.env.render.example`
  - `frontend/.env.vercel.example`

---

## 1. 部署后端（Render）

### 1.1 导入仓库
1. 打开 Render 控制台，点击 **New +**。
2. 选择 **Blueprint**（推荐）或 **Web Service**。
3. 连接你的 Git 仓库 `ArxivDigest`。
4. 确认使用根目录 `render.yaml`，开始创建资源。

### 1.2 等待资源就绪
- Render 会创建：
  - 一个 Web Service（后端）
  - 一个 Postgres 数据库
- 先等待状态变成 **Live**。

### 1.3 补齐后端环境变量（最关键）
进入 Render 的后端服务页面：
1. 打开 **Environment**。
2. 检查/填写以下变量：

| 变量名 | 示例值 | 说明 |
|---|---|---|
| `ENV` | `production` | 生产模式 |
| `DEBUG` | `false` | 关闭调试 |
| `SCHEDULER_ENABLED` | `true` | 开启每日调度 |
| `BASE_URL` | `https://your-backend-service.onrender.com` | 后端公网根地址 |
| `FRONTEND_URL` | `https://your-frontend-app.vercel.app` | 前端公网地址 |
| `CORS_ORIGINS` | `https://your-frontend-app.vercel.app` | 跨域白名单 |
| `JWT_SECRET_KEY` | 长随机字符串 | JWT 密钥 |
| `SMTP_HOST` | `smtp.qq.com` 等 | SMTP 主机 |
| `SMTP_PORT` | `465` | SMTP 端口 |
| `SMTP_USER` | 你的邮箱 | 发件邮箱 |
| `SMTP_PASSWORD` | SMTP 授权码 | 邮件密码/授权码 |
| `SMTP_USE_TLS` | `true` | TLS 开关 |
| `SMTP_FROM_NAME` | `ArxivDigest` | 发件人名称 |

> `DATABASE_URL` 在 `render.yaml` 中通常自动从 Postgres 注入，不需要手填。

### 1.4 保存并重新部署
1. 点击保存后，进入 **Manual Deploy**。
2. 点击 **Deploy latest commit**。
3. 等待日志出现启动完成信息。

### 1.5 后端验收
浏览器访问：
- `https://your-backend-service.onrender.com/healthz`（应返回 `ok`）
- `https://your-backend-service.onrender.com/docs`（应看到 Swagger UI）

---

## 2. 部署前端（Vercel）

### 2.1 导入仓库
1. 打开 Vercel 控制台，点击 **Add New... -> Project**。
2. 选择仓库 `ArxivDigest`。
3. 配置：
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`

### 2.2 设置环境变量
在 Vercel 项目配置的 **Environment Variables** 增加：
- `VITE_API_BASE_URL = https://your-backend-service.onrender.com/api`

### 2.3 部署并获取前端地址
1. 点击 **Deploy**。
2. 部署成功后得到地址：
   - `https://your-frontend-app.vercel.app`

---

## 3. 回填 Render 跨域（非常重要）

拿到前端地址后，回到 Render 后端服务，更新这两个变量并重新部署：
- `FRONTEND_URL=https://your-frontend-app.vercel.app`
- `CORS_ORIGINS=https://your-frontend-app.vercel.app`

如果你有多个前端域名（比如预发布域名），可逗号分隔：
- `CORS_ORIGINS=https://a.vercel.app,https://b.vercel.app`

---

## 4. 端到端验收（按用户流程）

1. 打开前端地址，先注册一个新账号并登录。
2. 新建订阅（研究兴趣 + LLM + API Key + 分类）。
3. 在仪表盘点击“手动触发推送”。
4. 检查邮箱是否收到推荐邮件。
5. 点击邮件中的收藏链接，确认跳转页面可交互。
6. 在研究库确认收藏、搜索、标签、笔记都可用。

---

## 5. 常见问题排查

### 5.1 前端报跨域错误（CORS）
- 现象：浏览器控制台出现 CORS 拒绝。
- 处理：确认 Render 的 `CORS_ORIGINS` 与 `FRONTEND_URL` 是当前 Vercel 域名，并重新部署后端。

### 5.2 前端 401 或登录后立刻掉线
- 检查 `VITE_API_BASE_URL` 是否正确（必须指向后端 `/api`）。
- 检查后端 `JWT_SECRET_KEY` 是否意外变更（变更会导致旧 token 失效）。

### 5.3 邮件不发送
- 检查 `SMTP_*` 是否完整，尤其授权码是否正确。
- 在 Render Logs 搜索 `send_email` 或异常栈。

### 5.4 Render 免费/低配实例冷启动慢
- 首次请求慢是正常现象。
- 可升级实例以减少冷启动影响。

---

## 6. 你最终会得到的两个地址

- 前端（用户入口）：`https://your-frontend-app.vercel.app`
- 后端（API）：`https://your-backend-service.onrender.com`

其中前端通过 `VITE_API_BASE_URL` 调用后端的 `/api/*` 接口。
