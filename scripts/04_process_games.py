#Now to prepare the data for joining

import polars as pl
games_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/games/train-00000-of-00001.parquet"
games_pl = pl.scan_parquet(games_path)

#only the relevant fields
games_pl = games_pl.select([
    'appID',
    'name',
    'release_date',
    'estimated_owners',
    'peak_ccu',
    'price',
    'windows',
    'mac',
    'linux',
    'metacritic_score',
    'positive',
    'negative',
    'recommendations',
    'average_playtime_forever',
    'median_playtime_forever',
    'developers',
    'publishers',
    'categories',
    'genres',
    'tags'
])

#fixing the two problems we already know (both stored are strings)
games_pl = games_pl.with_columns([pl.col('appID').cast(pl.Int64),
                                  pl.col('release_date').str.strptime(pl.Date, format='%b %d, %Y', strict=False)])

#quick inspection
print(games_pl.select(['appID',
                       'name',
                       'release_date',
                       'estimated_owners']).head(10).collect())
#schema check
print(games_pl.collect_schema())
#conversions worked, appID is now int and release_date as data
#two concerns. one: - tags = list(null) - this parquet shard may only have reviews with no tags

#checking if tags has anything compared to genres and/or categories
tags_check = (
    games_pl
    .select([pl.len().alias('total_games'),
             pl.col('tags').list.len().gt(0).sum().alias('games_with_tags'),
             pl.col('genres').list.len().gt(0).sum().alias('games_with_genres'),
             pl.col('categories').list.len().gt(0).sum().alias('games_with_categories')
             ]).collect())
print(tags_check)

#another concern: estimated_owners is a range
#I want to inspect it
owners_check = (games_pl.group_by('estimated_owners')
                .agg(pl.len().alias('game_count'))
                .sort('game_count', descending=True)
                .collect())
print(owners_check)

#firstly, tags is empty in this dataset, so I could use either genres/categories if needed.
#second, estimated_owners is stored in buckets , with 14 ranges
#I wont treat the 0-0 range as having no owners, but more like no ownership estimate 

#transforming the ownership range; the separator is a dash '-'.
games_pl = games_pl.with_columns(
    [pl.col('estimated_owners').str.split(' - ').list.get(0).cast(pl.Int64).alias('owner_lower'),
    pl.col('estimated_owners').str.split(' - ').list.get(1).cast(pl.Int64).alias('owner_upper')])

#creating a midpoint estimate
games_pl = games_pl.with_columns([
    pl.when(
        (pl.col('owner_lower') == 0) &
        (pl.col('owner_upper') == 0)
    )
    .then(None)
    .otherwise(
        (pl.col('owner_lower') + pl.col('owner_upper')) / 2
    )
    .alias('owner_midpoint')
])
#just gives 0 a null - I dont want it to claim zero owners

#inspect
print(games_pl.select(['name',
                       'estimated_owners',
                       'owner_lower',
                       'owner_upper',
                       'owner_midpoint'])
                       .head(15).collect())
#how many midpoint vals are missing
print(games_pl.select([pl.col('owner_midpoint').is_null().sum()
                       .alias('missing_owner_estimates')])
                       .collect())

#great, now 0-0 is null, 0-20000 has 10000 as midpoint and so on.
#around 23k dont have ownership estimate

#time to explode
#genre lists into a long form table
game_genres = (games_pl.select(['appID','name','genres'])
               .explode('genres')
               .filter(pl.col('genres').is_not_null())
               .rename({'genres': 'genre'}))
print(game_genres.head(15).collect())
#inspect size
print(game_genres.select([
    pl.len().alias('genre_rows'),
    pl.col('genre').n_unique().alias('unique_genres')])
    .collect()
)

#most common genres - count descending per genre
print(game_genres.group_by('genre')
      .agg(pl.len()
           .alias('game_count'))
           .sort('game_count', descending=True)
           .head(15)
           .collect()
)
#genre normaliztion works 
#also only 33 unique genres around 333k rows , could be good for a readable network

#now the same transformation but for categories