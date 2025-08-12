import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { createCase, listCases, type Case } from "#/api/cases";

const LS_SELECTED_CASE_ID = "selected_case_id";

export default function CasesPage() {
  const qc = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [showModal, setShowModal] = React.useState(false);
  const [newName, setNewName] = React.useState("");
  const [newDesc, setNewDesc] = React.useState("");

  const casesQuery = useQuery({
    queryKey: ["cases", { q: search }],
    queryFn: () => listCases(search || undefined),
  });

  const createMut = useMutation({
    mutationFn: () => createCase({ name: newName, description: newDesc }),
    onSuccess: () => {
      setShowModal(false);
      setNewName("");
      setNewDesc("");
      qc.invalidateQueries({ queryKey: ["cases"] });
    },
  });

  const onSelect = (c: Case) => {
    localStorage.setItem(LS_SELECTED_CASE_ID, c.id);
    // For now, just acknowledge selection; "Continue" can route to /conversations later
    alert(`Selected case: ${c.name}`);
  };

  const onContinue = () => {
    const id = localStorage.getItem(LS_SELECTED_CASE_ID);
    if (!id) {
      alert("Please select a case first.");
      return;
    }
    // TODO: Create conversation bound to this case and navigate
    alert(`Continue with case ${id} (conversation creation to be implemented)`);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Select a Case</h1>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search cases..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="border rounded px-3 py-2 bg-transparent"
          />
          <button
            className="px-4 py-2 rounded bg-primary text-white"
            onClick={() => setShowModal(true)}
          >
            Create Case
          </button>
          <button
            className="px-4 py-2 rounded bg-secondary text-white"
            onClick={onContinue}
          >
            Continue
          </button>
        </div>
      </div>

      {/* List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {casesQuery.data?.items?.map((c) => (
          <div
            key={c.id}
            className="border rounded p-4 hover:border-primary cursor-pointer"
            onClick={() => onSelect(c)}
          >
            <div className="text-lg font-medium">{c.name}</div>
            {c.description && (
              <div className="text-sm text-gray-400">{c.description}</div>
            )}
            <div className="text-xs text-gray-500 mt-2">
              Last updated: {new Date(c.updated_at).toLocaleString()}
            </div>
            <div className="text-xs text-gray-500">Storage: {c.storage.type}</div>
          </div>
        ))}
        {casesQuery.isLoading && <div>Loading...</div>}
        {casesQuery.isError && <div>Error loading cases</div>}
        {casesQuery.data && casesQuery.data.items.length === 0 && (
          <div>No cases found.</div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-[#111] border rounded p-6 w-full max-w-md space-y-4">
            <h2 className="text-xl font-semibold">Create Case</h2>
            <div className="space-y-2">
              <label className="block text-sm">Name</label>
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full border rounded px-3 py-2 bg-transparent"
                placeholder="e.g., ACME-2025-Incident"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm">Description</label>
              <textarea
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="w-full border rounded px-3 py-2 bg-transparent"
                placeholder="Optional description"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button className="px-3 py-2" onClick={() => setShowModal(false)}>
                Cancel
              </button>
              <button
                className="px-4 py-2 rounded bg-primary text-white"
                disabled={!newName || createMut.isPending}
                onClick={() => createMut.mutate()}
              >
                {createMut.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

