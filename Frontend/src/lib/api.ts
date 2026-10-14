import {
  agentExecutionManager,
  AgentCancelledError,
} from "./agent-execution";
export { agentExecutionManager, AgentCancelledError };

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

export function getOAuthLoginUrl(provider: "google" | "github"): string {
  const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost:8080";
  return `${API_BASE_URL}/auth/login/${provider}?origin=${encodeURIComponent(origin)}`;
}

async function handleResponse(response: Response) {
  const data = await response.json();

  if (response.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new Error("Session expired. Please login again.");
  }

  if (!response.ok) {
    throw new Error(
      data?.message ||
        data?.detail ||
        "Something went wrong"
    );
  }

  return data;
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export function getAuthJsonHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  return getAuthHeaders({
    "Content-Type": "application/json",
    ...extraHeaders,
  });
}

// ==========================

// Health
// ==========================
export async function checkBackend() {
  const response = await fetch(
    `${API_BASE_URL}/health`
  );

  return handleResponse(response);
}

// ==========================
// Authentication
// ==========================
export async function login(
  email: string,
  password: string
) {
  const response = await fetch(
    `${API_BASE_URL}/login`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );

  return handleResponse(response);
}

export async function register(
  name: string,
  email: string,
  password: string
) {
  const response = await fetch(
    `${API_BASE_URL}/register`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        email,
        password,
      }),
    }
  );

  return handleResponse(response);
}

export async function getCurrentUser(
  token: string
) {
  const response = await fetch(
    `${API_BASE_URL}/me`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return handleResponse(response);
}

// ==========================
// Upload PDF
// ==========================
export async function uploadPaper(
  file: File
) {
  const formData = new FormData();

  formData.append("file", file);

  const response = await fetch(
    `${API_BASE_URL}/upload`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    }
  );

  return handleResponse(response);
}

// ==========================
// Get Papers
// ==========================
export async function getPapers() {
  const response = await fetch(
    `${API_BASE_URL}/papers`,
    {
      headers: getAuthHeaders(),
    }
  );

  return handleResponse(response);
}

// ==========================
// Delete Paper
// ==========================
export async function deletePaper(
  filename: string
) {
  const response = await fetch(
    `${API_BASE_URL}/papers/${encodeURIComponent(
      filename
    )}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );

  return handleResponse(response);
}

// ==========================
// Plagiarism / Similarity Checker
// ==========================
export interface PlagiarismMatch {
  id: number;
  match_id?: number;
  page: number;
  matched_text: string;
  source_passage: string;
  source_document: string;
  source_page?: number;
  similarity: number;
  similarity_percentage?: number;
  match_type: "exact_match" | "near_exact" | "similar_text" | string;
}

export interface PlagiarismResult {
  pdf_id: string;
  filename: string;
  title: string;
  similarity_score: number;
  original_content: number;
  originality_score?: number;
  potential_matches_count: number;
  matches_count?: number;
  comparison_sources_count: number;
  total_compared_documents?: number;
  comparison_scope: string;
  comparison_corpus?: string;
  total_words_analyzed: number;
  matches: PlagiarismMatch[];
  checked_at: string;
  analyzed_at?: string;
  cached?: boolean;
}

export interface PlagiarismCheckResponse {
  success: boolean;
  message: string;
  data: PlagiarismResult;
}

export async function checkPlagiarism(
  pdfId: string,
  forceRefresh: boolean = false
): Promise<PlagiarismCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/plagiarism/check`, {
    method: "POST",
    headers: getAuthJsonHeaders(),
    body: JSON.stringify({
      pdf_id: pdfId,
      force_refresh: forceRefresh,
    }),
  });

  return handleResponse(response);
}

// ==========================
// AI Search & Document Chat
// ==========================
export interface ChatSource {
  chunk_index?: number;
  page?: number | string | null;
  section?: string | null;
  snippet?: string;
  distance?: number;
}

