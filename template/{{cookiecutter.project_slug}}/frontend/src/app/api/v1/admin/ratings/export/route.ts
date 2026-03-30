{%- if cookiecutter.use_jwt %}
import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";

export async function GET(request: NextRequest) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;

    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const searchParams = request.nextUrl.searchParams;
    const export_format = searchParams.get("export_format") || "json";
    const ratingFilter = searchParams.get("rating_filter");
    const withCommentsOnly = searchParams.get("with_comments_only") === "true";

    let url = `/api/v1/admin/ratings/export?export_format=${export_format}`;
    if (ratingFilter) url += `&rating_filter=${ratingFilter}`;
    if (withCommentsOnly) url += `&with_comments_only=true`;

    const data = await backendFetch(url, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    const filename = `ratings_export_${new Date().toISOString().slice(0, 10)}.${export_format}`;

    if (export_format === "csv") {
      return new NextResponse(data as string, {
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition": `attachment; filename="${filename}"`,
        },
      });
    }

    return NextResponse.json(data, {
      headers: {
        "Content-Disposition": `attachment; filename="${filename}"`,
      },
    });
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json(
        { detail: error.message || "Failed to export ratings" },
        { status: error.status }
      );
    }
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
{%- endif %}
