# Frontend Component Architecture and State Management

## Technology Stack
- **Framework**: React 18+ with TypeScript
- **State Management**: Redux Toolkit + RTK Query
- **Routing**: React Router v6
- **UI Library**: Tailwind CSS + Headless UI
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios with interceptors

## Project Structure
```
src/
├── components/           # Reusable UI components
│   ├── ui/              # Basic UI components (Button, Input, etc.)
│   ├── forms/           # Form components
│   ├── layout/          # Layout components
│   └── legal/           # Legal-specific components
├── pages/               # Page components
├── hooks/               # Custom React hooks
├── store/               # Redux store and slices
├── services/            # API services
├── types/               # TypeScript type definitions
├── utils/               # Utility functions
└── constants/           # Application constants
```

## State Management Architecture

### Redux Store Configuration
```typescript
// store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import authSlice from './slices/authSlice';
import caseSlice from './slices/caseSlice';
import workspaceSlice from './slices/workspaceSlice';
import { apiSlice } from './api/apiSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    cases: caseSlice,
    workspace: workspaceSlice,
    api: apiSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(apiSlice.middleware),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

### Authentication Slice
```typescript
// store/slices/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface User {
  id: string;
  email: string;
  fullName: string;
  role: 'lawyer' | 'paralegal' | 'pro_se' | 'admin';
  organization?: string;
  barNumber?: string;
  practiceAreas: string[];
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.isLoading = true;
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
      state.isLoading = false;
      state.error = null;
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
      state.isLoading = false;
      state.error = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const { loginStart, loginSuccess, loginFailure, logout, clearError } = authSlice.actions;
export default authSlice.reducer;
```

### Case Management Slice
```typescript
// store/slices/caseSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface CaseFile {
  id: string;
  caseId: string;
  logicalPath: string;
  fileName: string;
  fileType?: string;
  mimeType?: string;
  fileSize: number;
  isDerived: boolean;
  uploadStatus: 'pending' | 'uploading' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
}

interface Case {
  id: string;
  ownerId: string;
  title: string;
  description?: string;
  clientName?: string;
  matterNumber?: string;
  caseType: 'litigation' | 'transactional' | 'estate' | 'corporate' | 'real_estate' | 'criminal' | 'family' | 'custom';
  status: 'active' | 'archived' | 'completed' | 'on_hold';
  court?: string;
  caseNumber?: string;
  incidentDate?: string;
  filingDate?: string;
  discoveryDeadline?: string;
  trialDate?: string;
  caseValue?: number;
  folderPath: string;
  totalSizeBytes: number;
  fileCount: number;
  isPinned: boolean;
  tags: string[];
  customFields: Record<string, any>;
  createdAt: string;
  updatedAt: string;
  lastAccessed: string;
}

interface CaseState {
  cases: Case[];
  selectedCase: Case | null;
  caseFiles: CaseFile[];
  isLoading: boolean;
  error: string | null;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    hasMore: boolean;
  };
  filters: {
    status?: string;
    search?: string;
    caseType?: string;
  };
}

const initialState: CaseState = {
  cases: [],
  selectedCase: null,
  caseFiles: [],
  isLoading: false,
  error: null,
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
    hasMore: false,
  },
  filters: {},
};

