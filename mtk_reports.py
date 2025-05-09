"""
# MTK Reports System
# Handles report generation and management
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional


class MTKReportManager:
    """Manages report generation and storage."""
    
    def __init__(self) -> None:
        """Initialize report manager."""
        self.reports_dir = "./MTK_TOOL/REPORTS"
        self.current_report = None
        self.report_data = {}
        
        os.makedirs(self.reports_dir, exist_ok=True)
    
    def start_operation_report(self, operation_type: str, device_info: Dict) -> None:
        """Start a new operation report."""
        self.current_report = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "device_info": device_info,
            "steps": [],
            "status": "in_progress"
        }
        
        self.report_data = {
            "success": True,
            "errors": [],
            "warnings": [],
            "details": {}
        }
    
    def add_step(self, step_name: str, status: str, details: Dict = None) -> None:
        """Add a step to the current report."""
        if not self.current_report:
            return
        
        step = {
            "name": step_name,
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "details": details or {}
        }
        
        self.current_report["steps"].append(step)
        
        if status == "error":
            self.report_data["success"] = False
            self.report_data["errors"].append(step)
        elif status == "warning":
            self.report_data["warnings"].append(step)
    
    def add_detail(self, category: str, key: str, value: any) -> None:
        """Add detailed information to the report."""
        if category not in self.report_data["details"]:
            self.report_data["details"][category] = {}
        
        self.report_data["details"][category][key] = value
    
    def finalize_report(self, operation_result: Dict) -> Dict:
        """Finalize and save the report."""
        if not self.current_report:
            return {"status": "error", "message": "No active report"}
        
        try:
            # Update report status
            self.current_report["status"] = operation_result.get("status", "unknown")
            self.current_report["result"] = operation_result
            
            # Generate report files
            report_path = self._get_report_path()
            
            # Save JSON report
            self._save_json_report(report_path)
            
            # Generate PDF report
            pdf_path = self._generate_pdf_report(report_path)
            
            return {
                "status": "success",
                "json_report": f"{report_path}.json",
                "pdf_report": pdf_path
            }
            
        except Exception as e:
            logging.error(f"Report generation failed: {str(e)}")
            return {"status": "error", "message": str(e)}
        finally:
            self.current_report = None
    
    def _get_report_path(self) -> str:
        """Generate report file path."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        operation = self.current_report["operation_type"]
        device = self.current_report["device_info"].get("model", "unknown")
        
        return os.path.join(self.reports_dir, f"{device}_{operation}_{timestamp}")
    
    def _save_json_report(self, base_path: str) -> None:
        """Save report in JSON format."""
        with open(f"{base_path}.json", "w") as f:
            json.dump(self.current_report, f, indent=4)
    
    def _generate_pdf_report(self, base_path: str) -> str:
        """Generate PDF report, with error handling for missing FPDF."""
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("FPDF library is not installed. Please install it with 'pip install fpdf'.")

        pdf = FPDF()
        pdf.add_page()
        
        # Set font
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, "MTK Tool Operation Report", ln=True, align="C")
        pdf.ln(10)
        
        # Device Information
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Device Information", ln=True)
        pdf.set_font("Arial", "", 12)
        
        device_info = self.current_report["device_info"]
        self._add_info_section(pdf, {
            "Model": device_info.get("model", "Unknown"),
            "Serial": device_info.get("serial", "Unknown"),
            "Chipset": device_info.get("chipset", "Unknown")
        })
        
        # Operation Information
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Operation Information", ln=True)
        pdf.set_font("Arial", "", 12)
        
        self._add_info_section(pdf, {
            "Operation": self.current_report["operation_type"],
            "Status": self.current_report["status"],
            "Timestamp": self.current_report["timestamp"]
        })
        
        # Steps
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Operation Steps", ln=True)
        pdf.set_font("Arial", "", 12)
        
        for step in self.current_report["steps"]:
            self._add_step_to_pdf(pdf, step)
        
        # Result
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Operation Result", ln=True)
        pdf.set_font("Arial", "", 12)
        
        result = self.current_report["result"]
        self._add_info_section(pdf, {
            "Status": result.get("status", "Unknown"),
            "Message": result.get("message", "No message")
        })
        
        # Save PDF
        pdf_path = f"{base_path}.pdf"
        pdf.output(pdf_path)
        
        return pdf_path
    
    def _add_info_section(self, pdf, info: Dict) -> None:
        """Add information section to PDF."""
        for key, value in info.items():
            pdf.cell(0, 10, f"{key}: {value}", ln=True)
        pdf.ln(5)
    
    def _add_step_to_pdf(self, pdf, step: Dict) -> None:
        """Add step information to PDF."""
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"Step: {step['name']}", ln=True)
        
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Status: {step['status']}", ln=True)
        pdf.cell(0, 10, f"Time: {step['timestamp']}", ln=True)
        
        if step.get("details"):
            pdf.cell(0, 10, "Details:", ln=True)
            for key, value in step["details"].items():
                pdf.cell(0, 10, f"  {key}: {value}", ln=True)
        
        pdf.ln(5)

    def self_test(self) -> Dict:
        """
        Run a self-test for the report manager.
        Returns a dict with the results of all critical checks.
        """
        results = {
            "reports_dir_exists": os.path.exists(self.reports_dir),
            "fpdf_installed": self._fpdf_available()
        }
        # Try creating a dummy report
        try:
            dummy_report = {
                "timestamp": datetime.now().isoformat(),
                "operation_type": "self_test",
                "device_info": {"model": "test", "serial": "0000", "chipset": "test"},
                "steps": [],
                "status": "success",
                "result": {"status": "success", "message": "Self test"}
            }
            self.current_report = dummy_report
            path = self._get_report_path()
            self._save_json_report(path)
            if results["fpdf_installed"]:
                self._generate_pdf_report(path)
            results["dummy_report_created"] = True
        except Exception as e:
            results["dummy_report_created"] = False
            results["error"] = str(e)
        results["all_ok"] = all(v is True for k, v in results.items() if k != "error")
        return results

    def _fpdf_available(self) -> bool:
        """Check if FPDF is installed."""
        try:
            import fpdf
            return True
        except ImportError:
            return False 