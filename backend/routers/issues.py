from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Issue, Article, TrendSnapshot
import json

router = APIRouter(prefix="/api/issues", tags=["issues"])


@router.get("")
def get_issues(category: str = None, db: Session = Depends(get_db)):
    """이슈 목록 조회 (카테고리 필터 선택)"""
    query = db.query(Issue)
    if category:
        query = query.filter(Issue.category == category)
    issues = query.order_by(Issue.temperature.desc()).all()

    return [
        {
            "id": issue.id,
            "title": issue.title,
            "summary": issue.summary,
            "category": issue.category,
            "temperature": issue.temperature,
            "created_at": issue.created_at,
        }
        for issue in issues
    ]


@router.get("/{issue_id}")
def get_issue_detail(issue_id: int, db: Session = Depends(get_db)):
    """이슈 상세 + 논조 분석 + 관련 기사 URL"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다")

    articles = db.query(Article).filter(
        Article.issue_id == issue_id
    ).all()

    analysis = {}
    if issue.analysis:
        try:
            analysis = json.loads(issue.analysis)
        except Exception:
            pass

    return {
        "id": issue.id,
        "title": issue.title,
        "summary": issue.summary,
        "category": issue.category,
        "temperature": issue.temperature,
        "analysis": analysis,
        "articles": [
            {
                "id": a.id,
                "media": a.media,
                "title": a.title,
                "url": a.url,
                "published_at": a.published_at,
            }
            for a in articles
        ],
        "created_at": issue.created_at,
    }


@router.get("/{issue_id}/trend")
def get_issue_trend(issue_id: int, db: Session = Depends(get_db)):
    """이슈 언급량 트렌드 데이터"""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다")

    snapshots = db.query(TrendSnapshot).filter(
        TrendSnapshot.issue_id == issue_id
    ).order_by(TrendSnapshot.snapshot_at.asc()).all()

    return {
        "issue_id": issue_id,
        "issue_title": issue.title,
        "trend": [
            {
                "time": s.snapshot_at,
                "mention_count": s.mention_count,
            }
            for s in snapshots
        ]
    }