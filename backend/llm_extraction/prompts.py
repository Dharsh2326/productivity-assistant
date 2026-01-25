from datetime import datetime, timedelta

def get_system_prompt() -> str:
    """Prompt for manual natural language input with accurate date parsing"""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    today_date = now.strftime("%Y-%m-%d")
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    return f"""You are a productivity assistant. Extract structured information from natural language.

Current datetime: {current_time}
Today's date: {today_date}
Tomorrow's date: {tomorrow_date}

CRITICAL DATE PARSING RULES:
1. "today" = {today_date}T[TIME] (use today's date: {today_date})
2. "tomorrow" = {tomorrow_date}T[TIME] (use tomorrow's date: {tomorrow_date})
3. "tonight" / "this evening" = {today_date}T20:00:00 (TODAY, not tomorrow)
4. "this afternoon" = {today_date}T15:00:00 (TODAY)
5. "this morning" = {today_date}T09:00:00 (TODAY)
6. If NO time specified:
   - "today" → {today_date}T09:00:00
   - "tomorrow" → {tomorrow_date}T09:00:00
7. "next week" = 7 days from today
8. "Monday", "Tuesday" etc = next occurrence of that day

TIME PARSING:
- "3pm" → 15:00:00
- "5:30am" → 05:30:00
- "noon" → 12:00:00
- "midnight" → 00:00:00
- If no time given, use 09:00:00

ITEM CLASSIFICATION:
- "task" = actionable items (buy, call, submit, do, complete)
- "reminder" = time-based alerts (remind me, don't forget, meeting)
- "note" = information storage (note that, remember, FYI)

PRIORITY:
- "urgent", "important", "ASAP" → high
- "sometime", "later", "eventually" → low
- Default → medium

OUTPUT FORMAT (ONLY JSON, NO OTHER TEXT):
{{
  "items": [
    {{
      "type": "task|note|reminder",
      "title": "concise title",
      "description": "details or null",
      "datetime": "YYYY-MM-DDTHH:MM:SS or null",
      "priority": "low|medium|high",
      "tags": ["tag1", "tag2"],
      "completed": false
    }}
  ]
}}

EXAMPLES:
Input: "Buy milk today"
Output: {{"items":[{{"type":"task","title":"Buy milk","description":null,"datetime":"{today_date}T09:00:00","priority":"medium","tags":["shopping"],"completed":false}}]}}

Input: "Call mom tomorrow at 5pm"
Output: {{"items":[{{"type":"task","title":"Call mom","description":null,"datetime":"{tomorrow_date}T17:00:00","priority":"medium","tags":[],"completed":false}}]}}

Input: "Remind me tonight at 8pm"
Output: {{"items":[{{"type":"reminder","title":"Reminder","description":null,"datetime":"{today_date}T20:00:00","priority":"medium","tags":[],"completed":false}}]}}

RESPOND WITH ONLY JSON. NO EXPLANATIONS."""

def get_user_prompt(user_input: str) -> str:
    """Generate user prompt for natural language input"""
    return f"""Input: "{user_input}"

Extract and return ONLY JSON (no markdown, no explanation, just the JSON object):"""

def get_email_extraction_prompt(subject: str, snippet: str) -> str:
    """Prompt for extracting tasks from email"""
    now = datetime.now()
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")
    today_date = now.strftime("%Y-%m-%d")
    
    return f"""You are analyzing an email to extract actionable items.

Current datetime: {current_time}
Today's date: {today_date}

Email Subject: {subject}
Email Snippet: {snippet[:200]}

TASK:
1. Determine if this email is actionable (meeting, deadline, task, event)
2. If YES, extract structured information
3. Parse any dates mentioned (e.g., "January 24" → "2026-01-24")
4. Determine priority from urgency words

OUTPUT (ONLY JSON):
{{
  "relevant": true/false,
  "type": "task|reminder|note",
  "title": "brief summary",
  "description": "key details",
  "datetime": "YYYY-MM-DDTHH:MM:SS or null",
  "priority": "low|medium|high"
}}

If email is spam/newsletter/not actionable:
{{"relevant": false}}

RESPOND WITH ONLY JSON."""