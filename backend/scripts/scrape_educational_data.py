import json
import os
import requests
from bs4 import BeautifulSoup
import time

# MEXT Middle School Curriculum Guidelines (Detailed Targets)
# 文部科学省 中学校学習指導要領 (平成29年告示) に基づく詳細な学習範囲
SUBJECTS_KEYWORDS = {
    "japanese": [
        "国語", "漢字", "書写", "古文", "漢文", "奥の細道", "枕草子", "竹取物語", "徒然草", "走れメロス", "故郷 (小説)", "高瀬舟", 
        "敬語", "現代文", "文学", "読書", "対話", "議論", "プレゼンテーション"
    ],
    "social": [
        "地理学", "世界地図", "アジア", "ヨーロッパ", "北アメリカ", "南アメリカ", "オセアニア", "アフリカ", "日本の地理", "九州地方", "中国地方", "四国地方", "近畿地方", "中部地方", "関東地方", "東北地方", "北海道地方", 
        "日本史", "縄文時代", "弥生時代", "古墳時代", "飛鳥時代", "奈良時代", "平安時代", "鎌倉時代", "室町時代", "安土桃山時代", "江戸時代", "明治維新", "大正デモクラシー", "第二次世界大戦", "戦後日本", 
        "政治", "日本国憲法", "三権分立", "国会", "内閣", "裁判所", "選挙", "経済", "需要と供給", "市場経済", "社会保障", "国際連合", "グローバル化"
    ],
    "math": [
        "算術", "正の数と負の数", "文字式", "一次方程式", "連立方程式", "二次方程式", "因数分解", "平方根", 
        "比例", "反比例", "一次関数", "二次関数", 
        "平面図形", "空間図形", "合同", "相似", "円周角の定理", "三平方の定理", 
        "確率", "統計学", "ヒストグラム", "平均値", "中央値", "最頻値", "箱ひげ図"
    ],
    "science": [
        "生物学", "細胞", "光合成", "呼吸", "消化", "血液循環", "神経系", "遺伝", "進化", 
        "化学", "原子", "分子", "化学反応式", "イオン", "酸と塩基", "酸化と還元", 
        "物理学", "光", "音", "力", "圧力", "電気", "電流", "電圧", "磁界", "エネルギー", "仕事", 
        "地学", "火山", "地震", "地層", "化石", "気象", "天気図", "天文学", "太陽系", "月", "金星", "銀河"
    ],
    "music": [
        "音楽学", "楽譜", "合唱", "器楽", "リコーダー", "ギター", "お琴", "和楽器", "クラシック音楽", "モーツァルト", "ベートーヴェン", "日本の伝統音楽", "雅楽"
    ],
    "art": [
        "美術", "デッサン", "水彩画", "版画", "彫刻", "デザイン", "色彩", "パース", "陶芸", "工芸", "日本の美術史", "西洋美術史"
    ],
    "pe": [
        "体育", "陸上競技", "短距離走", "長距離走", "走り幅跳び", "水泳", "器械運動", "跳び箱", "マット運動", "球技", "サッカー", "バスケットボール", "バレーボール", "テニス", "ベースボール", "卓球", "武道", "柔道", "剣道", "弓道", "ダンス", 
        "保健", "思春期", "ストレス", "生活習慣病", "応急手当", "環境衛生", "薬物乱用防止"
    ],
    "tech": [
        "技術学", "材料工学", "木材加工", "金属加工", "プラスチック加工", "電気回路", "モーター", "発電", "プログラミング", "情報ネットワーク", "サイバーセキュリティ", "ロボット工学"
    ],
    "home": [
        "家庭科", "食育", "栄養素", "調理", "裁縫", "衣服の管理", "住居", "家族", "保育", "高齢者福祉", "消費者の権利"
    ],
    "gs": [
        "英語", "英文法", "代名詞", "現在進行形", "過去形", "未来形", "助動詞", "不定詞", "動名詞", "比較級", "受動態", "現在完了形", "関係代名詞", "英会話", "英単語", "リスニング"
    ],
    "moral": [
        "道徳", "礼儀", "友情", "公正", "生命尊重", "自然愛護", "郷土愛", "国際理解"
    ],
    "integrated": [
        "総合的な学習の時間", "SDGs", "キャリア教育", "防災", "福祉", "ボランティア", "プレゼンテーション技法"
    ]
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
                    # Get more content (up to 8 paragraphs)
                    paragraphs = soup.find_all('p')[:8]
                    text_content = "\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 20])

                    if text_content:
                        # 2. Data Augmentation: Create multiple variations per knowledge piece
                        
                        # Style A: Direct explanation
                        scraped_data.append({
                            "text": f"### Subject: {subject}\n### User: {kw}について詳しく教えて！\n### Assistant: {text_content[:1000]}（出典: Wikipedia）"
                        })
                        
                        # Style B: Friendly classroom talk
                        scraped_data.append({
                            "text": f"### Subject: {subject}\n### User: {kw}がよくわからないんだけど、教えてくれる？\n### Assistant: もちろんだよ！{kw}はね、中学校の勉強だとこういうところがポイントなんだ。{text_content[:400]}...って感じかな。一緒に覚えよう！"
                        })

                        # Style C: Quiz style
                        scraped_data.append({
                            "text": f"### Subject: {subject}\n### User: {kw}に関するクイズを出して！\n### Assistant: いいよ！じゃあ問題。{kw}について、{text_content[:150]}...という特徴があるけど、これって何のことか覚えてるかな？答えは{kw}だよ！"
                        })

                        # Style D: Short summary
                        scraped_data.append({
                            "text": f"### Subject: {subject}\n### User: {kw}を短くまとめると？\n### Assistant: 簡単に言うとね、{text_content[:200]}...っていうことだよ！テストに出やすいからチェックしておこう。"
                        })

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
