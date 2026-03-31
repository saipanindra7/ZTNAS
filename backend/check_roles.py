"""
Check what roles exist in the database
"""
import sys
import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from app.models import Role

db = SessionLocal()

try:
    roles = db.query(Role).all()
    print("Roles in database:")
    for role in roles:
        print(f"  ID: {role.id}, Name: '{role.name}', Description: {role.description}")
    
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    db.close()
