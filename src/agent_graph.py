from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
import sys
import os
import json

# Add 'src' to path so we can import our modules easily
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your "Specialists" (The code you already wrote)
from src.utils import fetch_telematics, fetch_owner_details
from src.diagnosis import analyze_vehicle
from src.chatbot import get_chatbot
from src.mqim import get_mqim
from src.ueba import get_ueba
from src.database import get_database

# --- 1. DEFINE THE SHARED STATE (The Clipboard) ---
# This is the data that gets passed around between agents.
class AgentState(TypedDict):
    vehicle_id: str
    telematics_data: dict
    diagnosis_report: dict
    severity: str
    messages: list
    mqim_notification: dict  # New: Manufacturing feedback
    security_threat: dict     # New: Security status
    user_id: str             # New: User performing the action

# --- 2. DEFINE THE NODES (The Agents) ---

def monitor_agent(state: AgentState):
    """
    Role: The Sensor Watcher
    Task: Fetches raw data from the car (JSON).
    """
    v_id = state['vehicle_id']
    print(f"\n[Monitor Agent] Fetching data for {v_id}...")
    
    # Call your Utils script
    data = fetch_telematics(v_id)
    
    if "error" in data:
        print(f"[Monitor Agent] Error: {data['error']}")
        return {"telematics_data": {}}
    
    return {"telematics_data": data}

def diagnosis_agent(state: AgentState):
    """
    Role: The Mechanic
    Task: Looks at the data and decides if the car is broken.
    """
    print("[Diagnosis Agent] Analyzing parameters...")
    
    # Call your Diagnosis script (The 'Brain' you just built)
    report = analyze_vehicle({"telematics": state['telematics_data']})
    
    severity = report['status']
    print(f"[Diagnosis Agent] Result: {severity} - {report['issues']}")
    
    return {
        "diagnosis_report": report,
        "severity": severity
    }

def customer_service_agent(state: AgentState):
    """
    Role: The Service Advisor
    Task: Only wakes up if there is a problem. Drafts a personalized message using AI.
    """
    print("[Customer Service Agent] Critical Issue detected. Preparing alert...")
    
    # Get chatbot instance
    chatbot = get_chatbot()
    
    # Get owner details
    vehicle_id = state['vehicle_id']
    owner = fetch_owner_details(vehicle_id)
    owner_name = owner.get('name', 'Valued Customer') if owner else 'Valued Customer'
    
    # Generate personalized alert using chatbot
    alert_msg = chatbot.generate_initial_alert(
        diagnosis_report=state['diagnosis_report'],
        vehicle_id=vehicle_id,
        owner_name=owner_name
    )
    
    # Save conversation to database
    db = get_database()
    db.save_message(vehicle_id, "assistant", alert_msg, {"severity": state['severity']})
    
    return {"messages": [alert_msg]}

def mqim_agent(state: AgentState):
    """
    Role: Manufacturing Quality Monitor
    Task: Reports failures to manufacturers and checks for recall patterns.
    """
    severity = state['severity']
    
    # Only process High and Critical failures
    if severity not in ['High', 'Critical']:
        print("[MQIM Agent] Severity not critical. No manufacturer notification needed.")
        return {"mqim_notification": {}}
    
    print("[MQIM Agent] Processing failure report for manufacturer notification...")
    
    # Get MQIM instance
    mqim = get_mqim()
    
    # Load vehicle data
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'data', 'vehicles.json')
    
    try:
        with open(db_path, 'r') as f:
            all_vehicles = json.load(f)
        
        vehicle_data = next((v for v in all_vehicles if v['vehicle_id'] == state['vehicle_id']), None)
        
        if vehicle_data:
            # Report failure to MQIM
            notification = mqim.report_failure(vehicle_data, state['diagnosis_report'])
            
            if notification:
                print(f"[MQIM Agent] Manufacturer notification sent: {notification['manufacturer']}")
                print(f"[MQIM Agent] Recall Risk: {notification['recall_risk']}")
                return {"mqim_notification": notification}
            else:
                return {"mqim_notification": {}}
        else:
            print(f"[MQIM Agent] Vehicle data not found for {state['vehicle_id']}")
            return {"mqim_notification": {}}
    
    except Exception as e:
        print(f"[MQIM Agent] Error: {e}")
        return {"mqim_notification": {}}

