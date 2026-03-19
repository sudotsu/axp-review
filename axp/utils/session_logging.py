"""
Session logging utilities for AxProtocol execution results.
"""

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def extract_kpi_rows(markdown_text: str):
    """
    Extract KPI rows from markdown table.

    Args:
        markdown_text: Markdown text containing KPI table

    Returns:
        List of [kpi, target, status] tuples
    """
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    rows = re.findall(pattern, markdown_text)
    out = []
    for r in rows:
        if "KPI" in r[0] or "---" in r[0]:
            continue
        out.append([x.strip() for x in r])
    return out


def log_session(
    objective: str,
    s: str,
    a: str,
    p_rev: str,
    c_rev: str,
    crit: str,
    results: Dict,
    base_dir: Path,
    tier: str,
    model: str
) -> str:
    """
    Log session results to file and generate ROI/KPI logs.

    Args:
        objective: Campaign objective
        s: Strategist output
        a: Analyst output
        p_rev: Producer revised output
        c_rev: Courier revised output
        crit: Critic output
        results: Results dictionary with TAES data
        base_dir: Base directory for logs
        tier: Tier name (DEV, PREP, CLIENT)
        model: Model name

    Returns:
        Path to log file as string
    """
    log_dir = base_dir / "logs" / "sessions"
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    log_path = log_dir / f"{ts}_{tier.lower()}.log"

    # Get domain from results
    domain = results.get('domain', 'unknown')

    with open(log_path, "w", encoding="utf8") as f:
        f.write(f"[Timestamp] {ts} UTC\n[Model] {model}\n[Tier] {tier}\n[Domain] {domain}\n\n")
        f.write("[Objective]\n" + objective + "\n\n")
        f.write("## STRATEGIST\n" + s + "\n\n")

        # Add TAES data
        if 'strategist' in results:
            taes = results['strategist']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## ANALYST\n" + a + "\n\n")

        if 'analyst' in results:
            taes = results['analyst']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## PRODUCER [Revised]\n" + p_rev + "\n\n")

        if 'producer_revised' in results:
            taes = results['producer_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## COURIER [Revised]\n" + c_rev + "\n\n")

        if 'courier_revised' in results:
            taes = results['courier_revised']['taes']
            f.write(f"TAES -> IV: {taes['integrity_vector']}, IRD: {taes['ird']}, RRP: {taes['requires_rrp']}\n\n")

        f.write("## CRITIC\n" + crit + "\n")

    # ROI trigger detection
    if "[Tier: Immediate ROI]" in (s + a + p_rev + c_rev + crit):
        payload = {
            "trigger": "AxP_Curve_ImmediateROI",
            "timestamp": ts,
            "tier": tier,
            "model": model,
            "domain": domain,
            "objective": objective[:300],
            "summary": "Immediate ROI trigger detected in AxProtocol chain output.",
            "source": "AxProtocol War Room v2.4",
        }
        with open(log_dir / f"{ts}_{tier.lower()}_ROI.json", "w", encoding="utf8") as jf:
            json.dump(payload, jf, indent=2)

    # KPI CSV
    kpi_rows = extract_kpi_rows(c_rev)
    if kpi_rows:
        csv_path = base_dir / "logs" / "kpi_log.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        header = ["timestamp", "objective", "kpi", "target", "status"]
        exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf8") as csvf:
            w = csv.writer(csvf)
            if not exists:
                w.writerow(header)
            for kpi, target, status in kpi_rows:
                w.writerow([ts, objective, kpi, target, status])

    return str(log_path)

