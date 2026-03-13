#!/usr/bin/env python3
"""
国产大模型清单生成工具

从 litellm 的模型库中筛选国产模型，生成标准化的模型清单 JSON
"""

import json
import requests
import re
from datetime import datetime
from typing import Dict, List, Any, Set, Optional
from pathlib import Path


# 国产模型提供商匹配规则
DOMESTIC_PATTERNS = [
    # 阿里云
    r"^(qwen|qwen-plus|qwen-turbo|qwen-max|qwen-long|qwen-vl|qwen-audio)",
    r"^(deepseek|deepseek-chat|deepseek-coder)",
    r"^(dashscope)",
    r"^(wenxin|ernie|ernie-bot|ernie-speed|ernie-lite|ernie-tiny)",
    r"^baidu/",
    # 百度文心一言
    r"^(yi|yi-lightning|yi-large|yi-medium|yi-spark|yi-vl)",
    r"^01\.ai/",
    # 零一万物
    r"^(hunyuan|hunyuan-lite|hunyuan-standard|hunyuan-pro|hunyuan-role)",
    r"^tencent/",
    # 腾讯混元
    r"^(chatglm|glm-4|glm-4-air|glm-4-flash|glm-4-plus|glm-4v|glm-3-turbo)",
    r"^zhipu/",
    # 智谱AI
    r"^(moonshot|moonshot-v1)",
    r"^kimi/",
    # 月之暗面
    r"^(minimax|minimax-abab|minimax-abab5|minimax-abab6)",
    r"^baichuan/",
    r"^internlm/",
    r"^spark|xinghua/",
    # 讯飞星火
    r"^(sensenova)",
    r"^(stepfun)",
    r"^claude-3-.*-cn",
    r"^doubao/",
    r"^volcengine/",
    # 火山引擎豆包
    r"^(hailuo|glm-4c)",
    r"^novita/",
]

# 编译正则表达式
DOMESTIC_REGEX = re.compile("|".join(f"({pattern})" for pattern in DOMESTIC_PATTERNS), re.IGNORECASE)


def is_domestic_model(model_name: str) -> bool:
    """
    判断是否为国产模型

    Args:
        model_name: 模型名称

    Returns:
        是否为国产模型
    """
    return bool(DOMESTIC_REGEX.search(model_name))


def download_litellm_data() -> Dict[str, Any]:
    """
    从 litellm 下载模型数据

    Returns:
        模型数据字典
    """
    url = "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json"
    print(f"正在从 {url} 下载数据...")

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    data = response.json()
    print(f"下载完成，共 {len(data)} 个模型")
    return data


