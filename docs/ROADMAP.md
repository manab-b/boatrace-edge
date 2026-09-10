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

## Phase 0 — Foundation

### Goal
リポジトリを「検証可能な予想システム」にする。

### Tasks

- [ ] Python backend
- [ ] Web frontend
- [ ] PostgreSQL-compatible data model
- [ ] Type-safe API contract
- [ ] Environment / secrets separation
- [ ] Logging
- [ ] Error handling
- [ ] Data timestamps in JST
- [ ] Reproducible local development
- [ ] CI for tests/lint/type checks

### Exit Criteria

- ローカルでWeb + APIが起動
- DB migrationが再現可能
- テストが自動実行できる

---

## Phase 1 — Historical Data Engine

### Goal
過去レースを「予想時点の情報」と「結果」に分離して保存する。

### Data

- race metadata
- entries
- racer statistics
- motor statistics
- boat statistics
- exhibition / pre-race information
- weather / water conditions
- odds snapshots
- final result
- payout

### Critical Rule

**未来情報の混入を絶対に許さない。**

例えば締切後オッズ、結果、後から更新された選手成績を、その時点の予想特徴量に混ぜない。

### Exit Criteria

- 数十万〜数百万レースを想定したschema
- 各featureにas-of timestampを持てる
- 過去データから任意時点の「予想可能な状態」を再現できる
- 欠損・重複・返還・同着を処理できる

---

## Phase 2 — Baseline Probability Model

### Goal
まず機械学習を複雑化せず、強いbaselineを作る。

### Candidate Features

- 艇番
- 全国 / 当地成績
- 勝率 / 2連率 / 3連率
- ST
- 平均ST
- F/L
- モーター成績
- ボート成績
- 展示タイム
- 展示気配
- 進入想定
- コース別成績
- 季節
- 場
- 天候
- 風向 / 風速
- 波高
- レースグレード
- 節内成績
- オッズ

### Modeling Strategy

1. まず勝着確率モデル
2. 次に着順分布モデル
3. そこから買い目確率を生成
4. Calibrationを実施
5. MLモデルを増やす前にbaselineを固定

### Exit Criteria

- out-of-sampleで確率予測が評価可能
- Brier score / Log loss / calibration curveを保存
- レース単位の確率合計が整合する

---

## Phase 3 — Market / EV Engine

### Goal
「当たりそう」から「買う価値がある」へ変換する。

### Core

For a single combination:

- model probability = p
- decimal payout odds = O
- expected return = p × O
- EV ROI = p × O - 1

例: p=0.30、O=4.0なら期待値は +20%。

### Cost Handling

BOAT RACEの払戻金は売上金を基礎に算定されるため、払戻率による市場側の控除はオッズ・払戻構造にすでに内包される。したがって同じ控除をEV計算で二重に差し引かない。

公式ガイドでは払戻金は原則として売上金（返還金を除く）の75%以上を的中者に按分して払い戻すと説明されている。

### Conservative EV

単純EVだけでは配信しない。

- probability uncertainty
- odds uncertainty
- odds drift
- minimum odds
- minimum edge
- model calibration
- sample size
- race quality
- market liquidity proxy

を考慮した**Conservative EV**を採用する。

### Exit Criteria

- EV計算が再現可能
- 予想時刻と使用オッズが保存される
- 後から「なぜ買いだったか」を説明できる
- EV positiveでも不確実性が高いケースを除外できる

---

## Phase 4 — Backtest / Walk-Forward Engine

### Goal
バックテストで勝てるように見せるのではなく、未来でも再現する戦略を探す。

### Rules

- Random train/test splitは禁止
- 時系列split
- Walk-forward validation
- 過学習防止
- Hyperparameter optimizationはvalidation期間内のみ
- test期間は最後まで触らない
- 予想生成時点以降の情報を使わない

### Metrics

