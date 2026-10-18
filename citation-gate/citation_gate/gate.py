"""Citation gate: drop LLM claims that cannot be traced to real records.

**中文** · **English**

模式 / The pattern: an LLM summarizing your data will invent fluent
conclusions. Require every claim to cite record ids from the exact set
you sent it; verify each citation against that set; discard anything
that does not resolve. A conclusion that cannot point back at the
evidence is indistinguishable from a hallucination — so it never gets
stored or shown.

    from citation_gate import verify_claims

    records = [{"id": 1, "text": "quoted source"}, ...]   # what you sent
    kept, rejected = verify_claims(claims, records, quote_key="text")
    # kept: claims with an `evidence` list of {id, quote} — ready to render

Generalized from a production AI-dossier feature (Trace): the model
answers JSON facts with ``message_ids``; every id must exist in the
window that was actually sent, else the fact is dropped and counted.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

DEFAULT_QUOTE_LEN = 120
DEFAULT_EVIDENCE_CAP = 4


def _coerce_ids(raw: Any) -> list[Any]:
    """Accept int, str, or list of either; strings may carry a '#' prefix."""
    if isinstance(raw, (int, str)):
        raw = [raw]
    out: list[Any] = []
    for value in raw or []:
        if isinstance(value, str):
            value = value.lstrip("#").strip()
            try:
                value = int(value)
            except ValueError:
                continue
        if isinstance(value, int):
            out.append(value)
    return out


def verify_claims(
    claims: Iterable[dict],
    records: Iterable[dict],
    id_key: str = "id",
    text_key: str = "text",
    quote_len: int = DEFAULT_QUOTE_LEN,
    evidence_cap: int = DEFAULT_EVIDENCE_CAP,
    is_valid_claim: Callable[[dict], bool] | None = None,
) -> tuple[list[dict], int]:
    """Filter claims down to the ones whose citations resolve.

    Args:
        claims: LLM output; each claim is a dict with ``text`` and a list
            of record ids under ``ids`` / ``ref_ids`` / ``message_ids``
            (first present key wins; bare int/str also accepted).
        records: the exact records that were sent to the model, dicts
            carrying ``id_key`` and ``text_key``.
        is_valid_claim: optional extra predicate (e.g. category whitelist);
            claims failing it are counted as rejected.

    Returns:
        ``(kept, rejected_count)`` — kept claims gain an ``evidence`` list:
        ``[{"id": ..., "quote": <first quote_len chars>, ...record extras}]``
        capped at ``evidence_cap`` entries.
    """
    by_id = {record[id_key]: record for record in records if id_key in record}
    kept: list[dict] = []
    rejected = 0
    for claim in claims:
        if not isinstance(claim, dict):
            rejected += 1
            continue
        text = str(claim.get("text") or "").strip()
        raw_ids = claim.get("ids") or claim.get("ref_ids") or claim.get("message_ids")
        resolved = [i for i in _coerce_ids(raw_ids) if i in by_id]
        if not text or not resolved:
            rejected += 1
            continue
        if is_valid_claim is not None and not is_valid_claim(claim):
            rejected += 1
            continue
        kept.append({
            **claim,
            "text": text,
            "evidence": [
                {"id": i, "quote": str(by_id[i].get(text_key, ""))[:quote_len], **{
                    k: v for k, v in by_id[i].items() if k not in (id_key, text_key)
                }}
                for i in resolved[:evidence_cap]
            ],
        })
    return kept, rejected
