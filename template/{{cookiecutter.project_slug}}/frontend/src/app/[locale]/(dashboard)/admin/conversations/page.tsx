"use client";

{%- if cookiecutter.use_jwt %}
import { useState, useEffect } from "react";
import { useAuthStore } from "@/stores";
import { apiClient } from "@/lib/api-client";
import type { Conversation } from "@/types";
import { formatDate } from "@/lib/utils";
import { Skeleton } from "@/components/ui";
import Link from "next/link";
import { ExternalLink, Search } from "lucide-react";

interface ConversationExport {
  conversations: Array<{
    id: string;
    title: string | null;
    created_at: string;
    updated_at: string;
    is_archived: boolean;
    messages: Array<{
      id: string;
      role: string;
      content: string;
      created_at: string;
    }>;
  }>;
  total: number;
}

export default function AdminConversationsPage() {
  const { user } = useAuthStore();
  const [conversations, setConversations] = useState<ConversationExport["conversations"]>([]);
  const [total, setTotal] = useState<number>(0);
  const [filtered, setFiltered] = useState<ConversationExport["conversations"]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [showArchived, setShowArchived] = useState(false);

  useEffect(() => {
    if (user?.role !== "admin") return;

    const fetchConversations = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await apiClient.get<ConversationExport>("/v1/admin/conversations");
        setConversations(data.conversations);
        setTotal(data.total);
        setFiltered(data.conversations);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to fetch conversations";
        setError(errorMessage);
        console.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, [user]);

  useEffect(() => {
    let filtered = conversations;

    // Filter by archived status
    if (!showArchived) {
      filtered = filtered.filter(c => !c.is_archived);
    }

    // Filter by search
    if (search) {
      const lowerSearch = search.toLowerCase();
      filtered = filtered.filter(c =>
        c.title?.toLowerCase().includes(lowerSearch) ||
        c.id.toLowerCase().includes(lowerSearch)
      );
    }

    setFiltered(filtered);
  }, [search, showArchived, conversations]);

  if (user?.role !== "admin") {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-muted-foreground">Access denied</div>
      </div>
    );
  }

  if (loading && conversations.length === 0) {
    return (
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">All Conversations</h1>
        <div className="bg-card rounded-lg border">
          <div className="p-4 border-b">
            <Skeleton className="h-10 w-48" />
          </div>
          <div className="p-4 space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error && conversations.length === 0) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">All Conversations</h1>

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title or ID..."
            className="w-full pl-10 pr-4 py-2 rounded-md border bg-background"
          />
        </div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            className="rounded"
          />
          Show archived
        </label>
      </div>

      {/* Stats */}
      <div className="mb-4 text-sm text-muted-foreground">
        Showing {filtered.length} of {total ?? conversations.length} conversations
      </div>

      {/* Conversations List */}
      <div className="bg-card rounded-lg border">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-4">Date</th>
              <th className="text-left p-4">Title</th>
              <th className="text-left p-4">Messages</th>
              <th className="text-left p-4">Status</th>
              <th className="text-left p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((conv) => (
              <tr key={conv.id} className="border-b hover:bg-muted/50">
                <td className="p-4 text-sm">
                  {formatDate(conv.created_at)}
                </td>
                <td className="p-4">
                  <div className="font-medium">{conv.title || "Untitled"}</div>
                  <div className="text-xs text-muted-foreground font-mono">
                    {conv.id.slice(0, 8)}...
                  </div>
                </td>
                <td className="p-4 text-sm text-muted-foreground">
                  {conv.messages.length}
                </td>
                <td className="p-4">
                  {conv.is_archived ? (
                    <span className="text-xs px-2 py-1 rounded-full bg-secondary text-secondary-foreground">
                      Archived
                    </span>
                  ) : (
                    <span className="text-xs px-2 py-1 rounded-full bg-green-500/10 text-green-600">
                      Active
                    </span>
                  )}
                </td>
                <td className="p-4">
                  <Link
                    href={`/chat?id=${conv.id}`}
                    className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                  >
                    View
                    <ExternalLink className="h-3 w-3" />
                  </Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="p-8 text-center text-muted-foreground">
                  No conversations found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
{%- else %}
// Admin conversations page placeholder - JWT not enabled
export default function AdminConversationsPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="text-center text-muted-foreground">
        Authentication not enabled
      </div>
    </div>
  );
}
{%- endif %}
