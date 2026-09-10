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
| Foundation verification | **COMPLETE** | GitHub Actions passed pytest and PostgreSQL migration validation |
| Historical data engine | NOT STARTED | **Current product bottleneck** |
| Probability model | BLOCKED | Must wait for historical PIT dataset |
| EV engine | BLOCKED | Must wait for valid probabilities + odds |
| Walk-forward research | BLOCKED | Must wait for PIT dataset/model |
| Signal selection | BLOCKED | Must wait for OOS evidence |
| Live prediction | BLOCKED | Must wait for paper-ready research |
| Web prediction UI | NOT STARTED | Intentionally deferred |

### Phase 0 Completion Evidence

GitHub Actions run #19 completed successfully on commit `6bf099daf152b7baa4125af53e8794b3d1284d37`. The job completed with `success`; pytest and the PostgreSQL migration validation step both completed successfully.

### Loop / Duplication Audit

The latest 20 commits are overwhelmingly Phase 0 work. Several are micro-fixes or documentation corrections rather than new product capability. This indicates process churn, but no duplicate production implementation was found in the reviewed files.

The foundation is now frozen. **Do not add infrastructure unless it directly unblocks a failing gate or the active phase.**

### Shortest Route

1. Phase 0 is complete.
2. Start Phase 1 immediately.
3. Implement the smallest real-data ingestion slice: one authoritative source → raw immutable record → normalized race/entry/odds/result records → source timestamps → validation tests.
4. Expand coverage only after that end-to-end slice is proven.

## Phase Progress

| Phase | Status | Gate |
|---|---|---|
| Phase 0 — Foundation | **COMPLETE** | Tests + PostgreSQL migration passed in CI |
| Phase 1 — Historical Data Engine | NOT STARTED | Phase 0 complete |
| Phase 2 — Baseline Probability Model | BLOCKED | Phase 1 pass |
| Phase 3 — Market / EV Engine | BLOCKED | Valid odds + settlement model |
| Phase 4 — Backtest / Walk-Forward | BLOCKED | Point-in-time + OOS integrity |
| Phase 5 — Signal Selection | BLOCKED | Positive OOS evidence |
| Phase 6 — Live Data / Prediction | BLOCKED | Paper pipeline ready |
| Phase 7 — Web App | NOT STARTED | Prediction engine available |
| Phase 8 — Paper Trading | BLOCKED | Live pipeline ready |
| Phase 9 — Production | BLOCKED | Paper trading evidence |

**Current phase: Phase 1 — Historical Data Engine.**

Phase 1 scope is deliberately limited to real historical data acquisition, immutable raw storage, normalization, timestamp/PIT integrity, and tests. Do not implement prediction, EV, signal selection, live trading, or unrelated infrastructure in Phase 1.
