# Multi-Tenant Architecture: Legal Case Management

## Overview

The legal case management system must support multiple users (lawyers, paralegals, pro se litigants) with isolated case data, user authentication, and role-based access control. This document outlines the high-level multi-tenant architecture focusing on user onboarding and case initialization.

## User Types and Roles

### User Categories
1. **Lawyers**: Full access to all features, case management, client data
2. **Paralegals**: Limited access based on assigned cases, document preparation
3. **Pro Se Litigants**: Self-representation, simplified interface, basic features
4. **Administrators**: System management, user oversight (future consideration)

### Permission Levels
- **Case Owner**: Full read/write access to case and all documents
- **Case Collaborator**: Read/write access to assigned documents/folders
- **Case Viewer**: Read-only access to shared documents
- **System User**: Basic authentication and profile management

## High-Level Multi-Tenant Flow

### Initial User Journey
```
1. Application Access
   ↓
2. Authentication Gate
   - New User: Registration → Profile Setup
   - Existing User: Login → Dashboard
   ↓
3. User Dashboard
   - My Cases (user-specific)
   - Shared Cases (collaborative)
   - Create New Case
   ↓
4. Case Selection/Creation
   - User-isolated case list
   - Simple case creation form
   ↓
5. Case Workspace
   - Basic folder structure
   - AI assistance within case context
```

## File System Architecture for Multi-Tenancy

### Directory Structure Approach
```
~/legal-workspace/                    # Root application directory
├── users/                           # User-specific data
│   ├── user-001-john-doe/           # Individual user directory
│   │   ├── .user-profile.json       # User metadata
│   │   ├── cases/                   # User's cases
│   │   │   ├── case-001/            # Individual case folder
│   │   │   ├── case-002/            # Individual case folder
│   │   │   └── shared/              # Cases shared with this user
│   │   └── templates/               # User-specific templates
│   ├── user-002-jane-smith/
│   └── user-003-mike-jones/
├── shared/                          # Shared resources
│   ├── templates/                   # System-wide templates
│   └── collaboration/               # Shared case metadata
└── .system/                         # System configuration
    ├── users.json                   # User registry
    └── config.json                  # System settings
```

### User Isolation Benefits
- **Data Security**: Each user has isolated directory
- **Simple Backup**: User directories can be backed up independently
- **Scalability**: Easy to move users to different storage locations
- **Compliance**: Clear data ownership and access boundaries

## Authentication and User Management

