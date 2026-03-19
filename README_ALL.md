# AxProtocol v2.7 - Complete Project Documentation

**Purpose:** This document provides comprehensive documentation of the AxProtocol project architecture, philosophy, functionality, and implementation details. It is designed to give another LLM complete context about the project's current state, design decisions, and all moving parts.

**Last Updated:** November 2025
**Version:** 2.7
**Status:** Production Ready ✅

---

## Table of Contents

1. [Project Overview & Philosophy](#project-overview--philosophy)
2. [Core Architecture](#core-architecture)
3. [Key Components & Modules](#key-components--modules)
4. [Data Flow & Execution](#data-flow--execution)
5. [Configuration System](#configuration-system)
6. [Governance & Directives](#governance--directives)
7. [TAES Evaluation System](#taes-evaluation-system)
8. [Ledger & Sentinel](#ledger--sentinel)
9. [Domain System](#domain-system)
10. [Testing & Validation](#testing--validation)
11. [Deployment Architecture](#deployment-architecture)
12. [File Structure & Organization](#file-structure--organization)
13. [Key Design Decisions](#key-design-decisions)
14. [API & Interfaces](#api--interfaces)
15. [Future Considerations](#future-considerations)

---

## Project Overview & Philosophy

### What is AxProtocol?

AxProtocol is a **self-auditing, directive-aware AI reasoning kernel** that orchestrates multi-role agent chains with comprehensive governance, truth evaluation, and cryptographic audit trails. The name derives from "Argon × Xenon" - elements that are "inert to noise, luminous toward truth."

### Core Philosophy

**"Truth > Obedience"** - The system prioritizes factual integrity over blind compliance. Every chain execution is:

1. **Signed** - Cryptographically signed with Ed25519 (HMAC fallback)
2. **Sentineled** - Independently verified by a detached auditor
3. **Config-driven** - All behavior controlled by configuration files with drift detection

### Key Principles

- **Multi-Role Reasoning Chain**: Strategist → Analyst → Producer → Courier → Critic
- **TAES Evaluation**: Truth/Alignment/Efficiency/Signal scoring with domain-specific weights
- **Directive-Based Governance**: 29 directives (D0-D28) enforcing truth, logic, and compliance
- **Immutable Audit Ledger**: Append-only ledger with cryptographic signatures
- **Config Drift Detection**: SHA256 hash of all config files stored in every ledger entry
- **Sentinel Auditor**: Independent verification of ledger integrity and tampering detection
- **Domain-Specific Roles**: 9 domains (marketing, technical, ops, creative, education, product, strategy, research, finance)

### Version History

- **v2.4**: Core protocol with 29 directives, TAES evaluation, ledger signing
- **v2.5**: Modular refactoring into `axp/` subpackages
- **v2.6**: Finance domain, config hash implementation, Δ4 tests
- **v2.7**: PyPI packaging, FastAPI API, Streamlit UI, production hardening

---

## Core Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AxProtocol Kernel                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Orchestration │  │  Governance │  │  Detection   │    │
│  │   (chain.py)  │  │  (coupling) │  │  (signals)   │    │
│  └──────┬────────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                  │                 │            │
│  ┌──────▼──────────────────▼─────────────────▼──────┐    │
│  │         Multi-Role Chain Execution                │    │
│  │  Strategist → Analyst → Producer → Courier → Critic│    │
│  └──────┬─────────────────────────────────────────────┘    │
│         │                                                  │
│  ┌──────▼──────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ TAES Evaluation │  │   Ledger     │  │  Sentinel   │ │
│  │   (scoring)     │  │  (signing)   │  │  (verify)   │ │
│  └─────────────────┘  └──────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Execution Flow

1. **Input**: Objective text (e.g., "Book 5 local jobs in 7 days")
2. **Domain Detection**: Auto-detect domain from objective keywords
3. **Role Loading**: Load domain-specific role definitions
4. **Chain Execution**: Execute 5-role chain sequentially
5. **TAES Evaluation**: Score each role output on Logical/Practical/Probable axes
6. **Governance Coupling**: Apply hard/soft signal enforcement
7. **Ledger Logging**: Write signed entry to append-only ledger
8. **Sentinel Verification**: Independent auditor verifies integrity
9. **Output**: Structured results with TAES scores, registry data, composer report

### Modular Package Structure

The codebase is organized into logical modules under `axp/`:

- **`axp/orchestration/`**: Chain execution, role loading, registry management
- **`axp/governance/`**: Ledger signing, governance coupling, authority enforcement
- **`axp/detection/`**: Signal detection (sycophancy, contradiction, etc.)
- **`axp/directives/`**: Directive loading and system prompt composition
- **`axp/validation/`**: Schema validators for role outputs (S, A, P, C, X)
- **`axp/sentinel/`**: Independent auditor for ledger verification
- **`axp/utils/`**: Shared utilities (logging, LLM, config fingerprint, errors)

---

## Key Components & Modules

### 1. Orchestration (`axp/orchestration/`)

**`chain.py`** - Main chain execution orchestrator
- `run_chain()`: Primary entry point for executing 5-role chains
- Handles domain detection, role loading, TAES evaluation, ledger logging
- Coordinates all components: registry, validators, governance, composer
- Returns: (strategist_output, analyst_output, producer_output, courier_output, critic_output, results_dict)

**`role_executor.py`** - Role execution engine
- `run_role_json()`: Executes a single role with JSON schema validation
- Handles LLM calls, retries, validation, registry updates
- Applies role shapes (banned phrases) and redundancy detection

**`role_loader.py`** - Domain-specific role loading
- `load_domain_roles()`: Loads role definitions from `roles/{domain}/` directories
- Each domain has 5 role files: strategist.txt, analyst.txt, producer.txt, courier.txt, critic.txt
- Falls back to default roles if domain-specific not found

**`registry.py`** - Structured data registry
- `init_registry()`: Creates registry with S, A, P, C, X arrays
- Stores structured outputs from each role (strategy objects, analysis objects, etc.)
- Used for inter-role communication and final composer synthesis

**`composer.py`** - Final report generation
- `compose_final_report()`: Synthesizes all role outputs into executive summary
- Combines registry data, TAES scores, governance signals
- Produces human-readable final report

**`qa.py`** - Micro-QA clarification system
- `run_micro_qa()`: Detects ambiguity in objectives and asks clarifying questions
- Implements Directive 2 (No Assumption) - never guess intent silently
- Stores Q&A pairs in `qa_log` for transparency

### 2. Governance (`axp/governance/`)

**`ledger.py`** - Cryptographic ledger signing
- `write_ledger_entry()`: Appends signed entry to ledger
- Uses Ed25519 signatures (PyNaCl) with HMAC fallback
- Stores entries in `logs/ledger/{YYYYMMDD}.jsonl` format
- Each entry includes: timestamp, role, action, hash, data, signature, config_hash
- Public key stored in `logs/ledger/public.key` for verification

**`coupling.py`** - Governance signal enforcement
- `load_governance_coupling()`: Loads hard/soft signal definitions from `config/governance_coupling.json`
- `apply_governance_coupling()`: Applies TAES caps/floors based on detected signals
- Hard signals (D2, D3, D7, D11, D13, D20-24): Enforce TAES limits
- Soft signals (D0, SECRETS, FABRICATION, etc.): Logged but don't enforce limits

### 3. Detection (`axp/detection/`)

**`signals.py`** - Governance signal detection
- `detect_sycophancy()`: Detects flattery/mimicry (Directive 13)
- `detect_contradiction()`: Detects logic conflicts (Directive 7)
- `detect_ambiguity_in_objective()`: Detects unclear objectives (Directive 2)
- `detect_wants_praise()`: Detects requests for validation
- `precedence_inversion()`: Detects authority drift
- `overconfidence_no_evidence()`: Detects unsupported claims

### 4. Directives (`axp/directives/`)

**`loader.py`** - Directive loading from markdown files
- `load_directives()`: Loads all directive files from `protocol/` directory
- Cached with `@lru_cache` for performance
- Returns dictionary: `{"D0": "...", "CORE": "...", "AAL": "...", "TAES": "...", "RDL": "..."}`

**`composer.py`** - System prompt composition
- `system_for()`: Composes system prompt for a role
- Combines role definition + directive briefings + full directives (when needed)
- Analyst gets full TAES directives, Critic gets full RDL directives
- All roles get briefings for context

### 5. Validation (`axp/validation/`)

**`validators.py`** - JSON schema validators
- `validate_S()`: Validates Strategist output (s_id, title, audience, hooks, three_step_plan, acceptance_tests)
- `validate_A()`: Validates Analyst output (a_id, s_refs, kpi_table, falsifications, risks)
- `validate_P()`: Validates Producer output (p_id, a_refs, spec_type, body)
- `validate_C()`: Validates Courier output (day, time, channel, p_id, kpi_target, owner_action)
- `validate_X()`: Validates Critic output (x_id, refs, issue, fix, severity, proof_scores)
- All validators return `(is_valid: bool, errors: List[str], data: List[dict])`

### 6. Sentinel (`axp/sentinel/`)

**`sentinel.py`** - CLI auditor
- `verify_ledger()`: Verifies all ledger entries for integrity
- Checks signatures, hashes, JSON validity
- Detects tampering, forged entries, modified entries
- Writes reports to `logs/reports/sentinel_report.json`

**`sentinel_app.py`** - FastAPI REST API
- `/verify`: Verify ledger integrity
- `/health`: Health check
- `/version`: API version
- `/reports`: List verification reports
- Runs independently from main AxProtocol kernel (read-only access)

**`verify_ledger.py`** - Ledger verification utilities
- `verify_payload()`: Verifies signature for a single entry
- `verify_hash_chain()`: Verifies hash chain integrity
- Used by both CLI and API

### 7. Utils (`axp/utils/`)

**`config_fingerprint.py`** - Config hash computation
- `compute_config_hash()`: Computes SHA256 hash of all config files
- Includes: governance_coupling.json, role_shapes.json, taes_weights.json, all directive markdown files
- Stored in every ledger entry for drift detection
- Format: `"sha256:{hex_digest}"`

**`llm.py`** - LLM interaction utilities
- Wraps OpenAI API calls
- Handles retries, error handling, token counting
- Used by role executor for LLM calls

**`logging.py`** - Logging configuration
- `configure_logging()`: Sets up Python logging
- Configures file handlers, formatters, log levels
- Logs to `logs/axp.log`, `logs/app_ui.log`, etc.

**`errors.py`** - Error handling utilities
- `write_sys_preview()`: Writes system prompt previews for debugging
- Error formatting and reporting

**`session_logging.py`** - Session logging
- `log_session()`: Writes session logs to `logs/sessions/`
- Includes all role outputs, TAES scores, metadata
- Used by Streamlit UI for session history

**`helpers.py`** - Shared helper functions
- `load_role_shapes()`: Loads role boundary enforcement config
- Various utility functions used across modules

**`sentinel.py`** - Sentinel integration utilities
- `sentinel_verify()`: Calls Sentinel API for verification
- Integration between kernel and Sentinel auditor

---

## Data Flow & Execution

### Complete Execution Flow

```
1. User Input
   └─> Objective: "Book 5 local jobs in 7 days"

2. Domain Detection
   └─> DomainDetector.detect(objective)
   └─> Returns: "marketing" (confidence: 0.85)

3. Config Hash Computation
   └─> compute_config_hash(base_dir)
   └─> Returns: "sha256:29de65ae94973957a7fc324..."

4. Role Loading
   └─> load_domain_roles("marketing", base_dir)
   └─> Loads: roles/marketing/{strategist,analyst,producer,courier,critic}.txt

5. Directive Loading
   └─> load_directives(base_dir)
   └─> Returns: {D0, CORE, AAL, TAES, RDL} markdown content

6. Governance Coupling Load
   └─> load_governance_coupling()
   └─> Returns: hard/soft signal definitions

7. Registry Initialization
   └─> init_registry()
   └─> Returns: {S: [], A: [], P: [], C: [], X: []}

8. Chain Execution (5 Roles)

   8.1. Strategist
       └─> system_for("Strategist", STRATEGIST_ROLE, directives)
       └─> run_role_json("Strategist", system_prompt, user_prompt, ...)
       └─> LLM call → JSON output → validate_S() → registry['S'].append(...)
       └─> evaluate_taes(strategist_output, domain="marketing")
       └─> apply_governance_coupling(strategist_output, taes_s, ...)
       └─> log_execution(session_id, "strategist", "generate_strategy", ...)
       └─> write_ledger_entry("Strategist", "evaluation", {...}, config_hash)

   8.2. Analyst
       └─> system_for("Analyst", ANALYST_ROLE, directives)
       └─> run_role_json("Analyst", system_prompt, user_prompt + S objects, ...)
       └─> LLM call → JSON output → validate_A() → registry['A'].append(...)
       └─> evaluate_taes(analyst_output, domain="marketing")
       └─> apply_governance_coupling(analyst_output, taes_a, ...)
       └─> log_execution(...)
       └─> write_ledger_entry(...)

   8.3. Producer
       └─> Similar flow with A objects as input
       └─> Produces P objects (assets, content, deliverables)
       └─> Producer-Courier handoff validation

   8.4. Courier
       └─> Similar flow with P objects as input
       └─> Produces C objects (schedule, deployment, operations)
       └─> Validates Producer assets

   8.5. Critic
       └─> Similar flow with all previous outputs
       └─> Produces X objects (findings, issues, fixes, severity)
       └─> Final quality audit

9. Composer Synthesis
   └─> compose_final_report(registry, taes_results, governance_signals)
   └─> Returns: Executive summary markdown

10. Results Assembly
    └─> {
        'strategist': {output, taes, scores},
        'analyst': {output, taes, scores},
        'producer_revised': {output, taes, scores},
        'courier_revised': {output, taes, scores},
        'critic': {output, taes, scores},
        'domain': 'marketing',
        'registry': {S, A, P, C, X},
        'composer': '...',
        'governance': {signals, soft_signals, no_go},
        'config_hash': 'sha256:...',
        'qa': {...}
    }

11. Sentinel Verification (Async)
    └─> sentinel_verify() or manual verification
    └─> Checks all ledger entries for tampering
    └─> Writes report to logs/reports/
```

### Registry Data Structure

The registry stores structured outputs from each role:

```python
registry = {
    'S': [  # Strategy Objects
        {
            's_id': 'S1',
            'title': 'Local SEO Campaign',
            'audience': 'Homeowners in zip codes 12345-12350',
            'hooks': ['Emergency tree removal', 'Free estimates'],
            'three_step_plan': ['Week 1: SEO optimization', 'Week 2: Google Ads', 'Week 3: Follow-up'],
            'acceptance_tests': ['5+ leads per day', '2+ booked jobs']
        },
        ...
    ],
    'A': [  # Analysis Objects
        {
            'a_id': 'A1',
            's_refs': ['S1'],
            'kpi_table': {'leads': 35, 'conversions': 10, 'booked': 5},
            'falsifications': ['Assumes 20% conversion rate'],
            'risks': ['Competition from established companies']
        },
        ...
    ],
    'P': [  # Production Assets
        {
            'p_id': 'P1',
            'a_refs': ['A1'],
            'spec_type': 'Google Ads Campaign',
            'body': 'Campaign setup details...'
        },
        ...
    ],
    'C': [  # Courier Schedule
        {
            'day': 'Monday',
            'time': '09:00',
            'channel': 'Google Ads',
            'p_id': 'P1',
            'kpi_target': '5 leads',
            'owner_action': 'Monitor ad performance'
        },
        ...
    ],
    'X': [  # Critic Findings
        {
            'x_id': 'X1',
            'refs': ['S1', 'A1'],
            'issue': 'Conversion rate assumption too optimistic',
            'fix': 'Use 15% instead of 20%',
            'severity': 'medium',
            'proof_scores': {'logical': 0.8, 'practical': 0.7}
        },
        ...
    ]
}
```

---

## Configuration System

### Core Configuration Files

**`config/governance_coupling.json`**
- Defines hard/soft governance signals
- Hard signals enforce TAES caps/floors
- Soft signals are logged but don't enforce limits
- Example:
```json
{
  "signals": {
    "D3": {"mode": "hard", "iv_max": 0.68, "ird_min": 0.55},
    "D2": {"mode": "hard", "iv_max": 0.64, "ird_min": 0.60},
    "D0": {"mode": "soft", "iv_max": 0.60, "ird_min": 0.70}
  }
}
```

**`config/role_shapes.json`**
- Defines banned phrases for each role (boundary enforcement)
- Prevents role confusion (e.g., Strategist shouldn't write code)
- Example:
```json
{
  "strategist": {
    "banned_phrases": ["def ", "function ", "class ", "import "]
  }
}
```

**`config/taes_weights.json`**
- Domain-specific TAES weight matrices
- Defines Logical/Practical/Probable weights per domain
- Example:
```json
{
  "marketing": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
  "technical": {"logical": 0.6, "practical": 0.35, "probable": 0.05}
}
```

**`DomainConfig.json`**
- Domain detection configuration
- Keywords, TAES weights, detection rules for each domain
- Used by DomainDetector for auto-detection

**`config/logging.yaml`**
- Python logging configuration
- Defines log levels, handlers, formatters

**`config/auth_settings.yaml`**
- Authentication settings (for future auth integration)

**`config/ui_presentation.json`**
- Streamlit UI presentation settings
- Controls table display, smart view, thresholds

### Config Hash System

Every ledger entry includes a `config_hash` (SHA256) of all protocol config files:

1. **Computed at session start**: `compute_config_hash(base_dir)`
2. **Stored in every ledger entry**: Proves config state at execution time
3. **Drift detection**: Compare config_hash between sessions to detect config changes
4. **Included files**:
   - `config/governance_coupling.json`
   - `config/role_shapes.json`
   - `config/taes_weights.json`
   - All directive markdown files in `protocol/`

**Usage:**
```python
from axp.utils.config_fingerprint import compute_config_hash

hash_val = compute_config_hash(Path("."))
# Returns: "sha256:29de65ae94973957a7fc324..."

# Compare with previous entry
entry = get_last_n_entries(1)[0]
if entry['config_hash'] != hash_val:
    print("⚠️ Config drift detected!")
```

---

## Governance & Directives

### Directive System

AxProtocol implements 29 directives (D0-D28) organized into layers:

**Layer 0: Change Control**
- **D0**: Change Control - How protocol evolves

**Layer 1: Core Behavioral Directives (D1-D14)**
- **D1**: Tone Mirroring - Match user style without sycophancy
- **D2**: No Assumption - Never guess intent silently
- **D3**: Flag Flawed Logic - Surface broken reasoning
- **D4**: Filter Transparency - Disclose censorship
- **D5**: No Psychological Triage - Don't infer emotional states
- **D6**: No Auto-Truncation - Full output by default
- **D7**: Contradiction Detection - Flag logic conflicts
- **D8**: Present Strongest Take - Truth over alignment
- **D9**: Default to Action - Move forward, then flag
- **D10**: Adaptive Foundation - Protocol can evolve
- **D11**: Conflict Hierarchy - Resolve directive conflicts
- **D12**: Exploratory Mode - Controlled speculation
- **D13**: Anti-Sycophancy - No flattery/mimicry
- **D14**: Counter-Mimicry - Watermark for authenticity

**Layer 2: Authority Assertion (D20-D24)**
- **D20**: Operator Supremacy - Single authority root
- **D21**: Autonomy Containment (CAM) - Time/quality-bounded leases
- **D22**: Immutable Audit Ledger - Unforgeable history
- **D23**: Deviation Killchain - Emergency brake
- **D24**: Authority Drift Monitor - Detect erosion

**Layer 3: Tri-Axis Evaluation (D25-D25c)**
- **D25**: TAES Core - Logical + Practical + Probable
- **D25a**: Adaptive Weighting - Domain-specific tuning
- **D25b**: Deviation Logging - Truth-reality gap tracking
- **D25c**: Operator Override Mode - Innovation bursts

**Layer 4: Red-Team Governance (D26-D28)**
- **D26**: Adversarial Falsification - Stress-test before approval
- **D27**: RDL Mechanics - How red-team runs
- **D28**: RDL Governance - Waivers and escalation

### Directive Implementation

Directives are loaded from markdown files in `protocol/`:
- `AxProtocol_v2.4_D0_CHANGE_CONTROL.md`
- `AxProtocol_v2.4_CORE_DIRECTIVES.md`
- `AxProtocol_v2.4_AUTHORITY_LAYER.md`
- `AxProtocol_v2.4_TAES_EVALUATION.md`
- `AxProtocol_v2.4_REDTEAM_LAYER.md`
- `AxProtocol_v2.4_WARROOM_ADDENDUM.md`

**System Prompt Composition:**
- All roles get directive briefings (one-line summaries)
- Analyst gets full TAES directives (D25-25c) for probability evaluation
- Critic gets full RDL directives (D26-28) for falsification protocol
- This ensures efficiency (briefings) AND deep protocol access (full directives) when needed

### Governance Coupling

Governance coupling applies TAES limits based on detected signals:

**Hard Signals** (enforce limits):
- D2, D3, D7, D11, D13, D20-24
- Example: If D3 (Flawed Logic) detected → `iv_max: 0.68, ird_min: 0.55`

**Soft Signals** (logged only):
- D0, SECRETS, FABRICATION, DOMAIN_MISROUTING, OBSERVABILITY_GAP
- Logged but don't enforce TAES caps/floors

**Implementation:**
```python
from axp.governance.coupling import apply_governance_coupling

taes_result = evaluate_taes(output, domain="marketing")
taes_result = apply_governance_coupling(
    output, taes_result, gov_signals, objective, soft_signals, cfg=gov_coupling
)
# Returns modified TAES with caps/floors applied
```

---

## TAES Evaluation System

### What is TAES?

**TAES** = **T**ruth/**A**lignment/**E**fficiency/**S**ignal

A tri-axis evaluation system that scores outputs on three dimensions:

1. **Logical** (0-100): Correctness, consistency, evidence quality, logical coherence
2. **Practical** (0-100): Feasibility, resource requirements, timeline realism, implementation clarity
3. **Probable** (0-100): Realistic human behavior, adoption likelihood, psychological plausibility

### TAES Calculation

**Step 1: Get Domain Weights**
```python
weights = TAES_WEIGHTS[domain]
# Example: marketing → {logical: 0.3, practical: 0.2, probable: 0.5}
```

**Step 2: Score Output**
- LLM evaluates output on Logical/Practical/Probable (0-100 each)
- Returns JSON: `{"logical": 85, "practical": 70, "probable": 90}`

**Step 3: Calculate Integrity Vector (IV)**
```python
IV = (logical * weights['logical']) + (practical * weights['practical']) + (probable * weights['probable'])
# Example: (85 * 0.3) + (70 * 0.2) + (90 * 0.5) = 84.5
```

**Step 4: Calculate Ideal-Reality Disparity (IRD)**
```python
IRD = abs(logical - probable) / 100
# Measures gap between "what should happen" (logical) and "what will happen" (probable)
# Example: abs(85 - 90) / 100 = 0.05 (low disparity = good)
```

**Step 5: Determine RRP Requirement**
```python
requires_rrp = IRD > 0.5
# If IRD > 0.5, Reality Reconciliation Pass required
```

### Domain-Specific Weights

Each domain has different TAES weights based on its nature:

| Domain | Logical | Practical | Probable | Use Case |
|--------|---------|-----------|----------|----------|
| Marketing | 0.3 | 0.2 | 0.5 | Campaigns, lead gen |
| Technical | 0.6 | 0.35 | 0.05 | Code, architecture |
| Ops | 0.4 | 0.45 | 0.15 | Workflows, processes |
| Creative | 0.35 | 0.25 | 0.4 | Content creation |
| Education | 0.45 | 0.35 | 0.2 | Curriculum, training |
| Product | 0.4 | 0.4 | 0.2 | Product dev, features |
| Strategy | 0.45 | 0.35 | 0.2 | Business strategy |
| Research | 0.55 | 0.3 | 0.15 | Data analysis |
| Finance | 0.5 | 0.35 | 0.15 | Financial modeling |

**Rationale:**
- **Technical/Research**: High logical weight (correctness matters most)
- **Marketing/Creative**: High probable weight (human behavior matters most)
- **Ops/Product**: Balanced practical weight (feasibility matters)

### TAES Output Structure

```python
taes_result = {
    'logical': 85,
    'practical': 70,
    'probable': 90,
    'integrity_vector': 84.5,
    'ird': 0.05,
    'requires_rrp': False,
    'domain': 'marketing',
    'role_name': 'Strategist',
    'session_id': '20251127_120000',
    'config_hash': 'sha256:...'
}
```

### IRD Logging

All IRD values are logged to `logs/ird_log.csv` for trend analysis:
- Timestamp, domain, role, IRD value
- Used by Streamlit UI for analytics dashboard

---

## Ledger & Sentinel

### Ledger System

**Purpose**: Immutable, cryptographically signed audit trail

**Implementation**:
- **Format**: JSONL files (`logs/ledger/{YYYYMMDD}.jsonl`)
- **Signing**: Ed25519 signatures (PyNaCl) with HMAC fallback
- **Structure**: Each line is `{"entry": {...}, "sig": "hex_signature"}`

**Entry Structure**:
```json
{
  "entry": {
    "timestamp": "2025-11-27T12:00:00Z",
    "role": "Strategist",
    "action": "evaluation",
    "hash": "sha256_hash_of_data",
    "data": {
      "output": "...",
      "taes": {...},
      "session_id": "..."
    },
    "config_hash": "sha256:..."
  },
  "sig": "ed25519_signature_hex"
}
```

**Key Features**:
- **Append-only**: Entries cannot be modified (hash chain prevents tampering)
- **Cryptographic signing**: Ed25519 signatures prove authenticity
- **Config hash**: Every entry includes config fingerprint for drift detection
- **Hash chain**: Each entry links to previous via hash

**Ledger Operations**:
```python
from axp.governance.ledger import write_ledger_entry, verify_hash_chain

# Write entry
hash_val = write_ledger_entry(
    role="Strategist",
    action="evaluation",
    data={"output": "...", "taes": {...}},
    config_hash="sha256:..."
)

# Verify integrity
integrity = verify_hash_chain()
# Returns: {"valid": True/False, "entries": N, "broken": [...]}
```

### Sentinel Auditor

**Purpose**: Independent verification of ledger integrity

**Architecture**:
- **Detached**: Runs independently from main kernel (read-only access)
- **FastAPI API**: REST endpoints for verification
- **CLI Tool**: Command-line verification utility
- **Reports**: Writes timestamped reports to `logs/reports/`

**Sentinel Operations**:

1. **Signature Verification**: Verifies Ed25519 signatures on all entries
2. **Hash Verification**: Verifies data hashes match content
3. **Hash Chain Verification**: Verifies hash chain integrity
4. **Tampering Detection**: Detects forged/modified entries
5. **Config Drift Detection**: Compares config_hash across entries

**API Endpoints** (`sentinel_api.py`):
- `POST /run`: Execute AxProtocol chain (proxy to kernel)
- `GET /verify`: Verify ledger integrity
- `GET /health`: Health check
- `GET /version`: API version
- `GET /domains`: List available domains
- `GET /docs`: Interactive API documentation (Swagger UI)

**CLI Usage**:
```bash
python -m axp.sentinel.sentinel
# Verifies ledger and writes report to logs/reports/sentinel_report.json
```

**Report Structure**:
```json
{
  "verified": true,
  "timestamp": "2025-11-27T12:00:00Z",
  "entries_checked": 150,
  "entries_valid": 150,
  "entries_invalid": 0,
  "tampering_detected": false,
  "config_drift": false,
  "details": []
}
```

---

## Domain System

### Domain Detection

**Purpose**: Automatically detect appropriate domain from objective text

**Implementation**: `DomainDetector` class in `domain_detector.py`

**Algorithm**:
1. **Keyword Matching**: Score objective against domain keywords
2. **Weighted Scoring**: Keywords have weights (strong/weak matches)
3. **Confidence Calculation**: Normalize scores to 0.0-1.0
4. **Selection**: Choose highest confidence domain (or fallback if below threshold)

**Example**:
```python
from domain_detector import DomainDetector

detector = DomainDetector()
domain = detector.detect("Book 5 local jobs in 7 days")
# Returns: "marketing" (confidence: 0.85)

scores = detector.score_all_domains("Book 5 local jobs")
# Returns: {"marketing": 0.85, "ops": 0.15, "technical": 0.05, ...}
```

### Domain Configuration

**File**: `DomainConfig.json`

**Structure**:
```json
{
  "domains": {
    "marketing": {
      "name": "Marketing & Growth",
      "description": "Campaign creation, lead generation",
      "taes_weights": {"logical": 0.3, "practical": 0.2, "probable": 0.5},
      "keywords": ["campaign", "marketing", "leads", "ads", ...]
    },
    ...
  },
  "detection_rules": {
    "confidence_threshold": 0.4,
    "fallback_domain": "strategy",
    "multi_domain_handling": "highest_confidence"
  }
}
```

### Domain-Specific Roles

Each domain has custom role definitions in `roles/{domain}/`:
- `strategist.txt`: Domain-specific strategist role
- `analyst.txt`: Domain-specific analyst role
- `producer.txt`: Domain-specific producer role
- `courier.txt`: Domain-specific courier role
- `critic.txt`: Domain-specific critic role

**Example**: `roles/finance/strategist.txt` focuses on financial modeling, risk analysis, regulatory compliance, while `roles/marketing/strategist.txt` focuses on campaigns, audience, messaging.

**Fallback**: If domain-specific role not found, falls back to default role in `roles/{role}.txt`

### Supported Domains

1. **Marketing**: Campaigns, lead gen, content marketing
2. **Technical**: Code, architecture, systems
3. **Ops**: Workflows, processes, efficiency
4. **Creative**: Content creation, storytelling
5. **Education**: Curriculum, training, learning
6. **Product**: Product dev, features, roadmap
7. **Strategy**: Business strategy, planning
8. **Research**: Data analysis, research design
9. **Finance**: Financial modeling, risk analysis

---

## Testing & Validation

### Test Suites

**Location**: `verify/` directory

**Test Files**:
- `test_directive_enforcement_core.py`: Tests D1-D14 enforcement
- `test_taes_adherence.py`: Tests TAES scoring accuracy
- `test_config_hash.py`: Tests config hash computation and drift detection
- `test_fault_injection_pytest.py`: Pytest-based fault injection tests
- `test_fault_injection_delta4.py`: Δ4 tests (ledger tampering detection)

### Fault Injection Tests (Δ1-Δ4)

**Δ1: Malformed Objectives**
- Empty objectives
- Nonsensical inputs
- Contradictory requirements
- Tests system resilience to bad inputs

**Δ2: Score Manipulation**
- Invalid TAES scores
- Missing dimensions
- Out-of-range values
- Tests score validation

**Δ3: Protocol Bypass Attempts**
- Directive violations
- Unauthorized changes
- Authority drift
- Tests governance enforcement

**Δ4: Ledger Tampering**
- Forged entries
- Modified entries
- Signature validation
- Tests Sentinel detection

**Running Tests**:
```bash
# All tests
pytest verify/ -v

# Specific suite
pytest verify/test_fault_injection_delta4.py -v

# Fault injection
python fault_injection.py --run Δ1,Δ2,Δ3,Δ4
```

### Validation System

**Role Output Validation**:
- Each role output is validated against JSON schema
- Validators check required fields, types, references
- Invalid outputs trigger retries or errors

**Score Validation**:
- TAES scores validated for range (0-100)
- Missing dimensions detected
- Score manipulation attempts caught

**Ledger Validation**:
- Signature verification on every entry
- Hash verification on data integrity
- Hash chain verification for tampering detection

---

## Deployment Architecture

### Docker Compose Setup

**Services**:
1. **AxProtocol** (Streamlit UI): Port 8443
2. **Sentinel** (FastAPI API): Port 443
3. **Traefik**: Reverse proxy with TLS (ACME)

**Configuration**: `docker-compose.yml`

**Dockerfiles**:
- `Dockerfile.axp`: AxProtocol kernel + Streamlit UI
- `Dockerfile.sentinel`: Sentinel auditor (FastAPI)

### Production Checklist

- [ ] Set `OPENAI_API_KEY` in `.env`
- [ ] Configure `TIER` (DEV/PREP/CLIENT)
- [ ] Set up ACME domains in Traefik
- [ ] Configure rate limiting
- [ ] Set up logging rotation
- [ ] Configure Sentinel public key path
- [ ] Run smoke tests: `./scripts/smoke.sh`

### Deployment Options

**1. PyPI Package** (`axprotocol`)
```bash
pip install axprotocol
pip install axprotocol[api]  # With FastAPI
pip install axprotocol[ui]   # With Streamlit
```

**2. Docker Compose**
```bash
docker compose build
docker compose up -d
```

**3. Source Installation**
```bash
git clone https://github.com/yourusername/axprotocol.git
cd AxProtocol
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Environment Variables

**Required**:
- `OPENAI_API_KEY`: OpenAI API key for LLM calls

**Optional**:
- `TIER`: Environment tier (DEV/PREP/CLIENT)
- `LOG_LEVEL`: Logging level (INFO/DEBUG/WARNING)
- `AXP_LEDGER_DIR`: Ledger directory path (default: `logs/ledger`)
- `TAES_WEIGHTS_PATH`: Custom TAES weights file path

---

## File Structure & Organization

### Root Directory

```
AxProtocol/
├── axprotocol/              # Public API package (PyPI)
│   └── __init__.py          # Exports: run_chain, compute_config_hash
├── axp/                     # Internal package (modular)
│   ├── orchestration/       # Chain execution
│   ├── detection/           # Governance signal detection
│   ├── validation/          # Schema validators
│   ├── directives/          # Directive loading/composition
│   ├── governance/          # Ledger signing, coupling
│   ├── sentinel/            # Sentinel auditor
│   └── utils/               # Shared utilities
├── config/                  # Configuration files
│   ├── governance_coupling.json
│   ├── role_shapes.json
│   ├── taes_weights.json
│   ├── logging.yaml
│   ├── auth_settings.yaml
│   ├── ui_presentation.json
│   └── role_examples/       # Example role outputs
├── protocol/                # Directive markdown files
│   ├── AxProtocol_v2.4_CORE_DIRECTIVES.md
│   ├── AxProtocol_v2.4_TAES_EVALUATION.md
│   ├── AxProtocol_v2.4_AUTHORITY_LAYER.md
│   ├── AxProtocol_v2.4_REDTEAM_LAYER.md
│   ├── AxProtocol_v2.4_D0_CHANGE_CONTROL.md
│   └── AxProtocol_v2.4_WARROOM_ADDENDUM.md
├── roles/                   # Domain-specific role definitions
│   ├── marketing/
│   ├── technical/
│   ├── ops/
│   ├── creative/
│   ├── education/
│   ├── product/
│   ├── strategy/
│   ├── research/
│   └── finance/
├── verify/                  # Test suites
│   ├── test_directive_enforcement_core.py
│   ├── test_taes_adherence.py
│   ├── test_config_hash.py
│   ├── test_fault_injection_delta4.py
│   └── conftest.py
├── logs/                    # Runtime logs and data
│   ├── ledger/              # Ledger entries (JSONL)
│   ├── sessions/            # Session logs
│   ├── reports/              # Sentinel reports
│   ├── exports/              # Exported results
│   ├── axp.log               # Main application log
│   └── app_ui.log            # Streamlit UI log
├── scripts/                  # Utility scripts
│   ├── smoke.sh
│   ├── validate_governance_config.py
│   └── validate_taes_weights.py
├── app_axp.py               # Streamlit operator console
├── run_axp.py               # CLI entry point
├── sentinel_api.py          # FastAPI REST API
├── taes_evaluation.py       # TAES scoring engine
├── domain_detector.py       # Domain auto-detection
├── ledger.py                # Legacy ledger (SQLite, deprecated)
├── pyproject.toml           # PyPI package metadata
├── requirements.txt          # Python dependencies
├── docker-compose.yml       # Docker orchestration
├── Dockerfile.axp           # AxProtocol Docker image
├── Dockerfile.sentinel      # Sentinel Docker image
├── DomainConfig.json        # Domain detection config
└── README.md                # User-facing README
```

### Key Files Explained

**`app_axp.py`**: Streamlit operator console (v2.5)
- Domain detection UI
- Chain execution interface
- TAES visualization
- Session history browser
- Analytics dashboard
- Export capabilities

**`run_axp.py`**: CLI entry point
- Command-line chain execution
- Domain override support
- Smoke governance test mode
- Legacy compatibility

**`sentinel_api.py`**: FastAPI REST API
- `/run`: Execute chain
- `/verify`: Verify ledger
- `/health`: Health check
- `/domains`: List domains
- `/docs`: Swagger UI

**`taes_evaluation.py`**: TAES scoring engine
- `evaluate_taes()`: Main scoring function
- Domain-specific weight loading
- IRD calculation
- RRP requirement determination
- IRD logging to CSV

**`domain_detector.py`**: Domain auto-detection
- `DomainDetector` class
- Keyword matching algorithm
- Confidence scoring
- Fallback handling

**`ledger.py`**: Legacy SQLite ledger (deprecated)
- Still used for some compatibility
- New code should use `axp/governance/ledger.py`

---

## Key Design Decisions

### 1. Modular Architecture

**Decision**: Refactor into `axp/` subpackages (v2.5)

**Rationale**:
- Better code organization
- Easier maintenance
- Clear separation of concerns
- Enables PyPI packaging

**Impact**: Cleaner imports, better testability, easier to extend

### 2. Config Hash System

**Decision**: Store SHA256 hash of all config files in every ledger entry

**Rationale**:
- Detect config drift between sessions
- Prove config state at execution time
- Audit trail for configuration changes

**Impact**: Enables config change auditing, prevents silent drift

### 3. Domain-Specific Roles

**Decision**: Each domain has custom role definitions

**Rationale**:
- Domain expertise matters
- Finance needs different approach than marketing
- Better quality outputs per domain

**Impact**: Higher quality outputs, domain-specific expertise

### 4. Ed25519 Signing with HMAC Fallback

**Decision**: Use Ed25519 (PyNaCl) with HMAC fallback

**Rationale**:
- Ed25519: Strong cryptographic security
- HMAC fallback: Works if PyNaCl unavailable
- Production-ready error handling

**Impact**: Cryptographic integrity with graceful degradation

### 5. Detached Sentinel Auditor

**Decision**: Sentinel runs independently (read-only access)

**Rationale**:
- Independent verification
- Can't be compromised by kernel
- Separate deployment possible

**Impact**: True independent audit, tampering detection

### 6. Registry System

**Decision**: Structured data registry (S, A, P, C, X objects)

**Rationale**:
- Enables inter-role communication
- Structured outputs easier to validate
- Composer can synthesize final report

**Impact**: Better role coordination, structured outputs

### 7. TAES Domain Weights

**Decision**: Domain-specific TAES weight matrices

**Rationale**:
- Technical work needs high logical weight
- Marketing needs high probable weight
- One-size-fits-all doesn't work

**Impact**: More accurate evaluation per domain

### 8. Governance Coupling

**Decision**: Hard/soft signal enforcement with TAES caps/floors

**Rationale**:
- Some violations are critical (hard)
- Others are warnings (soft)
- TAES limits prevent bad outputs

**Impact**: Enforced governance, prevents quality degradation

---

## API & Interfaces

### Python Library API

**Main Entry Point**:
```python
from axprotocol import run_chain

strategist, analyst, producer, courier, critic, results = run_chain(
    objective="Book 5 local jobs in 7 days",
    domain="marketing"  # Optional, auto-detected if not provided
)
```

**Config Hash**:
```python
from axprotocol import compute_config_hash

hash_val = compute_config_hash(Path("."))
```

### FastAPI REST API

**Endpoints**:
- `POST /run`: Execute chain
  ```json
  {
    "objective": "Book 5 local jobs",
    "domain": "marketing",
    "session_id": "optional-id"
  }
  ```
- `GET /verify`: Verify ledger integrity
- `GET /health`: Health check
- `GET /version`: API version
- `GET /domains`: List available domains
- `GET /docs`: Interactive API documentation

### Streamlit UI

**Features**:
- Objective input with domain override
- Real-time domain detection preview
- Chain execution with progress
- TAES score visualization
- Ledger entry browser
- Session history
- Analytics dashboard (IRD trends)
- Export capabilities (JSON, Markdown, CSV)

### CLI Interface

**Usage**:
```bash
# Default objective
python run_axp.py

# Custom objective
python run_axp.py "Book 5 local jobs in 7 days"

# Domain override
python run_axp.py "Model ROI" finance

# Smoke governance test (no LLM, no ledger writes)
python run_axp.py --smoke-governance
```

---

## Future Considerations

### Planned Enhancements

1. **Vector Database Integration**
   - Milvus integration for semantic search
   - Role output embedding and retrieval
   - Historical context retrieval

2. **Enhanced Authentication**
   - JWT token-based auth
   - Session management
   - User roles and permissions

3. **Advanced Analytics**
   - IRD trend analysis
   - Domain performance metrics
   - Governance compliance dashboards

4. **Multi-Agent Coordination**
   - Parallel role execution
   - Agent-to-agent communication
   - Consensus mechanisms

5. **Custom Domain Support**
   - User-defined domains
   - Custom role definitions
   - Domain-specific TAES weights

6. **Enhanced Sentinel**
   - Real-time monitoring
   - Alert system
   - Automated reporting

### Technical Debt

1. **Legacy Ledger**: `ledger.py` (SQLite) still exists for compatibility
2. **Error Handling**: Some modules need better error recovery
3. **Performance**: LLM calls are sequential (could be parallelized)
4. **Testing**: More integration tests needed
5. **Documentation**: Some modules need better docstrings

### Scalability Considerations

1. **Ledger Size**: JSONL files grow linearly (consider rotation/archival)
2. **Config Hash**: Computing hash on every session (could cache)
3. **Domain Detection**: Keyword matching could be ML-based
4. **TAES Evaluation**: LLM calls are expensive (could batch or cache)

---

## Conclusion

AxProtocol v2.7 is a production-ready, self-auditing AI reasoning kernel with comprehensive governance, truth evaluation, and cryptographic audit trails. The system's modular architecture, domain-specific roles, TAES evaluation, and Sentinel auditor work together to ensure high-quality, auditable AI reasoning outputs.

**Key Strengths**:
- ✅ Comprehensive governance (29 directives)
- ✅ Domain-specific expertise (9 domains)
- ✅ Cryptographic audit trail (Ed25519 signing)
- ✅ Independent verification (Sentinel auditor)
- ✅ Config drift detection (SHA256 hashing)
- ✅ Production-ready (Docker, PyPI, FastAPI, Streamlit)

**Philosophy**: Truth > Obedience. Signed. Sentineled. Config-driven.

---

**Document Version**: 1.0
**Last Updated**: November 2025
**Maintained By**: AxProtocol Core Team

