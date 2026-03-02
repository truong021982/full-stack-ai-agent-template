/**
 * RAG (Retrieval Augmented Generation) API client.
 * Provides methods for document upload and collection management.
 */

import { apiClient, ApiError } from "./api-client";

// RAG API Routes
export const RAG_API_ROUTES = {
  COLLECTIONS: "/rag/collections",
  COLLECTIONS_UPLOAD: (name: string) => `/rag/collections/${name}/upload`,
  COLLECTIONS_INFO: (name: string) => `/rag/collections/${name}/info`,
  COLLECTIONS_CREATE: (name: string) => `/rag/collections/${name}`,
  COLLECTIONS_DELETE: (name: string) => `/rag/collections/${name}`,
  COLLECTIONS_DOCUMENT_DELETE: (name: string, documentId: string) =>
    `/rag/collections/${name}/documents/${documentId}`,
  SEARCH: "/rag/search",
} as const;

// Types
export interface RAGCollection {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export interface RAGCollectionList {
  items: string[];
}

export interface RAGCollectionInfo {
  name: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

export interface RAGUploadResponse {
  message: string;
}

export interface RAGSearchRequest {
  query: string;
  collection_name: string;
  limit?: number;
  min_score?: number;
  filter?: string;
}

export interface RAGSearchResult {
  text: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  metadata: Record<string, any>;
  score: number;
}

export interface RAGSearchResponse {
  results: RAGSearchResult[];
}

// Check if RAG is enabled
export const isRagEnabled = (): boolean => {
  return process.env.NEXT_PUBLIC_RAG_ENABLED === "true";
};

// Upload a document to a collection
export async function uploadDocument(
  collectionName: string,
  file: File
): Promise<RAGUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `/api/v1/rag/collections/${collectionName}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  if (!response.ok) {
    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = null;
    }
    throw new ApiError(
      response.status,
      errorData?.detail || errorData?.message || "Upload failed",
      errorData
    );
  }

  return response.json();
}

// List all collections
export async function listCollections(): Promise<RAGCollectionList> {
  return apiClient.get<RAGCollectionList>(RAG_API_ROUTES.COLLECTIONS);
}

// Get collection info
export async function getCollectionInfo(
  collectionName: string
): Promise<RAGCollectionInfo> {
  return apiClient.get<RAGCollectionInfo>(
    RAG_API_ROUTES.COLLECTIONS_INFO(collectionName)
  );
}

// Create a new collection
export async function createCollection(
  collectionName: string
): Promise<{ message: string }> {
  return apiClient.post<{ message: string }>(
    RAG_API_ROUTES.COLLECTIONS_CREATE(collectionName)
  );
}

// Delete a collection
export async function deleteCollection(collectionName: string): Promise<void> {
  return apiClient.delete(RAG_API_ROUTES.COLLECTIONS_DELETE(collectionName));
}

// Delete a document from a collection
export async function deleteDocument(
  collectionName: string,
  documentId: string
): Promise<void> {
  return apiClient.delete(
    RAG_API_ROUTES.COLLECTIONS_DOCUMENT_DELETE(collectionName, documentId)
  );
}

// Search documents
export async function searchDocuments(
  request: RAGSearchRequest
): Promise<RAGSearchResponse> {
  return apiClient.post<RAGSearchResponse>(RAG_API_ROUTES.SEARCH, request);
}
