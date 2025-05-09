import json
import os
import logging
import sys
from mtk_safety import MTKSafetySystem
from mtk_device_manager import MTKDeviceManager
from mtk_update_manager import MTKUpdateManager
from mtk_reports import MTKReportManager

# Path configuration
CONFIG_FILE = 'config.json'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def load_config(path):
    """Load configuration from JSON file."""
    config_path = os.path.join(PROJECT_ROOT, path)
    if not os.path.exists(config_path):
        print(f"Config file '{path}' not found!")
        return {}
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_folders(folders_list):
    """Check and create folders if missing."""
    print("Checking and creating folders if missing:")
    for folder in folders_list:
        path = folder['path']
        if not os.path.isabs(path):
            path = os.path.join(PROJECT_ROOT, path)
            
        if os.path.exists(path):
            print(f"✔️ Exists: {path}")
        else:
            try:
                os.makedirs(path, exist_ok=True)
                print(f"➕ Created: {path}")
            except Exception as e:
                print(f"❌ Failed to create {path}: {e}")

def setup_logging():
    """Set up basic logging configuration."""
    log_dir = os.path.join(PROJECT_ROOT, "Logs")
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        filename=os.path.join(log_dir, "mtk_tool.log"),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info("=== MTK Tool Started ===")

def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    
    # Load config
    config = load_config(CONFIG_FILE)
    if not config:
        logging.error("No config loaded. Exiting.")
        print("No config loaded. Exiting.")
        return

    # Ensure folders
    ensure_folders(config.get('ANDROID_Forensics', []))

    try:
        # Initialize core classes
        logging.info("Initializing core systems...")
        safety = MTKSafetySystem()
        device_manager = MTKDeviceManager()
        update_manager = MTKUpdateManager()
        report_manager = MTKReportManager()
        
        # Run self-tests
        safety_test = safety.self_test({"chipset": "MT6853", "serial": "test_device"})
        device_test = device_manager.self_test({"chipset": "MT6853", "serial": "test_device"})
        update_test = update_manager.self_test()
        report_test = report_manager.self_test()
        
        # Log test results
        logging.info(f"Safety System Test: {safety_test.get('all_ok', False)}")
        logging.info(f"Device Manager Test: {device_test.get('all_ok', False)}")
        logging.info(f"Update Manager Test: {update_test.get('all_ok', False)}")
        logging.info(f"Report Manager Test: {report_test.get('all_ok', False)}")
        
        print("\nAll folders checked and core systems initialized.")
        print("MTK Tool is ready to use! 🚀")
        
        # For command-line interface, you can add user interaction here
        # For GUI, this would be replaced with the GUI initialization
        
    except Exception as e:
        logging.error(f"Initialization error: {str(e)}")
        print(f"Error during initialization: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())