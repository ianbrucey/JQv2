import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithProviders } from 'test-utils';
import { DocumentsUploader } from '#/components/features/legal-cases/documents-uploader';

// Mock the hooks
vi.mock('#/hooks/mutation/use-legal-cases', () => ({
  useUploadCaseDocuments: vi.fn(),
  useListCaseDocuments: vi.fn(),
  useEnterLegalCase: vi.fn(),
}));

const mockUploadDocs = vi.fn();
const mockRefetch = vi.fn();

// Mock implementations
const { useUploadCaseDocuments, useListCaseDocuments, useEnterLegalCase } = await import('#/hooks/mutation/use-legal-cases');

describe('DocumentsUploader', () => {
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();

    // Reset mocks
    vi.clearAllMocks();

    // Setup default mock implementations
    vi.mocked(useEnterLegalCase).mockReturnValue({
      mutateAsync: vi.fn().mockResolvedValue({}),
      isPending: false,
    } as any);

    vi.mocked(useUploadCaseDocuments).mockReturnValue({
      mutateAsync: mockUploadDocs,
      isPending: false,
    } as any);

    vi.mocked(useListCaseDocuments).mockReturnValue({
      data: [],
      refetch: mockRefetch,
    } as any);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = (props = {}) => {
    const defaultProps = {
      caseId: 'test-case-123',
      ...props,
    };

    return renderWithProviders(<DocumentsUploader {...defaultProps} />);
  };

  describe('Basic Rendering', () => {
    it('renders the component with all essential elements', () => {
      renderComponent();

      expect(screen.getByText('Target Folder')).toBeInTheDocument();
      expect(screen.getByDisplayValue('inbox')).toBeInTheDocument();
      expect(screen.getByText('Drag and drop files here')).toBeInTheDocument();
      expect(screen.getByText('Select files')).toBeInTheDocument();
      expect(screen.getByText('PDF, Images (PNG/JPG/TIFF), DOCX, TXT, MD • Max 100MB each')).toBeInTheDocument();
    });

    it('renders folder dropdown with all options', () => {
      renderComponent();

      const folderSelect = screen.getByDisplayValue('inbox');
      expect(folderSelect).toBeInTheDocument();

      // Check all folder options are present
      expect(screen.getByRole('option', { name: 'Inbox' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Exhibits' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Research' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Active Drafts' })).toBeInTheDocument();
    });
  });

  describe('File Selection', () => {
    it('opens file picker when Select files button is clicked', async () => {
      renderComponent();

      const selectButton = screen.getByText('Select files');
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Mock the click method
      const clickSpy = vi.spyOn(fileInput, 'click');

      await user.click(selectButton);

      expect(clickSpy).toHaveBeenCalled();
    });

    it('handles file selection correctly', async () => {
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Create mock files
      const file1 = new File(['content1'], 'test1.pdf', { type: 'application/pdf' });
      const file2 = new File(['content2'], 'test2.jpg', { type: 'image/jpeg' });

      // Simulate file selection
      await user.upload(fileInput, [file1, file2]);

      // Check that files are displayed
      await waitFor(() => {
        expect(screen.getByText('test1.pdf')).toBeInTheDocument();
        expect(screen.getByText('test2.jpg')).toBeInTheDocument();
      });
    });

    it('validates file types and shows errors for invalid files', async () => {
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Create invalid file
      const invalidFile = new File(['content'], 'test.exe', { type: 'application/x-executable' });

      await user.upload(fileInput, [invalidFile]);

      await waitFor(() => {
        expect(screen.getByText(/Unsupported file type/)).toBeInTheDocument();
      });
    });

    it('validates file size and shows errors for oversized files', async () => {
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;

      // Create oversized file (mock size > 100MB)
      const oversizedFile = new File(['x'.repeat(101 * 1024 * 1024)], 'large.pdf', {
        type: 'application/pdf'
      });

      await user.upload(fileInput, [oversizedFile]);

      await waitFor(() => {
        expect(screen.getByText(/File too large/)).toBeInTheDocument();
      });
    });
  });

  describe('Upload Functionality', () => {
    it('enables upload button when files are selected', async () => {
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(fileInput, [file]);

      await waitFor(() => {
        const uploadButton = screen.getByText('Upload');
        expect(uploadButton).not.toBeDisabled();
      });
    });

    it('disables upload button when upload is pending', () => {
      vi.mocked(useUploadCaseDocuments).mockReturnValue({
        mutateAsync: mockUploadDocs,
        isPending: true,
      } as any);

      renderComponent();

      const uploadButton = screen.getByText('Uploading…');
      expect(uploadButton).toBeDisabled();
    });

    it('calls upload function with correct parameters', async () => {
      mockUploadDocs.mockResolvedValue({ success: true });

      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(fileInput, [file]);

      await waitFor(() => {
        const uploadButton = screen.getByText('Upload');
        expect(uploadButton).not.toBeDisabled();
      });

      await user.click(screen.getByText('Upload'));

      await waitFor(() => {
        expect(mockUploadDocs).toHaveBeenCalledWith({
          files: [file],
          targetFolder: 'inbox',
        });
      });
    });

    it('clears files after successful upload', async () => {
      mockUploadDocs.mockResolvedValue({ success: true });
      
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(fileInput, [file]);
      
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Upload'));

      await waitFor(() => {
        expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
      });
    });
  });

  describe('Folder Selection', () => {
    it('changes target folder when dropdown selection changes', async () => {
      renderComponent();

      const folderSelect = screen.getByDisplayValue('inbox');
      
      await user.selectOptions(folderSelect, 'exhibits');

      expect(screen.getByDisplayValue('exhibits')).toBeInTheDocument();
    });

    it('uploads to correct folder based on selection', async () => {
      mockUploadDocs.mockResolvedValue({ success: true });
      
      renderComponent();

      // Change folder to exhibits
      const folderSelect = screen.getByDisplayValue('inbox');
      await user.selectOptions(folderSelect, 'exhibits');

      // Add file and upload
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(fileInput, [file]);
      await user.click(screen.getByText('Upload'));

      await waitFor(() => {
        expect(mockUploadDocs).toHaveBeenCalledWith({
          files: [file],
          targetFolder: 'exhibits',
        });
      });
    });
  });

  describe('Clear Functionality', () => {
    it('clears selected files when Clear button is clicked', async () => {
      renderComponent();

      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      const file = new File(['content'], 'test.pdf', { type: 'application/pdf' });

      await user.upload(fileInput, [file]);
      
      await waitFor(() => {
        expect(screen.getByText('test.pdf')).toBeInTheDocument();
      });

      await user.click(screen.getByText('Clear'));

      expect(screen.queryByText('test.pdf')).not.toBeInTheDocument();
    });
  });

  describe('Document List', () => {
    it('displays uploaded documents', () => {
      const mockDocuments = [
        { id: '1', original_name: 'doc1.pdf', target_folder: 'inbox', size: 1024 },
        { id: '2', original_name: 'doc2.jpg', target_folder: 'exhibits', size: 2048 },
      ];

      vi.mocked(useListCaseDocuments).mockReturnValue({
        data: mockDocuments,
        refetch: mockRefetch,
      } as any);

      renderComponent();

      expect(screen.getByText('doc1.pdf')).toBeInTheDocument();
      expect(screen.getByText('doc2.jpg')).toBeInTheDocument();
      expect(screen.getByText('[inbox]')).toBeInTheDocument();
      expect(screen.getByText('[exhibits]')).toBeInTheDocument();
    });

    it('shows refresh button and calls refetch when clicked', async () => {
      renderComponent();

      const refreshButton = screen.getByText('Refresh');
      await user.click(refreshButton);

      expect(mockRefetch).toHaveBeenCalled();
    });
  });
});
