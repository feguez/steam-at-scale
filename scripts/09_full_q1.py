import polars as pl

reviews_path = "/users/feguezlo/steam_project/data/raw/reviews/*.parquet"
output_path = "/users/feguezlo/steam_project/data/processed/q1_playtime_summary.parquet"

reviews = (
    pl.scan_parquet(reviews_path)
    .select([
        'author_playtime_at_review',
        'voted_up',
        'votes_up'
    ])
    .with_columns([
        (pl.col('author_playtime_at_review') / 60)
        .alias('playtime_hours_at_review'),

        pl.col('voted_up')
        .cast(pl.Int64),

        (pl.col('votes_up') > 0)
        .cast(pl.Int64)
        .alias('received_helpful_vote')
    ])
)

quartiles = (
    reviews
    .select([
        pl.col('playtime_hours_at_review')
        .quantile(0.25, interpolation='linear')
        .alias('q1'),

        pl.col('playtime_hours_at_review')
        .quantile(0.50, interpolation='linear')
        .alias('q2'),

        pl.col('playtime_hours_at_review')
        .quantile(0.75, interpolation='linear')
        .alias('q3')
    ])
    .collect()
)

q1 = quartiles['q1'][0]
q2 = quartiles['q2'][0]
q3 = quartiles['q3'][0]

print("Quartiles:", q1, q2, q3)

reviews = reviews.with_columns([
    pl.when(pl.col('playtime_hours_at_review') <= q1)
    .then(pl.lit('Low'))

    .when(pl.col('playtime_hours_at_review') <= q2)
    .then(pl.lit('Moderate'))

    .when(pl.col('playtime_hours_at_review') <= q3)
    .then(pl.lit('High'))

    .otherwise(pl.lit('Very High'))
    .alias('playtime_group')
])

summary = (
    reviews
    .group_by('playtime_group')
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
        .alias('helpful_review_rate')
    ])
    .collect()
)

print(summary)

summary.write_parquet(output_path)
