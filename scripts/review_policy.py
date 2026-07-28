from __future__ import annotations

import re
from typing import Any


NEGATION_RE = re.compile(r"不需|不需要|無須|不必|不得|不可|不要|不因")
EXPLICIT_LABEL_RE = re.compile(
    r"(?:"
    r"(?:缺少|缺乏|未列|未標|沒有).{0,16}大概念.{0,10}"
    r"(?:顯性|明列|標記|標示|標題|專頁|頁面|字樣)"
    r"|大概念.{0,8}(?:顯性標記|顯性標示|標題|專頁|頁面|字樣)"
    r"|(?:補上|補寫|新增|增加|標明|標示|明列).{0,16}大概念"
    r")"
)


def _action_texts(review: dict[str, Any]):
    scalar_paths = ("decision_reason", "suggested_path")
    for key in scalar_paths:
        value = review.get(key)
        if isinstance(value, str):
            yield key, value

    list_fields = {
        "content_scores": ("judgment", "minimal_fix"),
        "critical_gates": ("evidence",),
        "slide_findings": ("title", "detail", "action"),
    }
    for field, keys in list_fields.items():
        items = review.get(field, [])
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for key in keys:
                value = item.get(key)
                if isinstance(value, str):
                    yield f"{field}[{index}].{key}", value

    for index, value in enumerate(review.get("priority_actions", [])):
        if isinstance(value, str):
            yield f"priority_actions[{index}]", value


def validate_review_policy(review: dict[str, Any]) -> list[str]:
    """Return violations of deterministic project review policies."""
    errors: list[str] = []
    for path, text in _action_texts(review):
        if NEGATION_RE.search(text):
            continue
        if EXPLICIT_LABEL_RE.search(text):
            errors.append(
                f"{path}: 不得把未明列「大概念」標題／專頁當成缺失或修正要求：{text}"
            )
    return errors