def normalize_model_spec(model_name: str, raw_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    将原始模型规格转换为标准格式

    Args:
        model_name: 模型名称
        raw_spec: 原始规格数据

    Returns:
        标准化后的规格数据
    """
    # 提取 max_tokens 信息
    max_tokens = raw_spec.get("max_tokens")
    max_input_tokens = raw_spec.get("max_input_tokens", max_tokens)
    max_output_tokens = raw_spec.get("max_output_tokens", max_tokens)

    # 确定提供商
    litellm_provider = raw_spec.get("litellm_provider", "unknown")

    # 推断模式
    mode = raw_spec.get("mode", "chat")
    if not mode:
        # 根据模型名称推断
        if "embed" in model_name.lower():
            mode = "embedding"
        elif "vision" in model_name.lower() or "vl" in model_name.lower():
            mode = "chat"  # 支持视觉的聊天模型
        elif "audio" in model_name.lower() or "speech" in model_name.lower() or "tts" in model_name.lower():
            mode = "audio_speech"
        elif "transcri" in model_name.lower() or "whisper" in model_name.lower():
            mode = "audio_transcription"

    # 构建标准化规格
    spec = {
        "mode": mode,
        "litellm_provider": litellm_provider,
        "max_tokens": max_tokens,
        "max_input_tokens": max_input_tokens if max_input_tokens else max_tokens,
        "max_output_tokens": max_output_tokens if max_output_tokens else max_tokens,
        "input_cost_per_token": float(raw_spec.get("input_cost_per_token", 0.0) or 0),
        "output_cost_per_token": float(raw_spec.get("output_cost_per_token", 0.0) or 0),
        "supports_function_calling": bool(raw_spec.get("supports_function_calling", False)),
        "supports_parallel_function_calling": bool(raw_spec.get("supports_parallel_function_calling", False)),
        "supports_vision": bool(raw_spec.get("supports_vision", False)),
        "supports_system_messages": bool(raw_spec.get("supports_system_messages", True)),
        "supports_prompt_caching": bool(raw_spec.get("supports_prompt_caching", False)),
        "supports_response_schema": bool(raw_spec.get("supports_response_schema", False)),
        "supports_audio_input": bool(raw_spec.get("supports_audio_input", False)),
        "supports_audio_output": bool(raw_spec.get("supports_audio_output", False)),
        "supports_reasoning": bool(raw_spec.get("supports_reasoning", False)),
        "supports_web_search": bool(raw_spec.get("supports_web_search", False)),
    }

    # 添加可选字段
    if raw_spec.get("deprecation_date"):
        spec["deprecation_date"] = raw_spec["deprecation_date"]

    if raw_spec.get("supported_regions"):
        spec["supported_regions"] = raw_spec["supported_regions"]

    # 添加高级成本字段
    if raw_spec.get("input_cost_per_audio_token"):
        spec["input_cost_per_audio_token"] = float(raw_spec["input_cost_per_audio_token"])

    if raw_spec.get("output_cost_per_reasoning_token"):
        spec["output_cost_per_reasoning_token"] = float(raw_spec["output_cost_per_reasoning_token"])

    # 添加服务成本字段
    additional_costs = [
        "code_interpreter_cost_per_session",
        "computer_use_input_cost_per_1k_tokens",
        "computer_use_output_cost_per_1k_tokens",
        "file_search_cost_per_1k_calls",
        "file_search_cost_per_gb_per_day",
        "vector_store_cost_per_gb_per_day",
    ]

    for cost_field in additional_costs:
        if raw_spec.get(cost_field) is not None:
            spec[cost_field] = float(raw_spec[cost_field])

    # 添加搜索上下文成本
    if raw_spec.get("search_context_cost_per_query"):
        spec["search_context_cost_per_query"] = raw_spec["search_context_cost_per_query"]

    return spec


def filter_and_normalize(data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    过滤国产模型并标准化格式

    Args:
        data: 原始模型数据

    Returns:
        标准化后的国产模型数据
    """
    print("正在筛选国产模型...")

    domestic_models = {}
    domestic_count = 0
    provider_stats: Dict[str, int] = {}

    for model_name, model_spec in data.items():
        if is_domestic_model(model_name):
            # 标准化规格
            normalized_spec = normalize_model_spec(model_name, model_spec)
            domestic_models[model_name] = normalized_spec
            domestic_count += 1

            # 统计提供商
            provider = normalized_spec.get("litellm_provider", "unknown")
            provider_stats[provider] = provider_stats.get(provider, 0) + 1

    print(f"筛选完成，共找到 {domestic_count} 个国产模型")

    # 打印提供商统计
    print("\n按提供商统计:")
    for provider, count in sorted(provider_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {provider}: {count} 个模型")

    return domestic_models


def save_output(data: Dict[str, Dict[str, Any]], output_path: str) -> None:
    """
    保存输出文件

    Args:
        data: 模型数据
        output_path: 输出文件路径
    """
    # 添加元信息
    output_data = {
        "metadata": {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "total_models": len(data),
            "source": "https://github.com/BerriAI/litellm",
            "description": "国产大模型清单 - 从 litellm 筛选并标准化"
        },
        "models": data
    }

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n输出文件已保存至: {output_path}")
    print(f"文件大小: {output_file.stat().st_size / 1024:.2f} KB")


def main():
    """主函数"""
    print("=" * 60)
    print("国产大模型清单生成工具")
    print("=" * 60)

    # 下载数据
    litellm_data = download_litellm_data()

    # 过滤和标准化
    domestic_models = filter_and_normalize(litellm_data)

    # 保存输出
    output_path = "output/domestic_llm_models.json"
    save_output(domestic_models, output_path)

    print("\n✅ 处理完成!")


if __name__ == "__main__":
    main()
