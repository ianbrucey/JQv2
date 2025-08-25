/**
 * Hook for real-time draft synchronization via WebSocket
 */

import { useEffect, useCallback, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useConversationId } from "./use-conversation-id";

// Draft-specific event types
export interface DraftSectionsChangedEvent {
  observation: "draft_sections_changed";
  case_id: string;
  draft_id: string;
  sections: Array<{
    id: string;
    name: string;
    file: string;
    order: number;
  }>;
  change_type: "added" | "removed" | "reordered";
  changed_section_id?: string;
}

export interface DraftContentChangedEvent {
  observation: "draft_content_changed";
  case_id: string;
  draft_id: string;
  section_id: string;
  content: string;
  file_path: string;
  change_source: "external" | "user" | "agent";
}

export interface DraftMetadataChangedEvent {
  observation: "draft_metadata_changed";
  case_id: string;
  draft_id: string;
  metadata: Record<string, any>;
  changed_fields: string[];
}

export interface DraftSyncStatusEvent {
  observation: "draft_sync_status";
  case_id: string;
  draft_id?: string;
  status: "connected" | "disconnected" | "syncing" | "error";
  message_text: string;
}

type DraftEvent = 
  | DraftSectionsChangedEvent 
  | DraftContentChangedEvent 
  | DraftMetadataChangedEvent 
  | DraftSyncStatusEvent;

interface UseDraftSyncOptions {
  caseId?: string;
  draftId?: string;
  onSectionsChanged?: (event: DraftSectionsChangedEvent) => void;
  onContentChanged?: (event: DraftContentChangedEvent) => void;
  onMetadataChanged?: (event: DraftMetadataChangedEvent) => void;
  onSyncStatus?: (event: DraftSyncStatusEvent) => void;
}

export function useDraftSync(options: UseDraftSyncOptions = {}) {
  const queryClient = useQueryClient();
  const { conversationId } = useConversationId();
  const eventHandlersRef = useRef(options);
  
  // Update event handlers ref when options change
  useEffect(() => {
    eventHandlersRef.current = options;
  }, [options]);

  const handleDraftEvent = useCallback((event: any) => {
    // Check if this is a draft-related event
    if (!event.observation || !event.observation.startsWith('draft_')) {
      return;
    }

    const draftEvent = event as DraftEvent;
    const handlers = eventHandlersRef.current;

    // Filter events by case/draft if specified
    if (handlers.caseId && draftEvent.case_id !== handlers.caseId) {
      return;
    }
    if (handlers.draftId && 'draft_id' in draftEvent && draftEvent.draft_id !== handlers.draftId) {
      return;
    }

    console.log('Draft sync event received:', draftEvent);

    switch (draftEvent.observation) {
      case 'draft_sections_changed':
        // Invalidate drafts queries to refresh section lists
        queryClient.invalidateQueries({
          queryKey: ['legal', 'cases', draftEvent.case_id, 'drafts']
        });
        queryClient.invalidateQueries({
          queryKey: ['legal', 'cases', draftEvent.case_id, 'drafts', draftEvent.draft_id]
        });
        
        handlers.onSectionsChanged?.(draftEvent as DraftSectionsChangedEvent);
        break;

      case 'draft_content_changed':
        // Invalidate section content queries
        const contentEvent = draftEvent as DraftContentChangedEvent;
        queryClient.invalidateQueries({
          queryKey: ['legal', 'cases', contentEvent.case_id, 'drafts', contentEvent.draft_id, 'sections', contentEvent.section_id]
        });
        
        handlers.onContentChanged?.(contentEvent);
        break;

      case 'draft_metadata_changed':
        // Invalidate draft metadata queries
        queryClient.invalidateQueries({
          queryKey: ['legal', 'cases', draftEvent.case_id, 'drafts', draftEvent.draft_id]
        });
        
        handlers.onMetadataChanged?.(draftEvent as DraftMetadataChangedEvent);
        break;

      case 'draft_sync_status':
        handlers.onSyncStatus?.(draftEvent as DraftSyncStatusEvent);
        break;
    }
  }, [queryClient]);

  useEffect(() => {
    // Listen for draft events from the WebSocket provider
    const handleMessage = (event: CustomEvent) => {
      handleDraftEvent(event.detail);
    };

    // Listen for WebSocket events on the global event bus
    window.addEventListener('oh_event', handleMessage as EventListener);

    return () => {
      window.removeEventListener('oh_event', handleMessage as EventListener);
    };
  }, [handleDraftEvent]);

  return {
    // Return utility functions for manual operations if needed
    invalidateDraftQueries: useCallback((caseId: string, draftId?: string) => {
      queryClient.invalidateQueries({
        queryKey: ['legal', 'cases', caseId, 'drafts', ...(draftId ? [draftId] : [])]
      });
    }, [queryClient]),
    
    invalidateSectionQueries: useCallback((caseId: string, draftId: string, sectionId?: string) => {
      queryClient.invalidateQueries({
        queryKey: ['legal', 'cases', caseId, 'drafts', draftId, 'sections', ...(sectionId ? [sectionId] : [])]
      });
    }, [queryClient])
  };
}

// Helper hook for draft editor components
export function useDraftEditorSync(caseId: string, draftId: string) {
  const queryClient = useQueryClient();

  return useDraftSync({
    caseId,
    draftId,
    onSectionsChanged: useCallback((event: DraftSectionsChangedEvent) => {
      console.log(`Sections changed in draft ${draftId}:`, event.change_type, event.changed_section_id);
      
      // Show a toast notification for section changes
      if (event.change_type === 'added') {
        // Could show a toast: "New section added: {section_name}"
      } else if (event.change_type === 'removed') {
        // Could show a toast: "Section removed: {section_name}"
      }
    }, [draftId]),
    
    onContentChanged: useCallback((event: DraftContentChangedEvent) => {
      if (event.change_source === 'external') {
        console.log(`External content change in section ${event.section_id}`);
        // Could show a toast: "Section content updated by external process"
      }
    }, []),
    
    onSyncStatus: useCallback((event: DraftSyncStatusEvent) => {
      console.log('Draft sync status:', event.status, event.message_text);
      // Could update a sync status indicator in the UI
    }, [])
  });
}
