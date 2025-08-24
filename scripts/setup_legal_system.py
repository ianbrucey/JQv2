#!/usr/bin/env python3
"""
Setup script for OpenHands Legal Document Management System
"""
import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the OpenHands directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from openhands.storage.legal_database_setup import setup_legal_database
from openhands.storage.legal_case_store import FileLegalCaseStore
from openhands.core.config import load_openhands_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def setup_directories():
    """Create necessary directories for legal document management."""
    logger.info("Setting up directories...")
    
    # Create legal workspace directories
    legal_workspace = Path(os.environ.get('LEGAL_WORKSPACE_ROOT', '/app/legal_workspace'))
    directories = [
        legal_workspace,
        legal_workspace / 'cases',
        legal_workspace / 'system' / 'backups',
        legal_workspace / 'system' / 'versions',
        legal_workspace / 'system' / 'audit_logs',
        legal_workspace / 'files'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Verify draft_system exists
    draft_system = Path(os.environ.get('DRAFT_SYSTEM_PATH', '/app/draft_system'))
    if not draft_system.exists():
        logger.warning(f"Draft system not found at {draft_system}")
        logger.info("Please ensure the draft_system folder is properly mounted or copied")
    else:
        logger.info(f"Draft system found at: {draft_system}")
    
    return True


async def test_case_creation():
    """Test creating a legal case."""
    logger.info("Testing case creation...")
    
    try:
        config = load_openhands_config()
        case_store = await FileLegalCaseStore.get_instance(config, user_id="test_user")
        
        # Create a test case
        test_case = await case_store.create_case(
            title="Test Legal Case",
            case_number="TEST-001",
            description="This is a test case for the legal document management system"
        )
        
        logger.info(f"✅ Successfully created test case: {test_case.case_id}")
        logger.info(f"   Title: {test_case.title}")
        logger.info(f"   Workspace: {test_case.workspace_path}")
        
        # Verify the case can be retrieved
        retrieved_case = await case_store.get_case(test_case.case_id)
        if retrieved_case:
            logger.info("✅ Successfully retrieved test case")
        else:
            logger.error("❌ Failed to retrieve test case")
            return False
        
        # List cases
        cases = await case_store.list_cases()
        logger.info(f"✅ Found {len(cases)} cases in system")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Case creation test failed: {e}")
        return False


async def verify_draft_system_integration():
    """Verify draft_system integration works correctly."""
    logger.info("Verifying draft_system integration...")
    
    try:
        config = load_openhands_config()
        case_store = await FileLegalCaseStore.get_instance(config, user_id="test_user")
        
        # Get the test case
        cases = await case_store.list_cases()
        if not cases:
            logger.error("❌ No test cases found")
            return False
        
        test_case = cases[0]
        workspace_path = Path(test_case.workspace_path)
        
        # Check if draft_system files exist
        required_files = [
            'README.md',
            'standards',
            'templates',
            'scripts',
            'active_drafts'
        ]
        
        for file_name in required_files:
            file_path = workspace_path / file_name
            if file_path.exists():
                logger.info(f"✅ Found: {file_name}")
            else:
                logger.error(f"❌ Missing: {file_name}")
                return False
        
        # Check if Case_Summary_and_Timeline.md was initialized
        case_summary = workspace_path / "Case_Summary_and_Timeline.md"
        if case_summary.exists():
            with open(case_summary, 'r') as f:
                content = f.read()
                if test_case.title in content:
                    logger.info("✅ Case summary properly initialized with case details")
                else:
                    logger.warning("⚠️  Case summary exists but may not be properly initialized")
        
        logger.info("✅ Draft system integration verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Draft system verification failed: {e}")
        return False


async def cleanup_test_data():
    """Clean up test data."""
    logger.info("Cleaning up test data...")
    
    try:
        config = load_openhands_config()
        case_store = await FileLegalCaseStore.get_instance(config, user_id="test_user")
        
        # Delete test cases
        cases = await case_store.list_cases()
        for case in cases:
            if case.title.startswith("Test"):
                await case_store.delete_case(case.case_id)
                logger.info(f"Deleted test case: {case.case_id}")
        
        logger.info("✅ Test data cleanup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return False


async def main():
    """Main setup function."""
    logger.info("🚀 Starting OpenHands Legal Document Management System Setup")
    
    # Check environment variables
    required_env_vars = [
        'LEGAL_WORKSPACE_ROOT',
        'DRAFT_SYSTEM_PATH',
        'POSTGRES_HOST',
        'POSTGRES_PORT',
        'POSTGRES_DB'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.info("Please set these variables or load the .env.legal file")
        return False
    
    try:
        # Step 1: Setup directories
        if not await setup_directories():
            logger.error("❌ Directory setup failed")
            return False
        
        # Step 2: Setup database
        logger.info("Setting up database...")
        if not await setup_legal_database():
            logger.error("❌ Database setup failed")
            return False
        
        # Step 3: Test case creation
        if not await test_case_creation():
            logger.error("❌ Case creation test failed")
            return False
        
        # Step 4: Verify draft_system integration
        if not await verify_draft_system_integration():
            logger.error("❌ Draft system verification failed")
            return False
        
        # Step 5: Cleanup test data
        if not await cleanup_test_data():
            logger.warning("⚠️  Test data cleanup had issues")
        
        logger.info("🎉 OpenHands Legal Document Management System setup completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start the OpenHands server")
        logger.info("2. Access the legal case management API at /api/legal/cases")
        logger.info("3. Create your first legal case")
        logger.info("4. Enter the case workspace to start working with documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed with error: {e}")
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    
    # Try to load .env.legal file
    env_file = Path(__file__).parent.parent / ".env.legal"
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment from: {env_file}")
    else:
        logger.warning("No .env.legal file found, using system environment variables")
    
    # Run setup
    success = asyncio.run(main())
    
    if not success:
        sys.exit(1)
