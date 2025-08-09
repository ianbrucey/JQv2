# File Storage Abstraction Layer

## Technology Stack
- **Cloud Storage**: AWS S3 / Azure Blob Storage / Google Cloud Storage
- **Python SDK**: boto3 (AWS) / azure-storage-blob / google-cloud-storage
- **Async Support**: aiofiles, aiohttp
- **File Processing**: python-magic for MIME type detection
- **Hashing**: hashlib for content integrity

## Storage Interface Design

### Abstract Storage Interface
```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, AsyncIterator, BinaryIO
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import mimetypes

@dataclass
class StorageObject:
    """Represents a stored object with metadata."""
    key: str
    size: int
    last_modified: datetime
    etag: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

@dataclass
class PresignedUrl:
    """Presigned URL for direct client uploads."""
    url: str
    fields: Dict[str, str]
    expires_at: datetime

class StorageInterface(ABC):
    """Abstract interface for object storage operations."""
    
    @abstractmethod
    async def upload_object(
        self,
        key: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StorageObject:
        """Upload object to storage."""
        pass
    
    @abstractmethod
    async def download_object(self, key: str) -> bytes:
        """Download object from storage."""
        pass
    
    @abstractmethod
    async def download_object_stream(self, key: str) -> AsyncIterator[bytes]:
        """Download object as async stream."""
        pass
    
    @abstractmethod
    async def get_object_metadata(self, key: str) -> Optional[StorageObject]:
        """Get object metadata without downloading content."""
        pass
    
    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        """Delete object from storage."""
        pass
    
    @abstractmethod
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[StorageObject]:
        """List objects with optional prefix filter."""
        pass
    
    @abstractmethod
    async def generate_presigned_upload_url(
        self,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600,
        max_size: Optional[int] = None
    ) -> PresignedUrl:
        """Generate presigned URL for direct client uploads."""
        pass
    
    @abstractmethod
    async def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate presigned URL for direct client downloads."""
        pass
    
    @abstractmethod
    async def copy_object(self, source_key: str, dest_key: str) -> bool:
        """Copy object within storage."""
        pass
    
    @abstractmethod
    async def object_exists(self, key: str) -> bool:
        """Check if object exists."""
        pass
```

## AWS S3 Implementation

