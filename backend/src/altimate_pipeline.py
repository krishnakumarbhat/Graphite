"""Altimate-inspired data pipeline layer for Graphite.

Provides:
  - SQL/schema validation for note_embeddings table health
  - Data lineage tracking (note → chunk → embedding → search result)
  - FinOps: token cost estimation per query
  - Pipeline health metrics
  - Memory tool integration (stores pipeline stats as notes)

Inspired by https://docs.altimate.sh/ toolset:
  SQL Tools, Lineage Tools, Schema Tools, FinOps Tools, Memory Tools.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Data Lineage ────────────────────────────────────────────────────────────
@dataclass
class LineageNode:
    id: str
    kind: str          # 'note' | 'chunk' | 'embedding' | 'result'
    label: str
    meta: dict[str, Any] = field(default_factory=dict)
    children: list['LineageNode'] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'kind': self.kind,
            'label': self.label,
            'meta': self.meta,
            'children': [c.to_dict() for c in self.children],
        }


def build_lineage_graph(
    note_id: str,
    note_title: str,
    chunks: list[dict[str, Any]],
    ranked_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a DAG lineage graph: note → chunks → embeddings → ranked results."""
    root = LineageNode(id=note_id, kind='note', label=note_title)
    for i, chunk in enumerate(chunks):
        chunk_node = LineageNode(
            id=chunk['id'],
            kind='chunk',
            label=f'Chunk {i+1} ({len(chunk["content"])} chars)',
            meta={'score': chunk.get('score', 0)},
        )
        emb_node = LineageNode(
            id=f'emb-{chunk["id"]}',
            kind='embedding',
            label='768-dim vector (Gemini text-embedding-004)',
            meta={'dim': 768},
        )
        chunk_node.children.append(emb_node)
        root.children.append(chunk_node)

    results_node = LineageNode(
        id='results',
        kind='result',
        label=f'Top-{len(ranked_results)} ranked results',
        meta={'count': len(ranked_results)},
    )
    root.children.append(results_node)
    return root.to_dict()


# ── FinOps: Cost Estimation ─────────────────────────────────────────────────
# Gemini 2.0 Flash pricing (as of Jun 2026)
_GEMINI_FLASH_INPUT_COST_PER_1K = 0.000075   # $0.075/1M tokens
_GEMINI_FLASH_OUTPUT_COST_PER_1K = 0.0003    # $0.30/1M tokens
_EMBEDDING_COST_PER_1K = 0.00001             # text-embedding-004 free tier estimate
_CHARS_PER_TOKEN = 4                          # rough estimate


def estimate_cost(
    query: str,
    chunks: list[dict[str, Any]],
    report_markdown: str,
) -> dict[str, Any]:
    """Estimate Gemini API cost for a deep-research query."""
    chunk_text = ' '.join(c.get('content', '') for c in chunks)
    prompt_chars = len(query) + len(chunk_text) + 500   # system prompt overhead
    output_chars = len(report_markdown)
    embed_chars = len(query) + sum(len(c.get('content', '')) for c in chunks)

    input_tokens = prompt_chars / _CHARS_PER_TOKEN
    output_tokens = output_chars / _CHARS_PER_TOKEN
    embed_tokens = embed_chars / _CHARS_PER_TOKEN

    input_cost = (input_tokens / 1000) * _GEMINI_FLASH_INPUT_COST_PER_1K
    output_cost = (output_tokens / 1000) * _GEMINI_FLASH_OUTPUT_COST_PER_1K
    embed_cost = (embed_tokens / 1000) * _EMBEDDING_COST_PER_1K
    total = input_cost + output_cost + embed_cost

    return {
        'input_tokens': round(input_tokens),
        'output_tokens': round(output_tokens),
        'embed_tokens': round(embed_tokens),
        'input_cost_usd': round(input_cost, 6),
        'output_cost_usd': round(output_cost, 6),
        'embed_cost_usd': round(embed_cost, 6),
        'total_cost_usd': round(total, 6),
        'model': 'gemini-2.0-flash',
    }


# ── Schema Validation ────────────────────────────────────────────────────────
def validate_schema(db_path: str) -> dict[str, Any]:
    """Check note_embeddings table health — Altimate-style schema tool."""
    issues: list[str] = []
    stats: dict[str, Any] = {}
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # Check tables exist
        tables = {r['name'] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        required = {'notes', 'note_embeddings', 'agent_runs'}
        missing = required - tables
        if missing:
            issues.append(f'Missing tables: {missing}')

        # Orphan embeddings (embedding without note)
        if 'note_embeddings' in tables and 'notes' in tables:
            orphans = conn.execute(
                'SELECT COUNT(*) FROM note_embeddings e '
                'LEFT JOIN notes n ON e.note_id = n.id WHERE n.id IS NULL'
            ).fetchone()[0]
            if orphans:
                issues.append(f'{orphans} orphaned embeddings (no matching note)')
            stats['orphan_embeddings'] = orphans

        # Notes without embeddings (not yet indexed)
        if 'note_embeddings' in tables and 'notes' in tables:
            unindexed = conn.execute(
                'SELECT COUNT(*) FROM notes n '
                'LEFT JOIN note_embeddings e ON n.id = e.note_id WHERE e.note_id IS NULL'
            ).fetchone()[0]
            if unindexed > 0:
                issues.append(f'{unindexed} notes missing embeddings (search gap)')
            stats['unindexed_notes'] = unindexed

        # Row counts
        for table in tables:
            try:
                stats[f'{table}_count'] = conn.execute(
                    f'SELECT COUNT(*) FROM {table}'  # noqa: S608
                ).fetchone()[0]
            except Exception:
                pass

        conn.close()
    except Exception as exc:
        issues.append(f'DB connection error: {exc}')

    return {
        'status': 'healthy' if not issues else 'warning',
        'issues': issues,
        'stats': stats,
        'checked_at': datetime.now(timezone.utc).isoformat(),
    }


# ── Pipeline Metrics ─────────────────────────────────────────────────────────
@dataclass
class PipelineRun:
    query: str
    started_at: float = field(default_factory=time.time)
    chunks_retrieved: int = 0
    embedding_ms: float = 0.0
    ranking_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0
    precision_at_5: float | None = None
    cost: dict[str, Any] = field(default_factory=dict)
    lineage: dict[str, Any] = field(default_factory=dict)

    def finish(self) -> None:
        self.total_ms = round((time.time() - self.started_at) * 1000, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            'query': self.query,
            'chunks_retrieved': self.chunks_retrieved,
            'latency_ms': {
                'embedding': self.embedding_ms,
                'ranking': self.ranking_ms,
                'llm': self.llm_ms,
                'total': self.total_ms,
            },
            'cost': self.cost,
            'precision_at_5': self.precision_at_5,
            'lineage': self.lineage,
        }