const caseSlice = createSlice({
  name: 'cases',
  initialState,
  reducers: {
    setCases: (state, action: PayloadAction<Case[]>) => {
      state.cases = action.payload;
    },
    addCase: (state, action: PayloadAction<Case>) => {
      state.cases.unshift(action.payload);
    },
    updateCase: (state, action: PayloadAction<Case>) => {
      const index = state.cases.findIndex(c => c.id === action.payload.id);
      if (index !== -1) {
        state.cases[index] = action.payload;
      }
      if (state.selectedCase?.id === action.payload.id) {
        state.selectedCase = action.payload;
      }
    },
    removeCase: (state, action: PayloadAction<string>) => {
      state.cases = state.cases.filter(c => c.id !== action.payload);
      if (state.selectedCase?.id === action.payload) {
        state.selectedCase = null;
      }
    },
    setSelectedCase: (state, action: PayloadAction<Case | null>) => {
      state.selectedCase = action.payload;
    },
    setCaseFiles: (state, action: PayloadAction<CaseFile[]>) => {
      state.caseFiles = action.payload;
    },
    addCaseFile: (state, action: PayloadAction<CaseFile>) => {
      state.caseFiles.push(action.payload);
    },
    updateCaseFile: (state, action: PayloadAction<CaseFile>) => {
      const index = state.caseFiles.findIndex(f => f.id === action.payload.id);
      if (index !== -1) {
        state.caseFiles[index] = action.payload;
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setPagination: (state, action: PayloadAction<Partial<CaseState['pagination']>>) => {
      state.pagination = { ...state.pagination, ...action.payload };
    },
    setFilters: (state, action: PayloadAction<Partial<CaseState['filters']>>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
  },
});

export const {
  setCases,
  addCase,
  updateCase,
  removeCase,
  setSelectedCase,
  setCaseFiles,
  addCaseFile,
  updateCaseFile,
  setLoading,
  setError,
  setPagination,
  setFilters,
} = caseSlice.actions;

export default caseSlice.reducer;
```

### Workspace Slice
```typescript
// store/slices/workspaceSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface WorkspaceState {
  isProvisioning: boolean;
  isReady: boolean;
  containerInfo: {
    containerId?: string;
    port?: number;
    sessionId?: string;
  } | null;
  activeCaseId: string | null;
  error: string | null;
  lastActivity: string | null;
}

const initialState: WorkspaceState = {
  isProvisioning: false,
  isReady: false,
  containerInfo: null,
  activeCaseId: null,
  error: null,
  lastActivity: null,
};

const workspaceSlice = createSlice({
  name: 'workspace',
  initialState,
  reducers: {
    startProvisioning: (state, action: PayloadAction<string>) => {
      state.isProvisioning = true;
      state.isReady = false;
      state.activeCaseId = action.payload;
      state.error = null;
    },
    provisioningComplete: (state, action: PayloadAction<WorkspaceState['containerInfo']>) => {
      state.isProvisioning = false;
      state.isReady = true;
      state.containerInfo = action.payload;
      state.error = null;
    },
    provisioningFailed: (state, action: PayloadAction<string>) => {
      state.isProvisioning = false;
      state.isReady = false;
      state.containerInfo = null;
      state.error = action.payload;
    },
    updateActivity: (state) => {
      state.lastActivity = new Date().toISOString();
    },
    resetWorkspace: (state) => {
      state.isProvisioning = false;
      state.isReady = false;
      state.containerInfo = null;
      state.activeCaseId = null;
      state.error = null;
      state.lastActivity = null;
    },
  },
});

export const {
  startProvisioning,
  provisioningComplete,
  provisioningFailed,
  updateActivity,
  resetWorkspace,
} = workspaceSlice.actions;

export default workspaceSlice.reducer;
```

## API Layer with RTK Query

### Base API Slice
```typescript
// store/api/apiSlice.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User', 'Case', 'File', 'Session'],
  endpoints: () => ({}),
});
```

### Authentication API
```typescript
// store/api/authApi.ts
import { apiSlice } from './apiSlice';

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  fullName: string;
  role: string;
  organization?: string;
  barNumber?: string;
  practiceAreas?: string[];
}

interface AuthResponse {
  accessToken: string;
  tokenType: string;
  expiresAt: string;
  user: User;
}

export const authApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation<AuthResponse, LoginRequest>({
      query: (credentials) => ({
        url: '/auth/login',
        method: 'POST',
        body: credentials,
      }),
    }),
    register: builder.mutation<User, RegisterRequest>({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
    }),
    logout: builder.mutation<void, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
    }),
    getCurrentUser: builder.query<User, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
} = authApi;
```

### Cases API
```typescript
// store/api/casesApi.ts
import { apiSlice } from './apiSlice';

interface CaseListParams {
  page?: number;
  pageSize?: number;
  status?: string;
  search?: string;
}

interface CreateCaseRequest {
  title: string;
  description?: string;
  clientName?: string;
  caseType: string;
  court?: string;
  caseNumber?: string;
  incidentDate?: string;
  filingDate?: string;
  discoveryDeadline?: string;
  trialDate?: string;
  caseValue?: number;
  tags?: string[];
  customFields?: Record<string, any>;
}

export const casesApi = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    getCases: builder.query<CaseListResponse, CaseListParams>({
      query: (params) => ({
        url: '/cases',
        params,
      }),
      providesTags: ['Case'],
    }),
    getCase: builder.query<Case, string>({
      query: (caseId) => `/cases/${caseId}`,
      providesTags: (result, error, caseId) => [{ type: 'Case', id: caseId }],
    }),
    createCase: builder.mutation<Case, CreateCaseRequest>({
      query: (caseData) => ({
        url: '/cases',
        method: 'POST',
        body: caseData,
      }),
      invalidatesTags: ['Case'],
    }),
    updateCase: builder.mutation<Case, { caseId: string; updates: Partial<CreateCaseRequest> }>({
      query: ({ caseId, updates }) => ({
        url: `/cases/${caseId}`,
        method: 'PUT',
        body: updates,
      }),
      invalidatesTags: (result, error, { caseId }) => [{ type: 'Case', id: caseId }],
    }),
    deleteCase: builder.mutation<void, { caseId: string; permanent?: boolean }>({
      query: ({ caseId, permanent = false }) => ({
        url: `/cases/${caseId}`,
        method: 'DELETE',
        params: { permanent },
      }),
      invalidatesTags: ['Case'],
    }),
    getCaseFiles: builder.query<FileListResponse, { caseId: string; path?: string }>({
      query: ({ caseId, path = '' }) => ({
        url: `/cases/${caseId}/files`,
        params: { path },
      }),
      providesTags: (result, error, { caseId }) => [{ type: 'File', id: caseId }],
    }),
  }),
});

