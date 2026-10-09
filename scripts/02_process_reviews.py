import pandas as pd
#paths to files
reviews_path = r"C:/Users/fabri/Downloads/MSBA Fall/Data Wrangling/steam_project/data/raw/reviews/part.0.parquet"
#read parquet
reviews = pd.read_parquet(reviews_path)

#appid current stored as float but we confirmed every number is a whole number
#so can safely convert its dtype to integer
reviews['appid'] = reviews['appid'].astype('int64')

#fix the binary fields which are 0/1 but stored as floats
binary_cols = [
    'voted_up',
    'steam_purchase',
    'received_for_free',
    'written_during_early_access'
]

reviews[binary_cols] = reviews[binary_cols].astype('int64')

#converting the unix timestamp and making it a new col
reviews['review_date'] = pd.to_datetime(reviews['timestamp_created'], unit='s')

#make a col for playtime hours; can be useful for interpretation over minutes
reviews['playtime_hours_at_review'] = (reviews['author_playtime_at_review'] / 60)


#can start with engineering some features for my first Q
#num of characters in each review
reviews['review_length'] = reviews['review'].str.len()
#word count as well
reviews['review_word_count'] = reviews['review'].str.split().str.len()

print(reviews[['review', 'review_length', 'review_word_count']].head())
print(reviews[['review_length', 'review_word_count']].describe())
#median review is only 17 characters and 3 words, but the max shows an extreme outlier
#inspect:
print(reviews[['appid', 'language', 'review_length', 'review_word_count']].sort_values('review_length', ascending=False).head(10))
#character counts look to work across languages relatively well but .str.split() 
#splits 'words' based on spaces, which can and cannot be as meaningful for every language 

#inspect common review languages
print(reviews['language'].value_counts().head(15))
#Thinking of making Q1 have all reviews' playtime, behavior of recommendation, 
#helpfulness , but for text measurements we could focus only on English language.

#inspecting the outliers
longest_reviews = (reviews.sort_values('review_length', ascending=False)
                   .loc[:,['appid','language','review_length','review_word_count','review']]
                   .head(10).copy())
#first 200 chars
longest_reviews['review_preview'] = (longest_reviews['review'].str[:200])
#print
print(longest_reviews[['appid','language','review_length','review_word_count','review_preview']])
#huge outliers seem to be repeated characters, ASCII art/image text, spam...common among steam users

#english-only reviews distribution
english_reviews = reviews[reviews['language'] == 'english']
print("Reviews in english:", len(english_reviews))
print(english_reviews['review_length'].quantile([0.50, 0.75, 0.90, 0.95, 0.99, 0.999]))
#The english quantiles look okay, so most legitimate 
#text reviews are below what we are considering extreme.

#flagging reviews over 8000 characters to be 'extreme'
reviews['extreme_text'] = (reviews['review_length'] > 8000).astype(int)
print(reviews['extreme_text'].value_counts())


#Start aggregations for the Q1: Player playtime relation to review behavior
#inspect playtime
print(reviews['playtime_hours_at_review'].quantile([0.25, 0.50, 0.75, 0.90, 0.95, 0.99]))
#max playtime
print(reviews['playtime_hours_at_review'].max())

#see a considerable right skew. median is about 36 hours, top 25% are around 378 
#and top 10% are already above 1,350 hours. Want to use quartiles, not making hardcoded cutoffs.

#grouping players into 4 equally sized groups
#using qcut() to group observations by quantiles
reviews['playtime_group'] = pd.qcut(
    reviews['playtime_hours_at_review'], q=4, labels=['Low','Moderate','High','Very High']
    )
print(reviews[['playtime_hours_at_review', 'playtime_group']].head(10))
#group sizes
print(reviews['playtime_group'].value_counts().sort_index())

#playtime summary groupby aggregation; size, mean, median
playtime_summary = (reviews
                    .groupby('playtime_group', observed=True, as_index=False).agg(
                        review_count=('voted_up', 'size'),
                        approval_rate=('voted_up', 'mean'),
                        median_playtime=('playtime_hours_at_review', 'median'),
                        median_helpful_votes=('votes_up', 'median'),
                        median_review_length=('review_length', 'median'))
                        )
print(playtime_summary.to_string(index=False)) #to see all cols
#great, nearly equal groups 
#can se that median helpful votes is 0 so median is maybe not useful for this variable
#also going higher in playtime, there is a decline in median review length;
#may be good to inspect if review length declines as playtime increases outside this shard as well.
#also, approval rate is increasing the more playtime (at least in this shard)

#median helpful votes zero everywhere, so can engineer it into something a bit more useful
#flag if a review received >1 helpful vote
#so now we can see what proportion of reviews in each group received 1+ helpful votes
reviews['received_helpful_vote'] = (reviews['votes_up'] > 0).astype(int)

#back to the groupby agg to add it
playtime_summary = (reviews
                    .groupby('playtime_group', observed=True, as_index=False).agg(
                        review_count=('voted_up', 'size'),
                        approval_rate=('voted_up', 'mean'),
                        median_playtime=('playtime_hours_at_review', 'median'),
                        helpful_review_rate=('received_helpful_vote', 'mean'),
                        median_review_length=('review_length', 'median'))
                        )
print(playtime_summary.to_string(index=False)) #to see all cols

#great, aggregation doing good, some patterns start to show up:
# approval going up across groups, 
# helpful review rate dropping slightly then increasing,
# review length declining a bit.
#patterns to revisit on the full data 