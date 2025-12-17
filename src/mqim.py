"""
Manufacturing Quality Insights Module (MQIM)
Tracks part failures and identifies recall patterns
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

@dataclass
class PartFailure:
    """Represents a part failure report"""
    vehicle_id: str
    manufacturer: str
    part_type: str
    severity: str
    description: str
    timestamp: str
    
    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'manufacturer': self.manufacturer,
            'part_type': self.part_type,
            'severity': self.severity,
            'description': self.description,
            'timestamp': self.timestamp
        }

class MQIM:
    """Manufacturing Quality Insights Module"""
    
    # Recall thresholds
    RECALL_THRESHOLD = 3  # Number of similar failures to trigger investigation
    CRITICAL_THRESHOLD = 2  # Critical failures to trigger immediate action
    
    def __init__(self):
        self.failures: List[PartFailure] = []
        self.notifications_sent = []
    
    def report_failure(self, vehicle_data: Dict, diagnosis_report: Dict) -> Optional[Dict]:
        """
        Report a part failure and check for recall patterns
        
        Returns notification dict if manufacturer should be notified
        """
        # Extract relevant information
        severity = diagnosis_report.get('severity', 'Unknown')
        
        # Only process High and Critical failures
        if severity not in ['High', 'Critical']:
            return None
        
        # Determine part type and manufacturer
        issues = diagnosis_report.get('issues', [])
        if not issues:
            return None
        
        # Extract first issue for simplicity
        first_issue = issues[0] if issues else "Unknown Issue"
        
        # Determine part type from issue description
        part_type = self._extract_part_type(first_issue)
        manufacturer = vehicle_data.get('make', 'Unknown')
        
        # Create failure report
        failure = PartFailure(
            vehicle_id=vehicle_data.get('vehicle_id', 'Unknown'),
            manufacturer=manufacturer,
            part_type=part_type,
            severity=severity,
            description=first_issue,
            timestamp=datetime.now().isoformat()
        )
        
        # Add to failures list
        self.failures.append(failure)
        
        # Check for recall patterns
        similar_failures = self._count_similar_failures(manufacturer, part_type)
        recall_risk = self._assess_recall_risk(manufacturer, part_type, severity)
        
        # Create notification if threshold exceeded
        if similar_failures >= self.RECALL_THRESHOLD or (severity == 'Critical' and similar_failures >= self.CRITICAL_THRESHOLD):
            notification = {
                'manufacturer': manufacturer,
                'part_type': part_type,
                'severity': severity,
                'similar_failures': similar_failures,
                'recall_risk': recall_risk,
                'recommendation': self._generate_recommendation(recall_risk, similar_failures),
                'timestamp': datetime.now().isoformat()
            }
            
            self.notifications_sent.append(notification)
            return notification
        
        return None
    
    def _extract_part_type(self, issue_description: str) -> str:
        """Extract part type from issue description"""
        issue_lower = issue_description.lower()
        
        if 'brake' in issue_lower:
            return 'Brake System'
        elif 'engine' in issue_lower or 'overheating' in issue_lower:
            return 'Engine'
        elif 'battery' in issue_lower:
            return 'Battery'
        elif 'transmission' in issue_lower:
            return 'Transmission'
        elif 'suspension' in issue_lower:
            return 'Suspension'
        elif 'tire' in issue_lower:
            return 'Tires'
        elif 'electrical' in issue_lower:
            return 'Electrical System'
        else:
            return 'Other'
    
    def _count_similar_failures(self, manufacturer: str, part_type: str) -> int:
        """Count similar failures for same manufacturer and part"""
        count = 0
        for failure in self.failures:
            if failure.manufacturer == manufacturer and failure.part_type == part_type:
                count += 1
        return count
    
    def _assess_recall_risk(self, manufacturer: str, part_type: str, severity: str) -> str:
        """Assess the recall risk level"""
        similar_failures = self._count_similar_failures(manufacturer, part_type)
        critical_count = sum(1 for f in self.failures 
                           if f.manufacturer == manufacturer 
                           and f.part_type == part_type 
                           and f.severity == 'Critical')
        
        if critical_count >= 2 or similar_failures >= 5:
            return 'HIGH'
        elif similar_failures >= 3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _generate_recommendation(self, recall_risk: str, similar_failures: int) -> str:
        """Generate recommendation based on risk"""
        if recall_risk == 'HIGH':
            return f"URGENT: {similar_failures} similar failures detected. Immediate recall investigation recommended."
        elif recall_risk == 'MEDIUM':
            return f"WARNING: {similar_failures} similar failures detected. Monitor closely and consider proactive recall."
        else:
            return f"NOTICE: {similar_failures} similar failures detected. Continue monitoring."
    
    def get_failures_by_manufacturer(self) -> Dict:
        """Get failure statistics by manufacturer"""
        stats = defaultdict(lambda: {'total': 0, 'critical': 0, 'high': 0, 'by_part': defaultdict(int)})
        
        for failure in self.failures:
            mfr = failure.manufacturer
            stats[mfr]['total'] += 1
            
            if failure.severity == 'Critical':
                stats[mfr]['critical'] += 1
            elif failure.severity == 'High':
                stats[mfr]['high'] += 1
            
            stats[mfr]['by_part'][failure.part_type] += 1
        
        # Add average severity calculation
        for mfr in stats:
            total = stats[mfr]['total']
            critical = stats[mfr]['critical']
            high = stats[mfr]['high']
            
            if total > 0:
                severity_score = (critical * 3 + high * 2) / total
                if severity_score >= 2:
                    stats[mfr]['avg_severity'] = 'High'
                elif severity_score >= 1:
                    stats[mfr]['avg_severity'] = 'Medium'
                else:
                    stats[mfr]['avg_severity'] = 'Low'
        
        return dict(stats)
    
    def get_recall_candidates(self) -> List[Dict]:
        """Get list of manufacturer/part combinations that are recall candidates"""
        candidates = []
        
        # Group failures by manufacturer and part
        grouped = defaultdict(list)
        for failure in self.failures:
            key = (failure.manufacturer, failure.part_type)
            grouped[key].append(failure)
        
        # Check each group for recall criteria
        for (manufacturer, part_type), failures in grouped.items():
            failure_count = len(failures)
            critical_count = sum(1 for f in failures if f.severity == 'Critical')
            
            if failure_count >= self.RECALL_THRESHOLD:
                recall_risk = self._assess_recall_risk(manufacturer, part_type, 'High')
                
                candidates.append({
                    'manufacturer': manufacturer,
                    'part_type': part_type,
                    'failure_count': failure_count,
                    'critical_count': critical_count,
                    'severity': 'Critical' if critical_count >= 2 else 'High' if critical_count >= 1 else 'Medium',
                    'recall_risk': recall_risk,
                    'pattern': self._identify_pattern(failures),
                    'recommendation': self._generate_recommendation(recall_risk, failure_count)
                })
        
        # Sort by failure count descending
        candidates.sort(key=lambda x: x['failure_count'], reverse=True)
        
        return candidates
    
    def _identify_pattern(self, failures: List[PartFailure]) -> str:
        """Identify common pattern in failures"""
        if not failures:
            return "No pattern identified"
        
        # Simple pattern identification - could be enhanced
        descriptions = [f.description.lower() for f in failures]
        
        # Common keywords
        common_words = set()
        for desc in descriptions:
            words = set(desc.split())
            if not common_words:
                common_words = words
            else:
                common_words = common_words.intersection(words)
        
        if common_words:
            pattern_words = [w for w in common_words if len(w) > 3]
            if pattern_words:
                return f"Common issue: {' '.join(pattern_words[:3])}"
        
        return f"Multiple failures reported for {failures[0].part_type}"
    
    def get_total_failures(self) -> int:
        """Get total number of failures reported"""
        return len(self.failures)
    
    def get_notifications_sent(self) -> List[Dict]:
        """Get list of all notifications sent to manufacturers"""
        return self.notifications_sent.copy()
    
    def clear_old_failures(self, days: int = 30):
        """Clear failures older than specified days"""
        # This would need proper date comparison
        # For now, just a placeholder
        pass

# Singleton instance
_mqim_instance = None

def get_mqim():
    """Get or create MQIM instance"""
    global _mqim_instance
    if _mqim_instance is None:
        _mqim_instance = MQIM()
    return _mqim_instance