def security_agent(state: AgentState):
    """
    Role: Security Monitor (UEBA)
    Task: Logs user activity and checks for security anomalies.
    """
    print("[Security Agent] Monitoring user activity...")
    
    # Get UEBA instance
    ueba = get_ueba()
    
    # Get user ID (default to system if not provided)
    user_id = state.get('user_id', 'SYSTEM')
    vehicle_id = state.get('vehicle_id', 'Unknown')
    
    # Log the diagnostic activity
    threat = ueba.log_activity(
        user_id,
        "run_diagnostics",
        {
            "vehicle_id": vehicle_id,
            "severity": state.get('severity', 'Unknown'),
            "timestamp": "now"
        }
    )
    
    if threat:
        print(f"[Security Agent] ⚠️  SECURITY THREAT DETECTED!")
        print(f"[Security Agent] Threat Type: {threat.threat_type}")
        print(f"[Security Agent] Severity: {threat.severity}")
        
        # Check if user should be blocked
        if ueba.is_user_blocked(user_id):
            print(f"[Security Agent] 🚫 USER BLOCKED: {user_id}")
            return {
                "security_threat": {
                    "blocked": True,
                    "threat": threat.to_dict()
                }
            }
        
        return {
            "security_threat": {
                "blocked": False,
                "threat": threat.to_dict()
            }
        }
    else:
        print("[Security Agent] ✅ Activity normal. No threats detected.")
        return {"security_threat": {}}

# --- 3. DEFINE THE LOGIC FLOW (The Graph) ---

workflow = StateGraph(AgentState)

# Add the nodes
workflow.add_node("security", security_agent)      # NEW: Security monitoring
workflow.add_node("monitor", monitor_agent)
workflow.add_node("mechanic", diagnosis_agent)
workflow.add_node("mqim", mqim_agent)              # NEW: Manufacturing feedback
workflow.add_node("support", customer_service_agent)

# Set the entry point - Security checks first!
workflow.set_entry_point("security")

# Security → Monitor (only if not blocked)
def security_control(state: AgentState):
    """
    Check if user is blocked by security.
    """
    security_threat = state.get('security_threat', {})
    
    if security_threat.get('blocked', False):
        return END  # Block the workflow
    else:
        return "monitor"  # Continue to monitoring

workflow.add_conditional_edges(
    "security",
    security_control,
    {
        "monitor": "monitor",
        END: END
    }
)

# Standard connection: Monitor → Mechanic
workflow.add_edge("monitor", "mechanic")

# Mechanic → MQIM (always report to manufacturing)
workflow.add_edge("mechanic", "mqim")

# --- CONDITIONAL LOGIC (The Router) ---
def traffic_control(state: AgentState):
    """
    Decides where to go after MQIM analysis.
    If Critical/High severity, alert customer.
    Otherwise, end workflow.
    """
    if state['severity'] == "Critical" or state['severity'] == "High":
        return "support"  # Go to Customer Service
    else:
        return END  # Vehicle is fine, stop the workflow.

workflow.add_conditional_edges(
    "mqim",
    traffic_control,
    {
        "support": "support",
        END: END
    }
)

workflow.add_edge("support", END)

# Compile the graph
app = workflow.compile()

# --- 4. TEST RUNNER ---
if __name__ == "__main__":
    # Test with our "Trigger" Vehicle
    test_id = "V-005"
    test_user = "U001"  # Alice Manager
    
    print(f"=== STARTING ENHANCED SIMULATION FOR {test_id} ===")
    print(f"User: {test_user}\n")
    
    initial_state = {
        "vehicle_id": test_id,
        "user_id": test_user,
        "telematics_data": {},
        "diagnosis_report": {},
        "severity": "Unknown",
        "messages": [],
        "mqim_notification": {},
        "security_threat": {}
    }
    
    # Run the graph
    result = app.invoke(initial_state)
    
    print("\n=== WORKFLOW FINISHED ===")
    print("\n--- Results Summary ---")
    
    # Security status
    if result.get('security_threat'):
        threat = result['security_threat']
        if threat.get('blocked'):
            print("🚫 SECURITY: User blocked due to suspicious activity!")
        elif threat.get('threat'):
            print(f"⚠️  SECURITY: Threat detected - {threat['threat'].get('threat_type')}")
        else:
            print("✅ SECURITY: No threats detected")
    
    # Diagnosis
    print(f"\n🔧 DIAGNOSIS: {result.get('severity', 'Unknown')}")
    if result.get('diagnosis_report', {}).get('issues'):
        print(f"   Issues: {result['diagnosis_report']['issues']}")
    
    # Manufacturing feedback
    if result.get('mqim_notification'):
        mqim = result['mqim_notification']
        print(f"\n🏭 MANUFACTURING ALERT:")
        print(f"   Manufacturer: {mqim.get('manufacturer', 'N/A')}")
        print(f"   Part: {mqim.get('part_type', 'N/A')}")
        print(f"   Recall Risk: {mqim.get('recall_risk', 'N/A')}")
        print(f"   Similar Failures: {mqim.get('similar_failures', 0)}")
    
    # Customer notification
    if result.get('messages'):
        print(f"\n📧 CUSTOMER NOTIFICATION:")
        print(f"{result['messages'][0][:200]}...")
    else:
        print("\n✅ Vehicle Healthy. No customer alert needed.")
    
    print("\n" + "="*50)