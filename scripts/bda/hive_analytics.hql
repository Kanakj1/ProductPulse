-- ProductPulse: Hive Analytics Table Definitions and Queries
-- Database initialization
CREATE DATABASE IF NOT EXISTS productpulse_bda;
USE productpulse_bda;

-- Drop table if exists to ensure idempotent execution
DROP TABLE IF EXISTS product_aspect_metrics;

-- External Table over Hadoop MapReduce Aggregation Output
-- Columns align with scripts/bda/aspect_reducer.py output:
-- parent_asin, aspect, review_count, avg_rating, total_helpful_votes, low_rating_count, med_rating_count, high_rating_count
-- NOTE: review_count represents distinct reviews mentioning the aspect for that product.
CREATE EXTERNAL TABLE IF NOT EXISTS product_aspect_metrics (
    parent_asin STRING,
    aspect STRING,
    review_count INT,
    avg_rating DOUBLE,
    total_helpful_votes INT,
    low_rating_count INT,
    med_rating_count INT,
    high_rating_count INT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
STORED AS TEXTFILE
LOCATION '/app/data/bda/hadoop_output';

-- -------------------------------------------------------------
-- Query 1: Overall Volume and Helpful Votes by Aspect
-- Measures aspect prevalence across the 25k review corpus
-- Excludes internal meta-records (__ALL_REVIEWS__, __NO_ASPECT__, __MALFORMED__)
-- Weighted average rating = sum(aspect_review_ratings) / sum(aspect_reviews)
-- -------------------------------------------------------------
SELECT 
    aspect,
    SUM(review_count) AS total_aspect_reviews,
    ROUND(SUM(avg_rating * review_count) / SUM(review_count), 4) AS weighted_avg_rating,
    SUM(total_helpful_votes) AS total_helpful_votes
FROM product_aspect_metrics
WHERE substr(aspect, 1, 2) != '__'
GROUP BY aspect
ORDER BY total_aspect_reviews DESC;

-- -------------------------------------------------------------
-- Query 2: Top Products Ranked by Aspect Review Count
-- Identifies products with highest aspect discussion volume (distinct reviews)
-- -------------------------------------------------------------
SELECT 
    parent_asin,
    aspect,
    review_count AS aspect_review_count,
    ROUND(avg_rating, 2) AS product_aspect_avg_rating,
    total_helpful_votes
FROM product_aspect_metrics
WHERE substr(aspect, 1, 2) != '__'
ORDER BY aspect_review_count DESC
LIMIT 25;

-- -------------------------------------------------------------
-- Query 3: Average Source Rating by Aspect and Product
-- Filters for statistically relevant products (minimum 5 distinct aspect reviews)
-- Ranked to surface lowest-rated product aspects (potential customer pain points)
-- -------------------------------------------------------------
SELECT 
    parent_asin,
    aspect,
    review_count AS aspect_review_count,
    ROUND(avg_rating, 2) AS avg_rating,
    total_helpful_votes
FROM product_aspect_metrics
WHERE substr(aspect, 1, 2) != '__' AND review_count >= 5
ORDER BY avg_rating ASC, aspect_review_count DESC
LIMIT 25;

-- -------------------------------------------------------------
-- Query 4: Rating-Band Distributions by Aspect
-- Explicitly designated as star-rating bands (1-2 low, 3 med, 4-5 high)
-- NOT to be conflated with text sentiment polarity
-- -------------------------------------------------------------
SELECT 
    aspect,
    SUM(low_rating_count) AS low_rating_reviews_1_to_2_stars,
    SUM(med_rating_count) AS med_rating_reviews_3_stars,
    SUM(high_rating_count) AS high_rating_reviews_4_to_5_stars,
    SUM(review_count) AS total_aspect_reviews,
    ROUND(SUM(high_rating_count) * 100.0 / SUM(review_count), 2) AS high_rating_pct,
    ROUND(SUM(low_rating_count) * 100.0 / SUM(review_count), 2) AS low_rating_pct
FROM product_aspect_metrics
WHERE substr(aspect, 1, 2) != '__'
GROUP BY aspect
ORDER BY total_aspect_reviews DESC;

-- -------------------------------------------------------------
-- Query 5: Aspect Review Penetration per Product
-- Compares distinct reviews mentioning aspect vs total product reviews.
-- Both numerator and denominator are distinct review counts, yielding a true
-- penetration rate bounded between 0.0% and 100.0%.
-- -------------------------------------------------------------
SELECT 
    a.parent_asin,
    p.review_count AS total_product_reviews,
    a.aspect,
    a.review_count AS reviews_mentioning_aspect,
    ROUND(a.review_count * 100.0 / p.review_count, 1) AS aspect_review_penetration_pct,
    ROUND(a.avg_rating, 2) AS aspect_avg_rating,
    ROUND(p.avg_rating, 2) AS overall_product_avg_rating
FROM product_aspect_metrics a
JOIN product_aspect_metrics p ON a.parent_asin = p.parent_asin AND p.aspect = '__ALL_REVIEWS__'
WHERE substr(a.aspect, 1, 2) != '__' AND p.review_count >= 10
ORDER BY reviews_mentioning_aspect DESC
LIMIT 25;
