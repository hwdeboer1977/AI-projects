import snscrape.modules.twitter as sntwitter

for i, tweet in enumerate(sntwitter.TwitterSearchScraper("ethereum lang:en since:2024-05-01").get_items()):
    print(tweet.date, tweet.user.username, tweet.content)
    if i > 5:
        break
