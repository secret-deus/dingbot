"""数据脱敏 - IP、主机名、Pod名、Token等敏感信息遮蔽与还原"""

from __future__ import annotations

import re
import uuid
from typing import Optional


class DataMasker:
    def __init__(self, session_id: Optional[str] = None) -> None:
        self.session_id = session_id or uuid.uuid4().hex[:8]
        self._mask_map: dict[str, str] = {}
        self._reverse_map: dict[str, str] = {}
        self._counter = 0

    def _next_tag(self, prefix: str) -> str:
        self._counter += 1
        return f"[{prefix}_{self.counter:03d}]"

    @property
    def counter(self) -> int:
        return self._counter

    def _mask(self, text: str, pattern: re.Pattern, prefix: str) -> str:
        def _replace(m: re.Match) -> str:
            original = m.group(0)
            if original in self._mask_map:
                return self._mask_map[original]
            tag = self._next_tag(prefix)
            self._mask_map[original] = tag
            self._reverse_map[tag] = original
            return tag
        return pattern.sub(_replace, text)

    def _unmask(self, text: str) -> str:
        for tag, original in self._reverse_map.items():
            text = text.replace(tag, original)
        return text

    # --- 正则模式 ---
    _IPV4 = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    _HOSTNAME = re.compile(r'\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+\b', re.IGNORECASE)
    _POD_NAME = re.compile(r'\b[a-z][a-z0-9-]{0,62}-[a-z0-9]{4,10}-[a-z0-9]{4,6}\b')
    _TOKEN = re.compile(r'\b(?:eyJ[A-Za-z0-9_-]{20,}|ghp_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,})\b')
    _K8S_SECRET = re.compile(r'\b(?:password|secret|token|api[_-]?key)\s*[:=]\s*["\']?\S{6,}["\']?', re.IGNORECASE)

    _TOOL_WHITELIST = {
        "k8s-prometheus-app-metrics",
        "k8s-update-knowledge-graph-metrics",
        "k8s-resource-analysis-report",
    }

    def mask(self, text: str) -> str:
        if not text:
            return text
        text = self._mask(text, self._TOKEN, "TOKEN")
        text = self._mask(text, self._K8S_SECRET, "SECRET")
        text = self._mask(text, self._IPV4, "IP")
        text = self._mask(text, self._POD_NAME, "POD")
        text = self._mask(text, self._HOSTNAME, "HOST")
        return text

    def mask_tool_result(self, tool_name: str, result: str) -> str:
        if tool_name in self._TOOL_WHITELIST:
            return result
        return self.mask(result)

    def unmask(self, text: str) -> str:
        if not text:
            return text
        return self._unmask(text)

    def clear(self) -> None:
        self._mask_map.clear()
        self._reverse_map.clear()
        self._counter = 0
