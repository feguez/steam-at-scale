import pandas as pd

#Paths to files
games_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/games/train-00000-of-00001.parquet"
reviews_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/reviews/part.0.parquet"

games = pd.read_parquet(games_path)
reviews = pd.read_parquet(reviews_path)

#Shapes
#Number of rows and cols
print("Games:", games.shape)
print("Reviews:", reviews.shape)

#Columns
#games col names
print(games.columns.to_list())
#reviews col names
print(reviews.columns.to_list())

# appID in games and appid in reviews can be used for a join

#Data Types
#games data types
print(games.dtypes)
#review data types
print(reviews.dtypes)

# appID in games is a str
# appid in reviews is a float
# need to standardize both to a same type


#voted_up, steam_purchase, recieved_for_free, 
#and written_during_early_access are coming as 
#floats, but they are conceptually boolean - 
#may be happening because of 0/1 values + missing values.

#inspecting important game columns
important_game_cols = [
    'appID',
    'release_date',
    'estimated_owners',
    'average_playtime_forever',
    'median_playtime_forever',
    'developers',
    'publishers',
    'categories',
    'genres',
    'tags'
]

print(games[important_game_cols].dtypes)

#genres
print(games['genres'].head())
#tags
print(games['tags'].head())
#devs
print(games['developers'].head())
#categories
print(games['categories'].head())

#genres, tags, developers, and categories have numpy.ndarray objects
#later can use .explode()


#Inspecting date/timestamp values
#release dates
print(games['release_date'].head(10))

#review timestamps
print(reviews['timestamp_created'].head(10))
print(reviews['timestamp_updated'].head(10))


#test to convert to Unix seconds
print(pd.to_datetime(
    reviews['timestamp_created'].head(10),
    unit='s')
)
#works

#review columns important for analysis
important_review_cols = [
    'appid',
    'author_playtime_at_review',
    'language',
    'review',
    'timestamp_created',
    'voted_up',
    'votes_up',
    'weighted_vote_score',
    'written_during_early_access'
]
#missing val check
print(reviews[important_review_cols].isna().sum())

#same w/ game cols
important_game_cols = [
    'appID',
    'release_date',
    'estimated_owners',
    'average_playtime_forever',
    'median_playtime_forever',
    'developers',
    'publishers',
    'categories',
    'genres',
    'tags'
]
#missing vals
print(games[important_game_cols].isna().sum())
#no missing vals

#inspect binary review fields
#since several came as float64 but should behave like 0/1
binary_cols = [
    'voted_up',
    'steam_purchase',
    'received_for_free',
    'written_during_early_access'
]
for col in binary_cols:
    print(reviews[col].value_counts())
    print()
#good, they are all 0/1 just stored as floats

#check the keys for joins
#gameids
print(games['appID'].head(10))

#reviewids
print(reviews['appid'].head(10))

#  something to note is that in this shard 97% are positive reviews,
#  because part.0 may cover only a subset of games, similarly with Early Access,
#  where 235k are non and only 772 are. This may reflect what games are contained
#  in this shard. Just a note as I plan to scale this to 114M rows in the CRC

#temp matching version of game and review ids
game_ids = pd.to_numeric(games['appID'], errors='coerce')
review_ids = reviews['appid'].astype('int64')

#unique games in this shard
print(review_ids.nunique())

#app id range in this shard
print(review_ids.min(), review_ids.max())

#if any game ids failed to convert to numeric
print(game_ids.isna().sum())

#review rows with matching games
matching_reviews = review_ids.isin(game_ids).mean()
print(matching_reviews)

# I see around 237k reivews but only 8 games, 
# so the shard is organized by game , rather than being a random 
# sample. It also speaks on the unusual high positive reviews and 
# also low Early Access. #This sahrd is only for development of the 
# pipeline to use later, so no conclusions for now.

#join coverage is great at 99.992% , small enough and could check later