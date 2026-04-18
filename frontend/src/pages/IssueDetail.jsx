import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { getIssueDetail, getIssueTrend, createDraft } from '../api';

const STANCE_COLOR = {
  보수: '#ef4444',
  중도: '#f59e0b',
  진보: '#3b82f6',
};

export default function IssueDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [issue, setIssue] = useState(null);
  const [trend, setTrend] = useState([]);
  const [direction, setDirection] = useState('');
  const [draft, setDraft] = useState(null);
  const [drafting, setDrafting] = useState(false);

  useEffect(() => {
    getIssueDetail(id).then((res) => setIssue(res.data));
    getIssueTrend(id).then((res) => setTrend(res.data.trend));
  }, [id]);

  const handleDraft = async () => {
    if (!direction.trim()) return;
    setDrafting(true);
    try {
      const res = await createDraft(parseInt(id), direction);
      setDraft(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setDrafting(false);
    }
  };

  if (!issue) return (
    <div style={{ textAlign: 'center', padding: 80, color: '#9ca3af' }}>불러오는 중...</div>
  );

  const perspectives = issue.analysis?.perspectives ?? [];
  const missingAngle = issue.analysis?.missing_angle ?? '';

  return (
    <div style={{ minHeight: '100vh', background: '#f9fafb', padding: '32px 24px' }}>
      <div style={{ maxWidth: 860, margin: '0 auto' }}>

        {/* 뒤로가기 */}
        <button
          onClick={() => navigate('/')}
          style={{ background: 'none', border: 'none', color: '#2563eb', fontSize: 14, cursor: 'pointer', marginBottom: 20, padding: 0 }}
        >
          ← 대시보드로 돌아가기
        </button>

        {/* 이슈 제목 */}
        <div style={{ background: '#fff', borderRadius: 12, padding: '24px 28px', marginBottom: 20, border: '1px solid #e5e7eb' }}>
          <span style={{
            fontSize: 12, fontWeight: 600,
            color: issue.category === '정치' ? '#2563eb' : '#16a34a',
            background: issue.category === '정치' ? '#eff6ff' : '#f0fdf4',
            padding: '2px 10px', borderRadius: 20,
          }}>
            {issue.category}
          </span>
          <h1 style={{ margin: '12px 0 8px', fontSize: 22, fontWeight: 800, color: '#111827' }}>
            {issue.title}
          </h1>
          <p style={{ margin: 0, fontSize: 15, color: '#4b5563', lineHeight: 1.7 }}>
            {issue.summary}
          </p>
        </div>

        {/* 매체별 논조 비교 */}
        {perspectives.length > 0 && (
          <div style={{ background: '#fff', borderRadius: 12, padding: '24px 28px', marginBottom: 20, border: '1px solid #e5e7eb' }}>
            <h2 style={{ margin: '0 0 16px', fontSize: 17, fontWeight: 700, color: '#111827' }}>
              매체별 논조 비교
            </h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f3f4f6' }}>
                  <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 13, color: '#6b7280', fontWeight: 600, borderRadius: '8px 0 0 0' }}>매체</th>
                  <th style={{ padding: '10px 14px', textAlign: 'left', fontSize: 13, color: '#6b7280', fontWeight: 600 }}>프레임 요약</th>
                  <th style={{ padding: '10px 14px', textAlign: 'center', fontSize: 13, color: '#6b7280', fontWeight: 600, borderRadius: '0 8px 0 0', whiteSpace: 'nowrap', width: 80 }}>논조</th>
                </tr>
              </thead>
              <tbody>
                {perspectives.map((p, i) => (
                  <tr key={i} style={{ borderTop: '1px solid #f3f4f6' }}>
                    <td style={{ padding: '12px 14px', fontWeight: 700, fontSize: 14, color: '#111827' }}>{p.media}</td>
                    <td style={{ padding: '12px 14px', fontSize: 14, color: '#4b5563', lineHeight: 1.5 }}>{p.frame}</td>
                    <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                      <span style={{
                        fontSize: 12, fontWeight: 700,
                        color: STANCE_COLOR[p.stance] ?? '#6b7280',
                        background: `${STANCE_COLOR[p.stance]}18` ?? '#f3f4f6',
                        padding: '3px 10px', borderRadius: 20, whiteSpace: 'nowrap',
                      }}>
                        {p.stance}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {missingAngle && (
              <div style={{ marginTop: 16, background: '#fffbeb', border: '1px solid #fcd34d', borderRadius: 8, padding: '12px 16px', fontSize: 14, color: '#92400e' }}>
                💡 <strong>비어있는 취재 각도:</strong> {missingAngle}
              </div>
            )}
          </div>
        )}

        {/* 트렌드 차트 */}
        {trend.length > 0 && (
          <div style={{ background: '#fff', borderRadius: 12, padding: '24px 28px', marginBottom: 20, border: '1px solid #e5e7eb' }}>
            <h2 style={{ margin: '0 0 16px', fontSize: 17, fontWeight: 700, color: '#111827' }}>
              이슈 언급량 트렌드
            </h2>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={trend}>
                <XAxis dataKey="time" tick={{ fontSize: 12 }} tickFormatter={(v) => v?.slice(11, 16)} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip labelFormatter={(v) => v?.slice(11, 16)} />
                <Line type="monotone" dataKey="mention_count" stroke="#2563eb" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 원문 기사 목록 */}
        {issue.articles?.length > 0 && (
          <div style={{ background: '#fff', borderRadius: 12, padding: '24px 28px', marginBottom: 20, border: '1px solid #e5e7eb' }}>
            <h2 style={{ margin: '0 0 16px', fontSize: 17, fontWeight: 700, color: '#111827' }}>
              원문 기사
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {issue.articles.map((a) => (
                <a
                  key={a.id}
                  href={a.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#f9fafb', borderRadius: 8, textDecoration: 'none' }}
                >
                  <span style={{ fontSize: 13, fontWeight: 700, color: '#1d4ed8', minWidth: 80 }}>{a.media}</span>
                  <span style={{ fontSize: 13, color: '#374151', flex: 1, margin: '0 12px' }}>{a.title}</span>
                  <span style={{ fontSize: 12, color: '#9ca3af' }}>→</span>
                </a>
              ))}
            </div>
          </div>
        )}

        {/* 기사 초안 드래프팅 */}
        <div style={{ background: '#fff', borderRadius: 12, padding: '24px 28px', border: '1px solid #e5e7eb' }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 17, fontWeight: 700, color: '#111827' }}>
            기사 초안 드래프팅
          </h2>
          <textarea
            value={direction}
            onChange={(e) => setDirection(e.target.value)}
            placeholder="취재 방향을 입력하세요. 예: 야당 입장 중심으로 작성, 경제적 영향 강조"
            style={{ width: '100%', minHeight: 80, padding: '12px 14px', borderRadius: 8, border: '1px solid #e5e7eb', fontSize: 14, resize: 'vertical', boxSizing: 'border-box', outline: 'none' }}
          />
          <button
            onClick={handleDraft}
            disabled={drafting || !direction.trim()}
            style={{
              marginTop: 12,
              background: '#1d4ed8',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '10px 24px',
              fontSize: 14,
              fontWeight: 600,
              cursor: drafting || !direction.trim() ? 'not-allowed' : 'pointer',
              opacity: drafting || !direction.trim() ? 0.6 : 1,
            }}
          >
            {drafting ? '생성 중...' : '초안 생성'}
          </button>

          {/* 생성된 초안 */}
          {draft && (
            <div style={{ marginTop: 24 }}>
              <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 700, color: '#111827' }}>제목 후보</h3>
              {draft.titles?.map((t, i) => (
                <div key={i} style={{ padding: '8px 14px', background: '#eff6ff', borderRadius: 8, marginBottom: 8, fontSize: 14, color: '#1e40af', fontWeight: 600 }}>
                  {i + 1}. {t}
                </div>
              ))}
              <h3 style={{ margin: '20px 0 12px', fontSize: 15, fontWeight: 700, color: '#111827' }}>기사 초안</h3>
              <div style={{ background: '#f9fafb', borderRadius: 8, padding: '16px 18px', fontSize: 14, color: '#374151', lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>
                {draft.draft}
              </div>
              {draft.further_reporting && (
                <div style={{ marginTop: 16, background: '#f0fdf4', border: '1px solid #86efac', borderRadius: 8, padding: '12px 16px', fontSize: 14, color: '#166534' }}>
                  📋 <strong>추가 취재 포인트:</strong> {draft.further_reporting}
                </div>
              )}
              <button
                onClick={() => navigator.clipboard.writeText(draft.draft)}
                style={{ marginTop: 12, background: '#f3f4f6', border: '1px solid #e5e7eb', borderRadius: 8, padding: '8px 18px', fontSize: 13, cursor: 'pointer' }}
              >
                초안 복사
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}