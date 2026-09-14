const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";

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
    `${API_BASE_URL}/papers`
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
    headers: {
      "Content-Type": "application/json",
    },
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
      headers: {
        "Content-Type": "application/json",
      },
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
  query?: string | null
): Promise<AnalysisResponse> {
  if (!paperName?.trim() && !query?.trim()) {
    throw new Error("Either a research paper or query is required.");
  }

  if (!analysisType) {
    throw new Error("Analysis type is required.");
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

  const response = await fetch(
    `${API_BASE_URL}/analysis/run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  const data = await handleResponse(response);

  console.log(
    "Coordinator Result:",
    data
  );

  return data as AnalysisResponse;
}

export type ReportResponse = {
  success: boolean;
  message: string;
  paper_name: string;
  result: string;
};

export async function generateIEEEReport(
  paperName: string,
  query?: string
): Promise<ReportResponse> {
  const payload: Record<string, any> = {
    paper_name: paperName,
  };
  if (query?.trim()) {
    payload.query = query.trim();
  }

  const response = await fetch(
    `${API_BASE_URL}/report/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    }
  );

  return handleResponse(response);
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
      headers: {
        "Content-Type": "application/json",
      },
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
  paperName: string
): Promise<PresentationResponse> {
  const response = await fetch(
    `${API_BASE_URL}/presentation/generate`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        paper_name: paperName,
      }),
    }
  );

  return handleResponse(response);
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
    headers: {
      "Content-Type": "application/json",
    },
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
    `${API_BASE_URL}/dashboard`
  );

  return handleResponse(response);
}

export async function searchDashboard(
  query: string
): Promise<DashboardSearchResponse> {
  console.log("Calling API:", query);

  const response = await fetch(
    `${API_BASE_URL}/dashboard/search?query=${encodeURIComponent(query)}`
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
    `${API_BASE_URL}/api/search?${params.toString()}`
  );

  return handleResponse(response);
}

export async function runAllWorkspaceAgents(
  topic: string,
  sessionId: string,
  papers: any[]
) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/workspace/run-all`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic,
        session_id: sessionId,
        papers,
      }),
    }
  );

  return handleResponse(response);
}

export async function deleteWorkspaceSession(sessionId: string) {
  const response = await fetch(
    `${API_BASE_URL}/analysis/workspace/${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
    }
  );

  return handleResponse(response);
}