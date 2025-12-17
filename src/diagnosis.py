import json
import os

def analyze_vehicle(vehicle):
    """
    Analyzes a single vehicle's data and returns a health report.
    This is a 'Pure Function' - it takes data in, gives a result out.
    """
    telematics = vehicle.get('telematics', {})
    history = vehicle.get('maintenance_history', {})
    
    # Defaults
    issues = []
    severity = "Normal"
    confidence = 1.0
    recommendation = "No action needed."

    # --- RULE 1: Critical Brake Failure (The Demo Trigger) ---
    brake_pad = telematics.get('brake_pad_thickness_mm', 10)
    if brake_pad < 3.0:
        issues.append(f"Critical Brake Wear ({brake_pad:.1f}mm)")
        severity = "Critical"
        confidence = 0.99
        recommendation = "Immediate Service Booking Required. Do not drive."

    # --- RULE 2: Overheating Risk ---
    # Only triggers if BOTH coolant is hot AND engine is working hard
    coolant = telematics.get('coolant_temp_c', 90)
    load = telematics.get('engine_load_pct', 30)
    
    if coolant > 105 and load > 80:
        issues.append(f"Engine Overheating Risk (Temp: {coolant:.1f}C, Load: {load:.0f}%)")
        if severity != "Critical": # Don't downgrade if already Critical
            severity = "High"
            confidence = 0.85
            recommendation = "Check coolant levels and radiator immediately."

    # --- RULE 3: Battery/Electrical Issue ---
    voltage = telematics.get('battery_voltage_v', 13.5)
    if voltage < 12.0:
        issues.append(f"Low Battery Voltage ({voltage:.1f}V)")
        if severity not in ["Critical", "High"]:
            severity = "Medium"
            recommendation = "Schedule battery inspection."

    # --- RULE 4: Maintenance Neglect (The 'At-Risk' Classifier) ---
    last_service = history.get('km_since_last_service', 0)
    repairs = history.get('num_repairs_last_12m', 0)
    
    if last_service > 15000 or repairs > 3:
        issues.append(f"Maintenance Overdue (+{last_service}km since service)")
        if severity == "Normal":
            severity = "Low"
            recommendation = "Book routine maintenance soon."

    return {
        "vehicle_id": vehicle.get('vehicle_id'),
        "status": severity,
        "issues": issues,
        "confidence": confidence,
        "recommendation": recommendation
    }

# --- TEST RUNNER (Only runs if you execute this file directly) ---
if __name__ == "__main__":
    # 1. Load the data we generated
    try:
        # Go up one level from 'src' to find 'data'
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_path, 'data', 'vehicles.json')
        
        with open(data_path, 'r') as f:
            all_vehicles = json.load(f)
            
        print(f"Loaded {len(all_vehicles)} vehicles for diagnosis...\n")

        # 2. Find our Trigger Vehicle (V-005)
        target_id = "V-005"
        target_vehicle = next((v for v in all_vehicles if v['vehicle_id'] == target_id), None)

        if target_vehicle:
            # 3. Run the diagnosis
            report = analyze_vehicle(target_vehicle)
            
            # 4. Print the result
            print(f"--- DIAGNOSIS REPORT FOR {target_id} ---")
            print(f"Status: {report['status']}")
            print(f"Issues: {report['issues']}")
            print(f"Recommendation: {report['recommendation']}")
            
            # Validation
            if report['status'] == "Critical":
                print("\n SUCCESS: Logic correctly identified the critical failure.")
            else:
                print("\n FAILED: Logic did not catch the issue.")
        else:
            print(f"Error: Could not find vehicle {target_id} in JSON.")

    except FileNotFoundError:
        print("Error: data/vehicles.json not found. Did you run the generator script?")