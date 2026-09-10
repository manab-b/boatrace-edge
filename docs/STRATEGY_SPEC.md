# BOAT RACE EDGE — Strategy Specification

## 1. Objective

The engine does not attempt to predict every race.

It estimates the probability of each candidate outcome and compares that probability with the market price. A signal is emitted only when the estimated advantage is sufficiently large and robust.

## 2. Separation of Concerns

### Data Layer
Responsible only for collection, normalization, timestamps, validation and storage.

### Feature Layer
Responsible only for transforming point-in-time data into model features.

### Model Layer
Responsible only for probability estimation.

### Market Layer
Responsible for odds snapshots, odds normalization and market-derived features.

### EV Layer
Responsible for expected return and conservative value calculation.

### Decision Layer
Responsible for NO BET / WATCH / VALUE / STRONG VALUE.

### Presentation Layer
Responsible only for displaying already-computed signals.

This separation is mandatory so the UI cannot silently alter prediction logic.

## 3. Point-in-Time Integrity

Every prediction must contain:

- race_id
- generated_at
- feature_cutoff_at
- odds_cutoff_at
- model_version
- feature_version
- data_version

A feature may only use records whose effective timestamp is <= feature_cutoff_at.

An odds value may only be used if it was observable at odds_cutoff_at.

## 4. EV

For a single outcome with decimal payout odds O and model probability p:

Expected return per 1 unit staked:

p × O

Expected value ROI:

p × O - 1

Break-even probability:

1 / O

The engine must never subtract the same market takeout twice.

## 5. Conservative Value

Raw EV is insufficient.

The production decision layer should use a conservative probability or conservative EV derived from validation error and uncertainty.

Conceptually:

Conservative EV = conservative_probability × conservative_odds - 1

The exact uncertainty method must be selected from walk-forward validation, not chosen to improve historical results.

## 6. Odds Timing

At minimum store:

- opening/first observed odds
- prediction odds
- subsequent snapshots
- closing-time odds
- final confirmed payout

The system must distinguish between:

- signal-time EV
- closing-line EV
- realized ROI

## 7. Backtesting

A backtest must reproduce the information available at the original prediction timestamp.

Forbidden:

- final result features
- post-race statistics
- future motor/boat statistics
- future race performance
- future odds
- revised data unavailable at prediction time

## 8. Signal Eligibility

A candidate is eligible only when:

- data quality passes
- probability model is valid
- calibration is acceptable
- odds are fresh enough
- minimum edge is exceeded
- uncertainty-adjusted edge is exceeded
- historical support is sufficient
- race is not excluded by risk rules

Otherwise:

NO BET.

## 9. Evaluation

Every signal must eventually produce an audit record containing:

- predicted probability
- odds
- raw EV
- conservative EV
- result
- payout
- theoretical P/L
- closing odds
- CLV
- model version
- feature version

This makes model improvement evidence-based rather than intuition-based.