- Bets
- Hit rate
- ROI
- Total P/L
- Profit Factor
- Max Drawdown
- Average EV
- Median EV
- CLV / odds drift
- Calibration
- Sharpe-like risk metric
- Worst losing streak
- Performance by venue
- Performance by race grade
- Performance by bet type
- Performance by odds bucket

### Exit Criteria

**最低でも複数期間でpositive ROIが再現し、特定期間だけの偶然に依存していないこと。**

---

## Phase 5 — Signal Selection Engine

### Goal
1日大量に予想を出すのではなく、本当に条件の良いものだけを残す。

### Signal Levels

- NO BET
- WATCH
- VALUE
- STRONG VALUE

最終ユーザー向け配信は原則VALUE以上。

### Example Filter

- probability calibration OK
- Conservative EV > threshold
- minimum odds threshold
- expected edge > safety margin
- sufficient historical support
- no data quality warning
- no abnormal race condition

閾値はバックテストで決める。最初から都合のよい数字を固定しない。

### Exit Criteria

- 1日あたりの配信数を制御可能
- 「予想しない」という判断が正常系
- フィルタ適用後もout-of-sampleで優位性が残る

---

## Phase 6 — Live Data / Prediction Pipeline

### Goal
開催中のレースを自動監視し、適切な時点で予想を生成する。

### Pipeline

Data ingestion
→ validation
→ feature snapshot
→ probability model
→ odds snapshot
→ EV engine
→ confidence / risk filter
→ signal
→ notification

### Important

公式サイトではオッズは更新ボタンによる更新で、締切時オッズは発売締切時点のものだが、最終確定オッズではないと説明されている。

そのため、

**「予想時点オッズ」と「締切時オッズ」を別データとして保存する。**

### Exit Criteria

- 予想生成が自動
- 同一レースの重複配信を防止
- データ遅延・欠損時は自動的にNO BET
- 締切直前の異常値に対する安全策がある

---

## Phase 7 — Web App

### Main Screens

1. Dashboard
2. Today's Signals
3. Race Detail
4. EV Analysis
5. Results / Track Record
6. Backtest
7. Model Performance
8. Data Health

### Signal Card

- 場
- レース
- 締切時刻
- 勝式
- 買い目
- 推定確率
- オッズ
- 損益分岐確率
- Raw EV
- Conservative EV
- Confidence
- 推奨度
- 根拠
- 予想生成時刻
- 使用オッズ時刻

### Exit Criteria

ユーザーが「なぜこの買い目なのか」を数秒で理解できる。

---

## Phase 8 — Paper Trading

### Goal

実際のお金を使わず、ライブ予想を完全に記録する。

### Track

- signal odds
- closing odds
- result
- theoretical P/L
- actual execution assumptions
- CLV
- model calibration

### Exit Criteria

最低でも十分なサンプル数を蓄積し、backtest → paper tradingの性能差を確認する。

---

## Phase 9 — Production

### Goal

初めて実運用。

### Requirements

- Monitoring
- Data freshness alerts
- Model drift detection
- Performance dashboard
- Automatic rollback
- Audit log
- Prediction history immutable storage

---

# Non-Negotiable Rules

1. 的中率だけで戦略を評価しない
2. バックテストの結果だけで本番投入しない
3. 未来情報を絶対に混ぜない
4. 最終オッズを予想時点のオッズとして使わない
5. EVが低いレースを無理に配信しない
6. データ欠損時は予想しない
7. モデルを複雑にする前にbaselineを検証する
8. すべての予想を後から再現可能にする
9. 良い期間だけを切り取って実績を表示しない
10. 「NO BET」を成功した判断として扱う

# Definition of Done

BOAT RACE EDGEが完成したと判断するのは、

**「予想が当たる」ことではなく、**

> 時系列out-of-sample → walk-forward → live paper trading

の3段階で、コスト・オッズ変動・不確実性を考慮した上で、正の期待値が再現されることを確認できたとき。

その後も実績を継続監視し、優位性が消えたら自動的に配信を停止できること。
