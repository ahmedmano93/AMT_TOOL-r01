# MTK Device Manager
# Handles device detection, connection and operations
import os
import logging
import subprocess
from typing import Dict, Optional, List
from enum import Enum
from shutil import which

class DeviceState(Enum):
    UNKNOWN = "unknown"
    NORMAL = "normal"
    META = "meta"
    FASTBOOT = "fastboot"
    RECOVERY = "recovery"

class MTKDeviceManager:
    """
    Manages MTK device operations and states."""
    def __init__(self) -> None:
        """Initialize device manager."""
        self.current_device: Optional[Dict] = None
        self.supported_chipsets = [
            "MT6789", "MT6833", "MT6853", "MT6873",
            "MT6885", "MT6889", "MT6893", "MT6895"
        ]
        self._load_device_commands()
        
    def _load_device_commands(self) -> None:
        """Load device-specific commands."""
        self.meta_commands = {
            "MT6789": ["adb reboot meta", "meta_mode --force"],
            "MT6833": ["adb reboot meta", "meta_mode --force"],
            "MT6853": ["adb reboot meta", "meta_mode --force"],
            "MT6873": ["adb reboot meta", "meta_mode --force"],
            "MT6885": ["adb reboot meta", "meta_mode --force"],
            "MT6889": ["adb reboot meta", "meta_mode --force"],
            "MT6893": ["adb reboot meta", "meta_mode --force"],
            "MT6895": ["adb reboot meta", "meta_mode --force"]
        }
        self.frp_commands = {
            "MT6789": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot reboot"
            ],
            "MT6833": [
                "fastboot erase frp",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6853": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6873": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6885": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6889": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6893": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ],
            "MT6895": [
                "fastboot erase frp",
                "fastboot erase config",
                "fastboot erase persist",
                "fastboot reboot"
            ]
        }
        
    def verify_device(self, device_info: Dict) -> Dict:
        """Verify device compatibility and connection."""
        try:
            # 1. Check chipset compatibility
            if not self._verify_chipset(device_info.get("chipset")):
                return {
                    "verified": False,
                    "message": "Unsupported chipset",
                    "details": device_info.get("chipset")
                }
            # 2. Check connection
            connection_status = self._verify_connection(device_info)
            if not connection_status["connected"]:
                return {
                    "verified": False,
                    "message": "Device connection failed",
                    "details": connection_status["error"]
                }
            # 3. Store current device
            self.current_device = device_info
            return {
                "verified": True,
                "message": "Device verified successfully",
                "device_info": device_info
            }
        except Exception as e:
            logging.error(f"Device verification error: {str(e)}")
            return {
                "verified": False,
                "message": "Verification failed",
                "error": str(e)
            }
            
    def handle_meta_mode(self, device_info: Dict) -> Dict:
        """Handle Meta mode operations."""
        try:
            current_state = self._get_device_state()
            if current_state == DeviceState.META:
                return {"status": "success", "message": "Device already in Meta mode"}
            chipset = device_info.get("chipset")
            if not chipset or chipset not in self.meta_commands:
                return {
                    "status": "error",
                    "message": "Unsupported chipset for Meta mode"
                }
            # Execute Meta mode commands
            for cmd in self.meta_commands[chipset]:
                result = self._execute_command(cmd)
                if not result["success"]:
                    return result
            # Verify Meta mode
            if self._get_device_state() != DeviceState.META:
                return {
                    "status": "error",
                    "message": "Failed to enter Meta mode"
                }
            return {
                "status": "success",
                "message": "Successfully entered Meta mode",
                "device_state": "meta"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "Meta mode operation failed",
                "error": str(e)
            }
            
    def handle_frp(self, device_info: Dict) -> Dict:
        """Handle FRP removal operations."""
        try:
            # Safety check before FRP operation
            if not self._verify_frp_safety(device_info):
                return {
                    "status": "error",
                    "message": "FRP operation safety check failed"
                }
            chipset = device_info.get("chipset")
            if not chipset or chipset not in self.frp_commands:
                return {
                    "status": "error",
                    "message": "Unsupported chipset for FRP removal"
                }
            # Execute FRP removal commands
            for cmd in self.frp_commands[chipset]:
                result = self._execute_command(cmd)
                if not result["success"]:
                    return result
            # Verify FRP removal
            if not self._verify_frp_removal():
                return {
                    "status": "error",
                    "message": "FRP removal verification failed"
                }
            return {
                "status": "success",
                "message": "FRP removed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": "FRP removal failed",
                "error": str(e)
            }
            
    def _verify_chipset(self, chipset: Optional[str]) -> bool:
        """Check if the chipset is supported."""
        return chipset in self.supported_chipsets
    
    def _verify_connection(self, device_info: Dict) -> Dict:
        """Verify device connection using adb."""
        try:
            if not self._adb_exists():
                return {"connected": False, "error": "ADB not found."}
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return {"connected": False, "error": "ADB devices command failed."}
            if device_info.get("serial") not in result.stdout:
                return {"connected": False, "error": "Device serial not found."}
            return {"connected": True}
        except subprocess.TimeoutExpired:
            return {"connected": False, "error": "Connection check timed out."}
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    def _get_device_state(self) -> DeviceState:
        """Get current device state."""
        try:
            result = subprocess.run(
                ["adb", "get-state"],
                capture_output=True,
                text=True
            )
            
            state_map = {
                "device": DeviceState.NORMAL,
                "recovery": DeviceState.RECOVERY,
                "fastboot": DeviceState.FASTBOOT,
                "sideload": DeviceState.UNKNOWN
            }
            
            return state_map.get(result.stdout.strip(), DeviceState.UNKNOWN)
        except Exception:
            return DeviceState.UNKNOWN
    
    def _execute_command(self, cmd: str) -> Dict:
        """Execute a shell command with improved error handling."""
        try:
            # Detect if command needs adb or fastboot
            if "adb" in cmd and not self._adb_exists():
                return {"success": False, "message": "ADB not found. Please install ADB and add it to PATH."}
            if "fastboot" in cmd and not self._fastboot_exists():
                return {"success": False, "message": "Fastboot not found. Please install Fastboot and add it to PATH."}
            result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=20)
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"Command failed: {cmd}",
                    "stderr": result.stderr.strip(),
                    "stdout": result.stdout.strip()
                }
            return {"success": True, "stdout": result.stdout.strip()}
        except subprocess.TimeoutExpired:
            return {"success": False, "message": f"Command timed out: {cmd}"}
        except Exception as e:
            return {"success": False, "message": f"Command error: {str(e)}"}
    
    def _verify_frp_safety(self, device_info: Dict) -> bool:
        """Verify if FRP operation is safe."""
        try:
            # Check device state
            if self._get_device_state() != DeviceState.FASTBOOT:
                return False
            
            # Check battery level
            battery_level = self._get_battery_level()
            if battery_level < 20:
                return False
            
            return True
        except Exception:
            return False
    
    def _verify_frp_removal(self) -> bool:
        """Verify FRP was successfully removed."""
        try:
            result = self._execute_command("fastboot getvar frp")
            return "empty" in result.get("stdout", "").lower()
        except Exception:
            return False
    
    def _get_battery_level(self) -> int:
        """Get device battery level."""
        try:
            result = subprocess.run(
                ["adb", "shell", "cat", "/sys/class/power_supply/battery/capacity"],
                capture_output=True,
                text=True
            )
            return int(result.stdout.strip())
        except Exception:
            return 0

    def _adb_exists(self) -> bool:
        """Check if ADB is available in the system PATH."""
        return which("adb") is not None

    def _fastboot_exists(self) -> bool:
        """Check if Fastboot is available in the system PATH."""
        return which("fastboot") is not None

    def self_test(self, device_info: Dict) -> Dict:
        """Run a self-test for the device manager.
        Returns a dict with the results of all critical checks.
        """
        results = {
            "adb_exists": self._adb_exists(),
            "fastboot_exists": self._fastboot_exists(),
            "chipset_supported": self._verify_chipset(device_info.get("chipset")),
            "connection_check": self._verify_connection(device_info)
        }
        all_ok = all(
            v is True or (isinstance(v, dict) and v.get("connected", True))
            for k, v in results.items() if k not in ["adb_exists", "fastboot_exists"]
        )
        results["all_ok"] = all_ok
        return results 