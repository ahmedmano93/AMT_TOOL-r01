# MTK Update Manager
# Handles updates and database management

import os
import json
import logging
import requests
from typing import Dict, Optional
from datetime import datetime

class MTKUpdateManager:
    """Manages updates and protection database."""
    
    def __init__(self) -> None:
        """Initialize update manager."""
        self.database_path = "./MTK_TOOL/DATABASE"
        self.protection_db_file = f"{self.database_path}/protection_db.json"
        self.last_update_file = f"{self.database_path}/last_update.json"
        
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database structure."""
        os.makedirs(self.database_path, exist_ok=True)
        
        if not os.path.exists(self.protection_db_file):
            self._create_default_db()
            
        if not os.path.exists(self.last_update_file):
            self._create_update_info()
    
    def _internet_available(self) -> bool:
        """Check if internet connection is available."""
        import socket
        try:
            # connect to one of the root DNS servers
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False

    def check_for_updates(self) -> Dict:
        """Check for available updates, with improved error handling."""
        try:
            if not self._internet_available():
                return {
                    "update_available": False,
                    "error": "No internet connection"
                }
            current_version = self._get_current_version()
            latest_version = self._fetch_latest_version()
            if latest_version > current_version:
                return {
                    "update_available": True,
                    "current_version": current_version,
                    "latest_version": latest_version
                }
            return {
                "update_available": False,
                "current_version": current_version
            }
        except Exception as e:
            logging.error(f"Update check failed: {str(e)}")
            return {
                "update_available": False,
                "error": str(e)
            }
    
    def update_protection_db(self) -> Dict:
        """Update protection database, with improved error handling."""
        try:
            if not self._internet_available():
                return {
                    "status": "error",
                    "message": "No internet connection"
                }
            new_data = self._fetch_protection_data()
            if not new_data:
                return {
                    "status": "error",
                    "message": "Failed to fetch protection data"
                }
            self._backup_current_db()
            with open(self.protection_db_file, 'w') as f:
                json.dump(new_data, f, indent=4)
            self._update_timestamp()
            return {
                "status": "success",
                "message": "Protection database updated successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database update failed: {str(e)}"
            }
    
    def get_protection_info(self, device_model: str) -> Dict:
        """Get protection information for specific device."""
        try:
            with open(self.protection_db_file, 'r') as f:
                db = json.load(f)
            
            device_info = db.get(device_model, {})
            
            if not device_info:
                return {
                    "status": "error",
                    "message": "Device not found in database"
                }
            
            return {
                "status": "success",
                "protection_info": device_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get protection info: {str(e)}"
            }
    
    def _create_default_db(self) -> None:
        """Create default protection database."""
        default_db = {
            "database_version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "devices": {}
        }
        
        with open(self.protection_db_file, 'w') as f:
            json.dump(default_db, f, indent=4)
    
    def _create_update_info(self) -> None:
        """Create update information file."""
        update_info = {
            "last_check": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "current_version": "1.0.0"
        }
        
        with open(self.last_update_file, 'w') as f:
            json.dump(update_info, f, indent=4)
    
    def _get_current_version(self) -> str:
        """Get current database version."""
        with open(self.last_update_file, 'r') as f:
            info = json.load(f)
        return info.get("current_version", "1.0.0")
    
    def _fetch_latest_version(self) -> str:
        """Fetch latest available version."""
        # Implement version check logic
        return "1.0.0"
    
    def _fetch_protection_data(self) -> Optional[Dict]:
        """Fetch new protection data."""
        # Implement protection data fetch logic
        return None
    
    def _backup_current_db(self) -> None:
        """Backup current database."""
        if os.path.exists(self.protection_db_file):
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"{self.database_path}/protection_db_backup_{backup_time}.json"
            
            with open(self.protection_db_file, 'r') as src, open(backup_file, 'w') as dst:
                json.dump(json.load(src), dst, indent=4)
    
    def _update_timestamp(self) -> None:
        """Update last update timestamp."""
        with open(self.last_update_file, 'r') as f:
            info = json.load(f)
        
        info["last_update"] = datetime.now().isoformat()
        
        with open(self.last_update_file, 'w') as f:
            json.dump(info, f, indent=4)

    def self_test(self) -> Dict:
        """
        Run a self-test for the update manager.
        Returns a dict with the results of all critical checks.
        """
        results = {
            "database_exists": os.path.exists(self.protection_db_file),
            "last_update_exists": os.path.exists(self.last_update_file),
            "internet_available": self._internet_available()
        }
        # Try reading the database file
        try:
            with open(self.protection_db_file, 'r') as f:
                db = json.load(f)
            results["db_readable"] = True
        except Exception:
            results["db_readable"] = False
        # Try reading the update info file
        try:
            with open(self.last_update_file, 'r') as f:
                info = json.load(f)
            results["update_info_readable"] = True
        except Exception:
            results["update_info_readable"] = False
        results["all_ok"] = all(results.values())
        return results 