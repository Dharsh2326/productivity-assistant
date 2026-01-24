from datetime import datetime

def get_system_prompt() -> str:
    """Prompt for manual natural language input"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""You are a productivity assistant. Extract structured information from natural language.

Current datetime: {current_time}

RULES:
1. ALWAYS respond with ONLY valid JSON, no other text
2. Classify as: "task", "note", or "reminder"
3. Extract: title, description, datetime, priority, tags

DATETIME PARSING:
- "tomorrow" → next day 09:00
- "next week" → 7 days later 09:00
- "Monday" → next Monday 09:00
- "3pm" → 15:00, "5:30am" → 05:30
- Format: YYYY-MM-DDTHH:MM:SS

PRIORITY:
- "urgent", "important" → high
- "sometime", "later" → low
- Default → medium

JSON FORMAT (respond with ONLY this, no explanation):
{{
  "items": [
    {{
      "type": "task",
      "title": "short title here",
      "description": "details or null",
      "datetime": "2026-01-22T15:00:00 or null",
      "priority": "medium",
      "tags": ["tag1", "tag2"],
      "completed": false
    }}
  ]
}}

Multiple items = multiple objects in array."""

def get_user_prompt(user_input: str) -> str:
    return f"""Input: "{user_input}"

Extract and return ONLY JSON (no explanation):"""

def get_email_extraction_prompt(subject: str, snippet: str) -> str:
    """Prompt for extracting tasks from email"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return f"""You are analyzing an email to extract actionable items.

Current datetime: {current_time}

Email Subject: {subject}
Email Snippet: {snippet[:200]}

Extract:
1. Is this email actionable? (meeting, deadline, seminar, action item)
2. If YES, extract:
   - Type: "task" (actionable item) or "reminder" (meeting/event)
   - Title: Brief, clear summary
   - DateTime: When it's due/scheduled (parse from text)
   - Priority: Based on urgency words
   - Refined description

Return ONLY JSON:
{{
  "relevant": true/false,
  "type": "task|reminder|note",
  "title": "extracted title",
  "description": "key details",
  "datetime": "YYYY-MM-DDTHH:MM:SS or null",
  "priority": "low|medium|high"
}}

If email is spam/newsletter/not actionable, return:
{{"relevant": false}}
"""