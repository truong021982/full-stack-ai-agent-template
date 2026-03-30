"use client";

{%- if cookiecutter.use_jwt %}
import { useState, useEffect, useCallback } from "react";
import { useAuthStore } from "@/stores";
import type {
  MessageRatingListResponse,
  RatingSummary,
} from "@/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import Link from "next/link";
import { ExternalLink, Download } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const PAGE_SIZE = 50;

type RatingFilter = "all" | "positive" | "negative";

export default function AdminRatingsPage() {
  const { user } = useAuthStore();
  const [summary, setSummary] = useState<RatingSummary | null>(null);
  const [ratings, setRatings] = useState<MessageRatingListResponse | null>(null);
  const [filter, setFilter] = useState<RatingFilter>("all");
  const [commentsOnly, setCommentsOnly] = useState(false);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<"json" | "csv">("csv");

  const fetchRatings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, ratingsRes] = await Promise.all([
        fetch("/api/v1/admin/ratings/summary?days=30", {
          credentials: "include",
        }),
        fetch(
          `/api/v1/admin/ratings?skip=${
            page * PAGE_SIZE
          }&limit=${PAGE_SIZE}&rating_filter=${
            filter === "all" ? "" : filter === "positive" ? "1" : "-1"
          }&with_comments_only=${commentsOnly}`,
          { credentials: "include" }
        ),
      ]);

      if (!summaryRes.ok && !ratingsRes.ok) {
        throw new Error("Failed to fetch ratings data");
      }

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json();
        setSummary(summaryData);
      }
      if (ratingsRes.ok) {
        const ratingsData = await ratingsRes.json();
        setRatings(ratingsData);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to fetch ratings";
      setError(errorMessage);
      console.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [page, filter, commentsOnly]);

  const handleExport = () => {
    const params = new URLSearchParams({
      export_format: exportFormat,
      rating_filter: filter === "all" ? "" : filter === "positive" ? "1" : "-1",
      with_comments_only: commentsOnly.toString(),
    });
    // Remove empty params
    if (!params.get("rating_filter")) params.delete("rating_filter");

    window.open(`/api/v1/admin/ratings/export?${params.toString()}`, "_blank");
  };

  useEffect(() => {
    if (user?.role !== "admin") return;

    fetchRatings();
  }, [user, fetchRatings]);

  if (user?.role !== "admin") {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-muted-foreground">Access denied</div>
      </div>
    );
  }

  if (loading && !summary && !error) {
    return (
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">Response Ratings</h1>
        {/* Summary Cards Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="bg-card p-4 rounded-lg border">
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-4 w-24" />
            </div>
          ))}
        </div>
        {/* Chart Skeleton */}
        <div className="bg-card p-6 rounded-lg border mb-8">
          <Skeleton className="h-6 w-40 mb-4" />
          <Skeleton className="h-[300px] w-full" />
        </div>
        {/* Table Skeleton */}
        <div className="bg-card rounded-lg border">
          <div className="p-4 border-b">
            <Skeleton className="h-10 w-32" />
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

  if (error && !summary) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center text-red-500">{error}</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Response Ratings</h1>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-2xl font-bold">{summary.total_ratings}</div>
            <div className="text-sm text-muted-foreground">Total Ratings</div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-2xl font-bold text-green-600">
              {summary.like_count}
            </div>
            <div className="text-sm text-muted-foreground">Likes</div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-2xl font-bold text-red-600">
              {summary.dislike_count}
            </div>
            <div className="text-sm text-muted-foreground">Dislikes</div>
          </div>
          <div className="bg-card p-4 rounded-lg border">
            <div className="text-2xl font-bold">
              {summary.average_rating.toFixed(2)}
            </div>
            <div className="text-sm text-muted-foreground">Average Rating</div>
          </div>
        </div>
      )}

      {/* Chart */}
      {summary && summary.ratings_by_day.length > 0 && (
        <div className="bg-card p-6 rounded-lg border mb-8">
          <h2 className="text-xl font-semibold mb-4">Ratings Over Time</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={summary.ratings_by_day}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="likes" fill="#22c55e" name="Likes" />
              <Bar dataKey="dislikes" fill="#ef4444" name="Dislikes" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-4">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          className="px-3 py-2 rounded-md border bg-background"
        >
          <option value="all">All Ratings</option>
          <option value="positive">Likes Only</option>
          <option value="negative">Dislikes Only</option>
        </select>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={commentsOnly}
            onChange={(e) => setCommentsOnly(e.target.checked)}
            className="rounded"
          />
          With comments only
        </label>
        <div className="flex items-center gap-2 ml-auto">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as "json" | "csv")}
            className="px-3 py-2 rounded-md border bg-background"
          >
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {/* Ratings List */}
      <div className="bg-card rounded-lg border">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-4">Date</th>
              <th className="text-left p-4">Rating</th>
              <th className="text-left p-4">Comment</th>
              <th className="text-left p-4">Message</th>
              <th className="text-left p-4">User</th>
              <th className="text-left p-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {ratings?.items.map((rating) => (
              <tr key={rating.id} className="border-b hover:bg-muted/50">
                <td className="p-4">{formatDate(rating.created_at)}</td>
                <td className="p-4">
                  {rating.rating === 1 ? (
                    <span className="text-green-600">👍 Like</span>
                  ) : (
                    <span className="text-red-600">👎 Dislike</span>
                  )}
                </td>
                <td className="p-4 max-w-md truncate">
                  {rating.comment || "-"}
                </td>
                <td className="p-4 max-w-xs truncate text-muted-foreground">
                  {rating.message_content || "-"}
                </td>
                <td className="p-4">
                  {rating.user_name || rating.user_email || "-"}
                </td>
                <td className="p-4">
                  {rating.conversation_id && (
                    <Link
                      href={`/chat?id=${rating.conversation_id}`}
                      className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                    >
                      View conversation
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  )}
                </td>
              </tr>
            ))}
            {loading && ratings && (
              <tr>
                <td colSpan={6} className="p-4">
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                  </div>
                </td>
              </tr>
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {ratings && ratings.total > PAGE_SIZE && (
          <div className="flex justify-center gap-2 p-4 border-t">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 rounded hover:bg-muted disabled:opacity-50"
            >
              Previous
            </button>
            <span className="px-3 py-1">
              Page {page + 1} of {Math.ceil(ratings.total / PAGE_SIZE)}
            </span>
            <button
              onClick={() => setPage(Math.min(Math.ceil(ratings.total / PAGE_SIZE) - 1, page + 1))}
              disabled={page >= Math.ceil(ratings.total / PAGE_SIZE) - 1}
              className="px-3 py-1 rounded hover:bg-muted disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
{%- else %}
// Admin ratings page placeholder - JWT not enabled
export default function AdminRatingsPage() {
  return (
    <div className="container mx-auto py-8">
      <div className="text-center text-muted-foreground">
        Authentication not enabled
      </div>
    </div>
  );
}
{%- endif %}
