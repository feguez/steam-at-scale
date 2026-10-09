#before heading into the CRC I am making a local script to confirm 
#it works on part.0.parquet, then on the CRC I will only change the 
#input path to all parquet files.


import polars as pl
reviews_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/reviews/part.0.parquet"

reviews = (
    pl.scan_parquet(reviews_path)
    .select([
        'appid',
        'author_playtime_at_review',
        'language',
        'review',
        'timestamp_created',
        'voted_up',
        'votes_up',
        'weighted_vote_score',
        'steam_purchase',
        'received_for_free',
        'written_during_early_access'
    ])
    .with_columns([
        pl.col('appid').cast(pl.Int64),
        pl.col([
            'voted_up',
            'steam_purchase',
            'received_for_free',
            'written_during_early_access']).cast(pl.Int64),
        pl.from_epoch(pl.col('timestamp_created'),time_unit='s').alias('review_date'),
        (pl.col('author_playtime_at_review') / 60).alias('playtime_hours_at_review'),
        (pl.col('votes_up') > 0).cast(pl.Int64).alias('received_helpful_vote')
    ])
)

print(reviews.explain())
#perfect, we get PROJECT 11/25 COLUMNS - polars is reading the 11 fields we need.

#one row per game
#review feature
reviews = reviews.with_columns([pl.col('review').str.len_chars().alias('review_length')])

#game level summary
# one row per game
game_review_summary = (
    reviews
    .group_by('appid')
    .agg([
        pl.len().alias('review_count'),
        pl.col('voted_up').mean().alias('approval_rate'),
        pl.col('playtime_hours_at_review').median().alias('median_playtime_hours'),
        pl.col('received_helpful_vote').mean().alias('helpful_review_rate'),
        pl.col('written_during_early_access').mean().alias('early_access_share'),
        pl.col('review_length').median().alias('median_review_length')
    ]))
#inspect
print(game_review_summary.sort('review_count', descending=True).collect())
#game level summary works , perfect

#create review month
reviews = reviews.with_columns([
    pl.col('review_date').dt.truncate('1mo').alias('review_month')
    ])

#monthly summary
#a row per game per month
game_monthly_reviews = (
    reviews
    .group_by(['appid','review_month'])
    .agg([
        pl.len().alias('review_count'),
        pl.col('voted_up').mean().alias('approval_rate'),
        pl.col('playtime_hours_at_review').median().alias('median_playtime_hours'),
        pl.col('received_helpful_vote').mean().alias('helpful_review_rate'),
        pl.col('written_during_early_access').mean().alias('early_access_share')
    ]))
#inspect
print(game_monthly_reviews.sort(['appid','review_month']).head(25).collect())
#number of rows created
print(game_monthly_reviews.select(pl.len().alias('game_month_rows')).collect())
#monthly aggregation works perfectly as well

#now saving the two outputs
game_summary_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/game_review_summary.parquet"
monthly_summary_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/game_monthly_reviews.parquet"

game_review_summary.collect().write_parquet(game_summary_path)
game_monthly_reviews.collect().write_parquet(monthly_summary_path)