export interface ChatResponse {
  status: string;
  answer?: string;
  sources?: ChatSource[];
  paper_name?: string;
  session_id?: string;
  data?: {
    answer?: string;
    sources?: ChatSource[];
    paper_name?: string;
    session_id?: string;
    query?: string;
  };
}

export async function searchPaper(
  query: string,
  sessionId: string,
  paperName?: string | null
): Promise<ChatResponse> {
  const response = await fetch(
    `${API_BASE_URL}/search`,
    {
      method: "POST",
      headers: getAuthJsonHeaders(),
      body: JSON.stringify({
        query,
        session_id: sessionId,
        paper_name: paperName || null,
      }),
    }
  );

  return handleResponse(response);
}


// ==========================
// Search History
// ==========================
export async function getSearchHistory(
  sessionId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/search-history/${encodeURIComponent(
      sessionId
    )}`
  );

  return handleResponse(response);
}

// ==========================
// Delete Search History
// ==========================
export async function deleteSearchHistory(
  sessionId: string
) {
  const response = await fetch(
    `${API_BASE_URL}/search-history/${encodeURIComponent(
      sessionId
    )}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(response);
}

// ==========================
// Get Sessions
// ==========================
export async function getSessions() {
  const response = await fetch(
    `${API_BASE_URL}/sessions`
  );

  return handleResponse(response);
}

// ==========================
// Structured AI Analysis Types
// ==========================
export type AnalysisType =
  | "summary"
  | "gaps"
  | "datasets"
  | "experiments"
  | "literature"
  | "novelty"
  | "report"
  | "ppt";

export type AnalysisResponse = {
  success: boolean;
  message: string;
  paper_name: string;
  analysis_type: AnalysisType;
  result: string;
};

// ==========================
// Intelligent Coordinator Analysis
// ==========================
export async function runAnalysis(
  paperName?: string | null,
  analysisType: AnalysisType = "summary",
  query?: string | null,
  options?: { signal?: AbortSignal; executionId?: number }
): Promise<AnalysisResponse> {
  if (!paperName?.trim() && !query?.trim()) {
    throw new Error("Either a research paper or query is required.");
  }

  if (!analysisType) {
    throw new Error("Analysis type is required.");
  }

  // Manage single active agent execution
  let signal: AbortSignal;
  let executionId: number;

  if (options?.signal && options?.executionId !== undefined) {
    signal = options.signal;
    executionId = options.executionId;
  } else {
    const started = agentExecutionManager.start(analysisType);
    signal = started.signal;
    executionId = started.executionId;
  }

  const payload: Record<string, any> = {
    analysis_type: analysisType,
  };

  if (paperName?.trim()) {
    payload.paper_name = paperName.trim();
  }
  if (query?.trim()) {
    payload.query = query.trim();
  }

  console.log(
    "ResearchX Coordinator Analysis:",
    payload
  );

  try {
    const response = await fetch(
      `${API_BASE_URL}/analysis/run`,
      {
        method: "POST",
        headers: getAuthJsonHeaders(),
        body: JSON.stringify(payload),
        signal,
      }
    );

    if (signal.aborted || !agentExecutionManager.isActive(executionId)) {
      throw new AgentCancelledError();
    }

    const data = await handleResponse(response);

    if (signal.aborted || !agentExecutionManager.isActive(executionId)) {
      throw new AgentCancelledError();
    }

    console.log(
      "Coordinator Result:",
      data
    );

    return data as AnalysisResponse;
  } catch (err: any) {
    if (err.name === "AbortError" || signal.aborted || err instanceof AgentCancelledError) {
      throw new AgentCancelledError();
    }
    throw err;
  } finally {
    if (agentExecutionManager.isActive(executionId)) {
      agentExecutionManager.stop(analysisType);
    }
  }
}

