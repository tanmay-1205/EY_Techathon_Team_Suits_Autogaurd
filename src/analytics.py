"""
Fleet Analytics Module
Provides predictive analytics, risk scoring, and insights
"""

from typing import List, Dict, Optional
from collections import defaultdict
import statistics

class FleetAnalytics:
    """Fleet-wide analytics and insights"""
    
    # Risk scoring weights
    STATUS_WEIGHTS = {
        'Critical': 100,
        'High': 70,
        'Medium': 40,
        'Low': 20,
        'Normal': 0
    }
    
    # Maintenance cost estimates (in USD)
    MAINTENANCE_COSTS = {
        'Critical': 5000,
        'High': 3000,
        'Medium': 1500,
        'Low': 500,
        'Normal': 200
    }
    
    def __init__(self, vehicles: List[Dict]):
        self.vehicles = vehicles
    
    def calculate_risk_score(self, vehicle: Dict) -> float:
        """Calculate risk score for a single vehicle (0-100)"""
        status = vehicle.get('status', 'Normal')
        base_score = self.STATUS_WEIGHTS.get(status, 0)
        
        # Factor in confidence (inverse relationship)
        confidence = vehicle.get('confidence', '100%')
        confidence_val = float(confidence.rstrip('%')) / 100
        
        # Lower confidence = higher risk
        confidence_modifier = (1 - confidence_val) * 20
        
        # Factor in mileage (if available)
        mileage_modifier = 0
        if 'mileage' in vehicle:
            mileage = vehicle['mileage']
            if mileage > 100000:
                mileage_modifier = 10
            elif mileage > 75000:
                mileage_modifier = 5
        
        total_score = min(100, base_score + confidence_modifier + mileage_modifier)
        
        return round(total_score, 1)
    
    def get_fleet_risk_score(self) -> float:
        """Calculate average risk score for entire fleet"""
        if not self.vehicles:
            return 0.0
        
        scores = [self.calculate_risk_score(v) for v in self.vehicles]
        return round(statistics.mean(scores), 1)
    
    def get_risk_breakdown(self) -> Dict:
        """Get risk breakdown by status category"""
        breakdown = defaultdict(lambda: {'count': 0, 'vehicles': [], 'risk_score': 0})
        
        for vehicle in self.vehicles:
            status = vehicle.get('status', 'Normal')
            risk_score = self.calculate_risk_score(vehicle)
            
            breakdown[status]['count'] += 1
            breakdown[status]['vehicles'].append(vehicle['vehicle_id'])
            breakdown[status]['risk_score'] = self.STATUS_WEIGHTS.get(status, 0)
        
        # Add severity classification
        for status in breakdown:
            count = breakdown[status]['count']
            if count >= 3:
                breakdown[status]['severity'] = 'High'
            elif count >= 2:
                breakdown[status]['severity'] = 'Medium'
            else:
                breakdown[status]['severity'] = 'Low'
        
        return dict(breakdown)
    
    def get_maintenance_forecast(self) -> Dict:
        """Forecast maintenance needs and costs"""
        forecast = {
            'immediate': {'count': 0, 'vehicles': [], 'cost': 0},
            'short_term': {'count': 0, 'vehicles': [], 'cost': 0},
            'long_term': {'count': 0, 'vehicles': [], 'cost': 0}
        }
        
        for vehicle in self.vehicles:
            status = vehicle.get('status', 'Normal')
            vehicle_id = vehicle['vehicle_id']
            cost = self.MAINTENANCE_COSTS.get(status, 0)
            
            if status in ['Critical', 'High']:
                forecast['immediate']['count'] += 1
                forecast['immediate']['vehicles'].append(vehicle_id)
                forecast['immediate']['cost'] += cost
            elif status == 'Medium':
                forecast['short_term']['count'] += 1
                forecast['short_term']['vehicles'].append(vehicle_id)
                forecast['short_term']['cost'] += cost
            else:
                forecast['long_term']['count'] += 1
                forecast['long_term']['vehicles'].append(vehicle_id)
                forecast['long_term']['cost'] += cost
        
        return forecast
    
    def identify_high_risk_vehicles(self, threshold: float = 70) -> List[Dict]:
        """Identify vehicles with risk score above threshold"""
        high_risk = []
        
        for vehicle in self.vehicles:
            risk_score = self.calculate_risk_score(vehicle)
            if risk_score >= threshold:
                high_risk.append({
                    'vehicle_id': vehicle['vehicle_id'],
                    'owner': vehicle.get('owner', 'Unknown'),
                    'make': vehicle.get('make', 'Unknown'),
                    'model': vehicle.get('model', 'Unknown'),
                    'status': vehicle.get('status', 'Unknown'),
                    'risk_score': risk_score,
                    'current_issue': vehicle.get('current_issue', 'None')
                })
        
        # Sort by risk score descending
        high_risk.sort(key=lambda x: x['risk_score'], reverse=True)
        
        return high_risk
    
    def get_manufacturer_insights(self) -> Dict:
        """Get insights by manufacturer"""
        mfr_stats = defaultdict(lambda: {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'normal': 0,
            'avg_risk': 0,
            'vehicles': []
        })
        
        for vehicle in self.vehicles:
            make = vehicle.get('make', 'Unknown')
            status = vehicle.get('status', 'Normal')
            risk_score = self.calculate_risk_score(vehicle)
            
            mfr_stats[make]['total'] += 1
            mfr_stats[make]['vehicles'].append(vehicle['vehicle_id'])
            mfr_stats[make][status.lower().replace(' ', '_')] += 1
            
            # Running average of risk
            current_total = mfr_stats[make]['total']
            current_avg = mfr_stats[make]['avg_risk']
            mfr_stats[make]['avg_risk'] = ((current_avg * (current_total - 1)) + risk_score) / current_total
        
        # Round averages
        for make in mfr_stats:
            mfr_stats[make]['avg_risk'] = round(mfr_stats[make]['avg_risk'], 1)
        
        return dict(mfr_stats)
    
    def generate_recommendations(self) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check for critical vehicles
        critical_count = len([v for v in self.vehicles if v.get('status') == 'Critical'])
        if critical_count > 0:
            recommendations.append({
                'priority': 'High',
                'title': f'{critical_count} Critical Vehicle(s) Need Immediate Attention',
                'description': 'Schedule emergency maintenance to prevent safety incidents and downtime.',
                'category': 'Maintenance'
            })
        
        # Check for high-risk concentration
        high_risk_count = len([v for v in self.vehicles if v.get('status') in ['Critical', 'High']])
        if high_risk_count > len(self.vehicles) * 0.2:  # More than 20%
            recommendations.append({
                'priority': 'High',
                'title': 'High Concentration of At-Risk Vehicles',
                'description': f'{high_risk_count} vehicles need attention. Consider fleet-wide inspection.',
                'category': 'Fleet Management'
            })
        
        # Check for manufacturer patterns
        mfr_insights = self.get_manufacturer_insights()
        for make, stats in mfr_insights.items():
            if stats['avg_risk'] > 60:
                recommendations.append({
                    'priority': 'Medium',
                    'title': f'{make} Vehicles Showing Elevated Risk',
                    'description': f'Average risk score: {stats["avg_risk"]}. Consider manufacturer-specific maintenance protocol.',
                    'category': 'Quality'
                })
        
        # Check maintenance forecast
        forecast = self.get_maintenance_forecast()
        if forecast['immediate']['cost'] > 20000:
            recommendations.append({
                'priority': 'High',
                'title': 'High Immediate Maintenance Costs Projected',
                'description': f'Estimated ${forecast["immediate"]["cost"]:,} in immediate repairs. Budget allocation recommended.',
                'category': 'Financial'
            })
        
        # General fleet health recommendation
        fleet_risk = self.get_fleet_risk_score()
        if fleet_risk < 30:
            recommendations.append({
                'priority': 'Low',
                'title': 'Fleet Health Excellent',
                'description': 'Continue current maintenance schedule. Consider preventive maintenance optimization.',
                'category': 'Optimization'
            })
        
        return recommendations
    
    def get_executive_summary(self) -> Dict:
        """Generate executive summary with all key insights"""
        forecast = self.get_maintenance_forecast()
        high_risk = self.identify_high_risk_vehicles()
        
        summary = {
            'summary': {
                'total_vehicles': len(self.vehicles),
                'average_risk_score': self.get_fleet_risk_score(),
                'immediate_action_required': forecast['immediate']['count'],
                'projected_maintenance_cost': forecast['immediate']['cost'] + forecast['short_term']['cost']
            },
            'high_risk_vehicles': high_risk[:5],  # Top 5
            'maintenance_forecast': forecast,
            'recommendations': self.generate_recommendations(),
            'manufacturer_insights': self.get_manufacturer_insights()
        }
        
        return summary
    
    def get_predictive_failures(self, days_ahead: int = 30) -> List[Dict]:
        """Predict potential failures in the near future"""
        # Simplified predictive model
        predictions = []
        
        for vehicle in self.vehicles:
            status = vehicle.get('status', 'Normal')
            
            # Vehicles in Medium status likely to degrade
            if status == 'Medium':
                predictions.append({
                    'vehicle_id': vehicle['vehicle_id'],
                    'predicted_status': 'High',
                    'confidence': '65%',
                    'days_until_failure': days_ahead,
                    'recommendation': 'Schedule preventive maintenance'
                })
            
            # High status likely to become critical
            elif status == 'High':
                predictions.append({
                    'vehicle_id': vehicle['vehicle_id'],
                    'predicted_status': 'Critical',
                    'confidence': '75%',
                    'days_until_failure': days_ahead // 2,
                    'recommendation': 'Immediate inspection required'
                })
        
        return predictions

# Helper function
def get_analytics(vehicles: List[Dict]) -> FleetAnalytics:
    """Create analytics instance"""
    return FleetAnalytics(vehicles)
