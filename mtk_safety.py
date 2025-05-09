# MTK Safety System
# Handles all safety and protection features

import os
import json
import logging
import subprocess
from datetime import datetime
from typing import Dict


class MTKSafetySystem:
    """Core safety system handling all protection and backup operations."""
    
    def __init__(self) -> None:
        """Initialize safety system with critical partitions and checks."""
        self.critical_partitions = [
            "nvram",
            "boot",
            "persist",
            "security",
            "userdata",
            "system"
        ]
        
        self.safety_checks = {
            "pre_operation": [
                "check_battery",
                "check_connection",
                "verify_device_state"
            ],
            "during_operation": [
                "monitor_connection",
                "monitor_progress",
                "check_device_response"
            ],
            "post_operation": [
                "verify_result",
                "check_device_state",
                "verify_functionality"
            ]
        }
        
        self.backup_root = "./MTK_TOOL/BACKUPS"
        os.makedirs(self.backup_root, exist_ok=True)

    def check_safety(self, device_info: Dict) -> Dict:
        """Perform comprehensive safety check."""
        try:
            # 1. Pre-operation checks
            for check in self.safety_checks["pre_operation"]:
                result = getattr(self, f"_{check}")(device_info)
                if not result["safe"]:
                    return result

            # 2. Check critical partitions
            partition_check = self._check_critical_partitions(device_info)
            if not partition_check["safe"]:
                return partition_check
            
            # 3. Verify backup availability
            backup_check = self._check_backup_availability(device_info)
            if not backup_check["safe"]:
                return backup_check

            return {"safe": True, "message": "All safety checks passed"}

        except Exception as e:
            return self._handle_safety_error(e)

    def create_backup(self, device_info: Dict) -> Dict:
        """Create backup of critical partitions."""
        try:
            backup_results = {}
            backup_path = self._get_backup_path(device_info)
            os.makedirs(backup_path, exist_ok=True)
            
            # Create backup info file
            self._create_backup_info(backup_path, device_info)

            for partition in self.critical_partitions:
                result = self._backup_partition(device_info, partition, backup_path)
                backup_results[partition] = result
                
                if not result["success"]:
                    return {
                        "status": "error",
                        "message": f"Backup failed for {partition}",
                        "details": result
                    }

            # Create backup verification file
            self._create_verification_file(backup_path, backup_results)

            return {
                "status": "success",
                "backup_path": backup_path,
                "results": backup_results
            }

        except Exception as e:
            return self._handle_backup_error(e)
    
    def restore_backup(self, backup_path: str, device_info: Dict) -> Dict:
        """Restore backup to device."""
        try:
            # Verify backup integrity
            if not self._verify_backup_integrity(backup_path):
                return {
                    "status": "error",
                    "message": "Backup integrity check failed"
                }
            
            restore_results = {}
            
            # Restore each partition
            for partition in self.critical_partitions:
                result = self._restore_partition(device_info, partition, backup_path)
                restore_results[partition] = result
                
                if not result["success"]:
                    return {
                        "status": "error",
                        "message": f"Restore failed for {partition}",
                        "details": result
                    }
            
            return {
                "status": "success",
                "message": "Backup restored successfully",
                "results": restore_results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Restore failed: {str(e)}"
            }

    def handle_error(self, error: Exception) -> Dict:
        """Handle errors safely."""
        logging.error(f"Operation error: {str(error)}")
        
        return {
            "status": "error",
            "message": str(error),
            "recovery_possible": self._check_recovery_possible(),
            "safe_to_continue": False
        }

    def _check_battery(self, device_info: Dict) -> Dict:
        """Check device battery level."""
        try:
            result = subprocess.run(
                ["adb", "shell", "cat", "/sys/class/power_supply/battery/capacity"],
                capture_output=True,
                text=True
            )
            
            battery_level = int(result.stdout.strip())
            
            if battery_level < 20:
                return {
                    "safe": False,
                    "message": "Battery level too low",
                    "required": "20%",
                    "current": f"{battery_level}%"
                }
            return {"safe": True}
        except Exception:
            return {"safe": False, "message": "Could not check battery"}

    def _check_connection(self, device_info: Dict) -> Dict:
        """Check connection stability."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )
            
            if device_info.get("serial") not in result.stdout:
                return {
                    "safe": False,
                    "message": "Device not connected"
                }
            
            return {"safe": True}
        except Exception:
            return {"safe": False, "message": "Connection check failed"}

    def _verify_device_state(self, device_info: Dict) -> Dict:
        """Verify device is in correct state."""
        try:
            result = subprocess.run(
                ["adb", "get-state"],
                capture_output=True,
                text=True
            )
            
            state = result.stdout.strip()
            expected_state = device_info.get("expected_state", "device")
            
            if state != expected_state:
                return {
                    "safe": False,
                    "message": f"Device in wrong state: {state}, expected: {expected_state}"
                }
            
            return {"safe": True}
        except Exception:
            return {"safe": False, "message": "Could not verify device state"}

    def _backup_partition(self, device_info: Dict, partition: str, backup_path: str) -> Dict:
        """Backup a single partition."""
        try:
            output_file = os.path.join(backup_path, f"{partition}.img")
            
            result = subprocess.run(
                ["adb", "shell", "dd", f"if=/dev/block/by-name/{partition}", "of=/data/local/tmp/temp.img"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            result = subprocess.run(
                ["adb", "pull", "/data/local/tmp/temp.img", output_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            subprocess.run(["adb", "shell", "rm", "/data/local/tmp/temp.img"])
            
            return {"success": True, "path": output_file}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _restore_partition(self, device_info: Dict, partition: str, backup_path: str) -> Dict:
        """Restore a single partition."""
        try:
            input_file = os.path.join(backup_path, f"{partition}.img")
            
            if not os.path.exists(input_file):
                return {
                    "success": False,
                    "error": f"Backup file not found: {input_file}"
                }
            
            result = subprocess.run(
                ["adb", "push", input_file, "/data/local/tmp/temp.img"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            result = subprocess.run(
                ["adb", "shell", "dd", "if=/data/local/tmp/temp.img", f"of=/dev/block/by-name/{partition}"],
                capture_output=True,
                text=True
            )
            
            subprocess.run(["adb", "shell", "rm", "/data/local/tmp/temp.img"])
            
            if result.returncode != 0:
                return {"success": False, "error": result.stderr}
            
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_backup_path(self, device_info: Dict) -> str:
        """Generate backup path based on device info."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        device_model = device_info.get("model", "unknown")
        return os.path.join(self.backup_root, f"{device_model}_{timestamp}")

    def _check_critical_partitions(self, device_info: Dict) -> Dict:
        """Check status of critical partitions."""
        try:
            result = subprocess.run(
                ["adb", "shell", "ls", "/dev/block/by-name/"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"safe": False, "message": "Could not access partitions"}
            
            available_partitions = result.stdout.split()
            
            for partition in self.critical_partitions:
                if partition not in available_partitions:
                    return {
                        "safe": False,
                        "message": f"Critical partition not found: {partition}"
                    }
            
            return {"safe": True}
        except Exception:
            return {"safe": False, "message": "Critical partition check failed"}

    def _check_backup_availability(self, device_info: Dict) -> Dict:
        """Check if backup can be created."""
        try:
            # Check storage space
            result = subprocess.run(
                ["adb", "shell", "df", "-h", "/data"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return {"safe": False, "message": "Could not check storage space"}
            
            # Parse df output
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return {"safe": False, "message": "Invalid storage info format"}
            
            # Get available space in MB
            parts = lines[1].split()
            if len(parts) < 4:
                return {"safe": False, "message": "Invalid storage info format"}
            
            available_space = self._convert_to_mb(parts[3])
            required_space = self._calculate_required_space(device_info)
            
            if available_space < required_space:
                return {
                    "safe": False,
                    "message": f"Insufficient storage space. Need {required_space}MB, have {available_space}MB"
                }
            
            return {"safe": True}
        except Exception as e:
            logging.error(f"Storage check error: {str(e)}")
            return {"safe": False, "message": "Backup availability check failed"}
    
    def _convert_to_mb(self, size_str: str) -> int:
        """Convert size string (like 1.5G, 800M) to MB."""
        try:
            size = float(size_str[:-1])
            unit = size_str[-1].upper()
            
            if unit == 'G':
                return int(size * 1024)
            elif unit == 'M':
                return int(size)
            elif unit == 'K':
                return int(size / 1024)
            else:
                return 0
        except Exception:
            return 0
    
    def _calculate_required_space(self, device_info: Dict) -> int:
        """Calculate required space for backup in MB."""
        # Base space requirement
        base_space = 500  # MB
        
        # Add space based on partition count
        partition_space = len(self.critical_partitions) * 100  # 100MB per partition
        
        # Add extra space based on device type
        extra_space = 0
        if "userdata" in self.critical_partitions:
            extra_space += 1000  # 1GB extra for userdata
        
        total_required = base_space + partition_space + extra_space
        
        # Add 20% safety margin
        return int(total_required * 1.2)

    def _create_backup_info(self, backup_path: str, device_info: Dict) -> None:
        """Create backup information file."""
        info = {
            "timestamp": datetime.now().isoformat(),
            "device_info": device_info,
            "partitions": self.critical_partitions
        }
        
        with open(os.path.join(backup_path, "backup_info.json"), "w") as f:
            json.dump(info, f, indent=4)

    def _create_verification_file(self, backup_path: str, results: Dict) -> None:
        """Create backup verification file."""
        verification = {
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "verified": all(r["success"] for r in results.values())
        }
        
        with open(os.path.join(backup_path, "verification.json"), "w") as f:
            json.dump(verification, f, indent=4)

    def _verify_backup_integrity(self, backup_path: str) -> bool:
        """Verify backup integrity."""
        try:
            # Check info file
            info_path = os.path.join(backup_path, "backup_info.json")
            if not os.path.exists(info_path):
                return False
            
            # Check verification file
            verification_path = os.path.join(backup_path, "verification.json")
            if not os.path.exists(verification_path):
                return False
            
            # Check partition files
            with open(info_path, "r") as f:
                info = json.load(f)
            
            for partition in info["partitions"]:
                if not os.path.exists(os.path.join(backup_path, f"{partition}.img")):
                    return False
            
            return True
        except Exception:
            return False

    def _check_recovery_possible(self) -> bool:
        """Check if recovery is possible after error."""
        try:
            # Check if device is still connected
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
            )
            
            if "device" not in result.stdout:
                return False
            
            # Check if we can access recovery
            result = subprocess.run(
                ["adb", "reboot", "recovery"],
                capture_output=True,
                text=True
            )
            
            return result.returncode == 0
        except Exception:
            return False

    def _handle_safety_error(self, error: Exception) -> Dict:
        """Handle safety check errors."""
        logging.error(f"Safety check error: {str(error)}")
        return {
            "safe": False,
            "message": "Safety check failed",
            "error": str(error)
        }

    def _handle_backup_error(self, error: Exception) -> Dict:
        """Handle backup operation errors."""
        logging.error(f"Backup error: {str(error)}")
        
        # Check if recovery is possible
        can_recover = self._check_recovery_possible()
        
        return {
            "status": "error",
            "message": "Backup operation failed",
            "error": str(error),
            "recoverable": can_recover,
            "timestamp": datetime.now().isoformat()
        }

    # Define standard size examples for reference
    SIZE_EXAMPLES = {
        "large": "1.5G",
        "medium": "800M" 
    }

    def self_test(self, device_info: Dict) -> Dict:
        """
        Run a self-test for the safety system.
        Returns a dict with the results of all critical checks.
        """
        results = {
            "backup_root_exists": os.path.exists(self.backup_root),
            "critical_partitions_defined": len(self.critical_partitions) > 0,
            "safety_checks_defined": all(len(checks) > 0 for checks in self.safety_checks.values())
        }
        
        # Test storage path access
        try:
            test_dir = os.path.join(self.backup_root, "test_dir")
            os.makedirs(test_dir, exist_ok=True)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)
                results["storage_writeable"] = True
            else:
                results["storage_writeable"] = False
        except Exception:
            results["storage_writeable"] = False
        
        # Try to run a simple ADB command (no device needed)
        try:
            result = subprocess.run(
                ["adb", "version"],
                capture_output=True,
                text=True,
                timeout=3
            )
            results["adb_available"] = result.returncode == 0
        except Exception:
            results["adb_available"] = False
        
        # Overall result
        results["all_ok"] = all(v is True for k, v in results.items())
        
        return results