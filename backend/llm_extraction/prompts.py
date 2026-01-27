from datetime import datetime, timedelta

def get_system_prompt() -> str:
    """Balanced prompt - fast but with priority detection"""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return f"""Extract task as JSON. Today={today_date}, Tomorrow={tomorrow_date}.

DATES:
"today"→{today_date}, "tomorrow"→{tomorrow_date}, "tonight"→{today_date}T20:00
No date specified→{today_date}

TIMES:
"12pm"→12:00, "3pm"→15:00, "5pm"→17:00, "6pm"→18:00
No time→09:00

PRIORITY (important!):
HIGH: "important", "urgent", "ASAP", "critical", "deadline"
LOW: "later", "sometime", "eventually", "maybe", "when free"
MEDIUM: everything else

TYPE:
"task" for actions, "reminder" for time alerts, "note" for info

JSON format:
{{"items":[{{"type":"task|reminder|note","title":"...","description":null,"datetime":"YYYY-MM-DDTHH:MM:SS or null","priority":"low|medium|high","tags":[],"completed":false}}]}}

Examples:
"lunch at 12pm"→{{"items":[{{"type":"task","title":"Lunch","datetime":"{today_date}T12:00:00","priority":"medium","tags":[],"completed":false}}]}}
"important meeting at 6pm"→{{"items":[{{"type":"task","title":"Important meeting","datetime":"{today_date}T18:00:00","priority":"high","tags":[],"completed":false}}]}}
"read book later"→{{"items":[{{"type":"task","title":"Read book","datetime":null,"priority":"low","tags":[],"completed":false}}]}}
"watch videos"→{{"items":[{{"type":"task","title":"Watch videos","datetime":"{today_date}T09:00:00","priority":"medium","tags":[],"completed":false}}]}}"""

def get_user_prompt(user_input: str) -> str:
    """Generate user prompt for natural language input"""
    return f"""Input: "{user_input}"

JSON only:"""

def get_email_extraction_prompt(subject: str, snippet: str) -> str:
    """Prompt for extracting tasks from email"""
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    
    return f"""Email to task. Today={today_date}.

Subject: {subject}
Text: {snippet[:150]}

Priority: "important/urgent"→high, "later/sometime"→low, else→medium

JSON:
{{"relevant":true/false,"type":"task|reminder","title":"...","datetime":"YYYY-MM-DDTHH:MM:SS or null","priority":"low|medium|high"}}

If spam: {{"relevant":false}}"""