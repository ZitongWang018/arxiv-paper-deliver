# Plan: 修复 XML 解析 + 加速筛选 + 增强进度可视化

## 问题

1. `lxml` 未安装 → `BeautifulSoup(xml)` 解析失败
2. LLM 分析 200 篇论文需要 ~40 次 API 调用（batch_size=5），太慢
3. 前端进度展示粒度太粗，只有 4 个大步骤，分析阶段没有实时进度

## 修改计划

### Step 1: 修复 XML 解析器 (backend)
- `requirements.txt` 添加 `lxml`

### Step 2: 加速 LLM 筛选 (backend)
- **增大 batch_size**：5 → 10（减少 API 调用次数一半）
- **并发批处理**：使用 `asyncio.gather` 并发处理多个 batch（限制并发数为 3，避免触发 rate limit）
- **进度回调**：给 `analyze_papers()` 添加 `on_progress` 回调，每处理完一批报告进度

### Step 3: 增强 push_tracker (backend)
- 新增字段：`papers_analyzed`（已分析数）、`current_step_detail`（子步骤详情）、`elapsed_seconds`
- 新增 `PushStep.ANALYZING` 阶段支持更细粒度的 progress（20-80 之间按 batch 比例插值）
- `to_dict()` 返回新字段

### Step 4: 更新 scheduler (backend)
- 传递 progress 回调给 `llm_service.analyze_papers()`
- 在回调中更新 task 的分析进度

### Step 5: 增强前端进度可视化 (frontend)
- **步骤指示器**：顶部横向 stepper 显示 4 个阶段（抓取 → 分析 → 发送 → 完成），当前步骤高亮 + 动画
- **分析进度条**：分析阶段显示 "已分析 45/200 篇"，带百分比
- **耗时显示**：实时显示已用时间
- **统计面板**：完成后展示汇总卡片（抓取数/相关数/发送数），带图标和颜色
- 轮询间隔从 2s 减为 1.5s，分析阶段更频繁

## 文件改动列表

| 文件 | 改动 |
|------|------|
| `backend/requirements.txt` | +lxml |
| `backend/app/services/llm_service.py` | 并发 batch + on_progress 回调 |
| `backend/app/services/push_tracker.py` | 新字段 + 细粒度进度 |
| `backend/app/services/scheduler.py` | 传递回调 |
| `frontend/src/api/index.ts` | PushStatus 类型更新 |
| `frontend/src/components/SubscriptionCard.vue` | 增强进度 UI |
