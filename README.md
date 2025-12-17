# AutoGuard: Autonomous Agentic AI Ecosystem

**EY Techathon 6.0 Submission - Team Suits**

Team Members 
Adway Jha
Parth Khose 
Viven Sharma
Tanmay Amritkar

## Executive Summary

AutoGuard is an autonomous predictive maintenance ecosystem designed to eliminate reactive vehicle downtime through intelligent, multi-agent orchestration. The system leverages a sophisticated multi-agent architecture built on LangGraph to automatically detect anomalies, diagnose root causes, engage customers via voice and text interfaces, and optimize service scheduling without human intervention.

By transforming traditional fleet management from reactive maintenance to proactive, AI-driven operations, AutoGuard delivers measurable ROI through reduced warranty costs, improved customer satisfaction, and optimized resource allocation.

## System Architecture

The AutoGuard ecosystem is built on a distributed agent architecture where specialized agents collaborate to deliver end-to-end fleet management capabilities:

### The Brain (Orchestrator)

Built on LangGraph, the orchestrator manages state and intelligent routing between agents. It coordinates the entire workflow from anomaly detection through customer engagement and service scheduling.

### Monitor Agent

Continuously ingests real-time telemetry data from vehicle sensors, processing data from `vehicles.json` to maintain an up-to-date view of fleet health. The agent normalizes sensor readings and flags anomalies for downstream processing.

### Diagnosis Agent

A deterministic rule engine that assesses failure severity across multiple dimensions. The agent classifies issues into severity levels (Critical, High, Medium, Low, Normal) based on telemetry thresholds and historical patterns, providing actionable insights with confidence scores.

### Customer Engagement Agent (CEA)

Personalized conversational AI interface supporting both voice (gTTS) and text communication. The CEA delivers proactive alerts, answers maintenance questions, and facilitates service booking through natural language interactions in multiple languages.

### Manufacturing Quality Insights Module (MQIM)

Analyzes defect trends and failure patterns to identify supply chain root causes. The module tracks component failures by manufacturer, batch, and part type, enabling proactive recall management and quality feedback loops. For example, the system can identify that Apex Dynamics batch failures are causing widespread brake pad issues.

### Security Agent (UEBA)

User & Entity Behavior Analytics engine that detects insider threats and anomalous access patterns. The agent monitors user activities, identifies suspicious behaviors, and automatically blocks unauthorized access attempts, providing real-time security posture visibility.

## Key Features

### Live Fleet Command

A comprehensive "Sea of Green" dashboard visualizing 50+ vehicles with real-time health status. The interface provides color-coded status indicators, advanced filtering capabilities, and drill-down analytics for fleet managers to maintain complete operational visibility.

### Voice-Enabled Engagement

Hybrid text-and-voice interface for seamless vehicle owner communication. The system automatically generates voice alerts for critical issues using Google Text-to-Speech (gTTS), enabling hands-free interaction and improved accessibility.

### Closed-Loop Scheduling

Automated service bay allocation using a mock Scheduling Agent that optimizes appointment booking based on vehicle criticality, service center capacity, and technician availability. The system provides real-time schedule visualization and demand forecasting.

### Supply Chain Feedback

Real-time impact analysis on warranty costs and recurrence rates. The MQIM module tracks how manufacturing defects propagate through the fleet, enabling data-driven decisions on supplier relationships and quality control measures.

## Technical Stack

- **Frontend:** Streamlit (Python)
- **Backend Logic:** Python 3.10+
- **Orchestration:** LangGraph, LangChain
- **Visualization:** Plotly, Altair
- **Voice Synthesis:** gTTS (Google Text-to-Speech)
- **Data Storage:** SQLite, JSON
- **Data Processing:** Pandas, NumPy

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- pip package manager
- Internet connection (for optional OpenAI features and gTTS)

### Step 1: Clone Repository

