{%- if cookiecutter.use_pydantic_deep and cookiecutter.use_jwt %}
"use client";

import { useCallback } from "react";

import { apiClient } from "@/lib/api-client";
import { useProjectStore } from "@/stores/project-store";
import type {
  Project,
  ProjectCreate,
  ProjectListResponse,
  ProjectMember,
  ProjectMemberCreate,
  ProjectMemberListResponse,
  ProjectMemberUpdate,
  ProjectUpdate,
} from "@/types/project";

export function useProjects() {
  const {
    projects,
    activeProjectId,
    isLoading,
    error,
    setProjects,
    addProject,
    updateProject: updateProjectInStore,
    removeProject,
    setActiveProject,
    setLoading,
    setError,
    getActiveProject,
  } = useProjectStore();

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<ProjectListResponse>("/projects");
      setProjects(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects");
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError, setProjects]);

  const createProject = useCallback(
    async (data: ProjectCreate): Promise<Project | null> => {
      setLoading(true);
      setError(null);
      try {
        const project = await apiClient.post<Project>("/projects", data);
        addProject(project);
        return project;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to create project");
        return null;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setError, addProject]
  );

  const updateProject = useCallback(
    async (projectId: string, data: ProjectUpdate): Promise<Project | null> => {
      setError(null);
      try {
        const project = await apiClient.patch<Project>(
          `/projects/${projectId}`,
          data
        );
        updateProjectInStore(project);
        return project;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update project");
        return null;
      }
    },
    [setError, updateProjectInStore]
  );

  const archiveProject = useCallback(
    async (projectId: string): Promise<Project | null> => {
      setError(null);
      try {
        const project = await apiClient.post<Project>(
          `/projects/${projectId}/archive`,
          {}
        );
        updateProjectInStore(project);
        if (activeProjectId === projectId) {
          setActiveProject(null);
        }
        return project;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to archive project");
        return null;
      }
    },
    [setError, updateProjectInStore, activeProjectId, setActiveProject]
  );

  const deleteProject = useCallback(
    async (projectId: string): Promise<boolean> => {
      setError(null);
      try {
        await apiClient.delete(`/projects/${projectId}`);
        removeProject(projectId);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to delete project");
        return false;
      }
    },
    [setError, removeProject]
  );

  // Member management

  const fetchMembers = useCallback(
    async (projectId: string): Promise<ProjectMember[]> => {
      try {
        const response = await apiClient.get<ProjectMemberListResponse>(
          `/projects/${projectId}/members`
        );
        return response.items;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load members");
        return [];
      }
    },
    [setError]
  );

  const addMember = useCallback(
    async (
      projectId: string,
      data: ProjectMemberCreate
    ): Promise<ProjectMember | null> => {
      try {
        return await apiClient.post<ProjectMember>(
          `/projects/${projectId}/members`,
          data
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to add member");
        return null;
      }
    },
    [setError]
  );

  const updateMemberRole = useCallback(
    async (
      projectId: string,
      userId: string,
      data: ProjectMemberUpdate
    ): Promise<ProjectMember | null> => {
      try {
        return await apiClient.patch<ProjectMember>(
          `/projects/${projectId}/members/${userId}`,
          data
        );
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to update member role"
        );
        return null;
      }
    },
    [setError]
  );

  const removeMember = useCallback(
    async (projectId: string, userId: string): Promise<boolean> => {
      try {
        await apiClient.delete(`/projects/${projectId}/members/${userId}`);
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to remove member");
        return false;
      }
    },
    [setError]
  );

  return {
    projects,
    activeProjectId,
    activeProject: getActiveProject(),
    isLoading,
    error,
    setActiveProject,
    fetchProjects,
    createProject,
    updateProject,
    archiveProject,
    deleteProject,
    fetchMembers,
    addMember,
    updateMemberRole,
    removeMember,
  };
}
{%- endif %}
