import httpx
import feedparser
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from database import SessionLocal, Article

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 수집 키워드
KEYWORDS = {
    "정치": ["국회", "대통령", "여야", "정책", "선거"],
    "경제": ["금리", "환율", "코스피", "기업", "경제정책"],
}

# 비교 대상 매체
TARGET_MEDIA = ["조선일보", "중앙일보", "한겨레", "경향신문", "연합뉴스"]


async def fetch_naver_news(keyword: str, media: str) -> list[dict]:
    """네이버 뉴스 API로 특정 키워드 + 매체 기사 수집"""
    url = "https://openapi.naver.com/v1/search/news.json"
    params = {
        "query": f"{keyword} {media}",
        "display": 5,
        "sort": "date",
    }
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    articles = []
    for item in data.get("items", []):
        articles.append({
            "media": media,
            "title": _clean_html(item.get("title", "")),
            "description": _clean_html(item.get("description", "")),
            "url": item.get("originallink") or item.get("link", ""),
            "published_at": _parse_date(item.get("pubDate", "")),
        })
    return articles


async def fetch_yonhap_rss() -> list[dict]:
    """연합뉴스 RSS 수집"""
    rss_urls = [
        "https://www.yna.co.kr/rss/politics.xml",   # 정치
        "https://www.yna.co.kr/rss/economy.xml",    # 경제
    ]

    articles = []
    for rss_url in rss_urls:
        category = "정치" if "politics" in rss_url else "경제"
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            articles.append({
                "media": "연합뉴스",
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "category": category,
                "published_at": datetime.now(timezone.utc),
            })
    return articles


async def run_collection():
    """전체 수집 파이프라인 실행 (스케줄러에서 호출)"""
    print(f"[{datetime.now(timezone.utc)}] 뉴스 수집 시작...")
    db = SessionLocal()

    try:
        total = 0

        # 1. 네이버 뉴스 API — 키워드 × 매체 수집
        for category, keywords in KEYWORDS.items():
            for keyword in keywords:
                for media in TARGET_MEDIA:
                    try:
                        articles = await fetch_naver_news(keyword, media)
                        for a in articles:
                            # 중복 URL 체크
                            exists = db.query(Article).filter(
                                Article.url == a["url"]
                            ).first()
                            if not exists:
                                db.add(Article(
                                    media=a["media"],
                                    title=a["title"],
                                    description=a["description"],
                                    url=a["url"],
                                    category=category,
                                    keyword=keyword,
                                    published_at=a["published_at"],
                                ))
                                total += 1
                    except Exception as e:
                        print(f"  [오류] {media} / {keyword}: {e}")

        # 2. 연합뉴스 RSS
        try:
            rss_articles = await fetch_yonhap_rss()
            for a in rss_articles:
                exists = db.query(Article).filter(
                    Article.url == a["url"]
                ).first()
                if not exists:
                    db.add(Article(
                        media=a["media"],
                        title=a["title"],
                        description=a["description"],
                        url=a["url"],
                        category=a["category"],
                        keyword="RSS",
                        published_at=a["published_at"],
                    ))
                    total += 1
        except Exception as e:
            print(f"  [오류] 연합뉴스 RSS: {e}")

        db.commit()
        print(f"[완료] 새 기사 {total}건 저장")

    finally:
        db.close()


def _clean_html(text: str) -> str:
    """네이버 API 응답에서 HTML 태그 제거"""
    import re
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def _parse_date(date_str: str) -> datetime:
    """pubDate 문자열 파싱"""
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)