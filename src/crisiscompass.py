# -*- coding: utf-8 -*-
"""crisiscompass.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19cTVdQ1mPLmORQgrfxHVrjYntoyE4_BY
"""

!pip install transformers

import feedparser
import requests
from transformers import pipeline
from googletrans import Translator
import json

# Initialize translation and classification
translator = Translator()
classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")

# User-Agent header for requests
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Updated RSS feeds list
rss_feeds = [
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "region": "USA", "language": "en"},
    {"url": "http://feeds.bbci.co.uk/news/world/rss.xml", "region": "UK", "language": "en"},
    {"url": "https://www.lemonde.fr/rss/une.xml", "region": "France", "language": "fr"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml", "region": "Middle East", "language": "en"},
    {"url": "https://www.scmp.com/rss/91/feed", "region": "China (Alt)", "language": "en"},
    {"url": "https://venezuelanalysis.com/rss", "region": "Venezuela", "language": "en"},
    {"url": "http://www.chinadaily.com.cn/rss/world_rss.xml", "region": "China", "language": "zh"},
    {"url": "https://www.theguardian.com/world/rss", "region": "Global (Guardian)", "language": "en"},
    {"url": "https://runrun.es/feed/", "region": "Venezuela (Alt)", "language": "es"}
]

# Function to fetch RSS feed with headers
def fetch_feed_with_headers(url):
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)  # SSL verification disabled
        response.raise_for_status()  # Raise error for bad HTTP responses
        return feedparser.parse(response.content)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching feed: {url} - {e}")
        return None

# Function to classify and save articles to category-specific JSON files
def classify_and_save_articles(feed_info, feed, categories):
    region = feed_info["region"]
    language = feed_info["language"]
    print(f"\nProcessing feed: {feed_info['url']} (Region: {region}, Language: {language})")

    # Initialize category results dictionary
    category_results = {category: [] for category in categories}

    # Loop through feed entries
    for entry in feed.entries[:5]:  # Top 5 articles for now
        title = entry.get("title", "No Title")
        summary = entry.get("summary", "No Summary Available")
        text = title + " " + summary
        print(f"\nTitle: {title}")
        print(f"Summary: {summary}")

        # If article is not in English, translate it
        if language != "en":
            try:
                translated_text = translator.translate(text, src=language, dest="en").text
            except Exception as e:
                print(f"Translation error for {title}: {e}")
                translated_text = text  # Fallback if translation fails
        else:
            translated_text = text

        # Classify the article for relevant categories
        result = classifier(translated_text, candidate_labels=categories)
        relevance_score = result['scores'][0]
        most_relevant_topic = result['labels'][0]

        # Store articles that are relevant (adjust threshold as needed)
        if relevance_score > 0.3:  # Adjust the threshold based on your need
            for category in categories:
                if most_relevant_topic == category:
                    category_results[category].append({
                        "title": title,
                        "summary": summary,
                        "translated_text": translated_text,
                        "relevance_score": relevance_score,
                        "topic": most_relevant_topic,
                        "region": region,
                        "link": entry.get("link", "No link available")
                    })

    # Save results to JSON files for each category
    for category, articles in category_results.items():
        if articles:
            print(f"Saving {len(articles)} articles to {category}.json.")
            with open(f"{category}.json", "w") as f:
                json.dump(articles, f, indent=4)

# Main loop to process feeds and save articles
categories = ["geopolitical", "environment", "humanitarian", "economy", "science"]
for feed_info in rss_feeds:
    feed_url = feed_info["url"]
    feed = fetch_feed_with_headers(feed_url)

    if feed:
        classify_and_save_articles(feed_info, feed, categories)