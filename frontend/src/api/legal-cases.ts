/**
 * API service for legal case management
 */

export interface LegalCase {
  case_id: string;
  title: string;
  case_number?: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
  last_accessed_at?: string;
  workspace_path?: string;
  draft_system_initialized: boolean;
  conversation_id?: string;
}

export interface CreateCaseRequest {
  title: string;
  case_number?: string;
  description?: string;
}

export interface SystemStatus {
  system_initialized: boolean;
  workspace_manager_ready: boolean;
  database_ready: boolean;
  draft_system_available: boolean;
  current_case_id?: string;
}

class LegalCaseAPI {
  // Base URLs
  private apiBaseUrl = "/api"; // for conversation/document endpoints
  private legalBaseUrl = "/api/legal"; // for legal cases endpoints

  async createCase(data: CreateCaseRequest): Promise<LegalCase> {
    const response = await fetch(`${this.legalBaseUrl}/cases`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to create case");
    }

    return response.json();
  }

  async listCases(): Promise<LegalCase[]> {
    const response = await fetch(`${this.legalBaseUrl}/cases`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to list cases");
    }

    return response.json();
  }

  async getCase(caseId: string): Promise<LegalCase> {
    const response = await fetch(`${this.legalBaseUrl}/cases/${caseId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get case");
    }

    return response.json();
  }

  async enterCase(caseId: string): Promise<{
    case_id: string;
    case_title: string;
    workspace_path: string;
    draft_system_initialized: boolean;
    workspace_mounted: boolean;
  }> {
    const response = await fetch(`${this.legalBaseUrl}/cases/${caseId}/enter`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to enter case");
    }

    return response.json();
  }

  async exitWorkspace(): Promise<{
    previous_case_id?: string;
    workspace_restored: boolean;
    message: string;
  }> {
    const response = await fetch(`${this.legalBaseUrl}/workspace/exit`, {
      method: "POST",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to exit workspace");
    }

    return response.json();
  }

  async getCurrentWorkspace(): Promise<{
    current_case_id?: string;
    is_in_case_workspace: boolean;
    workspace_base?: string;
    current_case?: {
      case_id: string;
      title: string;
      case_number?: string;
      status: string;
    };
  }> {
    const response = await fetch(`${this.legalBaseUrl}/workspace/current`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get workspace info");
    }

    return response.json();
  }

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.legalBaseUrl}/system/status`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to get system status");
    }

    return response.json();
  }

  async deleteCase(caseId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.legalBaseUrl}/cases/${caseId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete case");
    }

    return response.json();
  }

  async uploadDocuments(
    conversationId: string,
    files: File[],
    options: { targetFolder: LegalFolder; tags?: string[]; note?: string },
  ): Promise<UploadDocumentsResponse> {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    form.append("target_folder", options.targetFolder);
    if (options.tags && options.tags.length)
      form.append("tags", JSON.stringify(options.tags));
    if (options.note) form.append("note", options.note);

    const response = await fetch(
      `${this.apiBaseUrl}/conversations/${conversationId}/documents/upload`,
      {
        method: "POST",
        body: form,
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to upload documents");
    }

    return response.json();
  }

  async listDocuments(conversationId: string): Promise<DocumentMeta[]> {
    // First get the case ID from conversation metadata
    const metaResponse = await fetch(
      `${this.apiBaseUrl}/conversations/${conversationId}/metadata`,
    );
    if (!metaResponse.ok) {
      throw new Error("Failed to get conversation metadata");
    }
    const metadata = await metaResponse.json();
    const caseId = metadata.case_id;

    if (!caseId) {
      throw new Error("No case ID found in conversation metadata");
    }

    // Now get documents using the case-based endpoint
    const response = await fetch(
      `${this.apiBaseUrl}/legal/cases/${caseId}/documents`,
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to list documents");
    }

    const result: ListDocumentsResponse = await response.json();
    return result.items;
  }

  async listFiles(
    conversationId: string,
    path?: string,
  ): Promise<FileListResponse> {
    const url = new URL(
      `${window.location.origin}${this.apiBaseUrl}/conversations/${conversationId}/files/browse`,
    );
    if (path) {
      url.searchParams.set("path", path);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to list files");
    }

    return response.json();
  }

  async deleteFile(conversationId: string, path: string): Promise<void> {
    const url = new URL(
      `${window.location.origin}${this.apiBaseUrl}/conversations/${conversationId}/files`,
    );
    url.searchParams.set("path", path);

    const response = await fetch(url.toString(), {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Failed to delete file");
    }
  }
}

// -------------------------------
// Documents API (Option A backend)
// -------------------------------
export type LegalFolder = "inbox" | "exhibits" | "research" | "active_drafts";

export interface DocumentMeta {
  id: string;
  case_id: string;
  original_name: string;
  stored_name: string;
  rel_path: string;
  size: number;
  mime?: string | null;
  checksum_sha256: string;
  target_folder: LegalFolder;
  tags: string[];
  note?: string | null;
  uploaded_at: string;
  source: "ui" | string;
}

export interface UploadDocumentsResponse {
  uploaded: DocumentMeta[];
  skipped: { original_name: string; reason: string; duplicate_of?: string }[];
  errors?: { file?: string; error: string; status?: number }[];
}

export interface ListDocumentsResponse {
  items: DocumentMeta[];
  total: number;
}

export interface FileItem {
  name: string;
  path: string;
  type: "file" | "directory";
  size?: number;
  modified: number;
  extension?: string;
}

export interface FileListResponse {
  items: FileItem[];
  path: string;
  total: number;
}

// Export the API instance
// Export the API instance
export const legalCaseAPI = new LegalCaseAPI();
