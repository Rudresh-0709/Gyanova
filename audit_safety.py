"""
Safety wrapper for audit Excel modifications.

RULE: Every script that modifies the audit Excel MUST:
  1. Import this module
  2. Call backup_audit() BEFORE making any changes
  3. Call commit_audit(message) AFTER saving successfully

This creates both a timestamped file backup AND a git commit,
so you can always recover any previous version.
"""
import os
import shutil
from datetime import datetime

EXCEL_PATH = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\GyML Content Block Variant Audit.xlsx'
BACKUP_DIR = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app\audit_backups'
REPO_ROOT = r'd:\DATA\Desktop\AI_TUTOR\ai-teacher-app'


def backup_audit() -> str:
    """
    Create a timestamped backup of the audit Excel.
    Returns the backup file path.
    Call this BEFORE any modifications.
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"audit_backup_{timestamp}.xlsx"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    shutil.copy2(EXCEL_PATH, backup_path)
    print(f"[BACKUP] Saved: {backup_path}")
    return backup_path


def commit_audit(message: str = "update audit Excel"):
    """
    Git-commit the audit Excel after modifications.
    Call this AFTER saving the workbook.
    """
    import subprocess
    subprocess.run(
        ["git", "add", "GyML Content Block Variant Audit.xlsx"],
        cwd=REPO_ROOT, capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", f"audit: {message}"],
        cwd=REPO_ROOT, capture_output=True,
    )
    print(f"[GIT] Committed: {message}")


def list_backups():
    """List all available backups."""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found.")
        return []
    backups = sorted(os.listdir(BACKUP_DIR), reverse=True)
    for b in backups:
        full = os.path.join(BACKUP_DIR, b)
        size = os.path.getsize(full)
        print(f"  {b}  ({size:,} bytes)")
    return backups


def restore_backup(backup_name: str):
    """Restore a specific backup to the main Excel file."""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if not os.path.exists(backup_path):
        print(f"[ERROR] Backup not found: {backup_path}")
        return False
    shutil.copy2(backup_path, EXCEL_PATH)
    print(f"[RESTORED] {backup_name} -> {EXCEL_PATH}")
    return True
