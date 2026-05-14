from __future__ import annotations

import random
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Sequence, Tuple


class PromptOptimizationError(ValueError):
    pass


def sample_records(records: Sequence[Dict[str, Any]], sample_size: int, seed: int) -> List[Dict[str, Any]]:
    if not isinstance(records, list):
        raise PromptOptimizationError("数据集必须是列表")
    if sample_size <= 0:
        return []
    if len(records) <= sample_size:
        return list(records)
    rng = random.Random(seed)
    return rng.sample(list(records), sample_size)


def rebuild_messages(record: Dict[str, Any], system_prompt: str, model: Any) -> List[Dict[str, Any]]:
    rebuilt: List[Dict[str, Any]] = []
    conversation: List[Dict[str, Any]] = []

    for message in record.get("messages") or []:
        role = message.get("role")
        content = message.get("content", "")
        if role == "system":
            rebuilt.append({"role": "system", "content": content})
            conversation.append({"role": "system", "content": content})
        elif role == "user":
            user_msg = {"role": "user", "content": content}
            rebuilt.append(user_msg)
            conversation.append(user_msg)
        elif role == "assistant":
            reply = model.generate_reply(system_prompt, conversation)
            assistant_msg = {"role": "assistant", "content": reply}
            rebuilt.append(assistant_msg)
            conversation.append(assistant_msg)

    return rebuilt


def optimize_single_record(
    record: Dict[str, Any],
    model: Any,
    base_system_prompt: str,
    max_rounds: int,
    progress_callback=None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    current_prompt = base_system_prompt
    rounds: List[Dict[str, Any]] = []
    final_messages: List[Dict[str, Any]] = []
    stop_reason = "max_rounds"

    if progress_callback:
        progress_callback(
            {
                "type": "record_started",
                "record_id": record.get("id"),
                "normalizedTag": record.get("normalizedTag"),
            }
        )

    for round_index in range(1, max_rounds + 1):
        if progress_callback:
            progress_callback(
                {
                    "type": "round_started",
                    "record_id": record.get("id"),
                    "normalizedTag": record.get("normalizedTag"),
                    "round": round_index,
                    "prompt": current_prompt,
                }
            )
        final_messages = rebuild_messages(record, current_prompt, model)
        evaluation = model.evaluate_prompt(current_prompt, record, final_messages, round_index, max_rounds)
        rounds.append(
            {
                "round": round_index,
                "prompt": current_prompt,
                "generated_messages": deepcopy(final_messages),
                "feedback": evaluation.get("feedback", ""),
                "satisfied": bool(evaluation.get("satisfied")),
                "should_update_prompt": bool(evaluation.get("should_update_prompt")),
                "optimized_prompt": evaluation.get("optimized_prompt", current_prompt),
            }
        )

        if progress_callback:
            progress_callback(
                {
                    "type": "round_completed",
                    "record_id": record.get("id"),
                    "normalizedTag": record.get("normalizedTag"),
                    "round": round_index,
                    "prompt": current_prompt,
                    "generated_messages": deepcopy(final_messages),
                    "feedback": evaluation.get("feedback", ""),
                    "satisfied": bool(evaluation.get("satisfied")),
                    "should_update_prompt": bool(evaluation.get("should_update_prompt")),
                    "optimized_prompt": evaluation.get("optimized_prompt", current_prompt),
                }
            )

        if evaluation.get("satisfied"):
            stop_reason = "satisfied"
            break

        if evaluation.get("should_update_prompt") and evaluation.get("optimized_prompt"):
            current_prompt = evaluation["optimized_prompt"]
            continue

        stop_reason = "no_update"
        break

    optimized_record = {
        "id": record.get("id"),
        "normalizedTag": record.get("normalizedTag"),
        "messages": deepcopy(final_messages),
    }
    debug_row = {
        "id": record.get("id"),
        "normalizedTag": record.get("normalizedTag"),
        "rounds": rounds,
        "final_prompt": current_prompt,
        "stop_reason": stop_reason,
    }
    return optimized_record, debug_row


def optimize_dataset_records(
    records: Sequence[Dict[str, Any]],
    model: Any,
    base_system_prompt: str,
    sample_size: int = 10,
    seed: int = 42,
    max_rounds: int = 3,
    progress_callback=None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    sampled = sample_records(records, sample_size=sample_size, seed=seed)
    optimized: List[Dict[str, Any]] = []
    debug_rows: List[Dict[str, Any]] = []

    for record in sampled:
        try:
            optimized_record, debug_row = optimize_single_record(
                record,
                model,
                base_system_prompt,
                max_rounds,
                progress_callback=progress_callback,
            )
            optimized.append(optimized_record)
            debug_rows.append(debug_row)
        except Exception as exc:
            debug_rows.append(
                {
                    "id": record.get("id"),
                    "normalizedTag": record.get("normalizedTag"),
                    "rounds": [],
                    "final_prompt": base_system_prompt,
                    "stop_reason": "error",
                    "error": str(exc),
                }
            )

    return optimized, debug_rows
