from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager
from database import init_db
from collector import run_collection
from analyzer import analyze_and_create_issues
from routers import issues, draft


async def scheduled_job():
    """30분마다 실행: 수집 → 분석"""
    await run_collection()
    await analyze_and_create_issues()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시
    init_db()
    print("DB 초기화 완료")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(scheduled_job, "interval", minutes=30)
    scheduler.start()
    print("스케줄러 시작 (30분 간격)")

    # 서버 시작 시 즉시 1회 수집
    await scheduled_job()

    yield

    # 서버 종료 시
    scheduler.shutdown()


app = FastAPI(
    title="미디어 인텔리전스 API",
    description="뉴스 수집·분석·브리핑 자동화 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(issues.router)
app.include_router(draft.router)


@app.post("/api/collect")
async def manual_collect():
    """수동 수집 트리거 (테스트용)"""
    await scheduled_job()
    return {"message": "수집 및 분석 완료"}


@app.get("/")
def root():
    return {"message": "미디어 인텔리전스 API 정상 동작 중"}