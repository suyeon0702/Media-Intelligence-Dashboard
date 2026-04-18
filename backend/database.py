from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc)

DATABASE_URL = "sqlite:///./media_intelligence.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Issue(Base):
    """수집된 이슈 (LLM이 클러스터링한 결과)"""
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)        # 이슈 제목
    summary = Column(Text, nullable=False)             # 핵심 요약 (3문장)
    category = Column(String(20), nullable=False)      # 정치 / 경제
    temperature = Column(Float, default=0.0)           # 이슈 온도 1~5
    analysis = Column(Text, nullable=True)             # 매체별 논조 분석 결과 (JSON string)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class Article(Base):
    """수집된 원문 기사"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, nullable=True)          # 연결된 이슈 ID
    media = Column(String(50), nullable=False)         # 매체명 (조선일보 등)
    title = Column(String(300), nullable=False)        # 기사 제목
    description = Column(Text, nullable=True)          # 기사 요약/본문 일부
    url = Column(String(500), nullable=False)          # 원문 URL
    category = Column(String(20), nullable=False)      # 정치 / 경제
    keyword = Column(String(50), nullable=True)        # 수집 키워드
    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, default=utcnow)


class TrendSnapshot(Base):
    """이슈 언급량 트렌드 스냅샷 (30분마다 저장)"""
    __tablename__ = "trend_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, nullable=False)
    mention_count = Column(Integer, default=0)         # 해당 시점 언급 기사 수
    snapshot_at = Column(DateTime, default=utcnow)


def init_db():
    """테이블 생성"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 의존성 주입용"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()