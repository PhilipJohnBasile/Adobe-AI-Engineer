"""
Enterprise-Grade Collaboration Platform

Provides real-time collaboration, approval workflows, version control, and 
stakeholder communication for creative campaigns.

Free technologies used:
- SQLite for database
- JSON for data exchange
- hashlib for version tracking
- smtplib for email notifications (simulated)
- pathlib for file management
"""

import logging
import json
import sqlite3
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import shutil
import uuid

logger = logging.getLogger(__name__)


class UserRole(Enum):
    ADMIN = "admin"
    CREATIVE_LEAD = "creative_lead"
    DESIGNER = "designer"
    COPYWRITER = "copywriter"
    ACCOUNT_MANAGER = "account_manager"
    CLIENT = "client"
    REVIEWER = "reviewer"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    IN_REVIEW = "in_review"


class CommentType(Enum):
    GENERAL = "general"
    REVISION_REQUEST = "revision_request"
    APPROVAL = "approval"
    QUESTION = "question"
    SUGGESTION = "suggestion"


class CollaborationDatabase:
    """Manages SQLite database for collaboration platform."""
    
    def __init__(self, db_path: str = "collaboration.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP,
                preferences TEXT
            )
        ''')
        
        # Projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                settings TEXT,
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        ''')
        
        # Assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                asset_id TEXT PRIMARY KEY,
                project_id TEXT,
                name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                asset_type TEXT,
                version INTEGER DEFAULT 1,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                checksum TEXT,
                metadata TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (project_id),
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        ''')
        
        # Asset versions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_versions (
                version_id TEXT PRIMARY KEY,
                asset_id TEXT,
                version_number INTEGER,
                file_path TEXT NOT NULL,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_description TEXT,
                checksum TEXT,
                FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
                FOREIGN KEY (created_by) REFERENCES users (user_id)
            )
        ''')
        
        # Comments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                comment_id TEXT PRIMARY KEY,
                asset_id TEXT,
                user_id TEXT,
                comment_type TEXT,
                content TEXT NOT NULL,
                position_x REAL,
                position_y REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parent_comment_id TEXT,
                resolved BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (parent_comment_id) REFERENCES comments (comment_id)
            )
        ''')
        
        # Approvals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approvals (
                approval_id TEXT PRIMARY KEY,
                asset_id TEXT,
                reviewer_id TEXT,
                status TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
                FOREIGN KEY (reviewer_id) REFERENCES users (user_id)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notification_id TEXT PRIMARY KEY,
                user_id TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT,
                related_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Project members table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_members (
                project_id TEXT,
                user_id TEXT,
                role TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                permissions TEXT,
                PRIMARY KEY (project_id, user_id),
                FOREIGN KEY (project_id) REFERENCES projects (project_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Collaboration database initialized")


class UserManager:
    """Manages users and authentication."""
    
    def __init__(self, db: CollaborationDatabase):
        self.db = db
    
    def create_user(self, username: str, email: str, role: UserRole, 
                   full_name: str = None) -> str:
        """Create a new user."""
        user_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, email, role, full_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, email, role.value, full_name or username))
            
            conn.commit()
            logger.info(f"Created user: {username} ({role.value})")
            return user_id
            
        except sqlite3.IntegrityError as e:
            logger.error(f"Error creating user: {e}")
            raise ValueError(f"Username or email already exists")
        finally:
            conn.close()
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0], 'username': row[1], 'email': row[2],
                'role': row[3], 'full_name': row[4], 'avatar_url': row[5],
                'created_at': row[6], 'last_active': row[7], 'preferences': row[8]
            }
        return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row[0], 'username': row[1], 'email': row[2],
                'role': row[3], 'full_name': row[4], 'avatar_url': row[5],
                'created_at': row[6], 'last_active': row[7], 'preferences': row[8]
            }
        return None
    
    def update_user_activity(self, user_id: str):
        """Update user's last active timestamp."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()


class ProjectManager:
    """Manages projects and project membership."""
    
    def __init__(self, db: CollaborationDatabase):
        self.db = db
    
    def create_project(self, name: str, description: str, created_by: str,
                      settings: Dict = None) -> str:
        """Create a new project."""
        project_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projects (project_id, name, description, created_by, settings)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, name, description, created_by, 
              json.dumps(settings or {})))
        
        # Add creator as admin member
        cursor.execute('''
            INSERT INTO project_members (project_id, user_id, role, permissions)
            VALUES (?, ?, ?, ?)
        ''', (project_id, created_by, 'admin', json.dumps(['all'])))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created project: {name}")
        return project_id
    
    def add_project_member(self, project_id: str, user_id: str, role: str,
                          permissions: List[str] = None) -> bool:
        """Add user to project."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO project_members (project_id, user_id, role, permissions)
                VALUES (?, ?, ?, ?)
            ''', (project_id, user_id, role, json.dumps(permissions or ['view'])))
            
            conn.commit()
            logger.info(f"Added user {user_id} to project {project_id} as {role}")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"User {user_id} already member of project {project_id}")
            return False
        finally:
            conn.close()
    
    def get_project_members(self, project_id: str) -> List[Dict]:
        """Get all project members."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pm.*, u.username, u.full_name, u.email, u.role as user_role
            FROM project_members pm
            JOIN users u ON pm.user_id = u.user_id
            WHERE pm.project_id = ?
        ''', (project_id,))
        
        members = []
        for row in cursor.fetchall():
            members.append({
                'project_id': row[0], 'user_id': row[1], 'role': row[2],
                'added_at': row[3], 'permissions': json.loads(row[4] or '[]'),
                'username': row[5], 'full_name': row[6], 'email': row[7],
                'user_role': row[8]
            })
        
        conn.close()
        return members


class AssetVersionControl:
    """Manages asset versioning and file tracking."""
    
    def __init__(self, db: CollaborationDatabase, storage_path: str = "collaboration_assets"):
        self.db = db
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def upload_asset(self, project_id: str, name: str, file_path: str,
                    uploaded_by: str, asset_type: str = None) -> str:
        """Upload new asset to project."""
        asset_id = str(uuid.uuid4())
        
        # Copy file to storage
        source_path = Path(file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        
        # Create project storage directory
        project_storage = self.storage_path / project_id
        project_storage.mkdir(exist_ok=True)
        
        # Generate unique filename
        file_extension = source_path.suffix
        stored_filename = f"{asset_id}_v1{file_extension}"
        stored_path = project_storage / stored_filename
        
        # Copy file
        shutil.copy2(source_path, stored_path)
        
        # Calculate checksum
        checksum = self._calculate_checksum(stored_path)
        file_size = stored_path.stat().st_size
        
        # Store in database
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO assets (asset_id, project_id, name, file_path, asset_type,
                              version, created_by, file_size, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (asset_id, project_id, name, str(stored_path), asset_type,
              1, uploaded_by, file_size, checksum))
        
        # Create version record
        version_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO asset_versions (version_id, asset_id, version_number,
                                      file_path, created_by, change_description, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (version_id, asset_id, 1, str(stored_path), uploaded_by,
              "Initial upload", checksum))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Uploaded asset: {name} (ID: {asset_id})")
        return asset_id
    
    def create_new_version(self, asset_id: str, new_file_path: str,
                          created_by: str, change_description: str) -> int:
        """Create new version of existing asset."""
        # Get current asset info
        asset_info = self.get_asset(asset_id)
        if not asset_info:
            raise ValueError(f"Asset not found: {asset_id}")
        
        # Get latest version number
        latest_version = self.get_latest_version_number(asset_id)
        new_version = latest_version + 1
        
        # Copy new file to storage
        source_path = Path(new_file_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {new_file_path}")
        
        project_storage = self.storage_path / asset_info['project_id']
        file_extension = source_path.suffix
        stored_filename = f"{asset_id}_v{new_version}{file_extension}"
        stored_path = project_storage / stored_filename
        
        shutil.copy2(source_path, stored_path)
        checksum = self._calculate_checksum(stored_path)
        
        # Update database
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Update asset version
        cursor.execute('''
            UPDATE assets SET version = ?, file_path = ?, checksum = ?
            WHERE asset_id = ?
        ''', (new_version, str(stored_path), checksum, asset_id))
        
        # Create version record
        version_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO asset_versions (version_id, asset_id, version_number,
                                      file_path, created_by, change_description, checksum)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (version_id, asset_id, new_version, str(stored_path),
              created_by, change_description, checksum))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created version {new_version} of asset {asset_id}")
        return new_version
    
    def get_asset(self, asset_id: str) -> Optional[Dict]:
        """Get asset information."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM assets WHERE asset_id = ?', (asset_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'asset_id': row[0], 'project_id': row[1], 'name': row[2],
                'file_path': row[3], 'asset_type': row[4], 'version': row[5],
                'created_by': row[6], 'created_at': row[7], 'file_size': row[8],
                'checksum': row[9], 'metadata': row[10]
            }
        return None
    
    def get_asset_versions(self, asset_id: str) -> List[Dict]:
        """Get all versions of an asset."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT av.*, u.username
            FROM asset_versions av
            LEFT JOIN users u ON av.created_by = u.user_id
            WHERE av.asset_id = ?
            ORDER BY av.version_number DESC
        ''', (asset_id,))
        
        versions = []
        for row in cursor.fetchall():
            versions.append({
                'version_id': row[0], 'asset_id': row[1], 'version_number': row[2],
                'file_path': row[3], 'created_by': row[4], 'created_at': row[5],
                'change_description': row[6], 'checksum': row[7], 'username': row[8]
            })
        
        conn.close()
        return versions
    
    def get_latest_version_number(self, asset_id: str) -> int:
        """Get latest version number for asset."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(version_number) FROM asset_versions WHERE asset_id = ?
        ''', (asset_id,))
        
        result = cursor.fetchone()[0]
        conn.close()
        
        return result or 0
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


class CommentSystem:
    """Manages comments and feedback on assets."""
    
    def __init__(self, db: CollaborationDatabase):
        self.db = db
    
    def add_comment(self, asset_id: str, user_id: str, content: str,
                   comment_type: CommentType = CommentType.GENERAL,
                   position_x: float = None, position_y: float = None,
                   parent_comment_id: str = None) -> str:
        """Add comment to asset."""
        comment_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO comments (comment_id, asset_id, user_id, comment_type,
                                content, position_x, position_y, parent_comment_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (comment_id, asset_id, user_id, comment_type.value,
              content, position_x, position_y, parent_comment_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Added comment on asset {asset_id} by user {user_id}")
        return comment_id
    
    def get_asset_comments(self, asset_id: str, include_resolved: bool = True) -> List[Dict]:
        """Get all comments for an asset."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT c.*, u.username, u.full_name
            FROM comments c
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE c.asset_id = ?
        '''
        
        if not include_resolved:
            query += ' AND c.resolved = FALSE'
        
        query += ' ORDER BY c.created_at ASC'
        
        cursor.execute(query, (asset_id,))
        
        comments = []
        for row in cursor.fetchall():
            comments.append({
                'comment_id': row[0], 'asset_id': row[1], 'user_id': row[2],
                'comment_type': row[3], 'content': row[4], 'position_x': row[5],
                'position_y': row[6], 'created_at': row[7], 'parent_comment_id': row[8],
                'resolved': bool(row[9]), 'username': row[10], 'full_name': row[11]
            })
        
        conn.close()
        return comments
    
    def resolve_comment(self, comment_id: str) -> bool:
        """Mark comment as resolved."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE comments SET resolved = TRUE WHERE comment_id = ?
        ''', (comment_id,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Resolved comment {comment_id}")
        
        return updated


class ApprovalWorkflow:
    """Manages approval workflows for assets."""
    
    def __init__(self, db: CollaborationDatabase):
        self.db = db
    
    def request_approval(self, asset_id: str, reviewer_id: str,
                        due_date: datetime = None) -> str:
        """Request approval for an asset."""
        approval_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO approvals (approval_id, asset_id, reviewer_id, status, due_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (approval_id, asset_id, reviewer_id, ApprovalStatus.PENDING.value,
              due_date.isoformat() if due_date else None))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Requested approval for asset {asset_id} from user {reviewer_id}")
        return approval_id
    
    def submit_approval(self, approval_id: str, status: ApprovalStatus,
                       feedback: str = None) -> bool:
        """Submit approval decision."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE approvals 
            SET status = ?, feedback = ?, updated_at = CURRENT_TIMESTAMP
            WHERE approval_id = ?
        ''', (status.value, feedback, approval_id))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if updated:
            logger.info(f"Submitted approval {approval_id}: {status.value}")
        
        return updated
    
    def get_asset_approvals(self, asset_id: str) -> List[Dict]:
        """Get all approvals for an asset."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.username, u.full_name
            FROM approvals a
            LEFT JOIN users u ON a.reviewer_id = u.user_id
            WHERE a.asset_id = ?
            ORDER BY a.created_at DESC
        ''', (asset_id,))
        
        approvals = []
        for row in cursor.fetchall():
            approvals.append({
                'approval_id': row[0], 'asset_id': row[1], 'reviewer_id': row[2],
                'status': row[3], 'feedback': row[4], 'created_at': row[5],
                'updated_at': row[6], 'due_date': row[7], 'username': row[8],
                'full_name': row[9]
            })
        
        conn.close()
        return approvals
    
    def get_pending_approvals(self, reviewer_id: str) -> List[Dict]:
        """Get pending approvals for a reviewer."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, ast.name as asset_name, p.name as project_name
            FROM approvals a
            LEFT JOIN assets ast ON a.asset_id = ast.asset_id
            LEFT JOIN projects p ON ast.project_id = p.project_id
            WHERE a.reviewer_id = ? AND a.status = ?
            ORDER BY a.due_date ASC NULLS LAST, a.created_at ASC
        ''', (reviewer_id, ApprovalStatus.PENDING.value))
        
        approvals = []
        for row in cursor.fetchall():
            approvals.append({
                'approval_id': row[0], 'asset_id': row[1], 'reviewer_id': row[2],
                'status': row[3], 'feedback': row[4], 'created_at': row[5],
                'updated_at': row[6], 'due_date': row[7], 'asset_name': row[8],
                'project_name': row[9]
            })
        
        conn.close()
        return approvals


class NotificationSystem:
    """Manages notifications and communications."""
    
    def __init__(self, db: CollaborationDatabase):
        self.db = db
    
    def send_notification(self, user_id: str, title: str, message: str,
                         notification_type: str = 'info', related_id: str = None) -> str:
        """Send notification to user."""
        notification_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notifications (notification_id, user_id, title, message,
                                     notification_type, related_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (notification_id, user_id, title, message, notification_type, related_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Sent notification to user {user_id}: {title}")
        return notification_id
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for user."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM notifications WHERE user_id = ?
        '''
        
        if unread_only:
            query += ' AND read_at IS NULL'
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, (user_id,))
        
        notifications = []
        for row in cursor.fetchall():
            notifications.append({
                'notification_id': row[0], 'user_id': row[1], 'title': row[2],
                'message': row[3], 'notification_type': row[4], 'related_id': row[5],
                'created_at': row[6], 'read_at': row[7]
            })
        
        conn.close()
        return notifications
    
    def mark_notification_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications SET read_at = CURRENT_TIMESTAMP
            WHERE notification_id = ?
        ''', (notification_id,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated


class CollaborationPlatform:
    """Main collaboration platform orchestrator."""
    
    def __init__(self, db_path: str = "collaboration.db"):
        self.db = CollaborationDatabase(db_path)
        self.user_manager = UserManager(self.db)
        self.project_manager = ProjectManager(self.db)
        self.asset_version_control = AssetVersionControl(self.db)
        self.comment_system = CommentSystem(self.db)
        self.approval_workflow = ApprovalWorkflow(self.db)
        self.notification_system = NotificationSystem(self.db)
        
        # Create default admin user if database is empty
        self._setup_default_users()
        
        logger.info("Collaboration platform initialized")
    
    def _setup_default_users(self):
        """Set up default users for demonstration."""
        try:
            # Create admin user
            admin_id = self.user_manager.create_user(
                username="admin",
                email="admin@company.com",
                role=UserRole.ADMIN,
                full_name="Platform Administrator"
            )
            
            # Create sample users
            self.user_manager.create_user(
                username="creative_lead",
                email="creative@company.com",
                role=UserRole.CREATIVE_LEAD,
                full_name="Creative Director"
            )
            
            self.user_manager.create_user(
                username="designer",
                email="designer@company.com",
                role=UserRole.DESIGNER,
                full_name="Senior Designer"
            )
            
            self.user_manager.create_user(
                username="client",
                email="client@company.com",
                role=UserRole.CLIENT,
                full_name="Client Stakeholder"
            )
            
            logger.info("Default users created successfully")
        except ValueError:
            # Users already exist
            logger.info("Default users already exist")
    
    def create_campaign_project(self, campaign_name: str, created_by_username: str,
                               team_members: List[str] = None) -> Dict:
        """Create a new campaign project with team."""
        # Get creator user
        creator = self.user_manager.get_user_by_username(created_by_username)
        if not creator:
            raise ValueError(f"User not found: {created_by_username}")
        
        # Create project
        project_id = self.project_manager.create_project(
            name=campaign_name,
            description=f"Creative campaign project: {campaign_name}",
            created_by=creator['user_id']
        )
        
        # Add team members
        if team_members:
            for username in team_members:
                user = self.user_manager.get_user_by_username(username)
                if user:
                    role = 'reviewer' if user['role'] == 'client' else 'contributor'
                    permissions = ['view', 'comment'] if role == 'reviewer' else ['view', 'comment', 'upload']
                    
                    self.project_manager.add_project_member(
                        project_id, user['user_id'], role, permissions
                    )
                    
                    # Send notification
                    self.notification_system.send_notification(
                        user['user_id'],
                        f"Added to Project: {campaign_name}",
                        f"You've been added to the {campaign_name} project as a {role}.",
                        'project_invitation',
                        project_id
                    )
        
        return {
            'project_id': project_id,
            'name': campaign_name,
            'created_by': creator['username'],
            'team_size': len(team_members or []) + 1,
            'collaboration_url': f"/projects/{project_id}"
        }
    
    def upload_campaign_asset(self, project_id: str, asset_name: str,
                             file_path: str, uploaded_by_username: str,
                             request_approval_from: List[str] = None) -> Dict:
        """Upload asset and optionally request approvals."""
        # Get uploader user
        uploader = self.user_manager.get_user_by_username(uploaded_by_username)
        if not uploader:
            raise ValueError(f"User not found: {uploaded_by_username}")
        
        # Upload asset
        asset_id = self.asset_version_control.upload_asset(
            project_id, asset_name, file_path, uploader['user_id'], 'creative'
        )
        
        # Request approvals if specified
        approval_requests = []
        if request_approval_from:
            for username in request_approval_from:
                reviewer = self.user_manager.get_user_by_username(username)
                if reviewer:
                    approval_id = self.approval_workflow.request_approval(
                        asset_id, reviewer['user_id'],
                        datetime.now() + timedelta(days=3)  # 3 day deadline
                    )
                    approval_requests.append(approval_id)
                    
                    # Send notification
                    self.notification_system.send_notification(
                        reviewer['user_id'],
                        f"Approval Request: {asset_name}",
                        f"Please review and approve the asset '{asset_name}' uploaded by {uploader['full_name']}.",
                        'approval_request',
                        asset_id
                    )
        
        return {
            'asset_id': asset_id,
            'asset_name': asset_name,
            'uploaded_by': uploader['username'],
            'approval_requests': len(approval_requests),
            'collaboration_url': f"/assets/{asset_id}"
        }
    
    def get_project_dashboard(self, project_id: str) -> Dict:
        """Get comprehensive project dashboard data."""
        # Get project members
        members = self.project_manager.get_project_members(project_id)
        
        # Get project assets
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, u.username
            FROM assets a
            LEFT JOIN users u ON a.created_by = u.user_id
            WHERE a.project_id = ?
            ORDER BY a.created_at DESC
        ''', (project_id,))
        
        assets = []
        for row in cursor.fetchall():
            asset_id = row[0]
            
            # Get approval status
            approvals = self.approval_workflow.get_asset_approvals(asset_id)
            approval_summary = self._get_approval_summary(approvals)
            
            # Get comment count
            comments = self.comment_system.get_asset_comments(asset_id, include_resolved=False)
            
            assets.append({
                'asset_id': asset_id, 'name': row[2], 'version': row[5],
                'created_by': row[11], 'created_at': row[7],
                'approval_status': approval_summary['status'],
                'pending_approvals': approval_summary['pending'],
                'unresolved_comments': len(comments)
            })
        
        conn.close()
        
        # Get activity summary
        activity_summary = self._get_project_activity(project_id)
        
        return {
            'project_id': project_id,
            'members': len(members),
            'assets': len(assets),
            'pending_approvals': sum(a['pending_approvals'] for a in assets),
            'unresolved_comments': sum(a['unresolved_comments'] for a in assets),
            'recent_assets': assets[:5],
            'activity_summary': activity_summary,
            'team_members': [{'username': m['username'], 'role': m['role']} for m in members]
        }
    
    def _get_approval_summary(self, approvals: List[Dict]) -> Dict:
        """Summarize approval status."""
        if not approvals:
            return {'status': 'no_approvals', 'pending': 0}
        
        pending = sum(1 for a in approvals if a['status'] == 'pending')
        approved = sum(1 for a in approvals if a['status'] == 'approved')
        rejected = sum(1 for a in approvals if a['status'] == 'rejected')
        
        if rejected > 0:
            status = 'rejected'
        elif pending > 0:
            status = 'pending'
        elif approved > 0:
            status = 'approved'
        else:
            status = 'no_approvals'
        
        return {'status': status, 'pending': pending}
    
    def _get_project_activity(self, project_id: str) -> Dict:
        """Get project activity summary."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Recent activity
        cursor.execute('''
            SELECT 'asset_upload' as activity_type, a.name, u.username, a.created_at
            FROM assets a
            LEFT JOIN users u ON a.created_by = u.user_id
            WHERE a.project_id = ?
            
            UNION ALL
            
            SELECT 'comment' as activity_type, 
                   'Comment on ' || ast.name as name, 
                   u.username, c.created_at
            FROM comments c
            LEFT JOIN assets ast ON c.asset_id = ast.asset_id
            LEFT JOIN users u ON c.user_id = u.user_id
            WHERE ast.project_id = ?
            
            ORDER BY created_at DESC
            LIMIT 10
        ''', (project_id, project_id))
        
        activities = []
        for row in cursor.fetchall():
            activities.append({
                'type': row[0], 'description': row[1],
                'user': row[2], 'timestamp': row[3]
            })
        
        conn.close()
        
        return {
            'recent_activities': activities,
            'total_activities': len(activities)
        }
    
    def get_collaboration_metrics(self) -> Dict:
        """Get platform-wide collaboration metrics."""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Total counts
        cursor.execute('SELECT COUNT(*) FROM projects')
        total_projects = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM assets')
        total_assets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM comments WHERE resolved = FALSE')
        unresolved_comments = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM approvals WHERE status = "pending"')
        pending_approvals = cursor.fetchone()[0]
        
        # Activity metrics
        cursor.execute('''
            SELECT COUNT(*) FROM assets 
            WHERE created_at > datetime('now', '-7 days')
        ''')
        assets_this_week = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM comments 
            WHERE created_at > datetime('now', '-7 days')
        ''')
        comments_this_week = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_projects': total_projects,
            'total_users': total_users,
            'total_assets': total_assets,
            'unresolved_comments': unresolved_comments,
            'pending_approvals': pending_approvals,
            'weekly_activity': {
                'assets_uploaded': assets_this_week,
                'comments_posted': comments_this_week
            },
            'platform_health': 'good' if pending_approvals < 10 and unresolved_comments < 20 else 'needs_attention'
        }