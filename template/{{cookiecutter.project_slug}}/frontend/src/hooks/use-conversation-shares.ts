{%- if cookiecutter.use_jwt and cookiecutter.use_database %}
{% raw %}
"use client";

import { useCallback, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type {
  Conversation,
  ConversationListResponse,
  ConversationShare,
  ConversationShareListResponse,
} from "@/types";

export function useConversationShares() {
  const [shares, setShares] = useState<ConversationShare[]>([]);
  const [sharedWithMe, setSharedWithMe] = useState<Conversation[]>([]);
  const [sharedWithMeTotal, setSharedWithMeTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shareConversation = useCallback(
    async (
      conversationId: string,
      data: {
        shared_with?: string;
        permission?: "view" | "edit";
        generate_link?: boolean;
      }
    ) => {
      setIsLoading(true);
      setError(null);
      try {
        const share = await apiClient.post<ConversationShare>(
          `/conversations/${conversationId}/shares`,
          data
        );
        setShares((prev) => [share, ...prev]);
        return share;
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to share";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const fetchShares = useCallback(async (conversationId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<ConversationShareListResponse>(
        `/conversations/${conversationId}/shares`
      );
      setShares(response.items);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to load shares";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const revokeShare = useCallback(
    async (conversationId: string, shareId: string) => {
      setIsLoading(true);
      setError(null);
      try {
        await apiClient.delete(
          `/conversations/${conversationId}/shares/${shareId}`
        );
        setShares((prev) => prev.filter((s) => s.id !== shareId));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Failed to revoke";
        setError(message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const fetchSharedWithMe = useCallback(
    async (skip = 0, limit = 50) => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<ConversationListResponse>(
          `/conversations/shared-with-me?skip=${skip}&limit=${limit}`
        );
        setSharedWithMe(response.items);
        setSharedWithMeTotal(response.total);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "Failed to load shared";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  return {
    shares,
    sharedWithMe,
    sharedWithMeTotal,
    isLoading,
    error,
    shareConversation,
    fetchShares,
    revokeShare,
    fetchSharedWithMe,
  };
}
{% endraw %}
{%- else %}
// Conversation sharing hook — requires JWT authentication + database.
export {};
{%- endif %}
