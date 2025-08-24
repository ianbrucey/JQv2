import React, { useEffect, useState } from "react";
import { useConversationId } from "#/hooks/use-conversation-id";

interface DraftMeta {
  draft_id: string;
  name: string;
  type: string | null;
  created_at: string | null;
  updated_at: string | null;
  sections: Array<{
    id: string;
    name: string;
    file: string;
  }>;
}

interface DraftsListResponse {
  items: DraftMeta[];
  total: number;
}

interface CreateDraftRequest {
  draft_type: string;
  name: string;
}

const DRAFT_TYPES = [
  { value: "complaint", label: "Complaint" },
  { value: "motion", label: "Motion" },
  { value: "pleading", label: "Pleading" },
  { value: "demurrer", label: "Demurrer" },
  { value: "brief", label: "Brief" },
  { value: "memo", label: "Memo" },
];

export default function DraftsTab() {
  const { conversationId } = useConversationId();
  const [caseId, setCaseId] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<DraftMeta[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  // Form state
  const [draftType, setDraftType] = useState("complaint");
  const [draftName, setDraftName] = useState("");

  // Resolve case_id from conversation metadata
  useEffect(() => {
    let ignore = false;

    async function resolveCaseId() {
      try {
        if (!conversationId) return;

        const metaRes = await fetch(
          `/api/conversations/${conversationId}/metadata`,
        );
        if (!metaRes.ok) {
          if (!ignore) setCaseId(null);
          return;
        }

        const meta = await metaRes.json();
        const resolvedCaseId = meta?.case_id;

        if (!ignore) {
          setCaseId(resolvedCaseId || null);
        }
      } catch (e) {
        console.error("Failed to resolve case ID:", e);
        if (!ignore) setCaseId(null);
      }
    }

    resolveCaseId();
    return () => {
      ignore = true;
    };
  }, [conversationId]);

  // Load drafts when case_id is available
  useEffect(() => {
    let ignore = false;

    async function loadDrafts() {
      if (!caseId) {
        setDrafts([]);
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/legal/cases/${caseId}/drafts`);
        if (!response.ok) {
          throw new Error(
            `Failed to load drafts: ${response.status} ${response.statusText}`,
          );
        }

        const data: DraftsListResponse = await response.json();
        if (!ignore) {
          setDrafts(data.items || []);
        }
      } catch (e: any) {
        console.error("Failed to load drafts:", e);
        if (!ignore) {
          setError(e?.message || String(e));
        }
      } finally {
        if (!ignore) {
          setLoading(false);
        }
      }
    }

    loadDrafts();
    return () => {
      ignore = true;
    };
  }, [caseId]);

  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!caseId || !draftName.trim()) return;

    try {
      setCreating(true);
      setError(null);

      const request: CreateDraftRequest = {
        draft_type: draftType,
        name: draftName.trim(),
      };

      const response = await fetch(`/api/legal/cases/${caseId}/drafts/create`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to create draft: ${response.status}`,
        );
      }

      const newDraft = await response.json();

      // Add the new draft to the list
      setDrafts((prev) => [...prev, newDraft]);

      // Reset form and hide it
      setDraftName("");
      setDraftType("complaint");
      setShowCreateForm(false);
    } catch (e: any) {
      console.error("Failed to create draft:", e);
      setError(e?.message || String(e));
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteDraft = async (draftId: string, draftName: string) => {
    if (!caseId) return;

    // Show confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to delete "${draftName}"?\n\nThis action cannot be undone and will permanently remove all draft content, research, and exhibits.`,
    );

    if (!confirmed) return;

    try {
      setDeleting(draftId);
      setError(null);

      const response = await fetch(
        `/api/legal/cases/${caseId}/drafts/${draftId}`,
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Failed to delete draft: ${response.status}`,
        );
      }

      // Remove the draft from the list
      setDrafts((prev) => prev.filter((draft) => draft.draft_id !== draftId));
    } catch (e: any) {
      console.error("Failed to delete draft:", e);
      setError(e?.message || String(e));
    } finally {
      setDeleting(null);
    }
  };

  if (!caseId) {
    return (
      <div className="p-6 text-center">
        <div className="text-gray-500">
          <p>This conversation is not associated with a legal case.</p>
          <p className="text-sm mt-2">
            Drafts are only available for legal case conversations.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-6 border-b border-neutral-600">
        <h2 className="text-xl font-semibold mb-4">Draft Workspace</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {drafts.length === 0 && !loading && (
          <div className="bg-neutral-800 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">
              Create Your First Draft
            </h3>
            <form onSubmit={handleCreateDraft} className="space-y-4">
              <div>
                <label
                  htmlFor="draft-type"
                  className="block text-sm font-medium mb-2"
                >
                  Draft Type
                </label>
                <select
                  id="draft-type"
                  value={draftType}
                  onChange={(e) => setDraftType(e.target.value)}
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {DRAFT_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="draft-name"
                  className="block text-sm font-medium mb-2"
                >
                  Draft Name
                </label>
                <input
                  id="draft-name"
                  type="text"
                  value={draftName}
                  onChange={(e) => setDraftName(e.target.value)}
                  placeholder="e.g., Motion to Dismiss"
                  className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={creating || !draftName.trim()}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? "Creating..." : "Create Draft"}
              </button>
            </form>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-auto p-6">
        {loading && (
          <div className="text-center py-8">
            <div className="text-gray-500">Loading drafts...</div>
          </div>
        )}

        {!loading && drafts.length > 0 && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">
                Your Drafts ({drafts.length})
              </h3>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(!showCreateForm);
                  if (!showCreateForm) {
                    setDraftName("");
                    setDraftType("complaint");
                    setError(null);
                  }
                }}
                className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                {showCreateForm ? "Cancel" : "New Draft"}
              </button>
            </div>

            {showCreateForm && (
              <div className="bg-neutral-800 rounded-lg p-6 border border-neutral-600">
                <h4 className="text-lg font-medium mb-4">Create New Draft</h4>
                <form onSubmit={handleCreateDraft} className="space-y-4">
                  <div>
                    <label
                      htmlFor="new-draft-type"
                      className="block text-sm font-medium mb-2"
                    >
                      Draft Type
                    </label>
                    <select
                      id="new-draft-type"
                      value={draftType}
                      onChange={(e) => setDraftType(e.target.value)}
                      className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {DRAFT_TYPES.map((type) => (
                        <option key={type.value} value={type.value}>
                          {type.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label
                      htmlFor="new-draft-name"
                      className="block text-sm font-medium mb-2"
                    >
                      Draft Name
                    </label>
                    <input
                      id="new-draft-name"
                      type="text"
                      value={draftName}
                      onChange={(e) => setDraftName(e.target.value)}
                      placeholder="e.g., Motion to Dismiss"
                      className="w-full px-3 py-2 bg-neutral-700 border border-neutral-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      required
                    />
                  </div>

                  <div className="flex gap-3">
                    <button
                      type="submit"
                      disabled={creating || !draftName.trim()}
                      className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {creating ? "Creating..." : "Create Draft"}
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowCreateForm(false)}
                      className="px-4 py-2 bg-neutral-600 text-white rounded-md hover:bg-neutral-500"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </div>
            )}

            <div className="grid gap-4">
              {drafts.map((draft) => (
                <div
                  key={draft.draft_id}
                  className="bg-neutral-800 rounded-lg p-4 border border-neutral-600"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{draft.name}</h4>
                      <p className="text-sm text-gray-400 capitalize">
                        {draft.type} • {draft.sections?.length || 0} sections
                      </p>
                      {draft.updated_at && (
                        <p className="text-xs text-gray-500 mt-1">
                          Updated{" "}
                          {new Date(draft.updated_at).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <button className="text-sm text-blue-400 hover:text-blue-300">
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          handleDeleteDraft(draft.draft_id, draft.name)
                        }
                        disabled={deleting === draft.draft_id}
                        className="text-sm text-red-400 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {deleting === draft.draft_id ? "Deleting..." : "Delete"}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