export type PlagiarismAudit = {
  originality_score: number;
  similarity_score: number;
  risk_level: "Low" | "Moderate" | "High" | string;
  verdict: string;
  total_words_analyzed: number;
  matches_count: number;
  comparison_corpus: string;
  checked_at: string;
  updated_content_summary?: string;
  matches?: Array<{
    matched_source: string;
    similarity: number;
    snippet: string;
    matched_passage: string;
  }>;
};

export type ReportResponse = {
  success: boolean;
  message: string;
  paper_name: string;
  result: string;
  plagiarism?: PlagiarismAudit;
  edit_summary?: string;
};

export async function generateIEEEReport(
  paperName: string,
  query?: string,
  options?: { signal?: AbortSignal; executionId?: number; force_refresh?: boolean }
): Promise<ReportResponse> {
  let signal: AbortSignal;
  let executionId: number;

  if (options?.signal && options?.executionId !== undefined) {
    signal = options.signal;
    executionId = options.executionId;
  } else {
    const started = agentExecutionManager.start("report");
    signal = started.signal;
    executionId = started.executionId;
  }

  const payload: Record<string, any> = {
    paper_name: paperName,
  };
  if (query?.trim()) {
    payload.query = query.trim();
  }
  if (options?.force_refresh) {
    payload.force_refresh = true;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/report/generate`,
      {
        method: "POST",
        headers: getAuthJsonHeaders(),
        body: JSON.stringify(payload),
        signal,
      }
    );

    if (signal.aborted || !agentExecutionManager.isActive(executionId)) {
      throw new AgentCancelledError();
    }

    return await handleResponse(response);
  } catch (err: any) {
    if (err.name === "AbortError" || signal.aborted || err instanceof AgentCancelledError) {
      throw new AgentCancelledError();
    }
    throw err;
  } finally {
    if (agentExecutionManager.isActive(executionId)) {
      agentExecutionManager.stop("report");
    }
  }
}

export async function downloadIEEEReportPDF(
  paperName: string,
  query?: string,
  content?: string
): Promise<Blob> {
  const payload: Record<string, any> = {
    paper_name: paperName,
  };
  if (query?.trim()) {
    payload.query = query.trim();
  }
  if (content?.trim()) {
    payload.content = content.trim();
  }

  const response = await fetch(
    `${API_BASE_URL}/report/pdf`,
    {
      method: "POST",
      headers: getAuthJsonHeaders(),
      body: JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    let errorDetail = "Failed to download IEEE report PDF";
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      const errText = await response.text();
      if (errText) errorDetail = errText;
    }
    throw new Error(errorDetail);
  }

  return await response.blob();
}

// ==========================
// Generate Presentation
// ==========================

export type PresentationResponse = {
  success: boolean;
  presentation: string;
};

export async function generatePresentation(
  paperName: string,
  options?: { signal?: AbortSignal; executionId?: number }
): Promise<PresentationResponse> {
  let signal: AbortSignal;
  let executionId: number;

  if (options?.signal && options?.executionId !== undefined) {
    signal = options.signal;
    executionId = options.executionId;
  } else {
    const started = agentExecutionManager.start("ppt");
    signal = started.signal;
    executionId = started.executionId;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/presentation/generate`,
      {
        method: "POST",
        headers: getAuthJsonHeaders(),
        body: JSON.stringify({
          paper_name: paperName,
        }),
        signal,
      }
    );

    if (signal.aborted || !agentExecutionManager.isActive(executionId)) {
      throw new AgentCancelledError();
    }

    return await handleResponse(response);
  } catch (err: any) {
    if (err.name === "AbortError" || signal.aborted || err instanceof AgentCancelledError) {
      throw new AgentCancelledError();
    }
    throw err;
  } finally {
    if (agentExecutionManager.isActive(executionId)) {
      agentExecutionManager.stop("ppt");
    }
  }
}