### Simplified Authentication Flow
```
┌─────────────────────────────────────────────────────────────┐
│ Login/Registration Screen                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Welcome to Legal Workspace                                 │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Email: [user@example.com                         ] │   │
│  │ Password: [••••••••••••••••••••••••••••••••••••] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Sign In]  [Create Account]                               │
│                                                             │
│  First time? Choose your role:                             │
│  ○ Lawyer        ○ Paralegal        ○ Self-Represented     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### User Profile Setup (New Users)
```
┌─────────────────────────────────────────────────────────────┐
│ Profile Setup                                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Tell us about yourself:                                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Full Name: [John Doe                              ] │   │
│  │ Role: [Lawyer ▼]                                   │   │
│  │ Organization: [Smith & Associates                 ] │   │
│  │ Bar Number: [12345 (optional)                     ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Practice Areas (select all that apply):                   │
│  ☑ Personal Injury    ☐ Corporate Law    ☐ Family Law     │
│  ☐ Criminal Defense   ☐ Real Estate     ☐ Estate Planning │
│                                                             │
│                                    [Complete Setup]        │
└─────────────────────────────────────────────────────────────┘
```

## User Dashboard Design

### Multi-User Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ Legal Workspace - John Doe (Lawyer)              [Profile ▼]│
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  My Cases                                [+ Create New Case]│
│                                                             │
│  Recent Cases                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📁 Smith v. Jones                                  │   │
│  │    Personal Injury • Last accessed: 2 hours ago    │   │
│  │    Status: Active                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📁 ACME Corp Contract Review                       │   │
│  │    Corporate • Last accessed: Yesterday             │   │
│  │    Status: In Progress                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Shared with Me                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📁 Johnson Estate (shared by Jane Smith)           │   │
│  │    Estate Planning • Role: Collaborator             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Simplified Case Creation for Multi-Tenant

### Minimal Case Creation Form
```
┌─────────────────────────────────────────────────────────────┐
│ Create New Case                                        [×]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Basic Information                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Case Name: [Smith v. Jones                        ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Client/Matter: [John Smith                        ] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Case Type (optional):                                      │
│  ○ Personal Injury    ○ Corporate      ○ Family Law        │
│  ○ Criminal Defense   ○ Real Estate    ○ Other             │
│                                                             │
│  This will create a basic folder structure for your case.  │
│                                                             │
│                              [Cancel]  [Create Case]       │
└─────────────────────────────────────────────────────────────┘
```

## Technical Implementation Considerations

### User Data Model
```json
{
  "user_id": "user-001-john-doe",
  "email": "john.doe@example.com",
  "full_name": "John Doe",
  "role": "lawyer",
  "organization": "Smith & Associates",
  "bar_number": "12345",
  "practice_areas": ["personal-injury", "corporate"],
  "created_date": "2024-01-15T10:30:00Z",
  "last_login": "2024-08-09T14:22:00Z",
  "preferences": {
    "theme": "light",
    "default_case_type": "personal-injury"
  }
}
```

### Case Ownership Model
```json
{
  "case_id": "case-001-smith-v-jones",
  "owner_id": "user-001-john-doe",
  "title": "Smith v. Jones",
  "client": "John Smith",
  "created_date": "2024-01-15T10:30:00Z",
  "collaborators": [
    {
      "user_id": "user-002-jane-smith",
      "role": "paralegal",
      "permissions": ["read", "write"]
    }
  ],
  "folder_path": "users/user-001-john-doe/cases/case-001-smith-v-jones"
}
```

## Security and Access Control

### File System Security
- **User Directory Isolation**: Each user can only access their own directory
- **Path Validation**: Prevent directory traversal attacks
- **Case Access Control**: Verify user ownership before case operations
- **Shared Case Permissions**: Validate collaborator access rights

### Session Management
- **JWT Tokens**: Stateless authentication with user claims
- **Session Timeout**: Automatic logout after inactivity
- **Role-Based Access**: Different UI features based on user role
- **Audit Logging**: Track user actions for compliance

## Database vs File System Decision

### File System Approach (Recommended for MVP)
**Pros:**
- Simple implementation and deployment
- Easy backup and migration
- Familiar to users (folders and files)
- No database setup or maintenance
- Version control friendly

**Cons:**
- Limited query capabilities
- Potential performance issues with many users
- Manual implementation of search and filtering
- Concurrent access challenges

### Hybrid Approach (Future Enhancement)
- **File System**: Document storage and case folders
- **SQLite Database**: User management, case metadata, search indexing
- **Migration Path**: Start with file system, add database later

## Implementation Priority

### Phase 1: Single-User Foundation
1. Basic case creation and folder management
2. Simple file system structure
3. Case selection interface

### Phase 2: Multi-User Authentication
1. User registration and login
2. User profile management
3. User-isolated case directories

### Phase 3: Collaboration Features
1. Case sharing between users
2. Role-based permissions
3. Collaborative editing

### Phase 4: Advanced Multi-Tenancy
1. Organization management
2. Advanced access controls
3. Audit trails and compliance

## Key Architectural Decisions

### User Identification
- **Email-based**: Use email as primary identifier
- **Folder-safe IDs**: Generate filesystem-safe user IDs
- **Human-readable**: Include name in folder structure for clarity

### Case Isolation
- **User-scoped**: Cases belong to specific users
- **Sharing Model**: Explicit sharing with permission levels
- **Data Ownership**: Clear ownership and access boundaries

### Scalability Considerations
- **Horizontal Scaling**: Easy to distribute users across servers
- **Storage Scaling**: User directories can be moved independently
- **Performance**: File system operations scale with user activity

This multi-tenant architecture provides a foundation for supporting multiple users while maintaining the simplicity of file system-based case management. The approach prioritizes user isolation, security, and ease of implementation while providing a clear path for future enhancements.
