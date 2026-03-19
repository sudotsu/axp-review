"""
Schema validators for role outputs.

Validates JSON structures for S (Strategist), A (Analyst), P (Producer),
C (Courier), and X (Critic) role outputs.
"""

from typing import Optional


def validate_S(items) -> tuple[bool, str]:
    """Validate Strategist output (S array)."""
    if not isinstance(items, list) or not items:
        return False, "S must be non-empty list"
    req = {"s_id", "title", "audience", "hooks", "three_step_plan"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "S item missing required keys"
    return True, "ok"


def validate_A(items, s_ids: set) -> tuple[bool, str]:
    """Validate Analyst output (A array) with S-ID references."""
    if not isinstance(items, list) or not items:
        return False, "A must be non-empty list"
    req = {"a_id", "s_refs", "kpi_table"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "A item missing required keys"
        if not set(it.get("s_refs", [])).issubset(s_ids):
            return False, "A item has unknown S refs"
    return True, "ok"


def validate_P(items, a_ids: set) -> tuple[bool, str]:
    """Validate Producer output (P array) with A-ID references."""
    if not isinstance(items, list) or not items:
        return False, "P must be non-empty list"
    req = {"p_id", "a_refs", "spec_type", "body"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "P item missing required keys"
        if not set(it.get("a_refs", [])).issubset(a_ids):
            return False, "P item has unknown A refs"
    return True, "ok"


def validate_C(items, p_ids: set, producer_assets: Optional[list] = None) -> tuple[bool, str]:
    """
    Validate Courier output (C array) with P-ID references.

    Args:
        items: C array to validate
        p_ids: Set of valid P-IDs (from Producer)
        producer_assets: Optional list of Producer assets for explicit validation

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(items, list) or not items:
        return False, "C must be non-empty list"
    req = {"day", "time", "channel", "p_id", "kpi_target", "owner_action"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "C row missing required keys"
        if it.get("p_id") not in p_ids:
            return False, "C row references unknown P-ID"

    # Explicit validation: Courier must only use Producer's declared assets
    if producer_assets is not None:
        used_p_ids = {row.get('p_id') for row in items}
        prod_p_ids = {asset.get('p_id') for asset in producer_assets if isinstance(asset, dict)}
        if not used_p_ids.issubset(prod_p_ids):
            missing = used_p_ids - prod_p_ids
            return False, f"Courier used undeclared assets: {missing}"

    return True, "ok"


def validate_X(items, s_ids: set, a_ids: set, p_ids: set, c_ids: set) -> tuple[bool, str]:
    """Validate Critic output (X array) with cross-references."""
    if not isinstance(items, list) or not items:
        return False, "X must be non-empty list"
    req = {"x_id", "refs", "issue", "fix", "severity", "proof_scores"}
    for it in items:
        if not isinstance(it, dict) or not req.issubset(it.keys()):
            return False, "X item missing required keys"
        refs = it.get("refs", {}) or {}
        if not isinstance(refs, dict):
            return False, "X refs must be dict"
        if not set(refs.get("s", [])).issubset(s_ids):
            return False, "X refs contain unknown S ids"
        if not set(refs.get("a", [])).issubset(a_ids):
            return False, "X refs contain unknown A ids"
        if not set(refs.get("p", [])).issubset(p_ids):
            return False, "X refs contain unknown P ids"
        if not set(refs.get("c", [])).issubset(c_ids):
            return False, "X refs contain unknown C ids"
    return True, "ok"

