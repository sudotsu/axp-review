# Timestamp: 2025-10-27 04:41:45 UTC
# Hash: 3b830aeb2a5f2bc77718bf9504bf4d811cfe6f783fa1a350152079f541885bc1
"""
AxProtocol War Room — Hybrid Runner with FULL ENFORCEMENT v2.4
=================================================================
Changes from v2.3:
- Multi-domain detection integrated (DomainDetector)
- Auto-detects domain from objective text
- Optional domain override via CLI
- Domain passed to role loader for domain-specific roles
- TAES evaluation with domain-specific weights
- All previous enforcement features maintained
"""

import os, sys, re, csv, json, uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# Import AxProtocol enforcement modules
from taes_evaluation import evaluate_taes, check_cognitive_disalignment
from score_validator import extract_scores, validate_scores, format_score_block
from auth import CAMLease, validate_op_token
from ledger import log_execution, get_last_n_entries, verify_hash_chain

# 🔥 NEW: Import domain detector
from domain_detector import DomainDetector

# ────────────────────────────────────────────────────────────────────────────
# 0) Setup
# ────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception as e:
    raise SystemExit(f"[ERROR] OpenAI init failed: {e}")

# 🔥 NEW: Initialize domain detector at startup
try:
    domain_detector = DomainDetector()
    print("[OK] Domain detector initialized")
except Exception as e:
    print(f"[WARN] Domain detector unavailable: {e}")
    domain_detector = None

# ────────────────────────────────────────────────────────────────────────────
# 1) Tiered model selection
# ────────────────────────────────────────────────────────────────────────────
TIER = os.getenv("TIER", "DEV").upper()
MODEL_MAP = {
    "DEV": os.getenv("MODEL_DEV", "gpt-4o-mini"),
    "PREP": os.getenv("MODEL_PREP", "gpt-4o-turbo"),
    "CLIENT": os.getenv("MODEL_CLIENT", "gpt-4o"),
}
MODEL = MODEL_MAP.get(TIER, "gpt-4o-mini")
print(f"[AxProtocol] Tier={TIER}  ->  Model={MODEL}")

# 🔥 REMOVED: Static DOMAIN variable (now detected per-objective)
# Old: DOMAIN = os.getenv("DOMAIN", "marketing").lower()

# ────────────────────────────────────────────────────────────────────────────
# 2) Directive loading (same as before)
# ────────────────────────────────────────────────────────────────────────────
def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf8") if path.exists() else f"[Missing: {path.name}]"

def load_directives():
    files = {
        "D0":   BASE_DIR / "protocol" / "AxProtocol_v2.4_D0_CHANGE_CONTROL.md",
        "CORE": BASE_DIR / "protocol" / "AxProtocol_v2.4_CORE_DIRECTIVES.md",
        "ADD":  BASE_DIR / "protocol" / "AxProtocol_v2.4_WARROOM_ADDENDUM.md",
        "AAL":  BASE_DIR / "protocol" / "AxProtocol_v2.4_AUTHORITY_LAYER.md",
        "TAES": BASE_DIR / "protocol" / "AxProtocol_v2.4_TAES_EVALUATION.md",
        "RDL":  BASE_DIR / "protocol" / "AxProtocol_v2.4_REDTEAM_LAYER.md",
    }
    return {k: _read_text(v) for k, v in files.items()}

DIRECTIVES = load_directives()

BRIEFINGS = {
    "d0":    "Observe Change Control (D0): record kernel modifications, maintain directive parity, enforce version integrity, rollback authority reserved to Operator.",
    "core":  "Enforce AxProtocol Core (1–14): truth discipline, logic integrity, contradiction detection.",
    "add":   "Apply War-Room Addendum (15–19): objective grounding, scoring ≥85, handoff, efficiency, client-readiness.",
    "aal":   "Respect Authority Assertion (20–24): Operator supremacy, CAM lease, immutable ledger, killchain, drift monitor.",
    "taes":  "Use TAES (25–25c): weigh Logical/Practical/Probable, IRD>0.5 -> RRP.",
    "rdl":   "Red-Team Layer (26–28): falsification MAS, CV detection, residual risk, structured dissent.",
}

def compose_system(role_prompt: str, include=("d0","core","add","aal","taes","rdl"), ask_full=None) -> str:
    buf = [BRIEFINGS[k] for k in include if k in BRIEFINGS]
    if role_prompt:
        buf.insert(0, role_prompt.strip())
    return "\n\n".join(buf)

