/**
 * React Query hooks for legal case management
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { legalCaseAPI, CreateCaseRequest, LegalCase } from '#/api/legal-cases';

// Query keys
export const legalCaseKeys = {
  all: ['legal-cases'] as const,
  lists: () => [...legalCaseKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...legalCaseKeys.lists(), { filters }] as const,
  details: () => [...legalCaseKeys.all, 'detail'] as const,
  detail: (id: string) => [...legalCaseKeys.details(), id] as const,
  workspace: () => [...legalCaseKeys.all, 'workspace'] as const,
  status: () => [...legalCaseKeys.all, 'status'] as const,
};

// Queries
export function useLegalCases() {
  return useQuery({
    queryKey: legalCaseKeys.lists(),
    queryFn: () => legalCaseAPI.listCases(),
    staleTime: 30000, // 30 seconds
    meta: { disableToast: true }, // Disable error toasts for this query
    retry: false, // Don't retry on failure
  });
}

export function useLegalCase(caseId: string) {
  return useQuery({
    queryKey: legalCaseKeys.detail(caseId),
    queryFn: () => legalCaseAPI.getCase(caseId),
    enabled: !!caseId,
  });
}

export function useCurrentWorkspace() {
  return useQuery({
    queryKey: legalCaseKeys.workspace(),
    queryFn: () => legalCaseAPI.getCurrentWorkspace(),
    staleTime: 10000, // 10 seconds
    refetchInterval: 30000, // Refetch every 30 seconds
    meta: { disableToast: true }, // Disable error toasts for this query
    retry: false, // Don't retry on failure
  });
}

export function useLegalSystemStatus() {
  return useQuery({
    queryKey: legalCaseKeys.status(),
    queryFn: () => legalCaseAPI.getSystemStatus(),
    staleTime: 60000, // 1 minute
    retry: 1, // Only retry once if system isn't ready
    meta: { disableToast: true }, // Disable error toasts for this query
  });
}

// Mutations
export function useCreateLegalCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateCaseRequest) => legalCaseAPI.createCase(data),
    onSuccess: (newCase: LegalCase) => {
      // Invalidate and refetch cases list
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.lists() });

      // Add the new case to the cache
      queryClient.setQueryData(legalCaseKeys.detail(newCase.case_id), newCase);
    },
  });
}

export function useEnterLegalCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (caseId: string) => legalCaseAPI.enterCase(caseId),
    onSuccess: (data, caseId) => {
      // Invalidate workspace query to reflect new state
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.workspace() });

      // Update the case's last_accessed_at in cache
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.detail(caseId) });
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.lists() });
    },
    meta: { disableToast: true },
    retry: false,
  });
}

export function useDeleteLegalCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (caseId: string) => legalCaseAPI.deleteCase(caseId),
    onSuccess: (data, caseId) => {
      // Invalidate and refetch cases list
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.lists() });
      // Also invalidate workspace query in case the deleted case was current
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.workspace() });
      // Remove the case from detail cache
      queryClient.removeQueries({ queryKey: legalCaseKeys.detail(caseId) });
    },
  });
}

export function useExitWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => legalCaseAPI.exitWorkspace(),
    onSuccess: () => {
      // Invalidate workspace query to reflect exit
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.workspace() });
    },
  });
}



// Documents hooks
export function useUploadCaseDocuments(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (params: { files: File[]; targetFolder: 'inbox' | 'exhibits' | 'research' | 'active_drafts'; tags?: string[]; note?: string }) =>
      legalCaseAPI.uploadDocuments(conversationId, params.files, { targetFolder: params.targetFolder, tags: params.tags, note: params.note }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.workspace() });
      // Invalidate a future documents list key if we add a dedicated key later
    },
  });
}

export function useListCaseDocuments(
  conversationId: string,
  folder?: 'inbox' | 'exhibits' | 'research' | 'active_drafts',
  options?: { enabled?: boolean },
) {
  return useQuery({
    queryKey: ['legal-cases', 'documents', conversationId, folder ?? 'all'],
    queryFn: () => legalCaseAPI.listDocuments(conversationId),
    enabled: (options?.enabled ?? true) && !!conversationId,
    staleTime: 10000,
  });
}

export function useListCaseFiles(conversationId: string, path?: string) {
  return useQuery({
    queryKey: ['legal-cases', 'files', conversationId, path ?? ''],
    queryFn: () => legalCaseAPI.listFiles(conversationId, path),
    enabled: !!conversationId,
    staleTime: 10000,
  });
}

export function useDeleteCaseFile(conversationId: string, path?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (filePath: string) => legalCaseAPI.deleteFile(conversationId, filePath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['legal-cases', 'files', conversationId, path ?? ''] });
    },
  });
}

