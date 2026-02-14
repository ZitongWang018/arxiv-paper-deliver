# ArxivDigest 部署实操手册（Render 免费版 + Vercel）

本手册目标：让你用免费套餐拿到两个公网地址并完成真实用户可交互验收。

> 重要：Render 免费 Web Service **不能**连接 SMTP 常用端口（25/465/587），
> 所以本项目在免费方案下使用 **Resend 邮件 API（HTTPS 443）** 发信。

---

## 0. 你现在已有的仓库能力

- 根目录 `render.yaml`：参数参考模板（免费版可手动按模板填写）
- 前端支持 `VITE_API_BASE_URL` 环境变量
- 健康检查接口：`/healthz`
- 变量模板：
  - `backend/.env.render.example`
  - `frontend/.env.vercel.example`

---

## 1. 部署后端（Render Free）

### 1.1 创建 Postgres（免费）
1. 打开 Render 控制台，点击 **New +**。
2. 选择 **Postgres**（不是 Blueprint）。
3. 计划选择 **Free**，区域尽量和后端服务同区域。
4. 创建后记录外部连接串（External Database URL）。

### 1.2 创建 Web Service（免费）
1. 点击 **New + -> Web Service**。
2. 连接你的 Git 仓库 `ArxivDigest`。
3. 关键配置：
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Python Version**: `3.11.11`（不要用 3.14）
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**
4. 创建并等待服务状态变为 **Live**。

> 仓库内已提供 `backend/runtime.txt`，用于固定 Python 版本；
> 如果 Render 控制台可直接选 Python 版本，优先以控制台为准并选择 `3.11.x`。

### 1.3 补齐后端环境变量（最关键）
进入 Render 的后端服务页面：
1. 打开 **Environment**。
2. 检查/填写以下变量：

| 变量名 | 示例值 | 说明 |
|---|---|---|
| `ENV` | `production` | 生产模式 |
| `DEBUG` | `false` | 关闭调试 |
| `SCHEDULER_ENABLED` | `false` | 免费版建议关闭内置调度 |
| `CRON_SECRET_KEY` | 长随机字符串 | 外部 Cron 调用密钥 |
| `BASE_URL` | `https://your-backend-service.onrender.com` | 后端公网根地址 |
| `FRONTEND_URL` | `https://your-frontend-app.vercel.app` | 前端公网地址 |
| `CORS_ORIGINS` | `https://your-frontend-app.vercel.app` | 跨域白名单 |
| `JWT_SECRET_KEY` | 长随机字符串 | JWT 密钥 |
| `EMAIL_PROVIDER` | `resend` | 邮件发送提供商 |
| `RESEND_API_KEY` | `re_xxx` | Resend API Key |
| `RESEND_FROM_EMAIL` | `onboarding@resend.dev` | 发件地址（测试可用） |
| `SMTP_FROM_NAME` | `ArxivDigest` | 发件人名称 |
| `DATABASE_URL` | `postgresql+asyncpg://...` | 使用你创建的 Free Postgres 连接串 |

> 免费版手动创建服务时，需要你手动填写 `DATABASE_URL`。

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

## 5. 配置外部定时任务（免费版核心步骤）

Render 免费实例会休眠，进程内 APScheduler 不可靠。  
请使用第三方 Cron（例如 `cron-job.org`）定时调用后端接口。

### 5.1 注册并创建任务
1. 打开 `https://cron-job.org` 注册账号并登录。
2. 点击 **Create cronjob**。
3. URL 填写：

`https://your-backend-service.onrender.com/api/system/cron/run?secret=你的CRON_SECRET_KEY`

4. 执行频率建议：
   - 每天 1 次（例如 UTC 00:30，对应北京时间 08:30）
5. 保存任务并启用。

### 5.2 手工验证 Cron 接口
在浏览器直接访问（或 Postman）：

`POST https://your-backend-service.onrender.com/api/system/cron/run?secret=你的CRON_SECRET_KEY`

返回示例：
- `{"message":"cron run completed","triggered_subscriptions":1}`

这表示当天自动订阅已被触发。

---

## 6. 常见问题排查

### 6.1 前端报跨域错误（CORS）
- 现象：浏览器控制台出现 CORS 拒绝。
- 处理：确认 Render 的 `CORS_ORIGINS` 与 `FRONTEND_URL` 是当前 Vercel 域名，并重新部署后端。

### 6.2 前端 401 或登录后立刻掉线
- 检查 `VITE_API_BASE_URL` 是否正确（必须指向后端 `/api`）。
- 检查后端 `JWT_SECRET_KEY` 是否意外变更（变更会导致旧 token 失效）。

### 6.3 邮件不发送
- 检查 `EMAIL_PROVIDER=resend` 和 `RESEND_API_KEY`。
- `RESEND_FROM_EMAIL` 必须符合 Resend 规则（测试默认可先用 `onboarding@resend.dev`）。
- 在 Render Logs 搜索 `Resend` 或异常栈。

### 6.4 Render 免费实例冷启动慢
- 首次请求慢是正常现象。
- 可升级实例以减少冷启动影响。

### 6.5 安装依赖时报 `pydantic-core` / Rust / read-only file system
- 根因通常是 Render 使用了过新的 Python（例如 3.14），导致 `pydantic-core` 没有对应 wheel，回退到 Rust 构建后失败。
- 处理：
  1. 在 Render 服务设置里将 Python 固定为 `3.11.x`；
  2. 确认仓库包含 `backend/runtime.txt`（`python-3.11.11`）；
  3. 点击 **Clear build cache & deploy** 重新部署。

---

## 7. 你最终会得到的两个地址

- 前端（用户入口）：`https://your-frontend-app.vercel.app`
- 后端（API）：`https://your-backend-service.onrender.com`

其中前端通过 `VITE_API_BASE_URL` 调用后端的 `/api/*` 接口。
