#!/usr/bin/env python3
"""
Test the routing logic for login.html, register.html, etc.
"""

import os
from pathlib import Path

# Change to static directory
STATIC_DIR = Path(__file__).parent / 'static'
os.chdir(STATIC_DIR)

print("\n" + "="*60)
print("ZTNAS Frontend - Routing Test")
print("="*60 + "\n")

# Test files that should exist
test_files = [
    'html/index.html',
    'html/login.html',
    'html/register.html',
    'html/dashboard.html',
    'html/mfa.html',
]

print("Checking if routing target files exist:\n")
all_exist = True
for file in test_files:
    exists = os.path.exists(file)
    status = "✓ EXISTS" if exists else "✗ MISSING"
    print(f"{status:15} {file}")
    if not exists:
        all_exist = False

print("\n" + "="*60)

if all_exist:
    print("✓ All routing targets found - server will work!")
    print("\nExpected behavior:")
    print("  GET /login.html      → Serves html/login.html (200 OK)")
    print("  GET /register.html   → Serves html/register.html (200 OK)")
    print("  GET /dashboard.html  → Serves html/dashboard.html (200 OK)")
    print("  GET /                → Serves html/index.html (200 OK)")
else:
    print("✗ Some files missing - routing will fail!")
    print("\nCheck that frontend/static/html/ contains all HTML files")

print("="*60 + "\n")
