# BOAT RACE EDGE — Quant / Architecture / QA Audit

Date: 2026-09-10
Reviewer: Senior Quant Engineer / Software Architect / QA

## Executive Verdict
**Status: NOT READY FOR RESEARCH RESULTS**

The repository currently contains project documentation only; there is no implemented data pipeline, database schema, model, backtest engine, frontend, test suite, or CI to validate. Therefore no claim of predictive performance, EV, ROI, or data integrity can currently be trusted.

## Scope Correction
The requested DLMM checks are not applicable to BOAT RACE EDGE. Active Bin, Position Range, X/Y amounts, Fee X/Y, token decimals, token USD price, Position MTM, IL, Fee PnL, Claim/Reset and pool-volume-derived fees belong to DeFi liquidity-position accounting and must not be introduced here.

For BOAT RACE EDGE, enforce separation of race, entry, bet combination, odds observation, ticket stake, result, payout, refund/返還 and bankroll ledger.

## Findings

### CRITICAL

#### C-001 — No point-in-time data implementation
Severity: CRITICAL
The specification requires point-in-time integrity, but no schema or ingestion implementation exists. Every observation needs source timestamp, ingestion timestamp, effective timestamp where applicable, race identifier and source/version information. Historical reconstruction must reproduce what was knowable at the prediction cutoff.

#### C-002 — No protection against look-ahead leakage
Severity: CRITICAL
No executable feature-generation or backtest code exists. Enforce feature effective time <= feature cutoff and odds observed time <= odds cutoff. Add tests containing intentionally leaked rows that must be rejected.

#### C-003 — No historical odds reconstruction
Severity: CRITICAL
EV research requires the odds actually observable when the signal was generated. Final or later odds cannot be substituted. Store race_id, bet combination, observed_at, odds, source, ingestion_at and validity/status.

#### C-004 — No immutable prediction audit trail
Severity: CRITICAL
Without immutable prediction records, model changes can silently alter historical results. Persist race_id, generated_at, feature_cutoff_at, odds_cutoff_at, model_version, feature_version and data_version.

### HIGH

#### H-001 — Cost model is underspecified
Severity: HIGH
Separate stake, payout, refund and net P/L. Never estimate ticket-level cost from aggregate pool volume and never double-count market takeout.

#### H-002 — Refund / 返還 handling is not implemented
Severity: HIGH
A refund is not profit. Settlement states must include WIN, LOSS, REFUND, VOID/invalid and UNKNOWN/unresolved. A refunded stake has zero net P/L.

#### H-003 — Calibration gate is not implemented
Severity: HIGH
Probability quality must be evaluated independently from ROI using Brier score, log loss and reliability/calibration analysis. A 30% prediction should behave approximately like a 30% event over adequate out-of-sample samples.

#### H-004 — Walk-forward engine is not implemented
Severity: HIGH
Random train/test splitting is prohibited for the production research path. Use chronological train/validation/test, walk-forward windows and a frozen final holdout.

#### H-005 — Selection bias controls are absent
Severity: HIGH
Because the product selects only high-EV opportunities, preserve all candidate bets, selected signals and rejection reasons. Do not keep only selected predictions.

#### H-006 — Baseline model is absent
Severity: HIGH
Build the simplest defensible probability baseline before adding complex ML. Later models must beat it on untouched out-of-sample data.

### MEDIUM

#### M-001 — Schema uniqueness constraints undefined
Race IDs, entry IDs, odds snapshots, predictions and settlements need explicit uniqueness constraints.

#### M-002 — Data-quality states undefined
Missing, stale, contradictory and corrected source records need explicit statuses.

#### M-003 — Duplicate/dead-code/ambiguous-state review is not yet possible
There is no application code yet. Keep ingestion, features, model, odds, EV, decision and presentation as separate concerns.

#### M-004 — Test coverage is currently zero
This is expected at an empty-repository stage, but no research phase is complete without automated tests.

### LOW

#### L-001 — Domain terminology needs canonical definitions
Define odds, payout, stake, refund, closing odds, signal time and settlement time in one domain document.

#### L-002 — Backtest, paper and live performance must remain separate
Never present them as one headline performance number.

## Research Integrity Checklist

| Risk | Status | Gate |
|---|---|---|
| Look-ahead bias | NOT IMPLEMENTED | Block |
| Data leakage | NOT IMPLEMENTED | Block |
| Repainting | Live pipeline not implemented | Block live |
| Survivorship bias | NOT VERIFIED | Block research |
| Selection bias | NOT IMPLEMENTED | Block EV claims |
| Overfitting | NOT IMPLEMENTED | Block model selection |
| IS/OOS contamination | NOT IMPLEMENTED | Block final evaluation |
| Calibration | NOT IMPLEMENTED | Block signal claims |
| Historical odds integrity | NOT IMPLEMENTED | Block EV claims |
| Refund handling | NOT IMPLEMENTED | Block P/L claims |
| Auditability | NOT IMPLEMENTED | Block production |

## Canonical BOAT RACE Accounting
`Race → Entry → Bet Combination → Odds Snapshot → Signal → Ticket → Settlement`

Settlement:
- WIN → payout
- LOSS → zero payout
- REFUND → stake returned, net P/L = 0
- VOID/UNKNOWN → excluded from finalized performance

Never infer ticket-level P/L from aggregate race pool statistics.

## QA Gates

Before Phase 1: duplicate race ingestion, duplicate odds snapshot, timestamp ordering, stale odds rejection, missing-field validation, refund, payout reconciliation, timezone, source consistency and point-in-time reconstruction tests.

Before Phase 2: leakage fixture, future-row exclusion, feature-cutoff, deterministic feature generation and probability-sum invariant tests.

Before Phase 4: chronological split, walk-forward boundary, frozen holdout, model-version reproducibility and no-training-on-test tests.

Before production: duplicate signal prevention, stale-data fail-closed behavior, prediction audit persistence, result reconciliation and paper/live metric separation.

## Phase Gate Decision
**Current phase: Phase 0 — Foundation**
**Phase 0: IN PROGRESS**
Do not advance to probability modeling until the data and audit architecture exists.

## Next Implementation Priority
1. Application structure.
2. Canonical domain schema.
3. Point-in-time data model.
4. Ingestion validation.
5. Odds snapshot storage.
6. Settlement/refund accounting.
7. Phase 1 QA suite.
8. Baseline probability model only after the above passes.