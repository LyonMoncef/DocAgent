import os
import shutil
from datetime import datetime
from pathlib import Path


class BackupManager:
    def __init__(self, backup_dir: str = "backups", max_versions: int = 5):
        self.backup_dir = Path(backup_dir)
        self.max_versions = max_versions
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _get_backup_subdir(self, filepath: str) -> Path:
        """Get backup subdirectory for a file (based on tool/filename)."""
        filename = Path(filepath).name
        subdir = self.backup_dir / filename.replace(".", "_")
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir

    def backup(self, filepath: str) -> str:
        """
        Create a backup of the file.
        Returns the backup path.
        """
        filepath = os.path.expanduser(filepath)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Cannot backup: {filepath} not found")

        subdir = self._get_backup_subdir(filepath)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        filename = Path(filepath).name
        backup_path = subdir / f"{filename}.{timestamp}"

        shutil.copy2(filepath, backup_path)
        self._prune_old_backups(subdir, filename)

        return str(backup_path)

    def _prune_old_backups(self, subdir: Path, filename: str):
        """Keep only the last N backups."""
        backups = sorted(subdir.glob(f"{filename}.*"), key=os.path.getmtime)
        while len(backups) > self.max_versions:
            oldest = backups.pop(0)
            oldest.unlink()

    def list_backups(self, filepath: str) -> list[str]:
        """List all backups for a file."""
        subdir = self._get_backup_subdir(filepath)
        filename = Path(filepath).name
        backups = sorted(subdir.glob(f"{filename}.*"), key=os.path.getmtime, reverse=True)
        return [str(b) for b in backups]

    def restore(self, backup_path: str, target_path: str) -> None:
        """Restore a backup to the target path."""
        backup_path = os.path.expanduser(backup_path)
        target_path = os.path.expanduser(target_path)

        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"Backup not found: {backup_path}")

        # Backup current before restoring
        if os.path.exists(target_path):
            self.backup(target_path)

        shutil.copy2(backup_path, target_path)