export async function exportPPTX(
  paperName: string,
  presentationText?: string
): Promise<Blob> {
  const payload: Record<string, any> = {
    paper_name: paperName,
  };
  if (presentationText?.trim()) {
    payload.presentation_text = presentationText.trim();
  }

  const response = await fetch(`${API_BASE_URL}/ppt/generate`, {
    method: "POST",
    headers: getAuthJsonHeaders(),
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let errorDetail = "Failed to export presentation (.pptx)";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch {
      const errText = await response.text();
      if (errText) errorDetail = errText;
    }
    throw new Error(errorDetail);
  }

  return await response.blob();
}

// ==========================
// Dashboard
// ==========================

export type DashboardResponse = {
  success: boolean;
  data: {
    papers: number;
    projects: number;
    reports: number;
    presentations: number;
    recentResearch: any[];
    tasks: any[];
    activity: any[];
    progress: any[];
    suggestions: string[];
  };
};

export interface SearchResult {
  title: string;
  uploaded_at: string;
}

export interface DashboardSearchResponse {
  success: boolean;
  results: SearchResult[];
}

export async function getDashboard(): Promise<DashboardResponse> {
  const response = await fetch(
    `${API_BASE_URL}/dashboard`,
    {
      headers: getAuthHeaders(),
    }
  );

  return handleResponse(response);
}

export async function searchDashboard(
  query: string
): Promise<DashboardSearchResponse> {
  console.log("Calling API:", query);

  const response = await fetch(
    `${API_BASE_URL}/dashboard/search?query=${encodeURIComponent(query)}`,
    {
      headers: getAuthHeaders(),
    }
  );

  const data = await handleResponse(response);

  console.log("API Returned:", data);

  return data;
}

// ==========================
// Research Papers Search
// ==========================

export interface ResearchPaper {
  id?: string;
  paperId?: string;
  title: string;
  authors: string[] | string;
  authors_str?: string;
  summary: string;
  abstract?: string;
  published: string;
  published_date?: string;
  year?: number;
  year_group?: string;
  citation_count: number;
  citations?: number;
  venue: string;
  source: string;
  publication_type?: string;
  is_ieee?: boolean;
  why_chosen?: string;
  relevance_reason?: string;
  relevance_score?: number;
  relevance_badge?: string;
  key_contribution?: string;
  pdf_url?: string;
  url?: string;
  tags?: string[];
  search_corrected_query?: string;
  search_original_query?: string;
}

export async function searchResearchPapers(
  query: string,
  sortBy: string = "relevance",
  year?: string,
  source?: string
): Promise<{
  success: boolean;
  results: ResearchPaper[];
  total?: number;
  query?: string;
  original_query?: string;
  corrected_query?: string;
  filter_source?: string;
  filter_year?: string;
}> {
  const params = new URLSearchParams({
    query: query,
    sort_by: sortBy,
  });

  if (year && year !== "all") {
    params.append("year", year);
  }

  if (source && source !== "all") {
    params.append("source", source);
  }

  const response = await fetch(
    `${API_BASE_URL}/api/search?${params.toString()}`,
    {
      headers: getAuthHeaders(),
    }
  );

  return handleResponse(response);
}

export async function runAllWorkspaceAgents(
  topic: string,
  sessionId: string,
  papers: any[],
  options?: { signal?: AbortSignal; executionId?: number }
) {
  let signal: AbortSignal;
  let executionId: number;

  if (options?.signal && options?.executionId !== undefined) {
    signal = options.signal;
    executionId = options.executionId;
  } else {
    const started = agentExecutionManager.start("all");
    signal = started.signal;
    executionId = started.executionId;
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/analysis/workspace/run-all`,
      {
        method: "POST",
        headers: getAuthJsonHeaders(),
        body: JSON.stringify({
          topic,
          session_id: sessionId,
          papers,
        }),
        signal,
      }
    );

    if (signal.aborted || !agentExecutionManager.isActive(executionId)) {
      throw new AgentCancelledError();
    }

    return await handleResponse(response);
  } catch (err: any) {
    if (err.name === "AbortError" || signal.aborted || err instanceof AgentCancelledError) {
      throw new AgentCancelledError();
    }
    throw err;
  } finally {
    if (agentExecutionManager.isActive(executionId)) {
      agentExecutionManager.stop("all");
    }
  }
}

export async function deleteWorkspaceSession(sessionId: string) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/workspace/${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
      headers: getAuthHeaders(),
    }
  );

  return handleResponse(response);
}

// ==========================
// User Activity History
// ==========================
export interface UserActivityItem {
  id: string;
  user_id: string;
  action_name: string;
  activity_type: string;
  topic?: string | null;
  paper_name?: string | null;
  agent?: string | null;
  status: "Completed" | "In Progress" | "Failed" | string;
  details?: string | null;
  timestamp: string;
  date_group: string;
  formatted_time: string;
  formatted_date: string;
}

export interface UserHistoryGroup {
  date: string;
  items: UserActivityItem[];
}

export interface UserHistoryResponse {
  success: boolean;
  message: string;
  user_id: string;
  data: {
    activities: UserActivityItem[];
    grouped: UserHistoryGroup[];
    total: number;
  };
}

export async function getUserHistory(
  limit: number = 150,
  activityType: string = "all"
): Promise<UserHistoryResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    activity_type: activityType,
  });

  const response = await fetch(`${API_BASE_URL}/api/history?${params.toString()}`, {
    method: "GET",
    headers: getAuthHeaders(),
  });

  return handleResponse(response);
}

export async function recordUserActivity(payload: {
  action_name: string;
  activity_type?: string;
  topic?: string | null;
  paper_name?: string | null;
  agent?: string | null;
  status?: string;
  details?: string | null;
}): Promise<{ success: boolean; data: any }> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/history/activity`, {
      method: "POST",
      headers: getAuthJsonHeaders(),
      body: JSON.stringify(payload),
    });
    return await handleResponse(response);
  } catch (e) {
    console.warn("[Activity Tracker] Failed to log activity:", e);
    return { success: false, data: null };
  }
}

