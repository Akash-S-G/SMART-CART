from __future__ import annotations

import sys
from pathlib import Path
from sqlalchemy import text

sys.path[:0] = [str(Path(__file__).resolve().parent.parent)]

from app.db.database import SessionLocal

def main():
    print(">>> SmartCart AI - Database Migration for Orders Table")
    db = SessionLocal()
    try:
        # Add columns to orders table
        alter_statements = [
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_number VARCHAR(100);",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS estimated_delivery TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipped_at TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_address TEXT;"
        ]
        
        for stmt in alter_statements:
            print(f"Executing: {stmt}")
            db.execute(text(stmt))
        
        db.commit()
        print("[done] Migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Migration failed: {e}")
        return 1
    finally:
        db.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