```bash
cd c:\Users\tanma\Desktop\EY_Prototype
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- streamlit
- langgraph
- langchain
- openai (optional)
- pandas
- plotly
- gtts
- And other dependencies

### Step 5: Launch Application

**Option A: Use Launcher Script**
```bash
launch.bat
```

**Option B: Command Line**
```bash
streamlit run src/dashboard_enhanced.py
```

### Step 6: Access Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

## Demo Scenarios

### Critical Brake Failure Detection

**Scenario:** The system detects critical brake pad wear requiring immediate attention.

**Trigger:** 
1. Navigate to the Fleet Overview dashboard
2. Select Vehicle **V-005** (Tesla Model Y) from the vehicle dropdown
3. Click **"Run Diagnostic and Connect with Customer"**

**Expected Outcome:** 
- System transitions to the Customer Experience Console
- AutoGuard AI automatically plays an audio alert: "Hello Arjun. Critical brake wear detected..."
- Customer receives personalized notification with severity assessment
- System suggests available service slots
- Customer can confirm appointment via voice or text interface
- Confirmation is sent via WhatsApp with service details

**Workflow Steps:**
1. Security Agent validates user permissions and logs activity
2. Monitor Agent fetches real-time telemetry for V-005
3. Diagnosis Agent identifies Critical Brake Wear (2.1mm)
4. MQIM Agent reports failure to manufacturer and checks for similar patterns
5. Customer Engagement Agent generates personalized alert
6. Scheduling Agent identifies available priority slot
7. System confirms booking and sends notification

## Project Structure

```
EY_Prototype/
├── src/
│   ├── dashboard_enhanced.py    # Main Streamlit application
│   ├── agent_graph.py           # LangGraph orchestrator
│   ├── diagnosis.py             # Diagnosis Agent logic
│   ├── chatbot.py               # Customer Engagement Agent
│   ├── mqim.py                  # Manufacturing Quality Insights
│   ├── ueba.py                  # Security Agent (UEBA)
│   ├── analytics.py             # Fleet Analytics engine
│   ├── database.py              # Database utilities
│   └── utils.py                 # Helper functions
├── data/
│   ├── vehicles.json            # Vehicle telemetry data
│   ├── autoguard.db             # SQLite database
│   ├── mqim_reports.json        # Manufacturing reports
│   └── ueba_activity.json       # Security activity logs
├── requirements.txt             # Python dependencies
├── launch.bat                   # Windows launcher script
└── README.md                    # This file
```

## Configuration

### User Accounts

Default demo accounts are configured in `src/ueba.py`:

- **Fleet Manager:** alice.manager@autoguard.com
- **Mechanic:** bob.mechanic@autoguard.com
- **Admin:** charlie.admin@autoguard.com
- **External User (for security testing):** eve.hacker@external.com

All accounts use password: `password`

### Data Sources

Vehicle telemetry is stored in `data/vehicles.json`. The system processes 50+ vehicles with real-time sensor data including:
- Brake pad thickness
- Coolant temperature
- Battery voltage
- Engine parameters
- Tire pressure

## API Reference

### Agent Orchestration

The main workflow is orchestrated through `src/agent_graph.py`:

```python
from src.agent_graph import app as agent_app

# Run diagnostic workflow
result = agent_app.invoke({
    "vehicle_id": "V-005",
    "user_id": "U001"
})
```

### Individual Agent Access

```python
from src.diagnosis import analyze_vehicle
from src.mqim import get_mqim
from src.ueba import get_ueba
from src.chatbot import get_chatbot

# Diagnosis Agent
result = analyze_vehicle("V-005")

# MQIM Agent
mqim = get_mqim()
report = mqim.process_failure("V-005", "brake_pad", "critical")

# Security Agent
ueba = get_ueba()
threat = ueba.detect_anomaly(user_id, activity)

# Customer Engagement Agent
chatbot = get_chatbot()
response = chatbot.get_response(message, context)
```

## Performance Metrics

- **Dashboard Load Time:** 2-3 seconds
- **Diagnostic Workflow:** 3-5 seconds
- **Voice Synthesis:** 1-2 seconds per message
- **AI Chat Response:** 2-4 seconds (with OpenAI API)
- **Fallback Response:** Instant (rule-based)

## Security Considerations

The UEBA agent implements multiple security layers:

- **Authentication:** Role-based access control
- **Activity Monitoring:** Real-time user behavior tracking
- **Threat Detection:** Anomaly pattern recognition
- **Automatic Blocking:** Immediate response to suspicious activities
- **Audit Logging:** Complete activity trail for compliance

## Troubleshooting

### Port Already in Use

```bash
streamlit run src/dashboard_enhanced.py --server.port 8502
```

### Module Not Found

```bash
pip install -r requirements.txt --force-reinstall
```

### Clear Streamlit Cache

```bash
streamlit cache clear
```

### Database Issues

If database errors occur, delete `data/autoguard.db` and restart the application. The system will automatically recreate the database schema.

## Contributing

This project was developed for EY Techathon 6.0. For questions or contributions, please refer to the project documentation in `QUICKSTART.md`.

## License

This project is developed for demonstration purposes as part of EY Techathon 6.0 submission.

## Acknowledgments

Built by Team Suits for EY Techathon 6.0. The system demonstrates advanced multi-agent orchestration, predictive maintenance, and autonomous fleet management capabilities.

---

**For detailed usage instructions, see `QUICKSTART.md`**
