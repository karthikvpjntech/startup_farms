import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / "agri_smart.db"
print(f"Connecting to database at {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_columns(table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]

# Check if tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables present: {tables}")

if 'tool_interests' in tables:
    ti_cols = get_columns('tool_interests')
    print('tool_interests columns:', ti_cols)
    if 'category' not in ti_cols:
        print('Adding category to tool_interests...')
        cursor.execute("ALTER TABLE tool_interests ADD COLUMN category VARCHAR(50) DEFAULT 'MACHINERY'")
        conn.commit()
        print('Successfully added category to tool_interests.')
    else:
        print('tool_interests.category already exists.')

    for col in ['notify_in_app', 'notify_sms', 'notify_sound']:
        if col not in ti_cols:
            print(f'Adding {col} to tool_interests...')
            cursor.execute(f"ALTER TABLE tool_interests ADD COLUMN {col} BOOLEAN DEFAULT 1")
            conn.commit()
            print(f'Successfully added {col} to tool_interests.')
        else:
            print(f'tool_interests.{col} already exists.')

if 'discovered_tool_locations' in tables:
    dtl_cols = get_columns('discovered_tool_locations')
    print('discovered_tool_locations columns:', dtl_cols)
    if 'products_available' not in dtl_cols:
        print('Adding products_available to discovered_tool_locations...')
        cursor.execute("ALTER TABLE discovered_tool_locations ADD COLUMN products_available JSON")
        conn.commit()
        print('Successfully added products_available to discovered_tool_locations.')
    else:
        print('discovered_tool_locations.products_available already exists.')

conn.close()
print("Migration completed successfully!")

