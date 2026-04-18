{%- if cookiecutter.use_jwt and cookiecutter.use_database %}
{% raw %}
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, MessageSquare, Search, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAdminConversations } from "@/hooks";
import type { AdminConversation, AdminUser } from "@/types";

export default function AdminConversationsPage() {
  const router = useRouter();
  const {
    conversations,
    conversationsTotal,
    users,
    usersTotal,
    selectedConversation,
    isLoading,
    fetchConversations,
    fetchUsers,
    fetchConversationDetail,
    setSelectedConversation,
  } = useAdminConversations();

  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState("conversations");
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  useEffect(() => {
    fetchConversations();
    fetchUsers();
  }, [fetchConversations, fetchUsers]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (activeTab === "conversations") {
        fetchConversations({
          search: search || undefined,
          user_id: selectedUserId || undefined,
        });
      } else {
        fetchUsers({ search: search || undefined });
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [search, activeTab, selectedUserId, fetchConversations, fetchUsers]);

  const handleViewConversation = async (conv: AdminConversation) => {
    await fetchConversationDetail(conv.id);
  };

  const handleUserClick = (user: AdminUser) => {
    setSelectedUserId(user.id);
    setActiveTab("conversations");
    setSearch("");
  };

  // Read-only conversation preview
  if (selectedConversation) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center gap-2 border-b p-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSelectedConversation(null)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h2 className="font-semibold">
              {selectedConversation.title || "Untitled"}
            </h2>
            <p className="text-xs text-muted-foreground">
              {selectedConversation.messages.length} messages (read-only)
            </p>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {selectedConversation.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                <p className="text-xs opacity-60 mt-1">
                  {new Date(msg.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Admin: Conversations</h1>
        <p className="text-muted-foreground">
          Browse and manage all conversations and users.
        </p>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        {selectedUserId && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSelectedUserId(null)}
          >
            Clear user filter
          </Button>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1">
        <TabsList>
          <TabsTrigger value="conversations">
            <MessageSquare className="mr-2 h-4 w-4" />
            Conversations ({conversationsTotal})
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="mr-2 h-4 w-4" />
            Users ({usersTotal})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="conversations" className="flex-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Owner</TableHead>
                <TableHead>Messages</TableHead>
                <TableHead>Created</TableHead>
                <TableHead>Status</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {conversations.map((conv) => (
                <TableRow key={conv.id}>
                  <TableCell className="font-medium">
                    {conv.title || "Untitled"}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {conv.user_email || "—"}
                  </TableCell>
                  <TableCell>{conv.message_count}</TableCell>
                  <TableCell>
                    {new Date(conv.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {conv.is_archived ? (
                      <Badge variant="secondary">Archived</Badge>
                    ) : (
                      <Badge variant="default">Active</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleViewConversation(conv)}
                    >
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && conversations.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No conversations found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="users" className="flex-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Email</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Conversations</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id}>
                  <TableCell className="font-medium">{user.email}</TableCell>
                  <TableCell>{user.full_name || "—"}</TableCell>
                  <TableCell>{user.conversation_count}</TableCell>
                  <TableCell>
                    {user.is_active ? (
                      <Badge variant="default">Active</Badge>
                    ) : (
                      <Badge variant="destructive">Inactive</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    {new Date(user.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleUserClick(user)}
                    >
                      View chats
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!isLoading && users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No users found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </div>
  );
}
{% endraw %}
{%- else %}
export default function AdminConversationsPage() {
  return <div>Admin conversations require JWT authentication.</div>;
}
{%- endif %}
