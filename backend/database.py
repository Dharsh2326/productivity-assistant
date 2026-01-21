import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Items table (unified for tasks, notes, reminders)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('task', 'note', 'reminder')),
                title TEXT NOT NULL,
                description TEXT,
                datetime TEXT,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')),
                tags TEXT,
                completed BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_item(self, item_data: Dict) -> int:
        """Create a new item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO items (type, title, description, datetime, priority, tags, completed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_data.get('type'),
            item_data.get('title'),
            item_data.get('description'),
            item_data.get('datetime'),
            item_data.get('priority', 'medium'),
            ','.join(item_data.get('tags', [])),
            item_data.get('completed', False),
            now,
            now
        ))
        
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return item_id
    
    def get_all_items(self, item_type: Optional[str] = None) -> List[Dict]:
        """Get all items, optionally filtered by type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if item_type:
            cursor.execute('SELECT * FROM items WHERE type = ? ORDER BY created_at DESC', (item_type,))
        else:
            cursor.execute('SELECT * FROM items ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_item_by_id(self, item_id: int) -> Optional[Dict]:
        """Get a single item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_item(self, item_id: int, updates: Dict) -> bool:
        """Update an item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates['updated_at'] = datetime.now().isoformat()
        
        # Build dynamic update query
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [item_id]
        
        cursor.execute(f'UPDATE items SET {set_clause} WHERE id = ?', values)
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0
    
    def delete_item(self, item_id: int) -> bool:
        """Delete an item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return rows_affected > 0