"""Frameset registry validation for Tokenese statements.

The registry is report-only in v0.3.x. It makes malformed registered ops
structurally detectable for the A/B harness without changing parse acceptance,
conformance level, or TKAB outcome classification.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .parser import Statement, parse_transcript


PACKAGE_REGISTRY = Path(__file__).with_name("framesets.json")
REPO_REGISTRY = Path(__file__).resolve().parents[3] / "framesets.json"

RESERVED_SLOT_KEYS = {
    "",
    "^",
    "#",
    "::",
    "->",
    "=>",
    "|",
    "~",
    "!",
    "†",
    "□",
    "??",
    "§",
    "ev",
    ">>>",
    "*>>",
    "?>>",
}


def load_frameset_registry(path: Optional[str] = None) -> Dict[str, Any]:
    """Load the frameset registry.

    Resolution order:
    1. explicit ``path``
    2. ``TOKENESE_FRAMESETS`` environment variable
    3. repository-root ``framesets.json`` when running from source
    4. packaged ``tokenese_translator/framesets.json``
    """
    candidates: List[Path] = []
    if path:
        candidates.append(Path(path))
    env_path = os.environ.get("TOKENESE_FRAMESETS")
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([REPO_REGISTRY, PACKAGE_REGISTRY])

    for candidate in candidates:
        if candidate.exists():
            with candidate.open("r", encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("no Tokenese frameset registry found")


def validate_framesets(
    text: str,
    *,
    registry: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Validate registered op shapes in a transcript.

    Unknown ops are intentionally skipped: content vocabulary and session-local
    registrations remain legal. Diagnostics are structural telemetry only.
    """
    reg = registry or load_frameset_registry()
    nodes = parse_transcript(text)
    issues: List[Dict[str, Any]] = []
    checked_ops: List[str] = []
    unregistered_ops: List[str] = []

    for index, node in enumerate(nodes, start=1):
        if not isinstance(node, Statement):
            continue
        frameset = (reg.get("ops") or {}).get(node.op)
        if frameset is None:
            if node.op not in unregistered_ops:
                unregistered_ops.append(node.op)
            continue
        checked_ops.append(node.op)
        line_no = getattr(node, "_line_no", index)
        issues.extend(_validate_statement(node, frameset, line_no))

    return {
        "schema_version": reg.get("schema_version", "tokenese-framesets-0.1"),
        "status": reg.get("status", "experimental-report-only"),
        "checked_statement_count": len(checked_ops),
        "checked_ops": checked_ops,
        "unregistered_ops": unregistered_ops,
        "issues": issues,
    }


def _validate_statement(node: Statement, frameset: Dict[str, Any], line_no: int) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    positional = _positional_args(node)
    positional_spec = frameset.get("positional") or []
    min_pos = sum(1 for p in positional_spec if p.get("required", True))
    max_pos = len(positional_spec)

    if len(positional) < min_pos:
        issues.append(
            _issue(
                line_no,
                node,
                "missing_positional",
                "error",
                f"op '{node.op}' expects at least {min_pos} positional arg(s); saw {len(positional)}",
                frameset,
            )
        )
    if max_pos and len(positional) > max_pos:
        issues.append(
            _issue(
                line_no,
                node,
                "extra_positional",
                "info",
                f"op '{node.op}' declares {max_pos} positional arg(s); saw {len(positional)}",
                frameset,
            )
        )

    seen_slot_keys = _regular_slot_keys(node)
    slot_spec = frameset.get("slots") or []
    declared_keys = [s["key"] for s in slot_spec if "key" in s]
    required_keys = [s["key"] for s in slot_spec if s.get("required")]

    for key in required_keys:
        if key not in seen_slot_keys:
            issues.append(
                _issue(
                    line_no,
                    node,
                    "missing_required_slot",
                    "error",
                    f"op '{node.op}' requires slot '{key}'",
                    frameset,
                )
            )

    registered_in_seen_order = [k for k in seen_slot_keys if k in declared_keys]
    canonical_order = [k for k in declared_keys if k in registered_in_seen_order]
    if registered_in_seen_order != canonical_order:
        issues.append(
            _issue(
                line_no,
                node,
                "noncanonical_slot_order",
                "info",
                f"op '{node.op}' slots should follow canonical order: {' '.join(declared_keys)}",
                frameset,
            )
        )

    for key in seen_slot_keys:
        if key not in declared_keys:
            issues.append(
                _issue(
                    line_no,
                    node,
                    "unregistered_slot",
                    "info",
                    f"slot '{key}' is not declared for op '{node.op}'",
                    frameset,
                )
            )

    return issues


def _positional_args(node: Statement) -> List[str]:
    args: List[str] = []
    if node.target is not None:
        args.append(node.target)
    for slot in node.slots:
        if slot.key in {"->", "=>", ">>>", "*>>", "?>>"}:
            break
        if slot.key == "":
            args.append(str(slot.value))
    return args


def _regular_slot_keys(node: Statement) -> List[str]:
    return [
        slot.key
        for slot in node.slots
        if slot.key not in RESERVED_SLOT_KEYS
    ]


def _issue(
    line_no: int,
    node: Statement,
    code: str,
    severity: str,
    message: str,
    frameset: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "line_no": line_no,
        "op": node.op,
        "code": code,
        "severity": severity,
        "message": message,
        "signature": frameset.get("signature"),
        "raw": node.raw,
    }


def registered_ops(registry: Optional[Dict[str, Any]] = None) -> Iterable[str]:
    reg = registry or load_frameset_registry()
    return (reg.get("ops") or {}).keys()
