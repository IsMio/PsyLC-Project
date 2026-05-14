from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

import yaml


EDITABLE_CONFIG_WHITELIST = {
    'dashscope': ['assist_api_base_url', 'api_base_url', 'model_name', 'model_max_tokens', 'embeddings_model_name'],
    'model': ['temperature', 'top_p', 'enable_search'],
    'app': [
        'memory_key',
        'system_prompt',
        'chroma_collection_name',
        'chroma_persist_dir',
        'prompt_template_path',
        'max_history_messages',
        'max_history_chars',
        'max_single_message_chars',
        'output_filter_enabled',
        'output_filter_review_enabled',
    ],
    'db': ['path'],
    'redis': ['redis_host', 'redis_port', 'redis_db'],
    'jwt': ['algorithm', 'access_token_expire_minutes'],
}


class ConfigService:
    def __init__(self, config_path: str):
        self.config_path = config_path

    def get_config(self) -> Dict[str, Any]:
        with open(self.config_path, 'r', encoding='utf-8') as handle:
            return yaml.safe_load(handle) or {}

    def update_config(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_config()
        merged = self._deep_merge(current, patch)
        with open(self.config_path, 'w', encoding='utf-8') as handle:
            yaml.safe_dump(merged, handle, allow_unicode=True, sort_keys=False)
        return merged

    def get_editable_config(self) -> Dict[str, Any]:
        current = self.get_config()
        editable: Dict[str, Any] = {}
        for section, allowed_keys in EDITABLE_CONFIG_WHITELIST.items():
            if section not in current:
                continue
            editable[section] = {
                key: current[section][key]
                for key in allowed_keys
                if isinstance(current[section], dict) and key in current[section]
            }
        return editable

    def update_editable_config(self, patch: Dict[str, Any]) -> Dict[str, Any]:
        current = self.get_config()
        sanitized_patch: Dict[str, Any] = {}
        for section, allowed_keys in EDITABLE_CONFIG_WHITELIST.items():
            section_patch = patch.get(section)
            if not isinstance(section_patch, dict):
                continue
            sanitized_values = {
                key: value
                for key, value in section_patch.items()
                if key in allowed_keys
            }
            if sanitized_values:
                sanitized_patch[section] = sanitized_values

        merged = self._deep_merge(current, sanitized_patch)
        with open(self.config_path, 'w', encoding='utf-8') as handle:
            yaml.safe_dump(merged, handle, allow_unicode=True, sort_keys=False)
        return self.get_editable_config()

    def _deep_merge(self, source: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
        result = deepcopy(source)
        for key, value in patch.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
