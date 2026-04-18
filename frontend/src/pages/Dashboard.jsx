import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getIssues, manualCollect } from "../api";

const TEMP_COLORS = ["#e2e8f0", "#bfdbfe", "#93c5fd", "#f97316", "#ef4444"];

function TemperatureBar({ value }) {
  const filled = Math.round(value);
  return (
    <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
      {[1, 2, 3, 4, 5].map((i) => (
        <div
          key={i}
          style={{
            width: 20,
            height: 20,
            borderRadius: 4,
            background: i <= filled ? TEMP_COLORS[filled - 1] : "#e2e8f0",
          }}
        />
      ))}
      <span style={{ marginLeft: 6, fontSize: 13, color: "#6b7280" }}>
        {value?.toFixed(1)}
      </span>
    </div>
  );
}

function IssueCard({ issue, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: "#fff",
        border: "1px solid #e5e7eb",
        borderRadius: 12,
        padding: "20px 24px",
        cursor: "pointer",
        transition: "box-shadow 0.2s",
      }}
      onMouseEnter={(e) =>
        (e.currentTarget.style.boxShadow = "0 4px 16px rgba(0,0,0,0.10)")
      }
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = "none")}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 10,
        }}
      >
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: issue.category === "정치" ? "#2563eb" : "#16a34a",
            background: issue.category === "정치" ? "#eff6ff" : "#f0fdf4",
            padding: "2px 10px",
            borderRadius: 20,
          }}
        >
          {issue.category}
        </span>
        <TemperatureBar value={issue.temperature} />
      </div>
      <h3
        style={{
          margin: "0 0 8px",
          fontSize: 17,
          fontWeight: 700,
          color: "#111827",
        }}
      >
        {issue.title}
      </h3>
      <p style={{ margin: 0, fontSize: 14, color: "#6b7280", lineHeight: 1.6 }}>
        {issue.summary?.slice(0, 100)}...
      </p>
    </div>
  );
}

export default function Dashboard() {
  const [issues, setIssues] = useState([]);
  const [category, setCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const navigate = useNavigate();

  const fetchIssues = async () => {
    setLoading(true);
    try {
      const res = await getIssues(category);
      setIssues(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [category]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      await manualCollect();
      await fetchIssues();
    } finally {
      setCollecting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f9fafb",
        padding: "32px 24px",
      }}
    >
      <div style={{ maxWidth: 900, margin: "0 auto" }}>
        {/* 헤더 */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: 28,
          }}
        >
          <div>
            <h1
              style={{
                margin: 0,
                fontSize: 26,
                fontWeight: 800,
                color: "#111827",
              }}
            >
              🗞 미디어 인텔리전스
            </h1>
            <p style={{ margin: "4px 0 0", fontSize: 14, color: "#6b7280" }}>
              주요 이슈 실시간 수집·분석 대시보드
            </p>
          </div>
          <button
            onClick={handleCollect}
            disabled={collecting}
            style={{
              background: "#1d4ed8",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              padding: "10px 20px",
              fontSize: 14,
              fontWeight: 600,
              cursor: collecting ? "not-allowed" : "pointer",
              opacity: collecting ? 0.7 : 1,
            }}
          >
            {collecting ? "수집 중..." : "지금 수집"}
          </button>
        </div>

        {/* 카테고리 탭 */}
        <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
          {[null, "정치", "경제"].map((cat) => (
            <button
              key={cat ?? "all"}
              onClick={() => setCategory(cat)}
              style={{
                padding: "8px 20px",
                borderRadius: 20,
                border: "1px solid #e5e7eb",
                background: category === cat ? "#1d4ed8" : "#fff",
                color: category === cat ? "#fff" : "#374151",
                fontWeight: 600,
                fontSize: 14,
                cursor: "pointer",
              }}
            >
              {cat ?? "전체"}
            </button>
          ))}
        </div>

        {/* 이슈 목록 */}
        {loading ? (
          <div style={{ textAlign: "center", padding: 80, color: "#9ca3af" }}>
            불러오는 중...
          </div>
        ) : issues.length === 0 ? (
          <div style={{ textAlign: "center", padding: 80, color: "#9ca3af" }}>
            수집된 이슈가 없습니다. '지금 수집' 버튼을 눌러주세요.
          </div>
        ) : (
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}
          >
            {issues.map((issue) => (
              <IssueCard
                key={issue.id}
                issue={issue}
                onClick={() => navigate(`/issues/${issue.id}`)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
