export type EmailListItem = {
  id: string;
  external_message_id: string;
  from_address: string;
  subject: string | null;
  received_at: string;
  category: string | null;
  confidence: number | null;
  priority: string | null;
  score: number | null;
  sentiment: string | null;
  urgency: string | null;
};

export type EmailListResponse = {
  items: EmailListItem[];
  total: number;
  limit: number;
  offset: number;
};

export type ClassificationResult = {
  category: string;
  confidence: number;
  tags: string[];
  reason: string;
};

export type ExtractedEntities = {
  contact_name: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
  product: string | null;
  order_id: string | null;
  invoice_id: string | null;
  amount: number | null;
  currency: string | null;
  deadline: string | null;
  requested_action: string | null;
  sentiment: string;
  language: string;
  urgency: string;
};

export type PriorityResult = {
  priority: string;
  score: number;
  factors: string[];
  reason: string;
};

export type EmailDetail = {
  id: string;
  external_message_id: string;
  from_address: string;
  to_addresses: string[];
  subject: string | null;
  body_text: string | null;
  received_at: string;
  classification: ClassificationResult | null;
  extraction: ExtractedEntities | null;
  priority: PriorityResult | null;
  meta: Record<string, any>;
};

export type DraftResponse = {
  draft_id: string;
  email_id: string;
  status: string;
  subject: string | null;
  body_text: string;
  tone: string | null;
  language: string | null;
  confidence: number;
  warnings: string[];
  cited_kb: string[];
  meta: {
    model: string;
    provider: string;
    latency_ms: number;
    fallback_used: boolean;
  };
};

export type ActionResponse = {
  draft_id: string;
  status: string;
  message: string;
};

export type AuditEntry = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: string;
  payload: Record<string, any>;
  created_at: string;
};

export type AuditListResponse = {
  items: AuditEntry[];
  total: number;
  limit: number;
  offset: number;
};
export type MetricsResponse = {
  total_emails: number;
  priority_stats: Record<string, number>;
  category_stats: Record<string, number>;
  avg_latency_ms: {
    classification: number;
    extraction: number;
    priority: number;
  };
  provider_stats: Record<string, number>;
  fallback_rate: number;
};