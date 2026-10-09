#same logic in polars

import polars as pl
reviews_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/reviews/part.0.parquet"
reviews_pl = pl.scan_parquet(reviews_path) #lazy evaluation; scan parquet doesn't immediately pull the entire dataset into memory and execute everything.

#schema check
print(reviews_pl.collect_schema())

#few rows
print(reviews_pl.head(5).collect())

#selecting only columns needed
reviews_pl = (pl.scan_parquet(reviews_path)
              .select([
                  'appid',
                  'game',
                  'author_playtime_forever',
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
                  ]))

#fixing the datatypes as we did before
reviews_pl = reviews_pl.with_columns([pl.col('appid').cast(pl.Int64)])
binary_cols = ['voted_up',
               'steam_purchase',
               'received_for_free',
               'written_during_early_access'
               ]
reviews_pl = reviews_pl.with_columns([pl.col(binary_cols).cast(pl.Int64)])

#unix timestamp to datetime
reviews_pl = reviews_pl.with_columns([
    pl.from_epoch(
        pl.col('timestamp_created'),
        time_unit='s'
    ).alias('review_date')
])

#creating playtime hours
reviews_pl = reviews_pl.with_columns([
    (pl.col('author_playtime_at_review') / 60).alias('playtime_hours_at_review')
])

#inspecting the plan
print(reviews_pl.explain())
#great, only the needed 13 cols and going to read those only
#will be a time saver when scaling to the whole 23 GB of reviews

#preview to check plan follows
print(reviews_pl.select(['appid',
                         'voted_up',
                         'written_during_early_access',
                         'review_date',
                         'playtime_hours_at_review'])
                         .head(10)
                         .collect())

print(reviews_pl.collect_schema())
#schema confirmed everything is in the right dtype

#now the text features
reviews_pl = reviews_pl.with_columns([pl.col('review').str.len_chars().alias('review_length'),
                                      pl.col('review')    .str.replace_all(r'\s+', ' ').str.strip_chars().str.split(' ').list.len().alias('review_word_count'),
                                      (pl.col('votes_up') > 0).cast(pl.Int64).alias('received_helpful_vote')])

#flagging extreme text
reviews_pl = reviews_pl.with_columns([(pl.col('review_length') > 8000).cast(pl.Int64).alias('extreme_text')])

#summary to compare to what we did on pandas
print(reviews_pl.select(['review',
                         'review_length',
                         'review_word_count',
                         'received_helpful_vote',
                         'extreme_text'
                         ]).head(10).collect())
print(
    reviews_pl.select([
        pl.col('review_length').median().alias('median_review_length'),
        pl.col('review_word_count').median().alias('median_word_count'),
        pl.col('extreme_text').sum().alias('extreme_text_count'),
        pl.col('received_helpful_vote').mean().alias('helpful_review_rate')
    ])
    .collect()
)

#playime quartiles and aggregation
quartiles = (reviews_pl.select([
    pl.col('playtime_hours_at_review').quantile(0.25, interpolation='linear').alias('q1'),
    pl.col('playtime_hours_at_review').quantile(0.50, interpolation='linear').alias('q2'),
    pl.col('playtime_hours_at_review').quantile(0.75, interpolation='linear').alias('q3')]).collect())
print(quartiles)

#quartile values
q1 = quartiles['q1'][0]
q2 = quartiles['q2'][0]
q3 = quartiles['q3'][0]

#groups low, moderate, high and very high
reviews_pl = reviews_pl.with_columns([pl.when(pl.col('playtime_hours_at_review') <= q1).then(pl.lit('Low'))
                                      .when(pl.col('playtime_hours_at_review') <= q2).then(pl.lit('Moderate'))
                                      .when(pl.col('playtime_hours_at_review') <= q3).then(pl.lit('High'))
                                      .otherwise(pl.lit('Very High')).alias('playtime_group')])

#aggreatation - count, mean, medians
playtime_summary_pl = (reviews_pl.group_by('playtime_group')
                       .agg([pl.len().alias('review_count'),
                             pl.col('voted_up').mean().alias('approval_rate'),
                             pl.col('playtime_hours_at_review').median().alias('median_playtime'),
                             pl.col('received_helpful_vote').mean().alias('helpful_review_rate'),
                             pl.col('review_length').median().alias('median_review_length')]).collect())
print(playtime_summary_pl)

#up until now all good, polars is reporducing the same things panas did
#only thing to clean up is the group ordering. 
#polars is correctly grouping but is placing Very High before High 
#just some presentation cleanup
playtime_summary_pl = (reviews_pl.group_by('playtime_group').agg([
    pl.len().alias('review_count'),
    pl.col('voted_up').mean().alias('approval_rate'),
    pl.col('playtime_hours_at_review').median().alias('median_playtime'),
    pl.col('received_helpful_vote').mean().alias('helpful_review_rate'),
    pl.col('review_length').median().alias('median_review_length')])
    .with_columns([
        pl.when(pl.col('playtime_group') == 'Low').then(1)
        .when(pl.col('playtime_group') == 'Moderate').then(2)
        .when(pl.col('playtime_group') == 'High').then(3)
        .otherwise(4)
        .alias('group_order')
    ])
    .sort('group_order')
    .drop('group_order')
    .collect()
)
print(playtime_summary_pl)
