# Scalable Storage Architecture: Enterprise Legal Case Management

## Overview

This document outlines a scalable storage architecture for a multi-tenant legal case management system supporting 1,000+ users with 20+ cases each (20,000+ case directories total). The architecture addresses performance, security, compliance, and disaster recovery requirements specific to the legal industry.

## Scale Requirements Analysis

### Current Scale Targets
- **Users**: 1,000+ concurrent users
- **Cases per User**: 20+ active cases
- **Total Cases**: 20,000+ case directories
- **File Types**: PDFs, Markdown, Word docs, scripts, images, videos
- **Storage Growth**: ~100GB per user annually (estimated)
- **Total Storage**: 100TB+ with 3-year retention

### Performance Requirements
- **Case Loading**: < 2 seconds for case file listing
- **File Access**: < 1 second for document retrieval
- **Search**: < 5 seconds for cross-case search
- **Concurrent Users**: 200+ simultaneous active users
- **Backup Window**: < 4 hours for full system backup

## Recommended Architecture: Hybrid Distributed Storage

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Application Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   App       │  │   App       │  │   App       │         │
│  │ Server 1    │  │ Server 2    │  │ Server 3    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Metadata Layer                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         PostgreSQL Cluster (Primary/Replica)       │   │
│  │  - User management & authentication                │   │
│  │  - Case metadata & permissions                     │   │
│  │  - File metadata & search indexes                  │   │
│  │  - Audit logs & compliance tracking                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                 Storage Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Storage   │  │   Storage   │  │   Storage   │         │
│  │   Node 1    │  │   Node 2    │  │   Node 3    │         │
│  │  (Users     │  │  (Users     │  │  (Users     │         │
│  │   1-333)    │  │  334-666)   │  │  667-1000)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## Storage Distribution Strategy

### 1. User-Based Sharding
**Approach**: Distribute users across multiple storage nodes based on user ID hash.

```python
# User distribution algorithm
def get_storage_node(user_id: str) -> str:
    user_hash = hashlib.md5(user_id.encode()).hexdigest()
    node_id = int(user_hash[:8], 16) % NUM_STORAGE_NODES
    return f"storage-node-{node_id:02d}"

# Example distribution for 1000 users across 3 nodes
# Node 1: Users 1-333   (~/legal-storage-01/users/)
# Node 2: Users 334-666 (~/legal-storage-02/users/)
# Node 3: Users 667-1000(~/legal-storage-03/users/)
```

### 2. Storage Node Structure
```
/legal-storage-{node-id}/
├── users/
│   ├── user-001-john-doe/
│   │   ├── .user-profile.json
│   │   ├── cases/
│   │   │   ├── case-001-smith-v-jones/
│   │   │   │   ├── .case-metadata.json
│   │   │   │   ├── pleadings/
│   │   │   │   ├── discovery/
│   │   │   │   └── exhibits/
│   │   │   └── case-002-acme-contract/
│   │   └── shared-cases/          # Symlinks to shared cases
├── shared/
│   └── case-collaborations/       # Multi-user case storage
├── backups/
│   └── incremental/              # Node-specific backups
└── .node-config.json            # Node configuration
```

### 3. Benefits of This Approach
- **Horizontal Scaling**: Add storage nodes as user base grows
- **Load Distribution**: Even distribution of users across nodes
- **Fault Isolation**: Node failure affects only subset of users
- **Maintenance Windows**: Rolling updates without full downtime

## File System vs Database Hybrid Solution

### Recommended: Hybrid Architecture

#### Database Layer (PostgreSQL)
**Purpose**: Metadata, search, permissions, audit trails
```sql
-- Core tables for metadata management
CREATE TABLE users (
    user_id VARCHAR(50) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50),
    storage_node VARCHAR(20),
    created_at TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE cases (
    case_id VARCHAR(100) PRIMARY KEY,
    owner_id VARCHAR(50) REFERENCES users(user_id),
    title VARCHAR(500),
    client_name VARCHAR(255),
    case_type VARCHAR(50),
    status VARCHAR(20),
    storage_path TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE case_files (
    file_id UUID PRIMARY KEY,
    case_id VARCHAR(100) REFERENCES cases(case_id),
    file_path TEXT,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    file_size BIGINT,
    content_hash VARCHAR(64),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE case_collaborators (
    case_id VARCHAR(100) REFERENCES cases(case_id),
    user_id VARCHAR(50) REFERENCES users(user_id),
    permission_level VARCHAR(20),
    added_at TIMESTAMP,
    PRIMARY KEY (case_id, user_id)
);

-- Full-text search indexes
CREATE INDEX idx_cases_search ON cases USING gin(to_tsvector('english', title || ' ' || client_name));
CREATE INDEX idx_files_search ON case_files USING gin(to_tsvector('english', file_name));
```

