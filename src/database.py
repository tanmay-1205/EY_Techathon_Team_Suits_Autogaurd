"""
Database module for AutoGuard Fleet Management
Handles data persistence using SQLite
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'data', 'autoguard.db')
        
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            role TEXT,
            message TEXT,
            metadata TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Diagnostic history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS diagnostics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            severity TEXT,
            issues TEXT,
            diagnosis_report TEXT,
            user_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Appointments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT,
            owner_email TEXT,
            appointment_date TEXT,
            service_type TEXT,
            status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_message(self, vehicle_id: str, role: str, message: str, metadata: Dict = None):
        """Save a chat message"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
        INSERT INTO conversations (vehicle_id, role, message, metadata)
        VALUES (?, ?, ?, ?)
        ''', (vehicle_id, role, message, metadata_json))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, vehicle_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history for a vehicle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT role, message, metadata, timestamp
        FROM conversations
        WHERE vehicle_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (vehicle_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'role': row[0],
                'message': row[1],
                'metadata': json.loads(row[2]) if row[2] else {},
                'timestamp': row[3]
            })
        
        return list(reversed(history))  # Return in chronological order
    
    def save_diagnostic(self, vehicle_id: str, severity: str, issues: List[str], 
                       diagnosis_report: Dict, user_id: str = None):
        """Save a diagnostic report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        issues_json = json.dumps(issues)
        report_json = json.dumps(diagnosis_report)
        
        cursor.execute('''
        INSERT INTO diagnostics (vehicle_id, severity, issues, diagnosis_report, user_id)
        VALUES (?, ?, ?, ?, ?)
        ''', (vehicle_id, severity, issues_json, report_json, user_id))
        
        conn.commit()
        conn.close()
    
    def get_diagnostic_history(self, vehicle_id: str, limit: int = 10) -> List[Dict]:
        """Get diagnostic history for a vehicle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT severity, issues, diagnosis_report, user_id, timestamp
        FROM diagnostics
        WHERE vehicle_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (vehicle_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'severity': row[0],
                'issues': json.loads(row[1]),
                'diagnosis_report': json.loads(row[2]),
                'user_id': row[3],
                'timestamp': row[4]
            })
        
        return history
    
    def create_appointment(self, vehicle_id: str, owner_email: str, 
                          appointment_date: str, service_type: str):
        """Create a service appointment"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO appointments (vehicle_id, owner_email, appointment_date, service_type, status)
        VALUES (?, ?, ?, ?, ?)
        ''', (vehicle_id, owner_email, appointment_date, service_type, 'scheduled'))
        
        appointment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return appointment_id
    
    def get_appointments(self, vehicle_id: str = None) -> List[Dict]:
        """Get appointments, optionally filtered by vehicle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if vehicle_id:
            cursor.execute('''
            SELECT id, vehicle_id, owner_email, appointment_date, service_type, status, created_at
            FROM appointments
            WHERE vehicle_id = ?
            ORDER BY appointment_date DESC
            ''', (vehicle_id,))
        else:
            cursor.execute('''
            SELECT id, vehicle_id, owner_email, appointment_date, service_type, status, created_at
            FROM appointments
            ORDER BY appointment_date DESC
            ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        appointments = []
        for row in rows:
            appointments.append({
                'id': row[0],
                'vehicle_id': row[1],
                'owner_email': row[2],
                'appointment_date': row[3],
                'service_type': row[4],
                'status': row[5],
                'created_at': row[6]
            })
        
        return appointments
    
    def update_appointment_status(self, appointment_id: int, status: str):
        """Update appointment status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE appointments
        SET status = ?
        WHERE id = ?
        ''', (status, appointment_id))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total conversations
        cursor.execute('SELECT COUNT(*) FROM conversations')
        stats['total_messages'] = cursor.fetchone()[0]
        
        # Total diagnostics
        cursor.execute('SELECT COUNT(*) FROM diagnostics')
        stats['total_diagnostics'] = cursor.fetchone()[0]
        
        # Total appointments
        cursor.execute('SELECT COUNT(*) FROM appointments')
        stats['total_appointments'] = cursor.fetchone()[0]
        
        # Critical diagnostics
        cursor.execute('SELECT COUNT(*) FROM diagnostics WHERE severity = ?', ('Critical',))
        stats['critical_diagnostics'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats

# Singleton instance
_db_instance = None

def get_database():
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
