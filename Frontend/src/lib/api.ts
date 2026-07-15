const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";
  
async function handleResponse(response: Response) {
  const data = await response.json();

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
// AI Search
// ==========================
export async function searchPaper(
  query: string,
  sessionId: string,
  paperName?: string | null
) {
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
// Run Structured AI Analysis
// ==========================
export async function runAnalysis(
  paperName: string,
  analysisType: AnalysisType
): Promise<AnalysisResponse> {
  const response = await fetch(
    `${API_BASE_URL}/analysis/run`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        paper_name: paperName,
        analysis_type: analysisType,
      }),
    }
  );

  return handleResponse(response);
}

export type ReportResponse = {
  success: boolean;
  message: string;
  paper_name: string;
  result: string;
};

export async function generateIEEEReport(
  paperName: string
): Promise<ReportResponse> {
  const response = await fetch(
    `${API_BASE_URL}/report/generate`,
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