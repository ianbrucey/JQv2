import React, { useState, useEffect, useCallback } from "react";
import { Editor } from "@monaco-editor/react";
import { ChevronLeft, Save, FileText, Eye, EyeOff } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkBreaks from "remark-breaks";
import { useTranslation } from "react-i18next";

interface Section {
  id: string;
  name: string;
  file: string;
  order?: string;
}

interface DraftMeta {
  draft_id: string;
  name: string;
  type: string | null;
  created_at: string | null;
  updated_at: string | null;
  sections: Section[];
}

interface SectionContent {
  section_id: string;
  name: string;
  content: string;
  file_path: string;
}

interface DraftEditorProps {
  caseId: string;
  draft: DraftMeta;
  onBack: () => void;
}

export default function DraftEditor({ caseId, draft, onBack }: DraftEditorProps) {
  const { t } = useTranslation();
  const [selectedSectionId, setSelectedSectionId] = useState<string>("");
  const [sectionContent, setSectionContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Auto-save functionality with debounce
  const saveSection = useCallback(async (content: string) => {
    if (!selectedSectionId || saving) return;

    try {
      setSaving(true);
      setError(null);
      setSaveError(null);

      const response = await fetch(
        `/api/legal/cases/${caseId}/drafts/${draft.draft_id}/sections/${selectedSectionId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to save section: ${response.status}`);
      }

      setHasUnsavedChanges(false);
      setLastSaved(new Date());
    } catch (e: any) {
      console.error("Failed to save section:", e);
      setSaveError(e?.message || String(e));
      setError(e?.message || String(e));
    } finally {
      setSaving(false);
    }
  }, [caseId, draft.draft_id, selectedSectionId, saving]);

  const handleSectionChange = (sectionId: string) => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        "You have unsaved changes. Do you want to save them before switching sections?"
      );
      if (confirmed) {
        saveSection(sectionContent);
      }
    }
    setSelectedSectionId(sectionId);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + S to save
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (hasUnsavedChanges) {
          saveSection(sectionContent);
        }
      }

      // Ctrl/Cmd + 1-9 to switch sections
      if ((e.ctrlKey || e.metaKey) && e.key >= '1' && e.key <= '9') {
        e.preventDefault();
        const sectionIndex = parseInt(e.key) - 1;
        if (sectionIndex < draft.sections.length) {
          handleSectionChange(draft.sections[sectionIndex].id);
        }
      }

      // Ctrl/Cmd + P to toggle preview
      if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
        e.preventDefault();
        setShowPreview(!showPreview);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [hasUnsavedChanges, sectionContent, saveSection, draft.sections, showPreview, handleSectionChange]);

  // Auto-select first section on mount
  useEffect(() => {
    if (draft.sections.length > 0 && !selectedSectionId) {
      setSelectedSectionId(draft.sections[0].id);
    }
  }, [draft.sections, selectedSectionId]);

  // Load section content when section changes
  useEffect(() => {
    if (!selectedSectionId) return;

    const loadSectionContent = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `/api/legal/cases/${caseId}/drafts/${draft.draft_id}/sections/${selectedSectionId}`
        );

        if (!response.ok) {
          throw new Error(`Failed to load section: ${response.status}`);
        }

        const data: SectionContent = await response.json();
        setSectionContent(data.content);
        setHasUnsavedChanges(false);
      } catch (e: any) {
        console.error("Failed to load section:", e);
        setError(e?.message || String(e));
      } finally {
        setLoading(false);
      }
    };

    loadSectionContent();
  }, [caseId, draft.draft_id, selectedSectionId]);

  // Debounced auto-save
  useEffect(() => {
    if (!hasUnsavedChanges || !sectionContent) return;

    const timeoutId = setTimeout(() => {
      saveSection(sectionContent);
    }, 2000); // Auto-save after 2 seconds of inactivity

    return () => clearTimeout(timeoutId);
  }, [sectionContent, hasUnsavedChanges, saveSection]);

  const handleContentChange = (value: string | undefined) => {
    if (value !== undefined) {
      setSectionContent(value);
      setHasUnsavedChanges(true);
    }
  };

  const handleManualSave = () => {
    if (hasUnsavedChanges) {
      saveSection(sectionContent);
    }
  };

  const currentSection = draft.sections.find(s => s.id === selectedSectionId);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-neutral-600 bg-neutral-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
            >
              <ChevronLeft size={16} />
              Back to Drafts
            </button>
            <div className="text-gray-400">|</div>
            <div>
              <h2 className="text-lg font-semibold">{draft.name}</h2>
              <p className="text-sm text-gray-400 capitalize">
                {draft.type} • {draft.sections.length} sections
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-sm">
              {saving && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse"></div>
                  <span className="text-yellow-400">Saving...</span>
                </div>
              )}
              {hasUnsavedChanges && !saving && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-orange-400 rounded-full"></div>
                  <span className="text-orange-400">Unsaved changes</span>
                </div>
              )}
              {!hasUnsavedChanges && !saving && !saveError && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-green-400">
                    Saved {lastSaved && `at ${lastSaved.toLocaleTimeString()}`}
                  </span>
                </div>
              )}
              {saveError && (
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                  <span className="text-red-400" title={saveError}>Save failed</span>
                </div>
              )}
            </div>

            <button
              onClick={handleManualSave}
              disabled={!hasUnsavedChanges || saving}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save size={14} />
              Save
            </button>
            
            <button
              onClick={() => setShowPreview(!showPreview)}
              className="flex items-center gap-2 px-3 py-1 text-sm bg-neutral-600 text-white rounded hover:bg-neutral-500"
            >
              {showPreview ? <EyeOff size={14} /> : <Eye size={14} />}
              {showPreview ? "Hide Preview" : "Show Preview"}
            </button>
          </div>
        </div>
      </div>

      {/* Section Tabs */}
      <div className="border-b border-neutral-600 bg-neutral-800">
        <div className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-neutral-600 scrollbar-track-neutral-800">
          {draft.sections.map((section, index) => {
            const isActive = selectedSectionId === section.id;
            const sectionNumber = index + 1;

            return (
              <button
                key={section.id}
                onClick={() => handleSectionChange(section.id)}
                className={`flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 transition-all duration-200 ${
                  isActive
                    ? "border-blue-500 text-blue-400 bg-neutral-700 shadow-sm"
                    : "border-transparent text-gray-400 hover:text-white hover:bg-neutral-700 hover:border-gray-500"
                }`}
                title={`${section.name} (Ctrl+${sectionNumber})`}
              >
                <div className="flex items-center gap-2">
                  <div className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                    isActive
                      ? "bg-blue-500 text-white"
                      : "bg-neutral-600 text-gray-300"
                  }`}>
                    {sectionNumber}
                  </div>
                  <FileText size={14} />
                  <span className="whitespace-nowrap">{section.name}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-red-900 border-b border-red-700 text-red-200 text-sm">
          {error}
        </div>
      )}

      {/* Editor Content */}
      <div className="flex-1 flex">
        {/* Editor Panel */}
        <div className={`${showPreview ? "w-1/2" : "w-full"} flex flex-col`}>
          <div className="p-3 bg-neutral-800 border-b border-neutral-600">
            <h3 className="text-sm font-medium">
              {currentSection?.name || "Select a section"}
            </h3>
          </div>
          
          <div className="flex-1">
            {loading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-gray-500">Loading section...</div>
              </div>
            ) : (
              <Editor
                height="100%"
                defaultLanguage="markdown"
                value={sectionContent}
                onChange={handleContentChange}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  wordWrap: "on",
                  lineNumbers: "on",
                  folding: false,
                  fontSize: 14,
                  padding: { top: 16, bottom: 16 },
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                }}
              />
            )}
          </div>
        </div>

        {/* Preview Panel */}
        {showPreview && (
          <div className="w-1/2 border-l border-neutral-600 flex flex-col">
            <div className="p-3 bg-neutral-800 border-b border-neutral-600">
              <h3 className="text-sm font-medium">Preview</h3>
            </div>

            <div className="flex-1 p-4 bg-white text-black overflow-auto">
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm, remarkBreaks]}
                  components={{
                    h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 text-gray-900">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 text-gray-800">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-lg font-medium mb-2 text-gray-700">{children}</h3>,
                    p: ({ children }) => <p className="mb-3 text-gray-900 leading-relaxed">{children}</p>,
                    strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                    em: ({ children }) => <em className="italic text-gray-800">{children}</em>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-3 text-gray-900">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-3 text-gray-900">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-700 mb-3">{children}</blockquote>,
                    code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>,
                    pre: ({ children }) => <pre className="bg-gray-100 p-3 rounded mb-3 overflow-x-auto">{children}</pre>,
                  }}
                >
                  {sectionContent || "# No content\n\nStart typing to see the preview..."}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
