"""
Database setup for legal case management system
"""
import asyncio
import logging
import os
from typing import Optional

import asyncpg
from asyncpg import Connection

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_CONFIG = {
    'host': os.environ.get('POSTGRES_HOST', 'localhost'),
    'port': int(os.environ.get('POSTGRES_PORT', '5433')),  # Laravel Herd uses 5433
    'database': os.environ.get('POSTGRES_DB', 'openhands_legal'),
    'user': os.environ.get('POSTGRES_USER', 'postgres'),
    'password': os.environ.get('POSTGRES_PASSWORD', '')
}

# SQL schema for legal case management
LEGAL_CASE_SCHEMA = """
-- Legal cases table
CREATE TABLE IF NOT EXISTS legal_cases (
    case_id UUID PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    case_number VARCHAR(100),
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    workspace_path TEXT,
    draft_system_initialized BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    conversation_id VARCHAR(255)
);

-- Case documents table
CREATE TABLE IF NOT EXISTS case_documents (
    document_id UUID PRIMARY KEY,
    case_id UUID REFERENCES legal_cases(case_id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    document_type VARCHAR(100) NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    size_bytes BIGINT DEFAULT 0,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}'
);

-- Document versions table
CREATE TABLE IF NOT EXISTS document_versions (
    version_id UUID PRIMARY KEY,
    document_id UUID REFERENCES case_documents(document_id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    change_summary TEXT,
    checksum VARCHAR(64)
);

-- User case access table (for future multi-user support)
CREATE TABLE IF NOT EXISTS user_case_access (
    user_id VARCHAR(255) NOT NULL,
    case_id UUID REFERENCES legal_cases(case_id) ON DELETE CASCADE,
    access_level VARCHAR(50) NOT NULL DEFAULT 'read',
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, case_id)
);

-- Audit log table
CREATE TABLE IF NOT EXISTS case_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    case_id UUID REFERENCES legal_cases(case_id) ON DELETE CASCADE,
    document_id UUID,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_legal_cases_user_id ON legal_cases(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_cases_status ON legal_cases(status);
CREATE INDEX IF NOT EXISTS idx_legal_cases_updated_at ON legal_cases(updated_at);
CREATE INDEX IF NOT EXISTS idx_case_documents_case_id ON case_documents(case_id);
CREATE INDEX IF NOT EXISTS idx_case_documents_type ON case_documents(document_type);
CREATE INDEX IF NOT EXISTS idx_document_versions_document_id ON document_versions(document_id);
CREATE INDEX IF NOT EXISTS idx_user_case_access_user_id ON user_case_access(user_id);
CREATE INDEX IF NOT EXISTS idx_case_audit_log_case_id ON case_audit_log(case_id);
CREATE INDEX IF NOT EXISTS idx_case_audit_log_timestamp ON case_audit_log(timestamp);

-- Update trigger for legal_cases updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_legal_cases_updated_at 
    BEFORE UPDATE ON legal_cases 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_documents_updated_at 
    BEFORE UPDATE ON case_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""


class LegalDatabaseManager:
    """Manages database operations for legal case system."""
    
    def __init__(self):
        self.connection: Optional[Connection] = None
    
    async def connect(self) -> Connection:
        """Connect to the PostgreSQL database."""
        try:
            self.connection = await asyncpg.connect(**DATABASE_CONFIG)
            logger.info(f"Connected to PostgreSQL database at {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
            return self.connection
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from the database."""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("Disconnected from database")
    
    async def create_database_if_not_exists(self):
        """Create the database if it doesn't exist."""
        try:
            # Connect to default postgres database first
            temp_config = DATABASE_CONFIG.copy()
            temp_config['database'] = 'postgres'

            temp_conn = await asyncpg.connect(**temp_config)

            # Check if database exists
            db_exists = await temp_conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1",
                DATABASE_CONFIG['database']
            )

            if not db_exists:
                # Create database
                await temp_conn.execute(f'CREATE DATABASE "{DATABASE_CONFIG["database"]}"')
                logger.info(f"✅ Created database: {DATABASE_CONFIG['database']}")
            else:
                logger.debug(f"Database already exists: {DATABASE_CONFIG['database']}")

            await temp_conn.close()

        except asyncpg.InvalidCatalogNameError:
            # Database doesn't exist, this is expected
            pass
        except Exception as e:
            logger.warning(f"Could not create database (this may be normal): {e}")
            # Don't raise - the database might already exist or we might not have permissions
    
    async def setup_schema(self):
        """Set up the database schema for legal case management."""
        if not self.connection:
            await self.connect()
        
        try:
            # Execute schema creation
            await self.connection.execute(LEGAL_CASE_SCHEMA)
            logger.info("Legal case database schema created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create schema: {e}")
            raise
    
    async def verify_setup(self) -> bool:
        """Verify that the database setup is correct."""
        if not self.connection:
            await self.connect()
        
        try:
            # Check if main tables exist
            tables = ['legal_cases', 'case_documents', 'document_versions', 'user_case_access', 'case_audit_log']
            
            for table in tables:
                exists = await self.connection.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                if not exists:
                    logger.error(f"Table {table} does not exist")
                    return False
            
            logger.info("Database setup verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Database verification failed: {e}")
            return False
    
    async def get_database_info(self) -> dict:
        """Get database information."""
        if not self.connection:
            await self.connect()
        
        try:
            version = await self.connection.fetchval("SELECT version()")
            
            # Count records in main tables
            case_count = await self.connection.fetchval("SELECT COUNT(*) FROM legal_cases")
            document_count = await self.connection.fetchval("SELECT COUNT(*) FROM case_documents")
            
            return {
                'database': DATABASE_CONFIG['database'],
                'host': DATABASE_CONFIG['host'],
                'port': DATABASE_CONFIG['port'],
                'version': version,
                'case_count': case_count,
                'document_count': document_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}


async def setup_legal_database():
    """Main function to set up the legal database."""
    db_manager = LegalDatabaseManager()
    
    try:
        # Create database if it doesn't exist
        await db_manager.create_database_if_not_exists()
        
        # Connect to the legal database
        await db_manager.connect()
        
        # Set up schema
        await db_manager.setup_schema()
        
        # Verify setup
        if await db_manager.verify_setup():
            logger.info("Legal database setup completed successfully")
            
            # Print database info
            info = await db_manager.get_database_info()
            logger.info(f"Database info: {info}")
            
            return True
        else:
            logger.error("Database setup verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False
        
    finally:
        await db_manager.disconnect()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run database setup
    success = asyncio.run(setup_legal_database())
    
    if success:
        print("✅ Legal database setup completed successfully!")
    else:
        print("❌ Legal database setup failed!")
        exit(1)
