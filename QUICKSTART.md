# AutoGuard Quick Start Guide

Get up and running with AutoGuard in under 5 minutes!

## Prerequisites

- Windows 10/11
- Python 3.8 or higher
- Internet connection (for optional OpenAI features)

## Installation

### Step 1: Install Python Dependencies

Open PowerShell or Command Prompt in the project directory:

```bash
cd c:\Users\tanma\Desktop\EY_Prototype
pip install -r requirements.txt
```

This will install:
- streamlit (Dashboard framework)
- langgraph (Multi-agent orchestration)
- openai (AI chatbot - optional)
- pandas (Data processing)
- And other dependencies

### Step 2: Launch the Dashboard

#### Option A: Use the Launcher (Easiest)
Double-click `launch.bat`

#### Option B: Command Line
```bash
streamlit run src/dashboard_enhanced.py
```

### Step 3: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8501
```

The dashboard will automatically open in your default browser.

## First Login

### Quick Demo (Recommended)
1. Click the **"Quick Demo"** button on the login page
2. You'll be automatically logged in as Alice Manager (Fleet Manager)

### Manual Login
Use any of these demo accounts:

**Fleet Manager**
- Email: `alice.manager@autoguard.com`
- Password: `password`

**Mechanic**
- Email: `bob.mechanic@autoguard.com`
- Password: `password`

**Admin**
- Email: `charlie.admin@autoguard.com`
- Password: `password`

## Your First Diagnostic

### Run a Complete Vehicle Diagnostic

1. After logging in, you'll see the **Fleet Overview** page
2. Look at the metrics at the top:
   - **Total Fleet**: Number of vehicles
   - **Critical**: Vehicles needing immediate attention
   - **High Risk**, **At Risk**, **Healthy**: Status distribution

3. Scroll down to **Live Fleet Status** table
   - Notice the **color-coded Vehicle IDs**:
     - Red = Critical/High
     - Yellow = Medium/Low
     - Green = Normal

4. Go to **Diagnostic Actions** section
5. Select vehicle **V-005** (this is a critical case)
6. Click **"Run Full Diagnostic"**

### What Happens Next?

The system will run a multi-agent workflow:

1. **Security Check** (UEBA Agent)
   - Logs your activity
   - Checks for suspicious patterns
   - May block if threat detected

2. **Data Collection** (Monitor Agent)
   - Fetches vehicle telemetry
   - Collects sensor readings

3. **AI Diagnosis** (Diagnosis Agent)
   - Analyzes all parameters
   - Classifies severity
   - Identifies specific issues

4. **Manufacturing Alert** (MQIM Agent)
   - Reports failure to manufacturer
   - Checks for similar failures
   - Assesses recall risk

5. **Customer Notification** (Customer Service Agent)
   - Generates personalized alert
   - Drafts message to vehicle owner

### Expected Results for V-005

```
✅ Diagnostic complete!
⚠️ Severity: Critical
Issues Found:
- Critical Brake Wear (2.1mm)

Manufacturing Quality Alert
Manufacturer: Tesla
Part Type: Brake System
Recall Risk: MEDIUM
Similar Failures: 1
```

## Exploring the Dashboard

### Navigation Sidebar (Left Panel)

The blue sidebar on the left contains:

1. **AUTOGUARD FLEET COMMAND** - Logo/Header
2. **Navigation Menu**:
   - Dashboard (Fleet Overview)
   - Manufacturing (MQIM)
   - Security (UEBA)
   - Analytics (Fleet Insights)
   - Customer Chat (AI Support)
3. **User Info** - Your name and role
4. **Logout Button**

Click any navigation button to switch pages.

### Dashboard Page Features

#### Filter by Status
- Use the checkboxes at the top to filter vehicles:
  - Critical
  - High
  - Medium
  - Low
  - Normal

#### Search Vehicle ID
- Type in the search box to find specific vehicles
- Example: "V-005"

#### Live Fleet Status Table
- Color-coded Vehicle IDs for quick status recognition
- Sortable columns
- Hover for subtle highlighting
- Shows: ID, Owner, Make, Model, Status, Issue, Confidence

### Manufacturing Quality Page

View:
- Total failure reports
- Critical failures count
- Recall candidates

Features:
- Failures by manufacturer table
- Recall investigation section
- Notify manufacturer buttons

### Security Page

Monitor:
- Active threats
- Blocked users
- Security metrics

Actions:
- Block suspicious users
- Resolve threats
- Monitor user activity

### Analytics Page

Insights:
- Fleet risk score
- Action required count
- Projected maintenance costs
- Key recommendations
- Risk breakdown by category

### Customer Chat Page

- AI-powered support chatbot
- Ask questions about vehicles
- Get maintenance advice
- Conversation history

## Testing the Security System

### Trigger a Security Threat

1. Login as **Eve Hacker** (external user)
   - Email: `eve.hacker@external.com`
   - Password: `password`

2. Try to run diagnostics
3. System will detect: "Unauthorized Access - External user attempting run_diagnostics"
4. Threat will be logged in Security page

### Block a User

1. Login as Admin
2. Go to **Security** page
3. In "Threat Management" section:
   - Enter User ID: `U004`
   - Click **"Block User"**

4. Try logging in as U004 again
5. Access will be denied

## Testing Manufacturing Quality

### Trigger a Recall Investigation

1. Run diagnostics on multiple vehicles with brake issues:
   - V-005 (Critical brake wear)
   - Run diagnostic multiple times to simulate pattern

2. Go to **Manufacturing** page
3. View "Recall Investigation Required" section
4. When 3+ similar failures occur, manufacturer notification is triggered

## Advanced Usage

### Running the Multi-Agent Workflow Directly

```bash
python src/agent_graph.py
```

This will run the complete workflow with detailed logging:
```
=== STARTING ENHANCED SIMULATION FOR V-005 ===
User: U001

