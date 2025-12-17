"""
User & Entity Behavior Analytics (UEBA)
Security monitoring and threat detection system
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import defaultdict

# User database
USERS_DB = [
    {
        "user_id": "U001",
        "email": "alice.manager@autoguard.com",
        "name": "Alice Manager",
        "role": "fleet_manager",
        "password": "password",  # In production, use hashed passwords!
        "department": "Operations"
    },
    {
        "user_id": "U002",
        "email": "bob.mechanic@autoguard.com",
        "name": "Bob Mechanic",
        "role": "mechanic",
        "password": "password",
        "department": "Maintenance"
    },
    {
        "user_id": "U003",
        "email": "charlie.admin@autoguard.com",
        "name": "Charlie Admin",
        "role": "admin",
        "password": "password",
        "department": "IT"
    },
    {
        "user_id": "U004",
        "email": "eve.hacker@external.com",
        "name": "Eve Hacker",
        "role": "external",
        "password": "password",
        "department": "External"
    }
]

@dataclass
class SecurityThreat:
    """Represents a security threat"""
    threat_id: int
    user_id: str
    threat_type: str
    severity: str
    details: str
    timestamp: str
    resolved: bool = False
    
    def to_dict(self):
        return {
            'threat_id': self.threat_id,
            'user_id': self.user_id,
            'threat_type': self.threat_type,
            'severity': self.severity,
            'details': self.details,
            'timestamp': self.timestamp,
            'resolved': self.resolved
        }

class UEBA:
    """User & Entity Behavior Analytics"""
    
    # Threat detection thresholds
    RAPID_ACCESS_THRESHOLD = 5  # Actions within short time
    SUSPICIOUS_PATTERN_THRESHOLD = 3  # Unusual activities
    
    # Suspicious patterns
    SUSPICIOUS_ROLES = ['external', 'contractor']
    HIGH_RISK_ACTIONS = ['delete', 'export', 'modify_critical']
    
    def __init__(self):
        self.activity_log: List[Dict] = []
        self.threats: List[SecurityThreat] = []
        self.blocked_users: set = set()
        self.threat_id_counter = 1
    
    def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Authenticate user and return success status, user info, and error message
        
        Returns: (success: bool, user_info: Dict, error_message: str)
        """
        # Find user by email
        user = next((u for u in USERS_DB if u['email'] == email), None)
        
        if not user:
            return False, None, "Invalid email or password"
        
        # Check password (in production, use proper password hashing)
        if user['password'] != password:
            return False, None, "Invalid email or password"
        
        # Check if user is blocked
        if user['user_id'] in self.blocked_users:
            # Log blocked access attempt
            self.log_activity(
                user['user_id'],
                "blocked_login_attempt",
                {"email": email, "timestamp": datetime.now().isoformat()}
            )
            return False, None, "Access denied: Account has been blocked"
        
        # Successful authentication
        return True, user, None
    
    def log_activity(self, user_id: str, action: str, metadata: Dict) -> Optional[SecurityThreat]:
        """
        Log user activity and check for threats
        
        Returns threat object if detected, None otherwise
        """
        activity = {
            'user_id': user_id,
            'action': action,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }
        
        self.activity_log.append(activity)
        
        # Analyze for threats
        threat = self._analyze_activity(user_id, action, metadata)
        
        if threat:
            self.threats.append(threat)
        
        return threat
    
    def _analyze_activity(self, user_id: str, action: str, metadata: Dict) -> Optional[SecurityThreat]:
        """Analyze activity for security threats"""
        
        # Get user info
        user = next((u for u in USERS_DB if u['user_id'] == user_id), None)
        if not user:
            return None
        
        # Check 1: Suspicious role
        if user['role'] in self.SUSPICIOUS_ROLES:
            # External users accessing critical systems
            if action in ['run_diagnostics', 'modify_vehicle', 'export_data']:
                return SecurityThreat(
                    threat_id=self._get_next_threat_id(),
                    user_id=user_id,
                    threat_type='Unauthorized Access',
                    severity='High',
                    details=f"External user {user_id} attempting {action}",
                    timestamp=datetime.now().isoformat()
                )
        
        # Check 2: Rapid successive actions (potential bot/script)
        recent_actions = self._get_recent_actions(user_id, seconds=60)
        if len(recent_actions) >= self.RAPID_ACCESS_THRESHOLD:
            return SecurityThreat(
                threat_id=self._get_next_threat_id(),
                user_id=user_id,
                threat_type='Rapid Access Pattern',
                severity='Medium',
                details=f"User {user_id} performed {len(recent_actions)} actions in 60 seconds",
                timestamp=datetime.now().isoformat()
            )
        
        # Check 3: After-hours access
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:
            if action in ['run_diagnostics', 'export_data', 'modify_vehicle']:
                return SecurityThreat(
                    threat_id=self._get_next_threat_id(),
                    user_id=user_id,
                    threat_type='After-Hours Access',
                    severity='Low',
                    details=f"User {user_id} accessing system at unusual hour: {current_hour}:00",
                    timestamp=datetime.now().isoformat()
                )
        
        # Check 4: Multiple failed login attempts
        if action == 'failed_login':
            failed_logins = [a for a in self._get_recent_actions(user_id, seconds=300) 
                           if a['action'] == 'failed_login']
            if len(failed_logins) >= 3:
                return SecurityThreat(
                    threat_id=self._get_next_threat_id(),
                    user_id=user_id,
                    threat_type='Brute Force Attempt',
                    severity='Critical',
                    details=f"Multiple failed login attempts detected for {user_id}",
                    timestamp=datetime.now().isoformat()
                )
        
        return None
    
    def _get_recent_actions(self, user_id: str, seconds: int = 60) -> List[Dict]:
        """Get recent actions for a user within specified time window"""
        # Simplified - just return last N actions
        # In production, would use proper time-based filtering
        user_actions = [a for a in self.activity_log if a['user_id'] == user_id]
        return user_actions[-10:]  # Return last 10 actions as proxy
    
    def _get_next_threat_id(self) -> int:
        """Get next threat ID"""
        threat_id = self.threat_id_counter
        self.threat_id_counter += 1
        return threat_id
    
    def block_user(self, user_id: str):
        """Block a user from accessing the system"""
        self.blocked_users.add(user_id)
        
        # Log the blocking action
        self.log_activity(
            'SYSTEM',
            'user_blocked',
            {'blocked_user': user_id, 'timestamp': datetime.now().isoformat()}
        )
    
    def unblock_user(self, user_id: str):
        """Unblock a user"""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users
    
    def resolve_threat(self, threat_id: int):
        """Mark a threat as resolved"""
        for threat in self.threats:
            if threat.threat_id == threat_id:
                threat.resolved = True
                break
    
    def get_active_threats(self) -> List[SecurityThreat]:
        """Get all unresolved threats"""
        return [t for t in self.threats if not t.resolved]
    
    def get_threats_by_user(self, user_id: str) -> List[SecurityThreat]:
        """Get threats for a specific user"""
        return [t for t in self.threats if t.user_id == user_id]
    
    def get_threat_summary(self) -> Dict:
        """Get summary statistics of threats"""
        active_threats = self.get_active_threats()
        
        summary = {
            'total_threats': len(self.threats),
            'total_active_threats': len(active_threats),
            'blocked_users': len(self.blocked_users),
            'by_severity': defaultdict(int),
            'by_type': defaultdict(int)
        }
        
        for threat in active_threats:
            summary['by_severity'][threat.severity] += 1
            summary['by_type'][threat.threat_type] += 1
        
        return summary
    
    def get_user_activity_summary(self, user_id: str) -> Dict:
        """Get activity summary for a user"""
        user = next((u for u in USERS_DB if u['user_id'] == user_id), None)
        
        user_activities = [a for a in self.activity_log if a['user_id'] == user_id]
        
        summary = {
            'user_id': user_id,
            'name': user['name'] if user else 'Unknown',
            'role': user['role'] if user else 'Unknown',
            'total_actions': len(user_activities),
            'is_blocked': self.is_user_blocked(user_id),
            'active_threats': len([t for t in self.get_threats_by_user(user_id) if not t.resolved]),
            'recent_actions': user_activities[-10:]  # Last 10 actions
        }
        
        return summary
    
    def get_all_users(self) -> List[Dict]:
        """Get all users (for admin purposes)"""
        return USERS_DB.copy()

# Singleton instance
_ueba_instance = None

def get_ueba():
    """Get or create UEBA instance"""
    global _ueba_instance
    if _ueba_instance is None:
        _ueba_instance = UEBA()
    return _ueba_instance