### S3 Storage Service
```python
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config
import aiohttp
import asyncio
from typing import Optional, Dict, List, AsyncIterator

class S3StorageService(StorageInterface):
    """AWS S3 implementation of storage interface."""
    
    def __init__(
        self,
        bucket_name: str,
        region: str = "us-east-1",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None  # For S3-compatible services
    ):
        self.bucket_name = bucket_name
        self.region = region
        
        # Configure boto3 client
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        )
        
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        self.s3_client = session.client(
            's3',
            config=config,
            endpoint_url=endpoint_url
        )
        
        # Verify bucket access
        self._verify_bucket_access()
    
    def _verify_bucket_access(self):
        """Verify bucket exists and is accessible."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise ValueError(f"Bucket {self.bucket_name} does not exist")
            elif error_code == '403':
                raise ValueError(f"Access denied to bucket {self.bucket_name}")
            else:
                raise
        except NoCredentialsError:
            raise ValueError("AWS credentials not found")
    
    async def upload_object(
        self,
        key: str,
        content: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> StorageObject:
        """Upload object to S3."""
        try:
            # Auto-detect content type if not provided
            if not content_type:
                content_type = self._detect_content_type(key, content)
            
            # Calculate content hash
            content_hash = hashlib.sha256(content).hexdigest()
            
            # Prepare metadata
            s3_metadata = metadata or {}
            s3_metadata['content-hash'] = content_hash
            
            # Upload to S3
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=content,
                    ContentType=content_type,
                    Metadata=s3_metadata,
                    ServerSideEncryption='AES256'
                )
            )
            
            return StorageObject(
                key=key,
                size=len(content),
                last_modified=datetime.utcnow(),
                etag=response['ETag'].strip('"'),
                content_type=content_type,
                metadata=s3_metadata
            )
            
        except ClientError as e:
            raise StorageError(f"Failed to upload object {key}: {e}")
    
    async def download_object(self, key: str) -> bytes:
        """Download object from S3."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectNotFoundError(f"Object {key} not found")
            raise StorageError(f"Failed to download object {key}: {e}")
    
    async def download_object_stream(self, key: str) -> AsyncIterator[bytes]:
        """Download object as async stream."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.get_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            )
            
            # Stream in chunks
            chunk_size = 8192
            body = response['Body']
            
            while True:
                chunk = await loop.run_in_executor(None, body.read, chunk_size)
                if not chunk:
                    break
                yield chunk
                
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise ObjectNotFoundError(f"Object {key} not found")
            raise StorageError(f"Failed to stream object {key}: {e}")
    
    async def get_object_metadata(self, key: str) -> Optional[StorageObject]:
        """Get object metadata from S3."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            )
            
            return StorageObject(
                key=key,
                size=response['ContentLength'],
                last_modified=response['LastModified'],
                etag=response['ETag'].strip('"'),
                content_type=response.get('ContentType'),
                metadata=response.get('Metadata', {})
            )
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            raise StorageError(f"Failed to get metadata for {key}: {e}")
    
    async def delete_object(self, key: str) -> bool:
        """Delete object from S3."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=key
                )
            )
            return True
            
        except ClientError as e:
            raise StorageError(f"Failed to delete object {key}: {e}")
    
    async def list_objects(
        self,
        prefix: str = "",
        max_keys: int = 1000
    ) -> List[StorageObject]:
        """List objects in S3 bucket."""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=prefix,
                    MaxKeys=max_keys
                )
            )
            
            objects = []
            for obj in response.get('Contents', []):
                objects.append(StorageObject(
                    key=obj['Key'],
                    size=obj['Size'],
                    last_modified=obj['LastModified'],
                    etag=obj['ETag'].strip('"')
                ))
            
            return objects
            
        except ClientError as e:
            raise StorageError(f"Failed to list objects: {e}")
    
    async def generate_presigned_upload_url(
        self,
        key: str,
        content_type: Optional[str] = None,
        expires_in: int = 3600,
        max_size: Optional[int] = None
    ) -> PresignedUrl:
        """Generate presigned URL for S3 upload."""
        try:
            conditions = []
            fields = {}
            
            if content_type:
                conditions.append({"Content-Type": content_type})
                fields['Content-Type'] = content_type
            
            if max_size:
                conditions.append(["content-length-range", 0, max_size])
            
            # Add server-side encryption
            conditions.append({"x-amz-server-side-encryption": "AES256"})
            fields['x-amz-server-side-encryption'] = "AES256"
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_post(
                    Bucket=self.bucket_name,
                    Key=key,
                    Fields=fields,
                    Conditions=conditions,
                    ExpiresIn=expires_in
                )
            )
            
            return PresignedUrl(
                url=response['url'],
                fields=response['fields'],
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in)
            )
            
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned upload URL: {e}")
    
    async def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate presigned URL for S3 download."""
        try:
            loop = asyncio.get_event_loop()
            url = await loop.run_in_executor(
                None,
                lambda: self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': key},
                    ExpiresIn=expires_in
                )
            )
            return url
            
        except ClientError as e:
            raise StorageError(f"Failed to generate presigned download URL: {e}")
    
    async def copy_object(self, source_key: str, dest_key: str) -> bool:
        """Copy object within S3 bucket."""
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.copy_object(
                    CopySource=copy_source,
                    Bucket=self.bucket_name,
                    Key=dest_key,
                    ServerSideEncryption='AES256'
                )
            )
            return True
            
        except ClientError as e:
            raise StorageError(f"Failed to copy object: {e}")
    
    async def object_exists(self, key: str) -> bool:
        """Check if object exists in S3."""
        try:
            await self.get_object_metadata(key)
            return True
        except ObjectNotFoundError:
            return False
    
    def _detect_content_type(self, key: str, content: bytes) -> str:
        """Detect content type from file extension and content."""
        # Try to detect from file extension
        content_type, _ = mimetypes.guess_type(key)
        
        if not content_type:
            # Try to detect from content using python-magic
            try:
                import magic
                content_type = magic.from_buffer(content[:1024], mime=True)
            except ImportError:
                # Fallback to application/octet-stream
                content_type = 'application/octet-stream'
        
        return content_type
```

## File Service Layer

