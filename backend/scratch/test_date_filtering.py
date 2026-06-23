import sys
import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database import Database

def run_test():
    print("=" * 60)
    print("RUNNING DATE FILTERING VERIFICATION TEST")
    print("=" * 60)
    
    db_path = "data/productivity.db"
    print(f"Database path: {db_path}")
    db = Database(db_path)
    
    # Calculate dates relative to today
    now = datetime.now()
    today_date = now.strftime("%Y-%m-%d")
    tomorrow_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    next_week_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
    
    task_a_dt = f"{today_date}T19:00:00"
    task_b_dt = f"{tomorrow_date}T09:00:00"
    task_c_dt = f"{next_week_date}T09:00:00"
    
    print(f"Today's Date: {today_date}")
    print(f"Tomorrow's Date: {tomorrow_date}")
    print(f"Next Week's Date: {next_week_date}")
    print("-" * 60)
    
    # 1. Clean up old test data if exists
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE title IN ('Task A', 'Task B', 'Task C', 'Task D')")
    conn.commit()
    conn.close()
    
    # 2. Insert test items
    # Task A: Today 7 PM
    item_a_id = db.create_item({
        'type': 'task',
        'title': 'Task A',
        'description': 'Today 7 PM',
        'datetime': task_a_dt,
        'priority': 'medium',
        'tags': ['test'],
        'completed': False
    })
    
    # Task B: Tomorrow 9 AM
    item_b_id = db.create_item({
        'type': 'task',
        'title': 'Task B',
        'description': 'Tomorrow 9 AM',
        'datetime': task_b_dt,
        'priority': 'medium',
        'tags': ['test'],
        'completed': False
    })
    
    # Task C: Next week
    item_c_id = db.create_item({
        'type': 'task',
        'title': 'Task C',
        'description': 'Next week',
        'datetime': task_c_dt,
        'priority': 'medium',
        'tags': ['test'],
        'completed': False
    })
    
    # Task D: No datetime
    item_d_id = db.create_item({
        'type': 'note',
        'title': 'Task D',
        'description': 'No datetime',
        'datetime': None,
        'priority': 'medium',
        'tags': ['test'],
        'completed': False
    })
    
    print("Inserted Test Tasks:")
    print(f"  Task A (ID {item_a_id}): Today 7 PM -> {task_a_dt}")
    print(f"  Task B (ID {item_b_id}): Tomorrow 9 AM -> {task_b_dt}")
    print(f"  Task C (ID {item_c_id}): Next week -> {task_c_dt}")
    print(f"  Task D (ID {item_d_id}): No datetime -> None (Type: Note)")
    print("-" * 60)
    
    # 3. Simulate date-based grouping logic
    all_items = db.get_all_items()
    
    local_tz = datetime.now().astimezone().tzinfo
    today = datetime.now().date()
    tomorrow = (datetime.now() + timedelta(days=1)).date()
    
    grouped = {
        'today': [],
        'tomorrow': [],
        'upcoming': []
    }
    
    # Track assignments to verify Task D/notes behaviors
    notes = [item for item in all_items if item['type'] == 'note' and item['title'] == 'Task D']
    
    for item in all_items:
        # Only check our test items to keep output clean
        if item['title'] not in ('Task A', 'Task B', 'Task C', 'Task D'):
            continue
            
        dt_str = item.get('datetime')
        if not dt_str:
            continue
            
        try:
            dt = datetime.fromisoformat(dt_str)
            if dt.tzinfo is not None:
                dt = dt.astimezone(local_tz)
            item_date = dt.date()
            
            if item_date == today:
                grouped['today'].append(item)
            elif item_date == tomorrow:
                grouped['tomorrow'].append(item)
                
            if item_date > today:
                grouped['upcoming'].append(item)
        except Exception as e:
            print(f"Error parsing date: {e}")
            
    print("TEST RESULTS:")
    print("-" * 60)
    print("Today View:")
    for item in grouped['today']:
        print(f"  - ID {item['id']}: {item['title']} | Date: {item['datetime']}")
    if not grouped['today']:
        print("  (Empty)")
        
    print("\nTomorrow View:")
    for item in grouped['tomorrow']:
        print(f"  - ID {item['id']}: {item['title']} | Date: {item['datetime']}")
    if not grouped['tomorrow']:
        print("  (Empty)")
        
    print("\nUpcoming View:")
    for item in grouped['upcoming']:
        print(f"  - ID {item['id']}: {item['title']} | Date: {item['datetime']}")
    if not grouped['upcoming']:
        print("  (Empty)")
        
    print("\nNotes View (Task D Check):")
    for item in notes:
        print(f"  - ID {item['id']}: {item['title']} | Date: {item['datetime']} | Type: {item['type']}")
    if not notes:
        print("  (Empty)")
    print("=" * 60)
    
    # Assert correctness
    today_titles = [i['title'] for i in grouped['today']]
    tomorrow_titles = [i['title'] for i in grouped['tomorrow']]
    upcoming_titles = [i['title'] for i in grouped['upcoming']]
    
    assert today_titles == ['Task A'], f"Expected Today View to contain ['Task A'], got {today_titles}"
    assert tomorrow_titles == ['Task B'], f"Expected Tomorrow View to contain ['Task B'], got {tomorrow_titles}"
    assert set(upcoming_titles) == {'Task B', 'Task C'}, f"Expected Upcoming View to contain ['Task B', 'Task C'], got {upcoming_titles}"
    assert all(item['title'] != 'Task D' for item in grouped['today'] + grouped['tomorrow'] + grouped['upcoming']), "Expected Task D to be excluded from all date buckets"
    
    print("\nALL VERIFICATION CHECKS PASSED SUCCESSFULLY! \n")

if __name__ == "__main__":
    run_test()