[Security Agent] Monitoring user activity...
[Security Agent] ✅ Activity normal. No threats detected.
[Monitor Agent] Fetching data for V-005...
[Diagnosis Agent] Analyzing parameters...
[Diagnosis Agent] Result: Critical - ['Critical Brake Wear (2.1mm)']
[MQIM Agent] Processing failure report...
[MQIM Agent] Manufacturer notification sent: Tesla
[Customer Service Agent] Critical Issue detected...

=== WORKFLOW FINISHED ===
```

### Testing Individual Components

**Test Diagnosis Engine:**
```bash
python src/diagnosis.py
```

**Test Chatbot:**
```python
from src.chatbot import get_chatbot
bot = get_chatbot()
response = bot.get_response("What should I do about low oil?", [])
print(response)
```

**Test Database:**
```python
from src.database import get_database
db = get_database()
stats = db.get_statistics()
print(stats)
```

## Common Tasks

### Add a New Vehicle

Edit `data/vehicles.json`:
```json
{
    "vehicle_id": "V-011",
    "owner": "New Owner",
    "make": "Toyota",
    "model": "Camry",
    "status": "Normal",
    "current_issue": "None",
    "confidence": "100%"
}
```

### Add a New User

Edit `src/ueba.py` - `USERS_DB`:
```python
{
    "user_id": "U005",
    "email": "newuser@autoguard.com",
    "name": "New User",
    "role": "fleet_manager",
    "password": "password",
    "department": "Operations"
}
```

### Customize UI Colors

Edit `src/dashboard_enhanced.py` - CSS section:
```css
/* Change sidebar color */
[data-testid="stSidebar"] {
    background: #YourColorHere !important;
}

/* Change primary button color */
.stButton > button[kind="primary"] {
    background: #YourColorHere !important;
}
```

## Data Persistence

### Database Location
- SQLite database: `data/autoguard.db`

### Tables Created:
- `conversations` - Chat history
- `diagnostics` - Diagnostic reports
- `appointments` - Service appointments

### Viewing Database

Use any SQLite browser:
```bash
sqlite3 data/autoguard.db
.tables
SELECT * FROM diagnostics;
```

## Performance Notes

- **Dashboard loads in**: ~2-3 seconds
- **Diagnostic workflow**: ~3-5 seconds
- **AI chat response**: ~2-4 seconds (with OpenAI)
- **Fallback response**: Instant

## Keyboard Shortcuts

- **Refresh Dashboard**: F5 or Ctrl+R
- **Hard Refresh**: Ctrl+Shift+R (clears cache)
- **Stop Server**: Ctrl+C in terminal

## Stopping the Server

In the terminal running Streamlit:
```
Press Ctrl+C
```

## Next Steps

1. Explore each dashboard page
2. Try different user roles
3. Run diagnostics on different vehicles
4. Monitor manufacturing quality patterns
5. Test security features
6. Review analytics and recommendations

## Tips & Tricks

### Best Viewing Experience
- Use a large monitor (1920x1080 or higher)
- Browser zoom at 100%
- Latest Chrome, Firefox, or Edge

### Color Coding System
- **Red**: Critical/High risk - immediate action needed
- **Yellow**: Medium/Low risk - schedule maintenance
- **Green**: Normal/Healthy - routine monitoring

### Dashboard Navigation
- Sidebar stays visible on all pages
- Active page highlighted with lighter background
- Click any navigation button to switch views

### Filters and Search
- Use checkboxes to filter by status
- Combine filters for advanced queries
- Search by vehicle ID for quick lookup

## Troubleshooting

### Issue: Port already in use
**Solution**: Change port
```bash
streamlit run src/dashboard_enhanced.py --server.port 8502
```

### Issue: Module not found
**Solution**: Reinstall dependencies
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: White screen or errors
**Solution**: Clear Streamlit cache
```bash
streamlit cache clear
```

### Issue: Table text not visible
**Solution**: Hard refresh browser (Ctrl+Shift+R)

### Issue: Sidebar disappeared
**Solution**: Refresh the page - JavaScript will restore it

## Getting Help

### Check Logs
Terminal running Streamlit shows all activity:
- Agent workflow steps
- Security detections
- Manufacturing notifications
- Errors and warnings

### Debug Mode
Add to top of `dashboard_enhanced.py`:
```python
import streamlit as st
st.write("Debug info:", st.session_state)
```

## What's Next?

Ready to dive deeper? Check out:
- `PROJECT_OVERVIEW.md` - Detailed architecture
- `SYSTEM_SUMMARY.md` - Component breakdown
- Code comments in each module

---

**Congratulations!** You're now ready to use AutoGuard Fleet Management System.

For advanced features and customization, explore the source code in the `src/` directory.
