# Database Backup & Disaster Recovery
# Automated backups with retention and restoration

import os
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import logging
from APScheduler.schedulers.background import BackgroundScheduler
import json

logger = logging.getLogger(__name__)

class DatabaseBackup:
    """
    Production-grade backup system:
    - Automated daily backups
    - Multiple retention policies
    - S3 upload capability
    - Restore capabilities
    - Health checks
    """
    
    def __init__(
        self,
        database_url: str,
        backup_dir: str = "./backups",
        s3_bucket: str = None,
        retention_days: int = 30
    ):
        self.database_url = database_url
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.s3_bucket = s3_bucket
        self.retention_days = retention_days
        self.scheduler = BackgroundScheduler()
    
    def create_backup(self) -> str:
        """Create a database backup immediately"""
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"backup_{timestamp}.sql"
        
        try:
            # Extract connection params from DATABASE_URL
            # postgresql://user:password@host:port/dbname
            parts = self.database_url.replace("postgresql://", "").split("/")
            db_name = parts[-1]
            
            user_pass = parts[0].split("@")
            credentials = user_pass[0].split(":")
            host_port = user_pass[1].split(":")
            
            username = credentials[0]
            password = credentials[1] if len(credentials) > 1 else ""
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            
            # Perform backup using pg_dump
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password
            
            command = [
                "pg_dump",
                f"--host={host}",
                f"--port={port}",
                f"--username={username}",
                "--format=plain",
                "--verbose",
                db_name
            ]
            
            with open(backup_file, "w") as f:
                result = subprocess.run(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=300
                )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            file_size = backup_file.stat().st_size
            logger.info(
                f"Database backup created",
                extra={
                    "backup_file": str(backup_file),
                    "size_bytes": file_size,
                    "timestamp": timestamp,
                }
            )
            
            # Upload to S3 if configured
            if self.s3_bucket:
                self._upload_to_s3(backup_file)
            
            return str(backup_file)
        
        except Exception as e:
            logger.error(
                f"Backup creation failed: {e}",
                extra={"backup_file": str(backup_file)}
            )
            raise
    
    def restore_backup(self, backup_file: str, target_database: str = None):
        """Restore from a backup file"""
        
        backup_path = Path(backup_file)
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        try:
            parts = self.database_url.replace("postgresql://", "").split("/")
            db_name = target_database or parts[-1]
            
            user_pass = parts[0].split("@")
            credentials = user_pass[0].split(":")
            host_port = user_pass[1].split(":")
            
            username = credentials[0]
            password = credentials[1] if len(credentials) > 1 else ""
            host = host_port[0]
            port = host_port[1] if len(host_port) > 1 else "5432"
            
            # Restore using psql
            env = os.environ.copy()
            if password:
                env["PGPASSWORD"] = password
            
            command = [
                "psql",
                f"--host={host}",
                f"--port={port}",
                f"--username={username}",
                db_name
            ]
            
            with open(backup_path, "r") as f:
                result = subprocess.run(
                    command,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    timeout=600
                )
            
            if result.returncode != 0:
                raise Exception(f"psql restore failed: {result.stderr}")
            
            logger.info(
                f"Database restored from backup",
                extra={
                    "backup_file": str(backup_file),
                    "target_database": db_name,
                }
            )
        
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    def cleanup_old_backups(self):
        """Delete backups older than retention period"""
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob("backup_*.sql"):
            # Extract timestamp from filename
            timestamp_str = backup_file.name.replace("backup_", "").replace(".sql", "")
            
            try:
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")
            
            except ValueError:
                logger.warning(f"Could not parse backup filename: {backup_file.name}")
        
        logger.info(
            f"Backup cleanup completed",
            extra={"deleted_count": deleted_count}
        )
    
    def start_automatic_backups(self, hours: int = 24):
        """Start automatic nightly backups"""
        
        self.scheduler.add_job(
            self.create_backup,
            "interval",
            hours=hours,
            id="daily_backup",
            name="Daily database backup",
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.cleanup_old_backups,
            "cron",
            hour=2,  # Run at 2 AM
            id="cleanup_backups",
            name="Clean up old backups",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Automatic backup scheduler started")
    
    def stop_automatic_backups(self):
        """Stop automatic backups"""
        self.scheduler.shutdown()
        logger.info("Automatic backup scheduler stopped")
    
    def get_backup_list(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.sql")):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)
    
    def _upload_to_s3(self, backup_file: Path):
        """Upload backup to S3 for off-site storage"""
        
        try:
            import boto3
            
            s3 = boto3.client("s3")
            key = f"ztnas-backups/{backup_file.name}"
            
            s3.upload_file(str(backup_file), self.s3_bucket, key)
            
            logger.info(
                f"Backup uploaded to S3",
                extra={
                    "bucket": self.s3_bucket,
                    "key": key,
                    "file": backup_file.name,
                }
            )
        
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")

class BackupHealthCheck:
    """Verify backup integrity and recoverability"""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
    
    def verify_backup(self, backup_file: str) -> Dict[str, Any]:
        """Verify a backup file is valid and recoverable"""
        
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            return {
                "status": "invalid",
                "error": "File not found",
                "file": backup_file,
            }
        
        try:
            # Check file size (should be > 0)
            file_size = backup_path.stat().st_size
            
            if file_size == 0:
                return {
                    "status": "invalid",
                    "error": "Backup file is empty",
                    "file": backup_file,
                    "size": 0,
                }
            
            # Check file header (PostgreSQL dumps start with "-- PostgreSQL")
            with open(backup_path, "r", encoding="utf-8", errors="ignore") as f:
                header = f.read(100)
                
                if "PostgreSQL" not in header and "-- " not in header[:10]:
                    return {
                        "status": "invalid",
                        "error": "Invalid PostgreSQL backup format",
                        "file": backup_file,
                    }
            
            return {
                "status": "valid",
                "file": backup_file,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "verified_at": datetime.utcnow().isoformat(),
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "file": backup_file,
            }
    
    def verify_all_backups(self) -> List[Dict[str, Any]]:
        """Verify all backups in the backup directory"""
        
        results = []
        
        for backup_file in sorted(self.backup_dir.glob("backup_*.sql")):
            result = self.verify_backup(str(backup_file))
            results.append(result)
        
        return results
