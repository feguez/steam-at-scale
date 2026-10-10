import polars as pl

reviews_path = "/users/feguezlo/steam_project/data/raw/reviews/*.parquet"
games_path = "/users/feguezlo/steam_project/data/processed/games_clean.parquet"

summary_path = "/users/feguezlo/steam_project/data/processed/q2_lifecycle_summary.parquet"
early_access_path = "/users/feguezlo/steam_project/data/processed/q2_early_access_check.parquet"

# review fields needed for lifecycle analysis
reviews = (
    pl.scan_parquet(reviews_path)
    .select([
        'appid',
        'timestamp_created',
        'voted_up',
        'author_playtime_at_review',
        'votes_up',
        'written_during_early_access'
    ])
    .with_columns([
        pl.col('appid').cast(pl.Int64),

        pl.col('voted_up').cast(pl.Int64),

        pl.col('written_during_early_access').cast(pl.Int64),

        pl.from_epoch(
            pl.col('timestamp_created'),
            time_unit='s'
        ).alias('review_date'),

        (
            pl.col('author_playtime_at_review') / 60
        ).alias('playtime_hours_at_review'),

        (
            pl.col('votes_up') > 0
        )
        .cast(pl.Int64)
        .alias('received_helpful_vote')
    ])
)

# game release dates
games = (
    pl.scan_parquet(games_path)
    .select([
        'appID',
        'release_date'
    ])
    .rename({
        'appID': 'appid'
    })
)

# join reviews to release dates
joined = reviews.join(
    games,
    on='appid',
    how='left'
)

# days relative to listed release date
joined = joined.with_columns([
    (
        pl.col('review_date').dt.date()
        - pl.col('release_date')
    )
    .dt.total_days()
    .alias('days_since_release')
])

# separate pre-release flag
joined = joined.with_columns([
    pl.when(pl.col('days_since_release').is_null())
    .then(None)
    .otherwise(
        pl.col('days_since_release') < 0
    )
    .cast(pl.Int64)
    .alias('before_release')
])

# lifecycle categories
joined = joined.with_columns([
    pl.when(pl.col('days_since_release').is_null())
    .then(pl.lit('Missing release date'))

    .when(pl.col('days_since_release') < 0)
    .then(pl.lit('Before release'))

    .when(pl.col('days_since_release') <= 30)
    .then(pl.lit('First 30 days'))

    .when(pl.col('days_since_release') <= 180)
    .then(pl.lit('1-6 months'))

    .when(pl.col('days_since_release') <= 365)
    .then(pl.lit('6-12 months'))

    .when(pl.col('days_since_release') <= 1095)
    .then(pl.lit('1-3 years'))

    .otherwise(pl.lit('3+ years'))
    .alias('lifecycle_group')
])

# final lifecycle summary
lifecycle_summary = (
    joined
    .group_by('lifecycle_group')
    .agg([
        pl.len().alias('review_count'),

        pl.col('voted_up')
        .mean()
        .alias('approval_rate'),

        pl.col('playtime_hours_at_review')
        .median()
        .alias('median_playtime_hours'),

        pl.col('received_helpful_vote')
        .mean()
        .alias('helpful_review_rate'),

        pl.col('written_during_early_access')
        .mean()
        .alias('early_access_share')
    ])
    .collect()
)

# compare release timing with explicit Early Access flag
early_access_check = (
    joined
    .group_by([
        'before_release',
        'written_during_early_access'
    ])
    .agg(
        pl.len().alias('review_count')
    )
    .sort([
        'before_release',
        'written_during_early_access'
    ])
    .collect()
)

print(lifecycle_summary)
print(early_access_check)

lifecycle_summary.write_parquet(summary_path)
early_access_check.write_parquet(early_access_path)