#### File System Layer
**Purpose**: Actual document storage with hierarchical structure
- **Maintains folder hierarchy** for legal document organization
- **Preserves file relationships** and document workflows
- **Supports all file types** without conversion
- **Enables direct file system operations** for bulk operations

### Why Hybrid Approach?

#### Database Advantages
- **Fast Metadata Queries**: User authentication, case listing, search
- **ACID Compliance**: Critical for legal audit trails
- **Concurrent Access**: Handle multiple users safely
- **Backup Consistency**: Point-in-time recovery for metadata

#### File System Advantages
- **Natural Hierarchy**: Legal documents have inherent folder structures
- **File Type Agnostic**: PDFs, Word docs, images, videos, scripts
- **Performance**: Direct file access without database overhead
- **Familiar Interface**: Users understand folders and files
- **Backup Simplicity**: Standard file system backup tools

## Scalability Patterns Implementation

### 1. Horizontal Sharding Strategy
```python
class StorageRouter:
    def __init__(self):
        self.storage_nodes = [
            "storage-node-01.legal.internal",
            "storage-node-02.legal.internal",
            "storage-node-03.legal.internal"
        ]

    def get_user_storage_node(self, user_id: str) -> str:
        """Route user to specific storage node."""
        node_index = hash(user_id) % len(self.storage_nodes)
        return self.storage_nodes[node_index]

    def get_case_storage_path(self, user_id: str, case_id: str) -> str:
        """Get full storage path for case."""
        node = self.get_user_storage_node(user_id)
        return f"{node}/users/{user_id}/cases/{case_id}"
```

### 2. Read Replica Strategy
- **Primary Database**: Write operations, user authentication
- **Read Replicas**: Case browsing, search operations, reporting
- **Cache Layer**: Redis for frequently accessed case metadata

### 3. Content Delivery Network (CDN)
```python
class FileAccessLayer:
    def get_file_url(self, user_id: str, case_id: str, file_path: str) -> str:
        """Generate secure, time-limited file access URL."""
        storage_node = self.router.get_user_storage_node(user_id)

        # Generate signed URL with expiration
        signed_url = self.generate_signed_url(
            node=storage_node,
            path=f"users/{user_id}/cases/{case_id}/{file_path}",
            expires_in=3600  # 1 hour
        )
        return signed_url
```

## Performance Optimization Strategies

### 1. Caching Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │───▶│   Redis Cache   │───▶│   PostgreSQL    │
│     Server      │    │                 │    │    Database     │
│                 │    │ - User sessions │    │                 │
│                 │    │ - Case metadata │    │                 │
│                 │    │ - File listings │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2. File System Optimizations
- **SSD Storage**: Fast random access for case file listings
- **File System Choice**: XFS or ext4 with optimized mount options
- **Directory Indexing**: Enable directory indexing for large folders
- **Async I/O**: Non-blocking file operations for better concurrency

### 3. Database Optimizations
```sql
-- Optimized indexes for common queries
CREATE INDEX idx_cases_owner_status ON cases(owner_id, status);
CREATE INDEX idx_cases_updated_desc ON cases(updated_at DESC);
CREATE INDEX idx_files_case_type ON case_files(case_id, file_type);

-- Partitioning for large tables
CREATE TABLE case_files_2024 PARTITION OF case_files
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## Security and Compliance Architecture

### 1. Data Encryption
```python
class SecureFileStorage:
    def store_file(self, user_id: str, case_id: str, file_data: bytes) -> str:
        """Store file with encryption at rest."""
        # Encrypt file content
        encrypted_data = self.encrypt_file(file_data, user_id)

        # Store with secure path
        storage_path = self.get_secure_path(user_id, case_id)
        file_id = self.write_encrypted_file(storage_path, encrypted_data)

        # Log access for audit trail
        self.audit_logger.log_file_access(user_id, case_id, file_id, "WRITE")

        return file_id