export const {
  useGetCasesQuery,
  useGetCaseQuery,
  useCreateCaseMutation,
  useUpdateCaseMutation,
  useDeleteCaseMutation,
  useGetCaseFilesQuery,
} = casesApi;
```

## Core Components

### Authentication Components
```typescript
// components/auth/LoginForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLoginMutation } from '../../store/api/authApi';
import { useAppDispatch } from '../../hooks/redux';
import { loginStart, loginSuccess, loginFailure } from '../../store/slices/authSlice';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export const LoginForm: React.FC = () => {
  const dispatch = useAppDispatch();
  const [login, { isLoading }] = useLoginMutation();
  
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    try {
      dispatch(loginStart());
      const result = await login(data).unwrap();
      dispatch(loginSuccess({
        user: result.user,
        token: result.accessToken,
      }));
    } catch (error: any) {
      dispatch(loginFailure(error.data?.detail || 'Login failed'));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          {...register('email')}
          type="email"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          {...register('password')}
          type="password"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
      >
        {isLoading ? 'Signing in...' : 'Sign in'}
      </button>
    </form>
  );
};
```

### Case Selection Component
```typescript
// components/legal/CaseSelectionPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGetCasesQuery } from '../../store/api/casesApi';
import { useAppDispatch } from '../../hooks/redux';
import { setSelectedCase } from '../../store/slices/caseSlice';
import { CaseCard } from './CaseCard';
import { CreateCaseModal } from './CreateCaseModal';

export const CaseSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState({
    search: '',
    status: '',
  });

  const {
    data: casesData,
    isLoading,
    error,
  } = useGetCasesQuery({
    page: 1,
    pageSize: 20,
    ...filters,
  });

  const handleCaseSelect = (caseItem: Case) => {
    dispatch(setSelectedCase(caseItem));
    navigate(`/workspace/${caseItem.id}`);
  };

  const handleCreateCase = () => {
    setShowCreateModal(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-600">Error loading cases</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Your Cases</h1>
        <button
          onClick={handleCreateCase}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
        >
          Create New Case
        </button>
      </div>

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search cases..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="w-full max-w-md px-3 py-2 border border-gray-300 rounded-md"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {casesData?.cases.map((caseItem) => (
          <CaseCard
            key={caseItem.id}
            case={caseItem}
            onSelect={() => handleCaseSelect(caseItem)}
          />
        ))}
      </div>

      {showCreateModal && (
        <CreateCaseModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={(newCase) => {
            setShowCreateModal(false);
            handleCaseSelect(newCase);
          }}
        />
      )}
    </div>
  );
};
```

### Workspace Component
```typescript
// components/legal/WorkspacePage.tsx
import React, { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { useGetCaseQuery } from '../../store/api/casesApi';
import { startProvisioning, provisioningComplete, provisioningFailed } from '../../store/slices/workspaceSlice';
import { WorkspaceInterface } from './WorkspaceInterface';
import { LoadingScreen } from '../ui/LoadingScreen';

export const WorkspacePage: React.FC = () => {
  const { caseId } = useParams<{ caseId: string }>();
  const dispatch = useAppDispatch();
  const workspace = useAppSelector((state) => state.workspace);
  
  const {
    data: caseData,
    isLoading: isCaseLoading,
    error: caseError,
  } = useGetCaseQuery(caseId!, {
    skip: !caseId,
  });

  useEffect(() => {
    if (caseData && !workspace.isReady && !workspace.isProvisioning) {
      provisionWorkspace();
    }
  }, [caseData, workspace.isReady, workspace.isProvisioning]);

  const provisionWorkspace = async () => {
    if (!caseId) return;

    try {
      dispatch(startProvisioning(caseId));
      
      // Call workspace provisioning API
      const response = await fetch(`/api/workspace/${caseId}/provision`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Workspace provisioning failed');
      }

      const result = await response.json();
      dispatch(provisioningComplete({
        containerId: result.containerId,
        port: result.port,
        sessionId: result.sessionId,
      }));
    } catch (error: any) {
      dispatch(provisioningFailed(error.message));
    }
  };

  if (isCaseLoading || workspace.isProvisioning) {
    return (
      <LoadingScreen 
        message={workspace.isProvisioning ? "Preparing your workspace..." : "Loading case..."}
      />
    );
  }

  if (caseError || workspace.error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-600">
          {workspace.error || 'Error loading case'}
        </div>
      </div>
    );
  }

  if (!workspace.isReady || !caseData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div>Workspace not ready</div>
      </div>
    );
  }

  return <WorkspaceInterface case={caseData} />;
};
```

This frontend architecture provides a robust, type-safe React application with efficient state management, proper separation of concerns, and reusable components optimized for the legal case management workflow.
