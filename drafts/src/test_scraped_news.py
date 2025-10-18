import json
import os

with open("../data/raw_news/articles.jsonl", "r") as f:
    lines = f.readlines()
    print(f"Number of lines: {len(lines)}")
    for line in lines[-10:-1]:  # Display the last 5 articles
        article = json.loads(line)
        print(f"Title: {article.get('title', 'No title')}")
        print(f"Body Length: {len(article.get('body', ''))} characters")
        print("-" * 40)