```

### 2. Access Control
- **Path Validation**: Prevent directory traversal attacks
- **User Isolation**: Strict enforcement of user boundaries
- **Permission Checking**: Database-driven access control
- **Audit Logging**: Complete trail of file access and modifications

### 3. Compliance Features
- **Data Retention**: Automated archival and deletion policies
- **Audit Trails**: Immutable logs of all system access
- **Encryption**: AES-256 encryption for sensitive documents
- **Access Logs**: Detailed logging for regulatory compliance

## Backup and Disaster Recovery

### 1. Multi-Tier Backup Strategy
```
┌─────────────────────────────────────────────────────────────┐
│                    Backup Architecture                      │
├─────────────────────────────────────────────────────────────┤
│  Tier 1: Real-time Replication                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Primary DB  │───▶│ Replica DB  │───▶│ Backup DB   │     │
│  │ Storage N1  │    │ Storage N2  │    │ Storage N3  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
│  Tier 2: Daily Incremental Backups                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Incremental backup to cloud storage (S3/Azure)     │   │
│  │ - Database dumps with point-in-time recovery       │   │
│  │ - File system snapshots with deduplication         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Tier 3: Weekly Full Backups                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Complete system backup to offsite location         │   │
│  │ - Encrypted archives with 7-year retention         │   │
│  │ - Geographic distribution for disaster recovery    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2. Recovery Procedures
```python
class DisasterRecovery:
    def restore_user_data(self, user_id: str, restore_point: datetime) -> bool:
        """Restore user data to specific point in time."""
        # 1. Restore database metadata
        self.restore_database_point_in_time(user_id, restore_point)

        # 2. Restore file system data
        storage_node = self.get_user_storage_node(user_id)
        self.restore_file_system_snapshot(storage_node, user_id, restore_point)

        # 3. Verify data integrity
        return self.verify_restoration(user_id)

    def failover_storage_node(self, failed_node: str) -> bool:
        """Failover users from failed storage node."""
        affected_users = self.get_users_on_node(failed_node)
        backup_node = self.get_available_backup_node()

        for user_id in affected_users:
            self.migrate_user_storage(user_id, failed_node, backup_node)

        return True
```

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-4)
- [ ] Set up PostgreSQL cluster with replication
- [ ] Implement user sharding algorithm
- [ ] Create storage node infrastructure
- [ ] Basic file operations with metadata tracking

### Phase 2: Scalability (Weeks 5-8)
- [ ] Implement caching layer with Redis
- [ ] Add read replicas for database
- [ ] Set up monitoring and alerting
- [ ] Performance testing and optimization

### Phase 3: Enterprise Features (Weeks 9-12)
- [ ] Implement backup and disaster recovery
- [ ] Add audit logging and compliance features
- [ ] Security hardening and penetration testing
- [ ] Load testing with 1000+ concurrent users

### Phase 4: Advanced Features (Weeks 13-16)
- [ ] Content delivery network integration
- [ ] Advanced search with Elasticsearch
- [ ] Automated scaling and load balancing
- [ ] Multi-region deployment capability

## Monitoring and Alerting

### Key Metrics to Monitor
- **Storage Node Health**: Disk usage, I/O performance, availability
- **Database Performance**: Query response times, connection pools, replication lag
- **Application Metrics**: User session counts, case access patterns, file upload/download rates
- **Security Events**: Failed login attempts, unauthorized access attempts, data access patterns

### Alerting Thresholds
- Storage node disk usage > 80%
- Database query response time > 2 seconds
- File access failure rate > 1%
- Backup failure or delay > 30 minutes

## Cost Analysis and ROI

### Infrastructure Costs (Annual)
- **Storage Nodes**: 3 nodes × $5,000 = $15,000
- **Database Cluster**: Primary + 2 replicas = $12,000
- **Cloud Backup**: 100TB × $23/TB/month = $27,600
- **Load Balancers & CDN**: $6,000
- **Total Annual Infrastructure**: ~$60,600

### Cost per User
- **1,000 users**: $60.60 per user per year
- **Scales efficiently**: Additional users have minimal marginal cost
- **Break-even**: Competitive with enterprise legal software licensing

### Performance Guarantees
- **99.9% Uptime**: Maximum 8.76 hours downtime per year
- **Sub-2 Second Response**: Case loading and file access
- **Concurrent Users**: Support for 200+ simultaneous users
- **Data Durability**: 99.999999999% (11 9's) with multi-tier backup

## Technology Stack Summary

### Core Technologies
- **Database**: PostgreSQL 15+ with streaming replication
- **Caching**: Redis 7+ for session and metadata caching
- **Storage**: XFS file system on SSD storage
- **Load Balancing**: HAProxy or NGINX for traffic distribution
- **Backup**: Incremental backups with cloud storage integration
- **Monitoring**: Prometheus + Grafana for metrics and alerting

### Legal Industry Compliance
- **HIPAA Ready**: Encryption at rest and in transit
- **SOC 2 Type II**: Audit trail and access controls
- **Data Retention**: Configurable retention policies
- **Geographic Restrictions**: Data residency controls
- **Audit Logging**: Immutable logs for regulatory compliance

This scalable storage architecture provides a robust foundation for enterprise-scale legal case management while maintaining the flexibility and performance required for legal document workflows. The hybrid approach balances the need for structured metadata management with the natural file system organization that legal professionals expect.
