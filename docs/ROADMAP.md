# BOAT RACE EDGE — Roadmap

## North Star

**高勝率ではなく、コスト控除後に長期的な正の期待値が確認できる買い目だけを厳選配信する。**

### 最終ゴール

- 全開催場・全レースを自動収集
- 出走表、選手、モーター、ボート、展示・直前情報、気象、水面、オッズ、結果を時系列で保存
- レース開始前情報だけから勝率を推定
- 2連系 / 3連系などの各買い目の確率を推定
- 現在オッズから期待値を計算
- オッズ変動と予測誤差を考慮した安全マージンを適用
- 条件を満たす買い目だけ配信
- すべての予想を後から検証可能にする
- 実運用では「見送り」を第一級の結果として扱う

## Progress Audit — 2026-09-10

| Area | Status | Assessment |
|---|---|---|
| Foundation implementation | COMPLETE | Sufficient for the foundation gate |
| Foundation verification | COMPLETE | GitHub Actions passed pytest and PostgreSQL migration validation |
| Historical data engine | COMPLETE | Real official-source vertical slice passed end-to-end in CI |
| Probability model | **IN PROGRESS** | PIT-safe lane baseline, dataset assembly, temporal split, calibration metrics, official daily LZH bulk acquisition, and batch persistence are implemented; the 10,000-race / 90-day research-volume gate is being verified in CI |
| EV engine | BLOCKED | Must wait for valid probabilities + timestamped odds |
| Walk-forward research | BLOCKED | Must wait for PIT dataset/model |
| Signal selection | BLOCKED | Must wait for OOS evidence |
| Live prediction | BLOCKED | Must wait for paper-ready research |
| Web prediction UI | NOT STARTED | Intentionally deferred |

### Phase 0 Completion Evidence

GitHub Actions run #19 completed successfully on commit `6bf099daf152b7baa4125af53e8794b3d1284d37`. The job completed with `success`; pytest and the PostgreSQL migration validation step both completed successfully.

### Loop / Duplication Audit

The latest 20 commits were overwhelmingly Phase 0 work. That process churn has now stopped. The foundation is frozen. **Do not add infrastructure unless it directly unblocks a failing gate or the active phase.**

## Phase 1 — Historical Data Engine — COMPLETE

### Completion evidence

GitHub Actions run #46 completed successfully on commit `926c6001d6719fcf6eac931d2421382bf9d8dd30`. The run passed 14 tests, all three PostgreSQL migrations, a real official-source ingestion of `20260226 / venue 04 / race 1`, and database verification.

The smoke test fetched and stored three official documents, normalized six entries and one official result, and explicitly classified the official 3T odds response as `INCOMPLETE_SOURCE_RESPONSE`; zero partial odds rows were promoted. This is intentional data-integrity behavior, not a missing-value imputation.

### Important data-integrity decisions

The official 3T page labels the displayed values as **締切時オッズ** and the fetched HTTP response did not expose a complete 120-combination matrix in CI. The ingestion layer therefore retains the raw odds document, marks coverage as incomplete, and refuses to normalize partial odds. It also does not fabricate an observation timestamp. This prevents a truncated or non-point-in-time market snapshot from contaminating model research.

## Phase 2 — Baseline Probability Model — IN PROGRESS

### Scope

Only point-in-time-safe feature preparation, a transparent baseline probability estimator, deterministic evaluation, and tests. No EV calculation, signal selection, web UI, live prediction, paper trading, or unrelated infrastructure.

### Completion gate

Phase 2 becomes COMPLETE only when all are true:

1. A reproducible training dataset can be assembled from sufficient historical normalized races using only information valid at the prediction cutoff.
2. The baseline probability model produces valid probabilities for the six lanes and a documented model version.
3. No odds, payouts, race results, or other post-cutoff information is accepted as a model feature.
4. Probability quality is measured with at least log loss, Brier score, and calibration bins on a temporally held-out dataset.
5. The holdout evaluation is separated from training data and its provenance is recorded.
6. Tests cover dataset integrity, probability bounds/normalization, deterministic outputs, and rejection of malformed training rows.
7. The historical dataset is large enough that the evaluation is not based on the single CI smoke-test race. For this gate, the operational minimum is **10,000 complete races spanning at least 90 calendar days, with at least 1,000 races in both train and holdout periods**. This threshold is a research-quality floor, not a claim that the resulting baseline is production-ready.

### Current Phase 2 implementation

- Transparent empirical lane-frequency baseline (`lane-frequency-v1`).
- Explicit six-lane / one-winner training-row validation.
- PIT-safe loader from normalized `race`, `entry`, and `race_result` tables using `scheduled_deadline_at` as the feature cutoff.
- Deterministic chronological whole-race holdout split.
- Reproducible baseline holdout evaluation with model version and train/holdout temporal provenance.
- Deterministic binary log-loss and Brier-score evaluation.
- Calibration-bin calculation.
- Tests for model invariants, malformed rows, temporal separation, deterministic evaluation, probability bounds, and calibration metrics.
- Official-source bulk outcome collector using the daily B/K LZH archives: two official downloads per day instead of per-race HTML acquisition, Shift-JIS decoding, venue/race boundary validation, complete six-lane program validation, and official result/payout extraction.
- Batch persistence in one PostgreSQL transaction per venue/day; incomplete or absent races are skipped rather than inferred.
- Batch CLI supports inclusive date ranges, official venues 01–24, race ranges 1–12, and the archive source explicitly.

### Current blocker

The previous CI proof covered 36 real races across three dates. The repository now has a dedicated official daily-archive acquisition path and CI gate for the required **10,000 complete races across 90+ calendar days with at least 1,000 train and 1,000 holdout races**. Phase 2 remains IN PROGRESS until that real-data CI evaluation passes. No synthetic rows are used in the production ingestion/evaluation path.

## Phase Progress

| Phase | Status | Gate |
|---|---|---|
| Phase 0 — Foundation | **COMPLETE** | Tests + PostgreSQL migration passed in CI |
| Phase 1 — Historical Data Engine | **COMPLETE** | Official-source vertical slice + raw immutability + explicit odds coverage + CI smoke test passed |
| Phase 2 — Baseline Probability Model | **IN PROGRESS** | PIT-safe dataset + baseline + metrics + temporal evaluation + official archive bulk collector implemented; CI must prove 10,000 real races across 90+ days |
| Phase 3 — Market / EV Engine | BLOCKED | Valid PIT odds + settlement model |
| Phase 4 — Backtest / Walk-Forward | BLOCKED | Point-in-time + OOS integrity |
| Phase 5 — Signal Selection | BLOCKED | Positive OOS evidence |
| Phase 6 — Live Data / Prediction | BLOCKED | Paper pipeline ready |
| Phase 7 — Web App | NOT STARTED | Prediction engine available |
| Phase 8 — Paper Trading | BLOCKED | Live pipeline ready |
| Phase 9 — Production | BLOCKED | Paper trading evidence |

**Current phase: Phase 2 — Baseline Probability Model.**
