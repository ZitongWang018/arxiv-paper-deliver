# Plan: 关键词预筛选 + 进度持久化 + 增强进度 UI

## 问题分析

1. **效率低**：200 篇论文全部送 LLM 分析（batch_size=5 → 40 次 API 调用），极慢
2. **进度丢失**：pushStatus 存在组件本地 ref 中，页面切换组件卸载 → 状态丢失、轮询停止
3. 需要增强进度可视化（显示预筛选结果等）

## 改动方案

### Step 1: 关键词预筛选（backend）

**流程变更：** `抓取 → 【关键词提取 + 粗筛】→ LLM 精分析 → 发送`

- `llm_service.py` 新增 `extract_keywords()`:
  - 一次 LLM 调用，从用户的 research_interest 中提取 3-5 个英文关键词
  - 返回 `list[str]`
- `arxiv_service.py` 新增 `filter_by_keywords()`:
  - 对每篇论文检查 title + abstract 是否包含任一关键词（大小写不敏感）
  - 纯字符串匹配，无 LLM 调用，毫秒级完成
- `scheduler.py` pipeline 调整：
  - fetch → extract_keywords → filter_by_keywords → analyze_papers
  - 如果粗筛后数量 < 5，则跳过粗筛直接全量分析（防止关键词太严漏掉论文）

**预期效果**：200 篇论文 → 粗筛后 30-60 篇 → LLM 只需分析 30-60 篇，速度提升 3-6 倍

### Step 2: push_tracker 增强（backend）

- 新增 PushStep: `KEYWORD_FILTERING = "keyword_filtering"`
- 新增字段: `papers_filtered` (粗筛后剩余数)、`papers_analyzed` (LLM 已分析数)
- `to_dict()` 返回新字段

### Step 3: 进度回调 + scheduler 更新（backend）

- `llm_service.analyze_papers()` 增加 `on_batch_done` 回调参数
  - 每处理完一个 batch 调用回调，报告已分析篇数
- `scheduler.py` 传递回调，实时更新 task 的 progress 和 message

### Step 4: 进度状态持久化（frontend）

- `stores/subscription.ts`:
  - 新增 `pushTasks: ref<Record<number, { taskId: string, status: PushStatus }>>()` (按 subscription ID 存储)
  - 新增 `startPolling(subId, taskId)` 方法 → 在 store 层轮询
  - 新增 `stopPolling(subId)` 方法
  - 轮询结果写入 store，不依赖组件生命周期
- `SubscriptionCard.vue`:
  - 从 store 读取 pushStatus（不再用本地 ref）
  - onMounted 时检查 store 中是否有进行中的任务，自动恢复显示
  - handleTrigger 只调 store 方法

### Step 5: 前端 PushStatus 类型更新

- `api/index.ts` PushStatus 增加 `papers_filtered`、`papers_analyzed` 字段

### Step 6: 增强 SubscriptionCard 进度 UI

- 显示步骤链：抓取 → 粗筛 → 分析 → 发送（当前步骤高亮）
- 分析阶段显示 "分析中 12/35 篇..."
- 粗筛后显示 "关键词筛选：200 → 42 篇"
- 完成后展示统计面板

## 文件改动

| 文件 | 改动类型 |
|------|----------|
| `backend/app/services/llm_service.py` | 新增 extract_keywords() + on_batch_done 回调 |
| `backend/app/services/arxiv_service.py` | 新增 filter_by_keywords() |
| `backend/app/services/push_tracker.py` | 新增步骤和字段 |
| `backend/app/services/scheduler.py` | 集成预筛选 + 进度回调 |
| `frontend/src/api/index.ts` | PushStatus 类型更新 |
| `frontend/src/stores/subscription.ts` | 推送状态持久化到 store |
| `frontend/src/components/SubscriptionCard.vue` | 增强进度 UI |