### Legal File Service
```python
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

class LegalFileService:
    """Service layer for legal file operations."""
    
    def __init__(self, storage: StorageInterface, db: AsyncSession):
        self.storage = storage
        self.db = db
    
    async def init_file_upload(
        self,
        case_id: uuid.UUID,
        file_data: FileUploadInit
    ) -> FileUploadResponse:
        """Initialize file upload process."""
        try:
            # Generate file ID
            file_id = uuid.uuid4()
            
            # Generate storage key
            storage_key = self._generate_storage_key(case_id, file_data.logical_path)
            
            # Create file record in database
            file_record = CaseFile(
                id=file_id,
                case_id=case_id,
                logical_path=file_data.logical_path,
                file_name=file_data.file_name,
                mime_type=file_data.mime_type,
                file_size=file_data.file_size,
                storage_key=storage_key,
                content_hash=file_data.content_hash,
                upload_status='pending'
            )
            
            self.db.add(file_record)
            await self.db.commit()
            
            # Generate presigned upload URL
            presigned_url = await self.storage.generate_presigned_upload_url(
                key=storage_key,
                content_type=file_data.mime_type,
                expires_in=3600,  # 1 hour
                max_size=100 * 1024 * 1024  # 100MB limit
            )
            
            return FileUploadResponse(
                file_id=file_id,
                upload_url=presigned_url.url,
                expires_at=presigned_url.expires_at,
                required_headers=presigned_url.fields
            )
            
        except Exception as e:
            await self.db.rollback()
            raise FileUploadError(f"Failed to initialize file upload: {e}")
    
    async def complete_file_upload(
        self,
        file_id: uuid.UUID,
        etag: str
    ) -> bool:
        """Complete file upload after successful upload to storage."""
        try:
            # Get file record
            file_record = await self.db.get(CaseFile, file_id)
            if not file_record:
                return False
            
            # Verify file exists in storage
            storage_object = await self.storage.get_object_metadata(file_record.storage_key)
            if not storage_object:
                return False
            
            # Update file record
            file_record.upload_status = 'completed'
            file_record.file_size = storage_object.size
            file_record.content_hash = storage_object.metadata.get('content-hash')
            file_record.updated_at = datetime.utcnow()
            
            # Update case statistics
            await self._update_case_statistics(file_record.case_id)
            
            await self.db.commit()
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise FileUploadError(f"Failed to complete file upload: {e}")
    
    async def download_file(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[bytes]:
        """Download file content."""
        try:
            # Get file record with access check
            file_record = await self._get_file_with_access_check(file_id, user_id)
            if not file_record:
                return None
            
            # Download from storage
            content = await self.storage.download_object(file_record.storage_key)
            
            # Log download for audit
            await self._log_file_access(file_id, user_id, 'download')
            
            return content
            
        except Exception as e:
            raise FileDownloadError(f"Failed to download file: {e}")
    
    async def get_download_url(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        expires_in: int = 3600
    ) -> Optional[str]:
        """Get presigned download URL for file."""
        try:
            # Get file record with access check
            file_record = await self._get_file_with_access_check(file_id, user_id)
            if not file_record:
                return None
            
            # Generate presigned download URL
            url = await self.storage.generate_presigned_download_url(
                file_record.storage_key,
                expires_in=expires_in
            )
            
            # Log access for audit
            await self._log_file_access(file_id, user_id, 'access')
            
            return url
            
        except Exception as e:
            raise FileDownloadError(f"Failed to generate download URL: {e}")
    
    async def list_case_files(
        self,
        case_id: uuid.UUID,
        path: str = ""
    ) -> List[CaseFile]:
        """List files in case directory."""
        try:
            query = select(CaseFile).where(
                CaseFile.case_id == case_id,
                CaseFile.upload_status == 'completed'
            )
            
            if path:
                # Filter by path prefix
                query = query.where(CaseFile.logical_path.startswith(path))
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            raise FileListError(f"Failed to list case files: {e}")
    
    async def delete_file(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> bool:
        """Delete file from case."""
        try:
            # Get file record with access check
            file_record = await self._get_file_with_access_check(file_id, user_id)
            if not file_record:
                return False
            
            # Delete from storage
            await self.storage.delete_object(file_record.storage_key)
            
            # Delete from database
            await self.db.delete(file_record)
            
            # Update case statistics
            await self._update_case_statistics(file_record.case_id)
            
            await self.db.commit()
            
            # Log deletion for audit
            await self._log_file_access(file_id, user_id, 'delete')
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            raise FileDeletionError(f"Failed to delete file: {e}")
    
    def _generate_storage_key(self, case_id: uuid.UUID, logical_path: str) -> str:
        """Generate storage key for file."""
        # Format: users/{user_id}/cases/{case_id}/{logical_path}
        # Note: user_id will be determined from case ownership
        return f"cases/{case_id}/{logical_path}"
    
    async def _get_file_with_access_check(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Optional[CaseFile]:
        """Get file record with access permission check."""
        query = select(CaseFile).join(Case).where(
            CaseFile.id == file_id,
            Case.owner_id == user_id  # Simple ownership check
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def _update_case_statistics(self, case_id: uuid.UUID):
        """Update case file count and total size."""
        # Calculate totals
        query = select(
            func.count(CaseFile.id),
            func.sum(CaseFile.file_size)
        ).where(
            CaseFile.case_id == case_id,
            CaseFile.upload_status == 'completed'
        )
        
        result = await self.db.execute(query)
        file_count, total_size = result.one()
        
        # Update case record
        case_query = update(Case).where(Case.id == case_id).values(
            file_count=file_count or 0,
            total_size_bytes=total_size or 0,
            updated_at=datetime.utcnow()
        )
        
        await self.db.execute(case_query)
    
    async def _log_file_access(
        self,
        file_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str
    ):
        """Log file access for audit trail."""
        audit_log = AuditLog(
            user_id=user_id,
            file_id=file_id,
            action=action,
            resource_type='file',
            resource_id=file_id
        )
        
        self.db.add(audit_log)
        await self.db.commit()
```

## Custom Exceptions

```python
class StorageError(Exception):
    """Base storage error."""
    pass

class ObjectNotFoundError(StorageError):
    """Object not found in storage."""
    pass

class FileUploadError(StorageError):
    """File upload error."""
    pass

class FileDownloadError(StorageError):
    """File download error."""
    pass

class FileListError(StorageError):
    """File listing error."""
    pass

class FileDeletionError(StorageError):
    """File deletion error."""
    pass
```

This storage abstraction layer provides a clean interface for file operations with support for multiple cloud storage providers, proper error handling, and integration with the legal case management system.
