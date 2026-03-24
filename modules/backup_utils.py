
import os
import shutil
import datetime
import sqlite3
import streamlit as st

DB_FILE = "box_costing.db"

from database import SessionLocal
from models import Settings

def get_backup_dir():
    db = SessionLocal()
    setting = db.query(Settings).filter(Settings.key == "backup_path").first()
    db.close()
    if setting and setting.value:
        return setting.value
    return "backups"

def ensure_backup_dir():
    path = get_backup_dir()
    if not os.path.exists(path):
        os.makedirs(path)

def create_backup():
    ensure_backup_dir()
    path = get_backup_dir()
    timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M")
    backup_filename = f"boxDB_{timestamp}.db"
    backup_path = os.path.join(path, backup_filename)
    
    try:
        source_conn = sqlite3.connect(DB_FILE)
        dest_conn = sqlite3.connect(backup_path)
        source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()
        return True, backup_path
    except Exception as e:
        return False, str(e)

def list_backups():
    path = get_backup_dir()
    if not os.path.exists(path):
        return []
    files = [f for f in os.listdir(path) if f.startswith("boxDB_") and f.endswith(".db")]
    files.sort(reverse=True) # Newest first
    return files

def restore_backup(backup_filename):
    path = get_backup_dir()
    backup_path = os.path.join(path, backup_filename)
    if not os.path.exists(backup_path):
        return False, "Backup file not found."
    
    try:
        dest_conn = sqlite3.connect(DB_FILE)
        source_conn = sqlite3.connect(backup_path)
        source_conn.backup(dest_conn)
        source_conn.close()
        dest_conn.close()
        return True, "Database restored successfully."
    except Exception as e:
        return False, str(e)

def delete_backup(backup_filename):
    path = get_backup_dir()
    backup_path = os.path.join(path, backup_filename)
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return True
    return False

def auto_backup_check():
    """Simple check to perform a daily backup on first run of the day"""
    ensure_backup_dir()
    today = datetime.datetime.now().strftime("%Y_%m_%d")
    # Check if a backup for today already exists
    backups = list_backups()
    if not any(today in f for f in backups):
        create_backup()