# ────────────────────────────────────────────────────────────────────────────
# 3) Role loading
# ────────────────────────────────────────────────────────────────────────────
STRATEGIST = ANALYST = PRODUCER = COURIER = CRITIC = None

def load_domain_roles(domain: str) -> dict:
    """
    Load roles for a specific domain.

    Args:
        domain: Domain name (e.g., 'marketing', 'technical', 'ops', 'creative', 'education', 'product', 'strategy', 'research')

    Returns:
        Dictionary with role contents
    """
    try:
        from load_roles import load_roles_by_pattern
        BUILD_TYPE = os.getenv("BUILD_TYPE", "stable")

        # 🔥 NEW: Pass domain to role loader
        _roles = load_roles_by_pattern(BUILD_TYPE, domain)

        print(f"✅ Loaded {domain} domain roles ({BUILD_TYPE})")
        return {
            'strategist': _roles["strategist"]["content"],
            'analyst': _roles["analyst"]["content"],
            'producer': _roles["producer"]["content"],
            'courier': _roles["courier"]["content"],
            'critic': _roles["critic"]["content"],
        }
    except Exception as e:
        print(f"⚠️ Role loader not available for {domain} — using inline defaults.\n{e}")
        # Fallback to generic roles
        return {
            'strategist': (
                "Role: Strategist. Define positioning, 3 audiences, 3 hooks, 3-step plan. "
                "Be decisive; ground in objective. End with KPI or action (Directive 15)."
            ),
            'analyst': (
                "Role: Analyst. Pressure-test assumptions; risks->mitigations; 3 KPIs with numeric targets; "
                "A/B plan; short validation table. Prioritize 95% workable now. Score ≥85."
            ),
            'producer': (
                "Role: Producer. Create publishable assets for Nextdoor, Facebook, Craigslist (≤180 words each), "
                "3 alt headlines, 1 proof bullet. Clear CTA. Platform-specific. Score ≥85."
            ),
            'courier': (
                "Role: Courier. Build D1–D7 schedule (times + channels), DM plan, KPI tracker, "
                "3 fallback moves if leads < target by Day 3. Score ≥85."
            ),
            'critic': (
                "Role: Critic. Audit for compliance, clarity, proof, CTA power, local tone. "
                "List 'Issue->Fix' pairs, give five 0–100 ratings + average. If <85, revise once, re-score."
            ),
        }

# ────────────────────────────────────────────────────────────────────────────
# 4) Core chat function
# ────────────────────────────────────────────────────────────────────────────
def llm(system_text: str, user_text: str, temperature=0.4, max_tokens=1600) -> str:
    r = client.chat.completions.create(
        model=MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_text},
        ],
    )
    return r.choices[0].message.content