export async function deleteUserActivity(activityId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/history/${encodeURIComponent(activityId)}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

export async function clearUserHistory(): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/history`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

// ==========================
// Saved Projects API
// ==========================
export interface ProjectItem {
  id: string;
  name: string;
  topic: string;
  last_updated: string;
  updated_at: string;
  created_at: string;
  last_activity: string;
  papers_count: number;
  reports_count: number;
  ppts_count: number;
  agents_used: string[];
  starred: boolean;
  status: string;
  papers?: any[];
  agent_results?: Record<string, any>;
}

export async function getProjects(): Promise<{ success: boolean; data: ProjectItem[] }> {
  const response = await fetch(`${API_BASE_URL}/analysis/projects`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(response);
}

export async function toggleProjectFavorite(
  sessionId: string
): Promise<{ success: boolean; session_id: string; is_favorite: boolean }> {
  const response = await fetch(
    `${API_BASE_URL}/analysis/projects/${encodeURIComponent(sessionId)}/favorite`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );
  return handleResponse(response);
}

export async function renameProject(
  sessionId: string,
  name: string
): Promise<{ success: boolean; session_id: string; name: string }> {
  const response = await fetch(
    `${API_BASE_URL}/analysis/projects/${encodeURIComponent(sessionId)}/rename`,
    {
      method: "POST",
      headers: getAuthJsonHeaders(),
      body: JSON.stringify({ name }),
    }
  );
  return handleResponse(response);
}

export async function duplicateProject(
  sessionId: string
): Promise<{ success: boolean; message: string; session_id: string; name: string }> {
  const response = await fetch(
    `${API_BASE_URL}/analysis/projects/${encodeURIComponent(sessionId)}/duplicate`,
    {
      method: "POST",
      headers: getAuthHeaders(),
    }
  );
  return handleResponse(response);
}

export async function deleteProject(sessionId: string): Promise<any> {
  return deleteWorkspaceSession(sessionId);
}

// ==========================
// Agent Evaluation API
// ==========================
export interface EvaluationMetrics {
  // Summary Agent
  semantic_similarity?: number;
  factuality?: number;
  faithfulness?: number;
  content_coverage?: number;
  // Research Gap Agent
  evidence_grounding?: number;
  relevance?: number;
  completeness?: number;
  reasoning_quality?: number;
  // Dataset Recommendation Agent
  topic_relevance?: number;
  suitability?: number;
  correctness?: number;
  justification_quality?: number;
  // Experiment Recommendation Agent
  problem_relevance?: number;
  feasibility?: number;
  methodological_correctness?: number;
  // Literature Survey Agent
  literature_coverage?: number;
  citation_correctness?: number;
  synthesis_quality?: number;
  // AI Workspace Multi-Paper
  paper_attribution?: number;
  information_coverage?: number;
  groundedness?: number;
  cross_paper_synthesis?: number;
  cross_paper_consistency?: number;
  cross_paper_contamination?: number;
  // IEEE Report & PPT
  factual_consistency?: number;
  section_completeness?: number;
  source_grounding?: number;
  structural_compliance?: number;
  structure?: number;
  // Legacy aliases
  paper_relevance?: number;
  limitation_coverage?: number;
  gap_soundness?: number;
  task_suitability?: number;
  context_grounding?: number;
  benchmark_coverage?: number;
  objective_relevance?: number;
  setup_completeness?: number;
  technical_plausibility?: number;
  taxonomic_coverage?: number;
  domain_relevance?: number;
  citation_soundness?: number;
  novelty_validation?: number;
  literature_grounding?: number;
  contribution_coverage?: number;
  claim_factuality?: number;
  metric_accuracy?: number;
  comparison_coverage?: number;
  slide_structure?: number;
  presentation_clarity?: number;
  source_consistency?: number;
  query_relevance?: number;
  technical_feasibility?: number;
  actionability?: number;
  [key: string]: number | undefined;
}

export interface HumanValidation {
  verdict: "Correct" | "Partially Correct" | "Incorrect";
  feedback_notes?: string;
  validated_at: string;
  user_id?: string;
}

export interface EvaluationResult {
  evaluation_id: string;
  agent: string;
  agent_title: string;
  paper_name: string;
  query?: string;
  evaluation_mode: "Ground-Truth Benchmark Evaluation" | "Source-Grounded Paper Evaluation" | "Multi-Paper Workspace Evaluation";
  is_ground_truth: boolean;
  reference_source: string;
  source_context?: string;
  semantic_similarity_score?: number;
  semantic_similarity_percentage?: number;
  semantic_label?: string;
  metrics: EvaluationMetrics;
  overall_score?: number | null;
  missing_information: string[];
  unsupported_claims: string[];
  strengths: string[];
  explanation: string;
  human_validation?: HumanValidation | null;
  execution_time_seconds: number;
  created_at: string;
  user_id?: string;
}

export async function evaluateAgentOutput(
  agentName: string,
  payload: {
    output_text: string;
    paper_name?: string;
    context?: string;
    query?: string;
    reference_text?: string;
    user_id?: string;
    papers?: any[];
    is_workspace?: boolean;
  }
): Promise<{ success: boolean; data: EvaluationResult; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/${encodeURIComponent(agentName)}`, {
    method: "POST",
    headers: getAuthJsonHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function submitHumanValidation(payload: {
  evaluation_id: string;
  verdict: "Correct" | "Partially Correct" | "Incorrect";
  feedback_notes?: string;
  user_id?: string;
}): Promise<{ success: boolean; data: any; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/evaluation/human-validation`, {
    method: "POST",
    headers: getAuthJsonHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function getEvaluationHistory(
  agentName: string,
  limit: number = 10
): Promise<{ success: boolean; data: EvaluationResult[]; message: string }> {
  const response = await fetch(
    `${API_BASE_URL}/api/evaluation/${encodeURIComponent(agentName)}/history?limit=${limit}`,
    {
      headers: getAuthHeaders(),
    }
  );
  return handleResponse(response);
}

