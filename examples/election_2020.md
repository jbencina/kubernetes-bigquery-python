# 2020 First Presidential Debate
This dataset contains a dump of all tweets referring to the first 2020 Presidential Debate starting around 5PM Pacific
through the end of the debate.

## Table Information
Capture criteria: English tweets mentioning `debate, debates, biden, trump`

Table Name: `jbencina-144002.debates_2020.first_debate`

Schmea: Full Twitter API [Link](https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/overview/tweet-object)

## Data Notes
1. There are likely duplicate entries in BigQuery. This is because multiple workers may grab the same message. Dedup on Tweet ID
2. Most Tweets are retweets. Filter for unique with `retweeted_status.id IS NULL`
3. Tweets over 140 characters are truncated with `...`. These are typically retweets but some original tweets may also exceed the limit. Use `extended_tweet.full_text` to capture the full tweet.
4. The data has many instances of Unicode

## Sample Queries

Querying for a sample of tweets with the user name, and the text. Extended tweet ensures we capture those tweets which are longer than 140 characters.
```sql
SELECT
  created_at,
  id,
  user.name,
  retweeted_status.id IS NOT NULL is_retweet,
  retweeted_status.text AS retweeted_text,
  COALESCE(extended_tweet.full_text, text) AS text
FROM `jbencina-144002.debates_2020.first_debate`
LIMIT 1000;
```

Query for original tweets mentioning either candidate
```sql
SELECT
  COUNT(DISTINCT IF(UPPER(COALESCE(extended_tweet.full_text, text)) LIKE '%TRUMP%', id, NULL)) AS count_trump,
  COUNT(DISTINCT IF(UPPER(COALESCE(extended_tweet.full_text, text)) LIKE '%BIDEN%', id, NULL)) AS count_biden
FROM `jbencina-144002.debates_2020.first_debate`
WHERE
  retweeted_status.id IS NULL
```
