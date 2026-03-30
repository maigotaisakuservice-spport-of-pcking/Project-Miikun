import json
import os
import requests
from bs4 import BeautifulSoup
import time

# MEXT Middle School Curriculum Guidelines (Comprehensive Targets)
# 文部科学省 中学校学習指導要領 (平成29年告示) に基づく詳細な学習範囲
SUBJECTS_KEYWORDS = {
    "japanese": ["中学校 国語 話すこと・聞くこと", "書くこと", "読むこと", "情報の扱い方", "我が国の言語文化 (古文・漢文・書写)"],
    "social": ["中学校 地理分野 (世界の様々な地域, 日本の様々な地域)", "歴史分野 (近代の日本と世界, 現代の日本と世界)", "公民分野 (現代社会と私たちの生活, 私たちの生活と経済, 私たちの生活と政治)"],
    "math": ["中学校 数学 数と式 (正負の数, 文字の式, 一次方程式)", "図形 (平面図形, 空間図形)", "関数 (比例, 反比例)", "データの活用 (ヒストグラム, 代表値)"],
    "science": ["中学校 理科 第1分野 (物質の成り立ち, 化学変化, 電気, 運動とエネルギー)", "第2分野 (生物の観察, 植物・動物の生活, 大地の変化, 気象の観察, 天体)"],
    "music": ["中学校 音楽 歌唱", "器楽", "創作", "鑑賞 (我が国の伝統音楽を含む)"],
    "art": ["中学校 美術 表現 (描画, 立体, デザイン, 工芸)", "鑑賞 (美術文化の継承と創造)"],
    "pe": ["中学校 保健体育 体育分野 (陸上競技, 水泳, 球技, 武道, ダンス)", "保健分野 (心身の機能の発達, 健康と生活, 傷害の防止, 精神の健康)"],
    "tech": ["中学校 技術・家庭(技術分野) 材料と加工の技術", "生物育成の技術", "エネルギー変換の技術", "情報の技術"],
    "home": ["中学校 技術・家庭(家庭分野) 食生活と自立", "衣生活・住生活と自立", "家族・家庭と子供の成長", "消費生活・環境と自立"],
    "gs": ["中学校 英語 聞くこと", "読むこと", "話すこと［やり取り・発表］", "書くこと", "言語材料 (助動詞, 不定詞, 現在完了形, 受動態, 関係代名詞)"],
    "moral": ["中学校 道徳 自己を見つめる", "人との関わり", "集団や社会との関わり", "生命や自然、崇高なものとの関わり"],
    "integrated": ["中学校 総合的な学習の時間 探究的な学習", "地域社会や世界の課題", "自己の生き方と進路"]
}

def scrape_educational_content():
    """
    Scrapes educational content from accessible public domains (Wikipedia/DuckDuckGo)
    targeting MEXT middle school keywords to gather real contextual data.
    """
    print("Scraping Japanese Middle School (MEXT-aligned) educational content...")

    scraped_data = []
    headers = {"User-Agent": "MiikunEducationalScraper/1.0 (Educational AI Project)"}

    for subject, keywords in SUBJECTS_KEYWORDS.items():
        print(f"--- Scraping Subject: {subject} ---")
        for kw in keywords:
            try:
                # 1. Search Wikipedia for key terms
                print(f"  Searching: {kw}")
                wiki_url = f"https://ja.wikipedia.org/wiki/{kw.replace('中学校 ', '')}"
                response = requests.get(wiki_url, headers=headers, timeout=10)

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    # Get first few paragraphs
                    paragraphs = soup.find_all('p')[:3]
                    text_content = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 20])

                    if text_content:
                        # Format as a QA pair
                        entry = {
                            "text": f"### Subject: {subject}\n### User: {kw}について教えて！\n### Assistant: {text_content[:800]}（出典: Wikipedia）"
                        }
                        scraped_data.append(entry)

                # 2. Add some synthetic conversational variations to the real data
                # to help the AI learn the "Miikun" persona with real knowledge
                if len(scraped_data) > 0 and scraped_data[-1]["text"].startswith(f"### Subject: {subject}"):
                    base_knowledge = scraped_data[-1]["text"].split("### Assistant: ")[1]
                    variation = {
                        "text": f"### Subject: {subject}\n### User: {kw}って中学校の勉強だとどんな感じ？\n### Assistant: {kw}だね！文科省の指針だと、こういうことが大事だよ。{base_knowledge[:200]}...って感じかな。一緒に頑張ろう！"
                    }
                    scraped_data.append(variation)

            except Exception as e:
                print(f"  Error scraping {kw}: {e}")

            time.sleep(1) # Respectful delay

    # Save to project root for easy access by training scripts
    output_file = "scraped_data.jsonl"

    with open(output_file, "w", encoding="utf-8") as f:
        for entry in scraped_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print(f"Success: Scraped {len(scraped_data)} MEXT-aligned items to {output_file}")

if __name__ == "__main__":
    scrape_educational_content()
