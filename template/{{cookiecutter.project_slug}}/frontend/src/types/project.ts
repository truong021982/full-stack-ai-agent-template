{%- if cookiecutter.use_pydantic_deep and cookiecutter.use_jwt %}
/**
 * Project types for DeepAgents project management.
 */

export type ProjectMemberRole = "viewer" | "editor" | "admin" | "owner";

export interface Project {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  image: string;
  container_name: string;
  volume_name: string;
  created_at: string;
  updated_at?: string;
  archived_at?: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  image?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  image?: string;
}

export interface ProjectMember {
  project_id: string;
  user_id: string;
  role: ProjectMemberRole;
  invited_by?: string;
  created_at: string;
}

export interface ProjectMemberListResponse {
  items: ProjectMember[];
  total: number;
}

export interface ProjectMemberCreate {
  user_id: string;
  role: "viewer" | "editor" | "admin";
}

export interface ProjectMemberUpdate {
  role: "viewer" | "editor" | "admin";
}
{%- endif %}
