import polars as pl
reviews_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/reviews_sample_clean.parquet"
games_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/games_clean.parquet"

#both processed files
reviews = pl.scan_parquet(reviews_path)
games = pl.scan_parquet(games_path)

#keeping the columns I will use for my first two Qs
#also renaming appID so both are now appid
games_join = (
    games
    .select([
        'appID',
        'name',
        'release_date',
        'estimated_owners',
        'owner_lower',
        'owner_upper',
        'owner_midpoint',
        'peak_ccu',
        'price',
        'metacritic_score'
    ])
    .rename({
        'appID': 'appid',
        'name': 'game_name'
    })
)

#left join on appid
joined = reviews.join(games_join,on='appid',how='left')

#inspection
print(
    joined
    .select([
        'appid',
        'game',
        'game_name',
        'review_date',
        'release_date',
        'voted_up',
        'playtime_hours_at_review',
        'owner_midpoint'
    ])
    .head(10)
    .collect()
)
#also check unmatched reviews
join_check = (
    joined
    .select([pl.len().alias('total_reviews'),
             pl.col('game_name').is_null().sum().alias('unmatched_reviews')])
    .collect()
)
print(join_check)
#join worked, the 18 unmatched reviews are the same as what we saw before.

#review date - release date to make days since release
joined = joined.with_columns([
    (pl.col('review_date').dt.date() - pl.col('release_date'))
    .dt.total_days()
    .alias('days_since_release')
])

#inspection
print(
    joined
    .select([
        'appid',
        'game_name',
        'review_date',
        'release_date',
        'days_since_release',
        'written_during_early_access'
    ])
    .head(15)
    .collect()
)
#also check min, median, and max days
print(
    joined
    .select([
        pl.col('days_since_release').min().alias('min_days'),
        pl.col('days_since_release').median().alias('median_days'),
        pl.col('days_since_release').max().alias('max_days')
    ])
    .collect()
)
#are there any reviews showing up before their listed release date?
#these can be relevant , can correspond to early access? 
print(
    joined
    .select([
        (pl.col('days_since_release') < 0)
        .sum()
        .alias('reviews_before_release')
    ])
    .collect()
)
#there are 804 reviews before release date, but we also saw 772 marked as early access
#close but not identical, lets check this:
#reviews written before the listed release date
joined = joined.with_columns([
    (pl.col('days_since_release') < 0)
    .cast(pl.Int64)
    .alias('before_release')
])
#compare with early access flag
early_access_check = (
    joined
    .group_by(['before_release','written_during_early_access' ])
    .agg(pl.len().alias('review_count'))
    .sort(['before_release','written_during_early_access'])
    .collect())
print(early_access_check)

#what games actually have pre-release reviews:
pre_release_games = (
    joined
    .filter(pl.col('days_since_release') < 0)
    .group_by(['appid','game_name','release_date'])
    .agg([pl.len().alias('pre_release_reviews'),
          pl.col('written_during_early_access').sum().alias('early_access_reviews'),
          pl.col('days_since_release').min().alias('earliest_days_before_release')])
    .sort('pre_release_reviews', descending=True)
    .collect()
)
print(pre_release_games)

#before release isnt the same as early access, 
# we obsreved that 804 reivews happen before the release data , 
# 771 of those were marked as early access, and only 1 early 
# access review happens after the listed release

#days since release is our lifecycle timing
#written during early access is steams flag

#lifecycle groups based on timing relative to release
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
#inspect counts
print(joined.group_by('lifecycle_group')
      .agg(pl.len().alias('review_count'))
      .sort('review_count', descending=True)
      .collect()
)

#Q2 summary
lifecycle_summary = (
    joined
    .group_by('lifecycle_group')
    .agg([pl.len().alias('review_count'),
        pl.col('voted_up').mean().alias('approval_rate'),
        pl.col('playtime_hours_at_review').median().alias('median_playtime'),
        pl.col('received_helpful_vote').mean().alias('helpful_review_rate'),
        pl.col('written_during_early_access').mean().alias('early_access_share')])
    .collect()
)

print(lifecycle_summary)

#our final summary has grouped lifecycle, review counts, approval rate, median playtime,
#helpful review rate, share of early access...
#The pipeline for Q2 works; but wont interpret 
#these numbers yet because this shard only has 8 games - will be great to see it with the larger data.

