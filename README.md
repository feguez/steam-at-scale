# Steam at Scale: Player Behavior and the Gaming Ecosystem

This project uses large-scale Steam review data and game metadata to study player behavior, game lifecycle patterns, and relationships across the Steam genre ecosystem.

## Data

- 113,883,717 Steam reviews
- 663 Parquet review files (~23.5 GB)
- 124,146 games in the metadata dataset
- 105,893 games with at least one review

## Tools

- Polars
- DuckDB
- Parquet
- NetworkX
- PyVis
- Notre Dame Center for Research Computing (CRC)

## Project Questions

1. How does player investment relate to review behavior?
2. How does review behavior evolve across a game’s lifecycle and Early Access period?
3. What does the Steam genre ecosystem look like?

## Data Pipeline

The project was first developed and validated locally on a 236,652-review shard before scaling the same Polars pipeline to the complete review dataset through the Notre Dame CRC.

The full pipeline includes:

- Lazy Parquet scanning and column projection with Polars
- Review feature engineering
- Game metadata cleaning
- Review-to-game joins
- Lifecycle feature engineering
- Game-level and monthly aggregations
- Nested genre normalization
- Genre co-occurrence analysis
- Interactive NetworkX/PyVis visualization
- Batch execution on CRC compute resources

The full CRC run processed all 113,883,717 reviews and produced 1,942,717 game-month observations.

## Key Findings

### 1. Player Investment and Review Behavior

Reviews were divided into playtime quartiles based on playtime at the time of review.

- Low playtime: 76.8% approval
- Moderate playtime: 89.2% approval
- High playtime: 90.1% approval
- Very high playtime: 86.2% approval

Approval rises sharply from low to moderate/high playtime, but falls again among the most heavily invested players.

Low-playtime reviews were also the most likely to receive at least one helpful vote, at 37.9%.

### 2. Game Lifecycle and Early Access

Approval generally increases as games mature:

- First 30 days: 80.0%
- 1–6 months: 83.2%
- 6–12 months: 83.9%
- 1–3 years: 85.7%
- 3+ years: 89.2%

Median reviewer playtime also increases across these lifecycle groups, while helpful-vote rates are highest for reviews written earlier in a game's lifecycle.

The analysis also showed that "before release" and Steam's explicit Early Access flag should not be treated as interchangeable:

- 8,931,961 reviews occurred before the listed release date
- 8,101,804 of those were marked Early Access
- 830,157 pre-release reviews were not marked Early Access
- 3,774,681 Early Access reviews occurred on or after the listed release date

### 3. Steam Genre Ecosystem

The game metadata contains 33 genres and 391 genre co-occurrence relationships.

For readability, the interactive network retains relationships shared by at least 2,500 games, resulting in:

- 11 core genres
- 36 strong genre relationships

The strongest connections include:

- Casual + Indie: 38,926 games
- Action + Indie: 35,223 games
- Adventure + Indie: 34,601 games
- Action + Adventure: 21,238 games
- Adventure + Casual: 17,923 games

Indie acts as one of the strongest connectors across Steam's genre ecosystem.

## Repository Structure

```text
scripts/
    01_inspect_data.py
    02_process_reviews.py
    02_process_reviews_polars.py
    03_validate_duckdb.py
    04_process_games.py
    05_join_sample.py
    06_build_genre_network.py
    07_genre_network.py
    08_full_review_pipeline.py
    09_full_q1.py
    10_full_q2.py

results/
    q1_playtime_summary.csv
    q2_lifecycle_summary.csv
    q2_early_access_check.csv

data/
    processed/
        genre_network.html
```

Raw datasets and generated Parquet outputs are excluded from GitHub because of file size.