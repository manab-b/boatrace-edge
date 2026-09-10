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
| Historical data engine | **IN PROGRESS** | Real official-source vertical slice implemented; current gate is live ingestion verification |
| Probability model | BLOCKED | Must wait for historical PIT dataset |
| EV engine | BLOCKED | Must wait for valid probabilities + timestamped odds |
| Walk-forward research | BLOCKED | Must wait for PIT dataset/model |
| Signal selection | BLOCKED | Must wait for OOS evidence |
| Live prediction | BLOCKED | Must wait for paper-ready research |
| Web prediction UI | NOT STARTED | Intentionally deferred |

### Phase 0 Completion Evidence

GitHub Actions run #19 completed successfully on commit `6bf099daf152b7baa4125af53e8794b3d1284d37`. The job completed with `success`; pytest and the PostgreSQL migration validation step both completed successfully.

### Loop / Duplication Audit

The latest 20 commits were overwhelmingly Phase 0 work. That process churn has now stopped. The foundation is frozen. **Do not add infrastructure unless it directly unblocks a failing gate or the active phase.**

## Phase 1 — Historical Data Engine

### Scope

Only real historical acquisition, immutable raw storage, normalization, timestamp/PIT integrity, and tests. No prediction, EV, signal selection, live trading, or unrelated infrastructure.

### Completion gate

Phase 1 becomes COMPLETE only when all are true:

1. An authoritative BOAT RACE official source is fetched over the network.
2. A fixed historical race is ingested end-to-end without synthetic production data.
3. Three raw official documents are stored immutably: race list, 3T odds, and race result.
4. Six race entries are normalized with official racer registration IDs.
5. The 3T odds response is captured and its coverage is explicitly classified. **Only a complete 120-combination response may be normalized into `historical_odds`; an incomplete response must produce zero normalized odds rather than invented or partial values.**
6. The official 3T/2T result and payouts are normalized.
7. Source fetch time and content SHA-256 are retained.
8. Closing odds are explicitly marked as having **no source observation timestamp** rather than inventing one. They are therefore not eligible for point-in-time model training as timestamped odds observations.
9. PostgreSQL migrations 001–003 and the end-to-end ingestion smoke test pass in CI.
10. Parser and integrity tests pass.

### Current Phase 1 implementation

- Official source URL builders for racelist, 3T odds, and race result.
- Immutable raw document table with mutation-blocking trigger.
- Normalized race, entries, 3T closing odds when complete, and race result storage.
- Explicit `odds_status` to distinguish complete source responses from incomplete source responses.
- Idempotent historical snapshot persistence.
- Parser validation for six entries, 120 unique 3T combinations on complete fixtures, and result/payout fields.
- CI smoke test against fixed official historical race `20260226 / venue 04 / race 1`.

### Important data-integrity decisions

The official 3T page labels the displayed values as **締切時オッズ** and states that they represent odds after sales-ticket aggregation. The page does not expose a source observation timestamp. The ingestion layer therefore never fabricates an observation timestamp. If the network response is incomplete, the raw document is retained, `odds_status` becomes `INCOMPLETE_SOURCE_RESPONSE`, and no partial odds are promoted into the normalized odds table. This prevents a silently truncated market from contaminating later research.

## Phase Progress

| Phase | Status | Gate |
|---|---|---|
| Phase 0 — Foundation | **COMPLETE** | Tests + PostgreSQL migration passed in CI |
| Phase 1 — Historical Data Engine | **IN PROGRESS** | Official-source vertical slice + raw immutability + explicit odds coverage + CI smoke test |
| Phase 2 — Baseline Probability Model | BLOCKED | Phase 1 pass |
| Phase 3 — Market / EV Engine | BLOCKED | Valid PIT odds + settlement model |
| Phase 4 — Backtest / Walk-Forward | BLOCKED | Point-in-time + OOS integrity |
| Phase 5 — Signal Selection | BLOCKED | Positive OOS evidence |
| Phase 6 — Live Data / Prediction | BLOCKED | Paper pipeline ready |
| Phase 7 — Web App | NOT STARTED | Prediction engine available |
| Phase 8 — Paper Trading | BLOCKED | Live pipeline ready |
| Phase 9 — Production | BLOCKED | Paper trading evidence |

**Current phase: Phase 1 — Historical Data Engine.**
