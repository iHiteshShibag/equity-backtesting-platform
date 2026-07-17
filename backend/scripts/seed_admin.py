#!/usr/bin/env python
"""
Create (or update the password of) the bootstrap admin account, from
Settings.ADMIN_EMAIL / Settings.ADMIN_PASSWORD (see backend/.env).
Safe to re-run: Run: python scripts/seed_admin.py
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db.session import SessionLocal
from app.modules.auth.models import User
from app.modules.auth.security import hash_password
from app.modules.orgs.models import Organization  # noqa: F401


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        if user is None:
            user = User(email=settings.ADMIN_EMAIL, full_name="Admin", role="admin")
            db.add(user)
            print(f"Creating admin user {settings.ADMIN_EMAIL!r}")
        else:
            print(f"Admin user {settings.ADMIN_EMAIL!r} already exists — updating password")

        user.hashed_password = hash_password(settings.ADMIN_PASSWORD)
        user.role = "admin"
        user.is_active = True
        db.commit()
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
