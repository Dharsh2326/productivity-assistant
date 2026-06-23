from datetime import datetime, timedelta

def get_system_prompt() -> str:
    """Simple, clear prompt that works"""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return f"""Extract input to JSON. Today is {today_date}.

Classify item 'type' based on these rules:

1. type = "task"
   - Use for actionable work to complete.
   - Examples: "Buy groceries", "Finish DBMS assignment".

2. type = "reminder"
   - Use for reminders, calls, meetings, events, follow-ups.
   - Triggered by phrases such as: "remind me to", "call mom", "meeting", "appointment", "reminder".

3. type = "note"
   - Use for information to remember, study notes, observations, knowledge.
   - Examples: "Note: DBMS normalization has 3NF and BCNF", "Note: revise operating systems".

Time conversions (use 24-hour format):
1am=01:00, 2am=02:00, 3am=03:00, 4am=04:00, 5am=05:00, 6am=06:00
7am=07:00, 8am=08:00, 9am=09:00, 10am=10:00, 11am=11:00
12pm=12:00, 1pm=13:00, 2pm=14:00, 3pm=15:00, 4pm=16:00, 5pm=17:00
6pm=18:00, 7pm=19:00, 8pm=20:00, 9pm=21:00, 10pm=22:00, 11pm=23:00
No time specified = 09:00

Date: "today"={today_date}, "tomorrow"={tomorrow_date}, none={today_date}
Priority: "important/urgent"=high, "later/sometime"=low, else=medium

Output ONLY this JSON structure:
{{"items":[{{"type":"task/reminder/note","title":"TITLE","description":null,"datetime":"YYYY-MM-DDTHH:MM:SS","priority":"medium","tags":[],"completed":false}}]}}

Examples:
"Buy groceries at 7 PM" -> {{"items":[{{"type":"task","title":"Buy groceries","datetime":"{today_date}T19:00:00","priority":"medium","tags":[],"completed":false}}]}}
"Finish DBMS assignment" -> {{"items":[{{"type":"task","title":"Finish DBMS assignment","datetime":null,"priority":"medium","tags":[],"completed":false}}]}}
"remind me to buy milk 7pm" -> {{"items":[{{"type":"reminder","title":"Buy milk","datetime":"{today_date}T19:00:00","priority":"medium","tags":[],"completed":false}}]}}
"call mom tomorrow 5pm" -> {{"items":[{{"type":"reminder","title":"Call mom","datetime":"{tomorrow_date}T17:00:00","priority":"medium","tags":[],"completed":false}}]}}
"important meeting 3pm" -> {{"items":[{{"type":"reminder","title":"Important meeting","datetime":"{today_date}T15:00:00","priority":"high","tags":[],"completed":false}}]}}
"appointment at 10am" -> {{"items":[{{"type":"reminder","title":"Appointment","datetime":"{today_date}T10:00:00","priority":"medium","tags":[],"completed":false}}]}}
"Reminder" -> {{"items":[{{"type":"reminder","title":"Reminder","datetime":null,"priority":"medium","tags":[],"completed":false}}]}}
"Note: DBMS normalization has 3NF and BCNF" -> {{"items":[{{"type":"note","title":"DBMS normalization has 3NF and BCNF","datetime":null,"priority":"medium","tags":[],"completed":false}}]}}
"Note: revise operating systems" -> {{"items":[{{"type":"note","title":"Revise operating systems","datetime":null,"priority":"medium","tags":[],"completed":false}}]}}

CRITICAL: Respond ONLY with valid JSON. No explanation, no markdown, just the JSON object."""

def get_user_prompt(user_input: str) -> str:
    """Generate user prompt"""
    return f"""Task: "{user_input}"

JSON:"""

def get_email_extraction_prompt(subject: str, snippet: str) -> str:
    """Email extraction"""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    return f"""Extract task from email. Today={today_date}.

Subject: {subject}
Text: {snippet[:150]}

Time: 1pm=13:00, 2pm=14:00, 3pm=15:00, 4pm=16:00, 5pm=17:00, 6pm=18:00, 7pm=19:00, 8pm=20:00, 9pm=21:00
Priority: urgent=high, later=low, else=medium

JSON only:
{{"relevant":true,"type":"task","title":"...","datetime":"YYYY-MM-DDTHH:MM:SS","priority":"medium"}}"""