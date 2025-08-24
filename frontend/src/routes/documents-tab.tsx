import React from "react";
import { useConversationId } from "#/hooks/use-conversation-id";
import { DocumentsUploader } from "#/components/features/legal-cases/documents-uploader";
import { CaseFileBrowser } from "#/components/features/legal-cases/case-file-browser";

export default function DocumentsTab() {
  const { conversationId } = useConversationId();

  // Fetch real case_id from conversation metadata
  const [realCaseId, setRealCaseId] = React.useState<string | undefined>(
    undefined,
  );
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `/api/conversations/${conversationId}/metadata`,
        );
        if (!res.ok) return;
        const meta = await res.json();
        if (!cancelled) setRealCaseId(meta?.case_id);
      } catch {}
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  return (
    <div className="h-full w-full p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-xl text-white font-semibold mb-2">
            Document Upload
          </h2>
          <p className="text-gray-400">
            Upload documents to your case workspace. Files will be saved to the
            Intake folder by default.
          </p>
        </div>

        <div className="bg-base-primary border border-gray-700 rounded-lg p-6">
          {realCaseId ? (
            <DocumentsUploader caseId={conversationId} />
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-400">Loading case information...</p>
            </div>
          )}
        </div>

        {/* File Browser Section */}
        <div className="mt-6">
          <div className="mb-4">
            <h2 className="text-xl text-white font-semibold mb-2">
              File Explorer
            </h2>
            <p className="text-gray-400">
              Browse the case workspace directory structure and verify document
              placement.
            </p>
          </div>

          {realCaseId ? (
            <CaseFileBrowser conversationId={conversationId} />
          ) : (
            <div className="bg-base-primary border border-gray-700 rounded-lg p-6">
              <div className="text-center py-8">
                <p className="text-gray-400">Loading case information...</p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 bg-base-primary border border-gray-700 rounded-lg p-4">
          <h3 className="text-lg text-white font-medium mb-3">
            Folder Structure
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-gray-300 font-medium">Inbox</span>
              </div>
              <p className="text-gray-500 ml-4">
                Initial document uploads and unprocessed files
              </p>

              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span className="text-gray-300 font-medium">Exhibits</span>
              </div>
              <p className="text-gray-500 ml-4">
                Evidence and supporting documents for the case
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                <span className="text-gray-300 font-medium">Research</span>
              </div>
              <p className="text-gray-500 ml-4">
                Legal research, case law, and reference materials
              </p>

              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                <span className="text-gray-300 font-medium">Active Drafts</span>
              </div>
              <p className="text-gray-500 ml-4">
                Working documents and drafts in progress
              </p>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-amber-900/20 border border-amber-500/50 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <svg
              className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <div>
              <h4 className="text-amber-300 font-medium mb-1">
                Supported File Types
              </h4>
              <p className="text-amber-200 text-sm">
                PDF, Images (PNG, JPG, TIFF), Word Documents (DOCX), Text Files
                (TXT), Markdown (MD)
              </p>
              <p className="text-amber-200 text-sm mt-1">
                Maximum file size: 100MB per file
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
