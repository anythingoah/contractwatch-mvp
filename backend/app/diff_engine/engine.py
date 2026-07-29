"""
The diff engine: compares two normalized contracts and produces a list of
classified changes. This module is pure (no I/O, no DB) so it can be unit
tested with plain dict fixtures — that's deliberate, this is the part of the
product customers have to trust.

Severity levels (matches models.Severity):
  critical -> breaking change, will break existing consumers
  warning  -> potentially breaking / needs attention
  info     -> safe / documentation-only change
"""
import hashlib
import json
from typing import TypedDict


class ChangeEvent(TypedDict):
    type: str
    severity: str
    message: str
    old_value: object
    new_value: object
    path: str


def contract_hash(normalized: dict) -> str:
    """Stable hash of a normalized contract — used to skip diffing when nothing changed."""
    canonical = json.dumps(normalized, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def diff_contracts(before: dict, after: dict) -> list[ChangeEvent]:
    """Compare two normalized contracts (see normalize.py) and return all changes found."""
    changes: list[ChangeEvent] = []

    before_ops = before.get("operations", {})
    after_ops = after.get("operations", {})

    removed_ops = set(before_ops) - set(after_ops)
    added_ops = set(after_ops) - set(before_ops)
    common_ops = set(before_ops) & set(after_ops)

    for op_name in removed_ops:
        changes.append(ChangeEvent(
            type="removed_endpoint",
            severity="critical",
            message=f"Removed: {op_name}",
            old_value=op_name,
            new_value=None,
            path=op_name,
        ))

    for op_name in added_ops:
        changes.append(ChangeEvent(
            type="added_endpoint",
            severity="info",
            message=f"Added: {op_name}",
            old_value=None,
            new_value=op_name,
            path=op_name,
        ))

    for op_name in common_ops:
        changes.extend(_diff_operation(op_name, before_ops[op_name], after_ops[op_name]))

    return changes


def _diff_operation(op_name: str, before_op: dict, after_op: dict) -> list[ChangeEvent]:
    changes: list[ChangeEvent] = []

    before_req = before_op.get("required_params", {})
    before_opt = before_op.get("optional_params", {})
    after_req = after_op.get("required_params", {})
    after_opt = after_op.get("optional_params", {})

    before_all = {**before_req, **before_opt}
    after_all = {**after_req, **after_opt}

    # Removed parameters (present before, gone entirely now)
    for name in set(before_all) - set(after_all):
        was_required = name in before_req
        changes.append(ChangeEvent(
            type="removed_parameter",
            severity="critical" if was_required else "warning",
            message=(
                f"Removed required parameter '{name}' from {op_name}"
                if was_required else
                f"Removed optional parameter '{name}' from {op_name}"
            ),
            old_value=name,
            new_value=None,
            path=f"{op_name}.{name}",
        ))

    # Added parameters
    for name in set(after_all) - set(before_all):
        is_required = name in after_req
        changes.append(ChangeEvent(
            type="added_required_parameter" if is_required else "added_parameter",
            severity="critical" if is_required else "info",
            message=(
                f"Added NEW required parameter '{name}' to {op_name} — existing "
                f"callers that don't send it will now fail"
                if is_required else
                f"Added new optional parameter '{name}' to {op_name}"
            ),
            old_value=None,
            new_value=name,
            path=f"{op_name}.{name}",
        ))

    # Params present in both — check required<->optional flips and type changes
    for name in set(before_all) & set(after_all):
        was_required = name in before_req
        is_required = name in after_req

        if was_required and not is_required:
            changes.append(ChangeEvent(
                type="required_to_optional",
                severity="warning",
                message=f"'{name}' on {op_name} changed from required to optional",
                old_value="required",
                new_value="optional",
                path=f"{op_name}.{name}",
            ))
        elif not was_required and is_required:
            changes.append(ChangeEvent(
                type="optional_to_required",
                severity="critical",
                message=f"'{name}' on {op_name} changed from optional to required",
                old_value="optional",
                new_value="required",
                path=f"{op_name}.{name}",
            ))

        before_type = before_all[name]
        after_type = after_all[name]
        if before_type != after_type and before_type != "any" and after_type != "any":
            changes.append(ChangeEvent(
                type="type_changed",
                severity="critical",
                message=f"'{name}' on {op_name} changed type from {before_type} to {after_type}",
                old_value=before_type,
                new_value=after_type,
                path=f"{op_name}.{name}",
            ))

    # Description-only changes — always informational, never structural
    if (before_op.get("description") or "") != (after_op.get("description") or ""):
        changes.append(ChangeEvent(
            type="description_changed",
            severity="info",
            message=f"Description changed for {op_name}",
            old_value=before_op.get("description"),
            new_value=after_op.get("description"),
            path=f"{op_name}.description",
        ))

    return changes


def overall_severity(changes: list[ChangeEvent]) -> str:
    """A batch of changes is as severe as its worst member."""
    if any(c["severity"] == "critical" for c in changes):
        return "critical"
    if any(c["severity"] == "warning" for c in changes):
        return "warning"
    return "info"


def is_breaking(changes: list[ChangeEvent]) -> bool:
    return any(c["severity"] == "critical" for c in changes)
