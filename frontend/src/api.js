import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
});

export const getIssues = (category) =>
  api.get("/api/issues", { params: category ? { category } : {} });

export const getIssueDetail = (id) => api.get(`/api/issues/${id}`);

export const getIssueTrend = (id) => api.get(`/api/issues/${id}/trend`);

export const createDraft = (issueId, direction) =>
  api.post("/api/draft", { issue_id: issueId, direction });

export const manualCollect = () => api.post("/api/collect");
