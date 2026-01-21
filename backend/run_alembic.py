#!/usr/bin/env python
"""
Helper script to run Alembic commands.
"""
import sys
import os
from alembic import command
from alembic.config import Config

# Ensure we're in the backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create versions directory if it doesn't exist
os.makedirs("alembic/versions", exist_ok=True)

# Load Alembic configuration
alembic_cfg = Config("alembic.ini")

if len(sys.argv) > 1:
    if sys.argv[1] == "autogenerate":
        message = sys.argv[2] if len(sys.argv) > 2 else "auto migration"
        print(f"Generating migration: {message}")
        command.revision(alembic_cfg, autogenerate=True, message=message)
    elif sys.argv[1] == "upgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "head"
        print(f"Upgrading database to: {target}")
        command.upgrade(alembic_cfg, target)
    elif sys.argv[1] == "downgrade":
        target = sys.argv[2] if len(sys.argv) > 2 else "-1"
        print(f"Downgrading database by: {target}")
        command.downgrade(alembic_cfg, target)
    else:
        print("Usage: python run_alembic.py [autogenerate|upgrade|downgrade] [message/target]")
else:
    print("Usage: python run_alembic.py [autogenerate|upgrade|downgrade] [message/target]")
