// Search API Types
export interface SearchQueryRequest {
  query: string;
  user_id?: string;
  limit?: number;
  session_id?: string;
}

export interface DocumentSource {
  document_id: string;
  document_title: string;
  document_source: string;
  chunk_content: string;
  page_number: number | null;
  relevance_score: number;
}

export interface PerformanceMetrics {
  embedding_time_ms: number;
  search_time_ms: number;
  llm_time_ms: number;
  total_time_ms: number;
}

export interface ResponseMetadata {
  is_fallback: boolean;
  fallback_reason: string | null;
  model_used: string;
  search_result_count: number;
}

export interface SearchQueryResponse {
  query_id: string;
  query: string;
  answer: string;
  sources: DocumentSource[];
  performance: PerformanceMetrics;
  metadata: ResponseMetadata;
}

// Health Check API
export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version: string;
}

// User History API
export interface SearchHistoryItem {
  query_id: string;
  query: string;
  answer: string;
  created_at: string;
  rating: number | null;
}

export interface SearchHistoryResponse {
  items: SearchHistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

// Feedback API
export interface FeedbackRequest {
  query_id: string;
  rating: number; // 1-5
  comment?: string;
}

export interface FeedbackResponse {
  feedback_id: string;
  message: string;
}

// Auth API (Task 3.5)
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    department: string;
    access_level: number;
  };
}

export interface LogoutResponse {
  message: string;
}

// Error Response
export interface ErrorResponse {
  error: string;
  message: string;
  details?: unknown;
  request_id?: string;
  timestamp?: string;
}
