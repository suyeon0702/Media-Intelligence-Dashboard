import os
import json
from dotenv import load_dotenv
from google import genai
from database import SessionLocal, Article, Issue, TrendSnapshot

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def _generate(prompt: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()

async def analyze_and_create_issues():
    """수집된 기사를 분석하여 이슈 생성/업데이트"""
    db = SessionLocal()
    try:
        # 아직 이슈에 연결되지 않은 기사들 가져오기
        unlinked_articles = db.query(Article).filter(
            Article.issue_id == None
        ).all()

        if not unlinked_articles:
            print("[분석] 새로 수집된 기사 없음")
            return

        print(f"[분석] 미분류 기사 {len(unlinked_articles)}건 분석 시작...")

        # 카테고리별로 분리
        politics = [a for a in unlinked_articles if a.category == "정치"]
        economy = [a for a in unlinked_articles if a.category == "경제"]

        for category, articles in [("정치", politics), ("경제", economy)]:
            if not articles:
                continue

            # 1단계: 이슈 클러스터링 + 요약
            issues_data = await _cluster_and_summarize(articles, category)

            for issue_data in issues_data:
                # 이슈 DB 저장
                issue = Issue(
                    title=issue_data["title"],
                    summary=issue_data["summary"],
                    category=category,
                    temperature=issue_data["temperature"],
                )
                db.add(issue)
                db.flush()  # ID 생성

                # 관련 기사 연결
                for article_id in issue_data.get("article_ids", []):
                    article = db.query(Article).filter(
                        Article.id == article_id
                    ).first()
                    if article:
                        article.issue_id = issue.id

                # 2단계: 매체별 논조 분석
                related_articles = [
                    a for a in articles
                    if a.id in issue_data.get("article_ids", [])
                ]
                if related_articles:
                    analysis = await _analyze_media_perspective(
                        issue_data["title"], related_articles
                    )
                    issue.analysis = json.dumps(analysis, ensure_ascii=False)

                # 트렌드 스냅샷 저장
                db.add(TrendSnapshot(
                    issue_id=issue.id,
                    mention_count=len(issue_data.get("article_ids", [])),
                ))

        db.commit()
        print("[분석] 완료")

    finally:
        db.close()


async def _cluster_and_summarize(articles: list, category: str) -> list[dict]:
    """기사 목록을 이슈로 클러스터링하고 요약"""
    articles_text = "\n".join([
        f"[ID:{a.id}] [{a.media}] {a.title} / {a.description or ''}"
        for a in articles
    ])

    prompt = f"""
다음은 오늘 수집된 {category} 분야 뉴스 기사 목록입니다.

{articles_text}

위 기사들을 분석하여 주요 이슈별로 묶어주세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

{{
  "issues": [
    {{
      "title": "이슈 제목 (20자 이내)",
      "summary": "핵심 요약 3문장",
      "temperature": 3.5,
      "article_ids": [1, 2, 3]
    }}
  ]
}}

온도 기준:
- 1.0~2.0: 소규모 이슈
- 2.0~3.0: 중간 관심
- 3.0~4.0: 주요 이슈
- 4.0~5.0: 매우 뜨거운 이슈 (언급량 많음)
"""

    try:
        text = await _generate(prompt)
        # JSON 코드블록 제거
        text = text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        return data.get("issues", [])
    except Exception as e:
        print(f"[오류] 클러스터링 실패: {e}")
        return []


async def _analyze_media_perspective(issue_title: str, articles: list) -> dict:
    """매체별 논조 비교 분석"""
    articles_text = "\n".join([
        f"[{a.media}] 제목: {a.title}\n내용: {a.description or '없음'}\n"
        for a in articles
    ])

    prompt = f"""
이슈: "{issue_title}"

아래는 각 매체의 관련 기사입니다:

{articles_text}

각 매체가 이 이슈를 어떤 프레임과 논조로 다루고 있는지 분석해주세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

{{
  "perspectives": [
    {{
      "media": "매체명",
      "frame": "이 매체의 프레임 요약 (1~2문장)",
      "stance": "보수" 또는 "중도" 또는 "진보"
    }}
  ],
  "missing_angle": "아직 다뤄지지 않은 취재 각도 제안 (1~2문장)"
}}
"""

    try:
        text = await _generate(prompt)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[오류] 논조 분석 실패: {e}")
        return {}


async def generate_draft(issue_id: int, direction: str) -> dict:
    """기사 초안 드래프팅"""
    db = SessionLocal()
    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return {"error": "이슈를 찾을 수 없습니다"}

        articles = db.query(Article).filter(
            Article.issue_id == issue_id
        ).all()

        articles_text = "\n".join([
            f"[{a.media}] {a.title}\n{a.description or ''}"
            for a in articles
        ])

        prompt = f"""
이슈: {issue.title}
요약: {issue.summary}
취재 방향: {direction}

참고 기사:
{articles_text}

위 내용을 바탕으로 서울신문 스타일의 기사 초안을 작성해주세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.

{{
  "titles": [
    "제목 후보 1",
    "제목 후보 2",
    "제목 후보 3"
  ],
  "draft": "기사 초안 (역피라미드 구조, 600~800자)",
  "further_reporting": "추가 취재 포인트 (2~3가지)"
}}
"""

        text = await _generate(prompt)
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except Exception as e:
        print(f"[오류] 초안 생성 실패: {e}")
        return {"error": str(e)}
    finally:
        db.close()