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
  private baseUrl = '/api/legal';

  async createCase(data: CreateCaseRequest): Promise<LegalCase> {
    const response = await fetch(`${this.baseUrl}/cases`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create case');
    }

    return response.json();
  }

  async listCases(): Promise<LegalCase[]> {
    const response = await fetch(`${this.baseUrl}/cases`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list cases');
    }

    return response.json();
  }

  async getCase(caseId: string): Promise<LegalCase> {
    const response = await fetch(`${this.baseUrl}/cases/${caseId}`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get case');
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
    const response = await fetch(`${this.baseUrl}/cases/${caseId}/enter`, {
      method: 'POST',
      headers: {
        'X-Session-ID': `legal_case_${caseId}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to enter case');
    }

    return response.json();
  }

  async exitWorkspace(): Promise<{
    previous_case_id?: string;
    workspace_restored: boolean;
    message: string;
  }> {
    const response = await fetch(`${this.baseUrl}/workspace/exit`, {
      method: 'POST',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to exit workspace');
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
    const response = await fetch(`${this.baseUrl}/workspace/current`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workspace info');
    }

    return response.json();
  }

  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${this.baseUrl}/system/status`);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get system status');
    }

    return response.json();
  }

  async deleteCase(caseId: string): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/cases/${caseId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete case');
    }

    return response.json();
  }

  async uploadDocuments(
    caseId: string,
    files: File[],
    options: { targetFolder: LegalFolder; tags?: string[]; note?: string; sessionId?: string }
  ): Promise<UploadDocumentsResponse> {
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    form.append('target_folder', options.targetFolder);
    if (options.tags && options.tags.length) form.append('tags', JSON.stringify(options.tags));
    if (options.note) form.append('note', options.note);

    const response = await fetch(`${this.baseUrl}/cases/${caseId}/documents/upload`, {
      method: 'POST',
      headers: {
        'X-Session-ID': options.sessionId || getSessionIdForCase(caseId),
      },
      body: form,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload documents');
    }

    return response.json();
  }

  async listDocuments(caseId: string, sessionId?: string): Promise<DocumentMeta[]> {
    const response = await fetch(`${this.baseUrl}/cases/${caseId}/documents`, {
      headers: {
        'X-Session-ID': sessionId || getSessionIdForCase(caseId),
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list documents');
    }

    const result: ListDocumentsResponse = await response.json();
    return result.items;
  }
}

// -------------------------------
// Documents API (Option A backend)
// -------------------------------
export type LegalFolder = 'inbox' | 'exhibits' | 'research' | 'active_drafts';

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
  source: 'ui' | string;
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

function getSessionIdForCase(caseId: string) {
  return `legal_case_${caseId}`;
}

// Export the API instance
// Export the API instance
export const legalCaseAPI = new LegalCaseAPI();
