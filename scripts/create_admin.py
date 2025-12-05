#!/usr/bin/env python
"""
Create or update an admin user for the TasteBook app.
Usage:
  python scripts/create_admin.py --username admin --password 'Secret123!'
  python scripts/create_admin.py --username admin          # generates a random password
  python scripts/create_admin.py --username admin --reset --password 'NewPass!'

Note: If an admin user already exists and --reset is not provided, the script will report and not change the password.
"""
import argparse
import secrets
import string
import os
import sys
# Ensure project root is on sys.path so imports like `from app import app` work when
# this script is executed from the scripts/ directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models import User


def gen_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    parser = argparse.ArgumentParser(description='Create or update an admin user')
    parser.add_argument('--username', '-u', required=True, help='Admin username')
    parser.add_argument('--email', '-e', help='Admin email (optional)')
    parser.add_argument('--password', '-p', help='Password to set (optional)')
    parser.add_argument('--reset', action='store_true', help='Reset password if user exists')
    args = parser.parse_args()

    username = args.username.strip()
    email = args.email.strip() if args.email else f"{username}@example.local"
    password = args.password

    with app.app_context():
        existing = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing:
            if existing.is_admin:
                if args.reset:
                    if not password:
                        password = gen_password()
                    existing.set_password(password)
                    db.session.commit()
                    print(f"Updated admin '{existing.username}'. New password: {password}")
                    return
                else:
                    print(f"Admin user '{existing.username}' already exists. Password cannot be retrieved. Use --reset to set a new password.")
                    return
            else:
                # Promote to admin
                if not password:
                    password = gen_password()
                existing.is_admin = True
                existing.set_password(password)
                existing.email = email
                db.session.commit()
                print(f"User '{existing.username}' promoted to admin. Password: {password}")
                return

        # Create new admin
        if not password:
            password = gen_password()
        new = User(username=username, email=email, is_admin=True)
        new.set_password(password)
        db.session.add(new)
        db.session.commit()
        print(f"Created new admin user '{username}' with password: {password}")


if __name__ == '__main__':
    main()
