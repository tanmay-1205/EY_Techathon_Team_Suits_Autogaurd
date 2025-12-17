import json
import os

# Dynamically find the path to the data folder
# This ensures it works whether you run from 'src' or the root folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'vehicles.json')

def fetch_telematics(vehicle_id):
    """
    Simulates an API call to the vehicle's onboard computer.
    Returns the 'telematics' dictionary or an error.
    """
    try:
        if not os.path.exists(DB_PATH):
            return {"error": f"Database file not found at {DB_PATH}"}

        with open(DB_PATH, 'r') as f:
            data = json.load(f)
            
        # Search for the vehicle in the list
        vehicle = next((v for v in data if v["vehicle_id"] == vehicle_id), None)
        
        if vehicle:
            return vehicle.get('telematics', {})
        else:
            return {"error": "Vehicle ID not found"}
            
    except Exception as e:
        return {"error": str(e)}

def fetch_owner_details(vehicle_id):
    """
    Simulates a CRM lookup to find who owns the car.
    Returns owner information from the vehicle database.
    """
    try:
        with open(DB_PATH, 'r') as f:
            data = json.load(f)
        vehicle = next((v for v in data if v["vehicle_id"] == vehicle_id), None)
        
        if vehicle:
            # Extract actual owner information from JSON
            owner_id = vehicle.get('owner_id', 'Unknown')
            owner_name = vehicle.get('owner_name', 'Valued Customer')
            owner_phone = vehicle.get('owner_phone', 'N/A')
            metadata = vehicle.get('metadata', {})
            
            return {
                "owner_id": owner_id,
                "name": owner_name,
                "phone": owner_phone,
                "model": metadata.get('model', 'Unknown Model'),
                "make": metadata.get('make', 'Unknown Make'),
                "year": metadata.get('year', 'Unknown Year')
            }
        return None
    except Exception as e:
        print(f"[fetch_owner_details] Error: {e}")
        return None

def check_service_slots(date=None):
    """
    Mock function to return available repair slots.
    """
    return ["10:00 AM", "02:00 PM", "04:30 PM"]