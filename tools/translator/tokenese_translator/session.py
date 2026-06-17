"""Session state for a Tokenese translator session.

Tracks (per spec.md + DESIGN.md):
  - The symbol table (@handle -> value), with bind/rebind/drop semantics.
  - Handshake state: 'pending' / 'probed' / 'open' / 'closed'.
  - Mode: 'dense' (default once handshake completes) or 'plain' (escape).
  - Repair history: how many ?? have hit the same content; after 3 we
    auto-pin to plain on that topic (and record it for L3 conformance).
  - Per-session diagnostics aggregated across lines.

A Session is intentionally cheap to create and serialize. The MCP server
keeps a dict of session_id -> Session in memory.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RepairRecord:
    topic: str           # the content the repair is targeting (referent or "<last line>")
    count: int = 0
    pinned_plain: bool = False


@dataclass
class Session:
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    bindings: Dict[str, str] = field(default_factory=dict)        # handle -> value (raw RHS)
    binding_order: List[str] = field(default_factory=list)
    numeric_seq: int = 0                                          # next implicit @N
    handshake: str = "pending"                                    # pending|probed|open|closed
    version: Optional[str] = None
    mode: str = "dense"                                           # spec default once open
    repair_history: Dict[str, RepairRecord] = field(default_factory=dict)
    diagnostics: List[str] = field(default_factory=list)
    last_statement_raw: Optional[str] = None                      # for `??` (bare) referent

    # ----- handshake -----

    def on_probe(self, version: Optional[str]) -> None:
        self.handshake = "probed"
        if version:
            self.version = version

    def on_ack(self, version: Optional[str]) -> None:
        # Ack only valid if either side already probed; we accept ack
        # opportunistically and note a diagnostic otherwise.
        if self.handshake not in ("probed", "open"):
            self.diagnostics.append("handshake ack without prior probe")
        self.handshake = "open"
        if version:
            self.version = version

    # ----- mode -----

    def on_mode(self, mode: str) -> None:
        if mode in ("dense", "plain"):
            self.mode = mode

    # ----- bindings -----

    def bind(self, handle: str, value: str) -> Optional[str]:
        """Returns an error diagnostic string on collision, else None."""
        if handle in self.bindings:
            return f"rebinding @{handle} (was '{self.bindings[handle]}', now '{value}') -- spec requires ?? @{handle}"
        self.bindings[handle] = value
        self.binding_order.append(handle)
        if handle.isdigit():
            try:
                n = int(handle)
                if n > self.numeric_seq:
                    self.numeric_seq = n
            except ValueError:
                pass
        return None

    def drop(self, handle: str) -> Optional[str]:
        if handle not in self.bindings:
            return f"drop @{handle} but handle not bound"
        del self.bindings[handle]
        self.binding_order = [h for h in self.binding_order if h != handle]
        return None

    def resolve(self, handle: str) -> Optional[str]:
        return self.bindings.get(handle)

    # ----- repair -----

    def on_repair(self, referent: Optional[str]) -> RepairRecord:
        topic = referent if referent else (self.last_statement_raw or "<last>")
        rec = self.repair_history.get(topic)
        if rec is None:
            rec = RepairRecord(topic=topic, count=0, pinned_plain=False)
            self.repair_history[topic] = rec
        rec.count += 1
        if rec.count >= 3:
            rec.pinned_plain = True
            # Per spec: stay in plain English for that topic. We approximate
            # 'topic' as session-wide mode for simplicity, since the spec
            # leaves topic-scoping informal. We record this as a diagnostic.
            self.diagnostics.append(
                f"three ?? on '{topic}' -> session pinned to plain for that topic"
            )
        return rec

    # ----- bookkeeping -----

    def remember_statement(self, raw: str) -> None:
        self.last_statement_raw = raw
