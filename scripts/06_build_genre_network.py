import polars as pl
genres_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/game_genres.parquet"
game_genres = pl.scan_parquet(genres_path)

#genre pairs within each game
genre_pairs = (game_genres.join(game_genres,on='appID',how='inner',suffix='_2')
    .filter(pl.col('genre') < pl.col('genre_2'))) #filter preventing repeated pairs in different orders

#aggregating the pairs
genre_edges = (genre_pairs
               .group_by(['genre','genre_2'])
               .agg(pl.len().alias('shared_games'))
               .sort('shared_games', descending=True))
 
#top connections
print(genre_edges.head(20).collect())

#total size
print(genre_edges.select([
    pl.len().alias('edge_count'),
    pl.col('shared_games').max().alias('max_shared_games')
    ]).collect())

#391 edges across 33 genres is dense for a readable network
#I will choose a threshold 

#how many edges remain at different connection strengths
threshold_check = (
    genre_edges
    .select([
        pl.len().alias('all_edges'),
        (pl.col('shared_games') >= 100).sum().alias('edges_100_plus'),
        (pl.col('shared_games') >= 500).sum().alias('edges_500_plus'),
        (pl.col('shared_games') >= 1000).sum().alias('edges_1000_plus'),
        (pl.col('shared_games') >= 2500).sum().alias('edges_2500_plus'),
        (pl.col('shared_games') >= 5000).sum().alias('edges_5000_plus')
    ]).collect()
)
print(threshold_check)

#edge weight distribution
print(genre_edges.select([
    pl.col('shared_games').min().alias('min'),
    pl.col('shared_games').median().alias('median'),
    pl.col('shared_games').quantile(0.75).alias('q75'),
    pl.col('shared_games').quantile(0.90).alias('q90'),
    pl.col('shared_games').max().alias('max')
]).collect())

#setting 2500 games as the threshold
#keeping only the strongest genre connections
genre_edges_filtered = (genre_edges.filter(pl.col('shared_games') >= 2500))
print(genre_edges_filtered.collect())

#save
genre_edges_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/processed/genre_edges.parquet"
genre_edges_filtered.collect().write_parquet(genre_edges_path)

#how many genres are in those edges
print(genre_edges_filtered.select([
    pl.concat_list([
        pl.col('genre'),
        pl.col('genre_2')])
        .list.explode()
        .n_unique()
        .alias('genres_in_network')
    ]).collect())

#great, now we have 36 edges/11 genres, which is good for our network size

