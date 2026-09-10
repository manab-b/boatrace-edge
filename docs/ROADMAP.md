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

---

## Phase Progress

| Phase | Status | Gate |
|---|---|---|
| Phase 0 — Foundation | **IN PROGRESS — CI execution pending** | Tests + PostgreSQL migration must pass |
| Phase 1 — Historical Data Engine | NOT STARTED | Phase 0 complete |
| Phase 2 — Baseline Probability Model | BLOCKED | Phase 1 pass |
| Phase 3 — Market / EV Engine | BLOCKED | Valid odds + settlement model |
| Phase 4 — Backtest / Walk-Forward | BLOCKED | Point-in-time + OOS integrity |
| Phase 5 — Signal Selection | BLOCKED | Positive OOS evidence |
| Phase 6 — Live Data / Prediction | BLOCKED | Paper pipeline ready |
| Phase 7 — Web App | NOT STARTED | Prediction engine available |
| Phase 8 — Paper Trading | BLOCKED | Live pipeline ready |
| Phase 9 — Production | BLOCKED | Paper trading evidence |

**Current gate: Phase 0. Do not start Phase 1 until automated tests are verified green.**

