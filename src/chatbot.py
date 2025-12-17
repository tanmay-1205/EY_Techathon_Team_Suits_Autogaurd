"""
AI Chatbot for Customer Service
Handles conversations with vehicle owners about diagnostics and service booking.
"""

import os
from typing import List, Dict

# Check if OpenAI is available, otherwise use a fallback
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class CustomerServiceBot:
    """
    AI chatbot for handling customer service conversations.
    Uses GPT-4 if available, otherwise falls back to rule-based responses.
    """
    
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.use_llm = True
        else:
            self.client = None
            self.use_llm = False
            print("[Chatbot] Running in fallback mode (no OpenAI API key found)")
    
    def generate_initial_alert(self, diagnosis_report: dict, vehicle_id: str, owner_name: str) -> str:
        """
        Generates the initial alert message sent to the customer.
        """
        severity = diagnosis_report.get('status', 'Unknown')
        issues = diagnosis_report.get('issues', [])
        recommendation = diagnosis_report.get('recommendation', 'Please contact service.')
        
        if severity == "Critical":
            urgency = "URGENT"
            greeting = f"⚠️ CRITICAL ALERT for {owner_name}"
        elif severity == "High":
            urgency = "IMPORTANT"
            greeting = f"⚠️ Important Notice for {owner_name}"
        else:
            urgency = "NOTICE"
            greeting = f"Hello {owner_name}"
        
        issues_text = "\n".join([f"• {issue}" for issue in issues]) if issues else "General maintenance required"
        
        message = f"""{greeting},

We've detected the following issue(s) with your vehicle ({vehicle_id}):

{issues_text}

Recommendation: {recommendation}

Please reply to schedule a service appointment or if you have any questions.

- AutoGuard Support Team"""
        
        return message
    
    def chat(self, user_message: str, context: dict = None) -> str:
        """
        Generate a response to the user's message.
        
        Args:
            user_message: The user's input message
            context: Additional context (vehicle info, diagnosis, etc.)
        
        Returns:
            Bot's response message
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        if self.use_llm:
            response = self._generate_llm_response(user_message, context)
        else:
            response = self._generate_fallback_response(user_message, context)
        
        # Add bot response to history
        self.conversation_history.append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def _generate_llm_response(self, user_message: str, context: dict) -> str:
        """Generate response using OpenAI GPT."""
        try:
            # Build system prompt with context
            system_prompt = """You are a helpful customer service agent for AutoGuard, an automotive fleet management company.
You help vehicle owners understand diagnostic issues and schedule service appointments.

Be professional, empathetic, and concise. Always prioritize safety.
If asked to schedule service, confirm the booking and provide a time slot.
"""
            
            if context:
                vehicle_id = context.get('vehicle_id', 'Unknown')
                diagnosis = context.get('diagnosis_report', {})
                severity = diagnosis.get('status', 'Normal')
                
                system_prompt += f"\n\nCurrent Context:\n- Vehicle ID: {vehicle_id}\n- Severity: {severity}"
                
                if diagnosis.get('issues'):
                    system_prompt += f"\n- Issues: {', '.join(diagnosis['issues'])}"
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(self.conversation_history[-10:])  # Last 10 messages for context
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"[Chatbot] LLM Error: {e}")
            return self._generate_fallback_response(user_message, context)
    
    def _generate_fallback_response(self, user_message: str, context: dict) -> str:
        """Generate rule-based response when LLM is unavailable."""
        msg_lower = user_message.lower()
        
        # Service booking keywords
        if any(word in msg_lower for word in ['book', 'schedule', 'appointment', 'service', 'fix']):
            return ("I've scheduled a service appointment for you tomorrow at 10:00 AM. "
                   "You'll receive a confirmation SMS shortly. Is there anything else I can help with?")
        
        # Question about issue
        elif any(word in msg_lower for word in ['what', 'why', 'how', 'explain', 'issue', 'problem']):
            if context and context.get('diagnosis_report'):
                issues = context['diagnosis_report'].get('issues', [])
                if issues:
                    return (f"The diagnostic system detected: {issues[0]}. "
                           f"This requires immediate attention to ensure your safety. "
                           f"Would you like me to schedule a service appointment?")
            return "Our diagnostic system has flagged a potential issue with your vehicle. I recommend scheduling a service check. Would you like me to book an appointment?"
        
        # Cost/price inquiry
        elif any(word in msg_lower for word in ['cost', 'price', 'how much', 'charge', 'fee']):
            return ("Service costs vary depending on the repair needed. Our technician will provide a detailed quote "
                   "after inspection. The diagnostic check is complimentary. Would you like to proceed with booking?")
        
        # Urgency/time questions
        elif any(word in msg_lower for word in ['urgent', 'now', 'immediately', 'wait', 'how long']):
            if context and context.get('diagnosis_report', {}).get('status') == 'Critical':
                return ("This is a critical safety issue. We strongly advise NOT driving the vehicle. "
                       "I can arrange emergency roadside assistance or towing. Should I proceed?")
            return "We have slots available as early as tomorrow morning. Would you like me to book the earliest available time?"
        
        # Thanks/acknowledgment
        elif any(word in msg_lower for word in ['thank', 'thanks', 'ok', 'yes', 'sure', 'great']):
            return "You're welcome! Your appointment is confirmed. We'll send you a reminder 24 hours before. Drive safely!"
        
        # Cancellation
        elif any(word in msg_lower for word in ['cancel', 'no', 'later', 'not now']):
            return "No problem. Feel free to reach out whenever you're ready. Stay safe!"
        
        # Default response
        else:
            return ("I'm here to help with your vehicle service needs. Would you like to:\n"
                   "1. Schedule a service appointment\n"
                   "2. Learn more about the detected issue\n"
                   "3. Speak with a technician\n"
                   "Please let me know how I can assist you.")
    
    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []


# Singleton instance
_bot_instance = None

def get_chatbot() -> CustomerServiceBot:
    """Get or create the chatbot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = CustomerServiceBot()
    return _bot_instance
