{%- if cookiecutter.use_database %}
/**
 * Conversation types for AI chat persistence.
 */

export interface Conversation {
  id: string;
  user_id?: string;
{%- if cookiecutter.use_pydantic_deep and cookiecutter.use_jwt %}
  project_id?: string;
{%- endif %}
  title?: string;
  created_at: string;
  updated_at: string;
  is_archived: boolean;
}

export interface ConversationMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
  model_name?: string;
  tokens_used?: number;
  tool_calls?: ConversationToolCall[];
}

export interface ConversationToolCall {
  id: string;
  message_id: string;
  tool_call_id: string;
  tool_name: string;
  args: Record<string, unknown>;
  result?: string;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
}

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
}

export interface ConversationWithMessages extends Conversation {
  messages: ConversationMessage[];
}

{%- if cookiecutter.use_jwt %}

// Sharing types

export interface ConversationShare {
  id: string;
  conversation_id: string;
  shared_by: string;
  shared_with?: string;
  share_token?: string;
  permission: "view" | "edit";
  shared_with_email?: string;
  shared_by_email?: string;
  created_at: string;
}

export interface ConversationShareListResponse {
  items: ConversationShare[];
  total: number;
}

// Admin types

export interface AdminConversation {
  id: string;
  user_id?: string;
{%- if cookiecutter.use_pydantic_deep %}
  project_id?: string;
{%- endif %}
  title?: string;
  is_archived: boolean;
  message_count: number;
  user_email?: string;
  created_at: string;
  updated_at?: string;
}

export interface AdminConversationListResponse {
  items: AdminConversation[];
  total: number;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  conversation_count: number;
  created_at: string;
}

export interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
}
{%- endif %}
{%- endif %}
