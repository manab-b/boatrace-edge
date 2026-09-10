# BOAT RACE EDGE

高勝率だけを追わず、**市場オッズに対して統計的な優位性（Edge）がある買い目だけを厳選配信する**ボートレース予想Webアプリ。

## Product Goal

> 「当たりそうな予想」ではなく、「推定確率に対してオッズが割安な買い目」だけを配信する。

本プロジェクトの最終評価指標は的中率単独ではない。

- ROI / 回収率
- Profit Factor
- 最大ドローダウン
- 期待値（EV）
- 期待値の実現度
- out-of-sample / walk-forward 成績
- 予測確率のCalibration
- オッズ取得時点から締切時までの価格変動
- レース・場・勝式ごとの安定性

## Core Principle

1. データを正確に取得する
2. レース開始前に利用可能な情報だけで特徴量を作る
3. 勝率を推定する
4. 市場オッズから損益分岐確率を求める
5. EVを計算する
6. 不確実性・オッズ変動・最低オッズ・流動性を考慮して厳格にフィルタする
7. 条件を満たさないレースは**「見送り」**
8. 実運用前に長期間のout-of-sample検証とpaper tradingを通す

## Important

このシステムは利益を保証するものではない。目標は「勝てると期待できる条件だけを機械的に選別し、負ける条件では賭けない」こと。

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).
See [docs/STRATEGY_SPEC.md](docs/STRATEGY_SPEC.md).
