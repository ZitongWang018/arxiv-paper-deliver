"""Unified LLM service for Qwen and DeepSeek.

Both providers expose an OpenAI-compatible chat completions API, so we use
the `openai` Python SDK with a custom base_url.
"""

import json
import logging
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

# ── Provider configuration ────────────────────────────

PROVIDER_CONFIG: dict[str, dict] = {
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
}

SYSTEM_PROMPT = """你是一个学术论文推荐助手。你需要分析论文与用户研究兴趣的相关性。

对于每一篇论文，你需要返回以下信息：
1. relevance_score: 1-10的相关性评分（10为最相关）
2. abstract_zh: 摘要的中文翻译（准确、学术化）
3. relevance_reason: 一段精炼的说明（2-3句话），解释为什么这篇论文与用户的研究问题相关或不相关

请严格以JSON数组格式返回结果，不要添加任何其他文字。"""


def _build_user_prompt(research_interest: str, papers: list[dict]) -> str:
    """Build the user prompt with research interest and paper metadata."""
    lines = [f"用户的研究兴趣：\n{research_interest}\n"]
    lines.append("请分析以下论文与上述研究兴趣的相关性：\n")

    for i, p in enumerate(papers, 1):
        lines.append(f"论文 {i}:")
        lines.append(f"  标题: {p['title']}")
        lines.append(f"  作者: {p['authors']}")
        lines.append(f"  摘要: {p['abstract']}")
        lines.append("")

    lines.append("请以JSON数组格式返回，每个元素对应一篇论文：")
    lines.append('[{"relevance_score": <int>, "abstract_zh": "<str>", "relevance_reason": "<str>"}, ...]')
    return "\n".join(lines)


def _get_client(provider: str, api_key: str) -> AsyncOpenAI:
    """Create an AsyncOpenAI client for the specified provider."""
    config = PROVIDER_CONFIG.get(provider)
    if not config:
        raise ValueError(f"Unsupported LLM provider: {provider}. Must be 'qwen' or 'deepseek'.")
    return AsyncOpenAI(api_key=api_key, base_url=config["base_url"])


def _parse_response(content: str, expected_count: int) -> list[dict]:
    """Parse the JSON array from the LLM response, with fallback handling."""
    # Strip markdown code fences if present
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json) and last line (```)
        lines = [l for l in lines[1:] if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract JSON array from the response
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1:
            try:
                data = json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                logger.error("Failed to parse LLM response as JSON: %s", content[:500])
                return [
                    {"relevance_score": 0, "abstract_zh": "", "relevance_reason": "LLM响应解析失败"}
                    for _ in range(expected_count)
                ]
        else:
            logger.error("No JSON array found in LLM response: %s", content[:500])
            return [
                {"relevance_score": 0, "abstract_zh": "", "relevance_reason": "LLM响应解析失败"}
                for _ in range(expected_count)
            ]

    if not isinstance(data, list):
        data = [data]

    # Pad or truncate to expected count
    while len(data) < expected_count:
        data.append({"relevance_score": 0, "abstract_zh": "", "relevance_reason": "未返回结果"})

    results: list[dict] = []
    for item in data[:expected_count]:
        results.append({
            "relevance_score": int(item.get("relevance_score", 0)),
            "abstract_zh": str(item.get("abstract_zh", "")),
            "relevance_reason": str(item.get("relevance_reason", "")),
        })
    return results


# ── Public API ────────────────────────────────────────

async def analyze_papers(
    papers: list[dict],
    research_interest: str,
    provider: str,
    api_key: str,
    model: Optional[str] = None,
    batch_size: int = 5,
) -> list[dict]:
    """Analyze a list of papers against the user's research interest.

    Returns papers augmented with: relevance_score, abstract_zh, relevance_reason.
    Results are sorted by relevance_score descending.
    """
    config = PROVIDER_CONFIG.get(provider, {})
    model_name = model or config.get("default_model", "")
    client = _get_client(provider, api_key)

    all_results: list[dict] = []

    for i in range(0, len(papers), batch_size):
        batch = papers[i:i + batch_size]
        user_prompt = _build_user_prompt(research_interest, batch)

        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1024 * batch_size,
            )
            content = response.choices[0].message.content or "[]"
            analysis = _parse_response(content, len(batch))
        except Exception as exc:
            logger.error("LLM API call failed: %s", exc)
            analysis = [
                {"relevance_score": 0, "abstract_zh": "", "relevance_reason": f"API调用失败: {exc}"}
                for _ in batch
            ]

        for paper, result in zip(batch, analysis):
            merged = {**paper, **result}
            all_results.append(merged)

    # Sort by relevance score descending
    all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    return all_results
