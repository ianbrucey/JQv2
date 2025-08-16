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
  });
}

export function useLegalSystemStatus() {
  return useQuery({
    queryKey: legalCaseKeys.status(),
    queryFn: () => legalCaseAPI.getSystemStatus(),
    staleTime: 60000, // 1 minute
    retry: 1, // Only retry once if system isn't ready
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

export function useDeleteLegalCase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (caseId: string) => legalCaseAPI.deleteCase(caseId),
    onSuccess: (_, caseId) => {
      // Remove from cache and invalidate lists
      queryClient.removeQueries({ queryKey: legalCaseKeys.detail(caseId) });
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: legalCaseKeys.workspace() });
    },
  });
}
