"""
配置加载与校验工具。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml


class ConfigError(Exception):
    """配置文件异常。"""


_CONFIG_CACHE: Optional[Dict[str, Any]] = None
_CONFIG_PATH: Optional[str] = None


def load_config(path: str = "config.yaml", force_reload: bool = False) -> Dict[str, Any]:
    """加载并校验配置。"""
    global _CONFIG_CACHE, _CONFIG_PATH

    normalized_path = os.path.abspath(path)
    if (
        not force_reload
        and _CONFIG_CACHE is not None
        and _CONFIG_PATH == normalized_path
    ):
        return _CONFIG_CACHE

    if not os.path.exists(path):
        raise ConfigError(f"配置文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    errors = _validate_config(data)
    if errors:
        bullet = "\n  - "
        raise ConfigError(f"配置校验失败:{bullet}{bullet.join(errors)}")

    _CONFIG_CACHE = data
    _CONFIG_PATH = normalized_path
    return data


def _validate_config(config: Dict[str, Any]) -> list[str]:
    errors: list[str] = []

    models = config.get("models")
    if not isinstance(models, dict):
        errors.append("缺少 models 配置块")
        return errors

    _validate_embedding(models.get("embedding"), errors)
    _validate_llm(models.get("llm"), errors)

    vector_store = config.get("vector_store")
    if not isinstance(vector_store, dict):
        errors.append("缺少 vector_store 配置块")
    else:
        if not vector_store.get("persist_dir"):
            errors.append("vector_store.persist_dir 不能为空")

    data_section = config.get("data")
    if not isinstance(data_section, dict):
        errors.append("缺少 data 配置块")
    else:
        if not data_section.get("documents_dir"):
            errors.append("data.documents_dir 不能为空")
        if not data_section.get("generated_dir"):
            errors.append("data.generated_dir 不能为空")

    document_cfg = config.get("document")
    if not isinstance(document_cfg, dict):
        errors.append("缺少 document 配置块")
    else:
        chunk_size = document_cfg.get("chunk_size")
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            errors.append("document.chunk_size 必须为正整数")
        chunk_overlap = document_cfg.get("chunk_overlap")
        if not isinstance(chunk_overlap, int) or chunk_overlap < 0:
            errors.append("document.chunk_overlap 必须为非负整数")

    rag_cfg = config.get("rag")
    if isinstance(rag_cfg, dict):
        top_k = rag_cfg.get("top_k")
        if not isinstance(top_k, int) or top_k <= 0:
            errors.append("rag.top_k 必须为正整数")
    else:
        errors.append("缺少 rag 配置块")

    return errors


def _validate_embedding(embedding: Optional[Dict[str, Any]], errors: list[str]) -> None:
    if not isinstance(embedding, dict):
        errors.append("缺少 models.embedding 配置")
        return

    provider = embedding.get("provider")
    if provider not in {"local", "openai"}:
        errors.append("models.embedding.provider 必须为 local 或 openai")

    if not embedding.get("model_name"):
        errors.append("models.embedding.model_name 不能为空")

    if provider == "openai" and not (
        embedding.get("api_key") or os.getenv("OPENAI_API_KEY")
    ):
        errors.append("使用 OpenAI embedding 需要在配置或环境变量中提供 OPENAI_API_KEY")


def _validate_llm(llm: Optional[Dict[str, Any]], errors: list[str]) -> None:
    if not isinstance(llm, dict):
        errors.append("缺少 models.llm 配置")
        return

    provider = llm.get("provider")
    if provider not in {"tongyi", "openai"}:
        errors.append("models.llm.provider 必须为 tongyi 或 openai")

    if provider == "tongyi":
        if not (llm.get("api_key") or os.getenv("DASHSCOPE_API_KEY")):
            errors.append("使用通义千问需在配置或环境变量中提供 DASHSCOPE_API_KEY")
    elif provider == "openai":
        if not (llm.get("api_key") or os.getenv("OPENAI_API_KEY")):
            errors.append("使用 OpenAI LLM 需在配置或环境变量中提供 OPENAI_API_KEY")