# ────────────────────────────────────────────────────────────────────────────
# 5) War Room chain WITH ENFORCEMENT + MULTI-DOMAIN SUPPORT
# ────────────────────────────────────────────────────────────────────────────
def run_chain(objective: str, session_id: Optional[str] = None, domain: Optional[str] = None):
    """
    Execute 5-role chain with full AxProtocol enforcement + multi-domain support:
    - Auto-detect domain from objective (or use override)
    - Load domain-specific roles
    - TAES evaluation with domain weights
    - Score validation (≥85 threshold)
    - Ledger logging
    - CAM lease tracking
    - RRP trigger on high IRD

    Args:
        objective: The campaign/project objective
        session_id: Optional session identifier
        domain: Optional domain override (e.g., 'technical', 'marketing')
    """

    if not session_id:
        session_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    print(f"\n[AxProtocol] Session: {session_id}")

    # ────────────────────────────────────────────────────────────────────────
    # 🔥 NEW: Auto-detect domain or use override
    # ────────────────────────────────────────────────────────────────────────
    if domain:
        # Manual override
        detected_domain = domain.lower()
        print(f"[AxProtocol] Using specified domain: {detected_domain.upper()}")
    elif domain_detector:
        # Auto-detection
        detected_domain = domain_detector.detect(objective, verbose=False)
        scores = domain_detector._score_all_domains(objective)
        confidence = scores.get(detected_domain, 0.0)
        print(f"[AxProtocol] Auto-detected domain: {detected_domain.upper()} (confidence: {confidence:.2f})")

        # Show top 3 for transparency
        top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_str = ", ".join([f"{d}({s:.2f})" for d, s in top_3])
        print(f"[AxProtocol] Top matches: {top_str}")
    else:
        # Fallback if detector unavailable
        detected_domain = "marketing"
        print(f"[AxProtocol] Domain detector unavailable - using fallback: {detected_domain.upper()}")

    # ────────────────────────────────────────────────────────────────────────
    # 🔥 NEW: Load domain-specific roles
    # ────────────────────────────────────────────────────────────────────────
    roles = load_domain_roles(detected_domain)
    STRATEGIST = roles['strategist']
    ANALYST = roles['analyst']
    PRODUCER = roles['producer']
    COURIER = roles['courier']
    CRITIC = roles['critic']

    # Initialize CAM lease (Directive 21)
    cam_lease = CAMLease(duration_seconds=180)

    results = {}

    # ────────────────────────────────────────────────────────────────────────
    # STRATEGIST
    # ────────────────────────────────────────────────────────────────────────
    print("\n[1/5] Strategist...")
    sys_s = compose_system(STRATEGIST, ask_full=objective)
    s = llm(sys_s, f"Objective:\n{objective}\nReturn positioning, audiences, hooks, 3-step plan.")

    # Log to ledger
    log_execution(
        session_id=session_id,
        agent_id=f"strategist-{uuid.uuid4().hex[:8]}",
        role_name="Strategist",
        action="generate_strategy",
        input_text=objective,
        output_text=s,
        directive=15
    )

    # 🔥 UPDATED: TAES evaluation with detected domain
    taes_s = evaluate_taes(s, domain=detected_domain, session_id=session_id, role_name="Strategist")
    print(f"   TAES -> IV: {taes_s['integrity_vector']}, IRD: {taes_s['ird']}")

    # Score validation
    scores_s = extract_scores(s)
    if scores_s:
        validation_s = validate_scores(scores_s, threshold=85)
        print(f"   Scores -> {validation_s['reason']}")
        if not validation_s['valid']:
            print(f"   ⚠️ Below threshold: {validation_s['below_threshold']}")

    results['strategist'] = {
        'output': s,
        'taes': taes_s,
        'scores': scores_s,
    }

    # ────────────────────────────────────────────────────────────────────────
    # ANALYST
    # ────────────────────────────────────────────────────────────────────────
    print("\n[2/5] Analyst...")
    sys_a = compose_system(ANALYST)
    a = llm(sys_a, f"Objective:\n{objective}\n\nStrategist:\n{s}\n\nReturn logic test + KPIs.")

    log_execution(
        session_id=session_id,
        agent_id=f"analyst-{uuid.uuid4().hex[:8]}",
        role_name="Analyst",
        action="validate_strategy",
        input_text=s,
        output_text=a,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_a = evaluate_taes(a, domain=detected_domain, session_id=session_id, role_name="Analyst")
    print(f"   TAES -> IV: {taes_a['integrity_vector']}, IRD: {taes_a['ird']}")

    scores_a = extract_scores(a)
    if scores_a:
        validation_a = validate_scores(scores_a, threshold=85)
        print(f"   Scores -> {validation_a['reason']}")

    results['analyst'] = {
        'output': a,
        'taes': taes_a,
        'scores': scores_a,
    }

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER [DRAFT]
    # ────────────────────────────────────────────────────────────────────────
    print("\n[3/5] Producer [draft]...")
    sys_p = compose_system(PRODUCER)
    p_draft = llm(sys_p, f"Objective:\n{objective}\n\nStrategy:\n{s}\n\nPlan:\n{a}\n\nReturn assets.")

    log_execution(
        session_id=session_id,
        agent_id=f"producer-draft-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Draft",
        action="generate_assets",
        input_text=f"{s}\n{a}",
        output_text=p_draft,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_p = evaluate_taes(p_draft, domain=detected_domain, session_id=session_id, role_name="Producer-Draft")
    print(f"   TAES -> IV: {taes_p['integrity_vector']}, IRD: {taes_p['ird']}")

    results['producer_draft'] = {
        'output': p_draft,
        'taes': taes_p,
    }

    # ────────────────────────────────────────────────────────────────────────
    # COURIER [DRAFT]
    # ────────────────────────────────────────────────────────────────────────
    print("\n[4/5] Courier [draft]...")
    sys_c = compose_system(COURIER)
    c_draft = llm(sys_c, f"Objective:\n{objective}\n\nAssets:\n{p_draft}\n\nReturn D1–D7 calendar + KPIs.")

    log_execution(
        session_id=session_id,
        agent_id=f"courier-draft-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Draft",
        action="create_schedule",
        input_text=p_draft,
        output_text=c_draft,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_c = evaluate_taes(c_draft, domain=detected_domain, session_id=session_id, role_name="Courier-Draft")
    print(f"   TAES -> IV: {taes_c['integrity_vector']}, IRD: {taes_c['ird']}")

    results['courier_draft'] = {
        'output': c_draft,
        'taes': taes_c,
    }

    # ────────────────────────────────────────────────────────────────────────
    # CRITIC
    # ────────────────────────────────────────────────────────────────────────
    print("\n[5/5] Critic...")
    sys_crit = compose_system(CRITIC)
    crit = llm(sys_crit, f"Objective:\n{objective}\n\nProducer:\n{p_draft}\n\nCourier:\n{c_draft}\n\nReturn issues + 5 scores.")

    log_execution(
        session_id=session_id,
        agent_id=f"critic-{uuid.uuid4().hex[:8]}",
        role_name="Critic",
        action="final_review",
        input_text=f"{p_draft}\n{c_draft}",
        output_text=crit,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_crit = evaluate_taes(crit, domain=detected_domain, session_id=session_id, role_name="Critic")
    print(f"   TAES -> IV: {taes_crit['integrity_vector']}, IRD: {taes_crit['ird']}")

    results['critic'] = {
        'output': crit,
        'taes': taes_crit,
    }

    scores_crit = extract_scores(crit)
    if scores_crit:
        validation_crit = validate_scores(scores_crit, threshold=85)
        print(f"   Scores -> {validation_crit['reason']}")

    # ────────────────────────────────────────────────────────────────────────
    # PRODUCER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Producer...")
    p_rev = llm(sys_p, f"Apply Critic fixes. Return [Revised] assets only.\n"
                       f"Critic:\n{crit}\nProducer [Draft]:\n{p_draft}")

    log_execution(
        session_id=session_id,
        agent_id=f"producer-rev-{uuid.uuid4().hex[:8]}",
        role_name="Producer-Revised",
        action="revise_assets",
        input_text=crit,
        output_text=p_rev,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_p_rev = evaluate_taes(p_rev, domain=detected_domain, session_id=session_id, role_name="Producer-Revised")
    print(f"   TAES -> IV: {taes_p_rev['integrity_vector']}, IRD: {taes_p_rev['ird']}")

    # RRP check (Directive 25)
    if taes_p_rev['requires_rrp']:
        print(f"   ⚠️ IRD > 0.5 detected - Reality Reconciliation Pass recommended")

    results['producer_revised'] = {
        'output': p_rev,
        'taes': taes_p_rev
    }

    # ────────────────────────────────────────────────────────────────────────
    # COURIER (revised)
    # ────────────────────────────────────────────────────────────────────────
    print("\n[Revision] Courier...")
    c_rev = llm(sys_c, f"Adjust per Critic. Return [Revised] calendar + KPI table.\n"
                       f"Critic:\n{crit}\nCourier [Draft]:\n{c_draft}")

    log_execution(
        session_id=session_id,
        agent_id=f"courier-rev-{uuid.uuid4().hex[:8]}",
        role_name="Courier-Revised",
        action="revise_schedule",
        input_text=crit,
        output_text=c_rev,
        directive=15
    )

    # 🔥 UPDATED: TAES with domain
    taes_c_rev = evaluate_taes(c_rev, domain=detected_domain, session_id=session_id, role_name="Courier-Revised")
    print(f"   TAES -> IV: {taes_c_rev['integrity_vector']}, IRD: {taes_c_rev['ird']}")

    if taes_c_rev['requires_rrp']:
        print(f"   ⚠️ IRD > 0.5 detected - Reality Reconciliation Pass recommended")

    results['courier_revised'] = {
        'output': c_rev,
        'taes': taes_c_rev
    }

    # ────────────────────────────────────────────────────────────────────────
    # Final checks
    # ────────────────────────────────────────────────────────────────────────
    print("\n[AxProtocol] Chain complete. Running final checks...")

    # Check for cognitive disalignment (Directive 25b)
    disalignment = check_cognitive_disalignment()
    if disalignment['alert']:
        print(f"   ⚠️ {disalignment['reason']}")

    # Verify ledger integrity (Directive 22)
    integrity = verify_hash_chain()
    if not integrity['valid']:
        print(f"   ❌ Ledger integrity compromised: {integrity['broken']}")
    else:
        print(f"   ✅ Ledger verified ({integrity['entries']} entries)")

    # 🔥 NEW: Store detected domain in results
    results['domain'] = detected_domain

    return s, a, p_rev, c_rev, crit, results

# ────────────────────────────────────────────────────────────────────────────
# 6) KPI extraction (unchanged)
# ────────────────────────────────────────────────────────────────────────────
def extract_kpi_rows(markdown_text: str):
    pattern = r"\| *([^\|]+)\| *([^\|]+)\| *([^\|]+)\|"
    rows = re.findall(pattern, markdown_text)
    out = []
    for r in rows:
        if "KPI" in r[0] or "---" in r[0]:
            continue
        out.append([x.strip() for x in r])
    return out

# ────────────────────────────────────────────────────────────────────────────
# 7) Logging + ROI JSON
# ────────────────────────────────────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs" / "sessions"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def log_session(objective, s, a, p_rev, c_rev, crit, results):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    log_path = LOG_DIR / f"{ts}_{TIER.lower()}.log"

    # 🔥 NEW: Get domain from results
    domain = results.get('domain', 'unknown')

    with open(log_path, "w", encoding="utf8") as f:
        f.write(f"[Timestamp] {ts} UTC\n[Model] {MODEL}\n[Tier] {TIER}\n[Domain] {domain}\n\n")
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
            "tier": TIER,
            "model": MODEL,
            "domain": domain,
            "objective": objective[:300],
            "summary": "Immediate ROI trigger detected in AxProtocol chain output.",
            "source": "AxProtocol War Room v2.4",
        }
        with open(LOG_DIR / f"{ts}_{TIER.lower()}_ROI.json", "w", encoding="utf8") as jf:
            json.dump(payload, jf, indent=2)

    # KPI CSV
    kpi_rows = extract_kpi_rows(c_rev)
    if kpi_rows:
        csv_path = BASE_DIR / "logs" / "kpi_log.csv"
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

# ────────────────────────────────────────────────────────────────────────────
# 8) Entry point with MULTI-DOMAIN SUPPORT
# ────────────────────────────────────────────────────────────────────────────
def main():
    # 🔥 NEW: Check for domain override as last argument
    domain_override = None
    args = sys.argv[1:]

    # Check if last arg is a domain name
    if args and args[-1].lower() in ['marketing', 'technical', 'ops', 'creative',
                                       'education', 'product', 'strategy', 'research']:
        domain_override = args[-1].lower()
        args = args[:-1]  # Remove domain from args

    if args:
        objective = " ".join(args)
    else:
        objective = (
            "Book 5 local jobs in 7 days for a tree service in Omaha. Create 3 assets "
            "(Nextdoor, Facebook, Craigslist; ≤180 words each; 3 alt headlines each); "
            "D1–D7 schedule with posting times, bumps, follow-ups, short DM scripts; "
            "KPI table (Day|Posts|Leads|Booked|Rev|Notes). Offer: 20% gap-fill. "
            "Cross-sell lawn/power wash/hauling. Contact: 402-306-4724."
        )

    print("\n[AxProtocol] Running governed five-role chain with FULL ENFORCEMENT...")
    print("[AxProtocol] Multi-domain support: Auto-detection active")
    print("[AxProtocol] TAES evaluation, score validation, and ledger logging active.")

    # 🔥 NEW: Pass domain override if provided
    s, a, p_rev, c_rev, crit, results = run_chain(objective, domain=domain_override)
    log_file = log_session(objective, s, a, p_rev, c_rev, crit, results)

    print(f"\n✅ Complete. Session log: {log_file}")
    print(f"✅ Ledger: logs/ledger/audit_ledger.db")
    print(f"✅ IRD log: logs/ird_log.csv")
    print(f"✅ Domain used: {results.get('domain', 'unknown').upper()}\n")

if __name__ == "__main__":
    main()
