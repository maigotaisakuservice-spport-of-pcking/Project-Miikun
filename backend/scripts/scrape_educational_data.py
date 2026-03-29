import json
import os

SUBJECTS = [
    "japanese", "math", "science", "social", "gs",
    "pe", "tech", "home", "moral", "career"
]

def scrape_and_format():
    """
    Template for educational data scraping.
    In a real implementation, this would use BeautifulSoup or Scrapy.
    """
    print("Scraping educational materials...")

    all_data = []
    for subject in SUBJECTS:
        # Simulated scraped content (In real life, this would be scraped from textbooks/sites)
        print(f"Gathering data for: {subject}")
        content = [
            {"q": f"{subject}の面白い雑学教えて", "a": f"{subject}の雑学だね！実は...（ここに審議済みの正確な情報を入れる）"},
            {"q": f"{subject}の試験対策はどうすればいい？", "a": "教科書の太字の部分を中心に、まずは全体を把握するのがいいと思うよ！"}
        ]

        for item in content:
            data = {
                "subject": subject,
                "text": f"### Subject: {subject}\n### User: {item['q']}\n### Assistant: {item['a']}"
            }
            all_data.append(data)

    with open("scraped_data.jsonl", "w", encoding="utf-8") as f:
        for entry in all_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Scraped {len(all_data)} items and saved to scraped_data.jsonl")

if __name__ == "__main__":
    scrape_and_format()
