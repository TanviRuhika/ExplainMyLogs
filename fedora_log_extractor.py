#!/usr/bin/env python3
"""
ExplainMyLogs - Fedora Log Extractor PoC
Proof of Concept script to extract logs from Fedora system and output in JSON format.
"""

import json
import subprocess
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional
import argparse

class FedoraLogExtractor:
    """Extracts and parses logs from Fedora system using journalctl and standard log files."""
    
    def __init__(self):
        self.log_sources = {
            'systemd': self._extract_systemd_logs,
            'kernel': self._extract_kernel_logs,
            'auth': self._extract_auth_logs,
            'application': self._extract_application_logs
        }
    
    def _run_command(self, command: List[str]) -> Optional[str]:
        """Execute system command and return output."""
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=30
            )
            return result.stdout
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Error running command {' '.join(command)}: {e}", file=sys.stderr)
            return None
    
    def _parse_journalctl_line(self, line: str) -> Optional[Dict]:
        """Parse a single journalctl line into structured data."""
        # journalctl output format: timestamp hostname service[pid]: message
        pattern = r'^(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\S+?)(?:\[(\d+)\])?\s*:\s*(.*)$'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp_str, hostname, service, pid, message = match.groups()
            
            # Parse timestamp (add current year since journalctl doesn't include it)
            try:
                current_year = datetime.now().year
                timestamp_str = f"{current_year} {timestamp_str}"
                timestamp = datetime.strptime(timestamp_str, "%Y %b %d %H:%M:%S")
            except ValueError:
                timestamp = datetime.now()
            
            return {
                'timestamp': timestamp.isoformat(),
                'hostname': hostname,
                'service': service,
                'pid': int(pid) if pid else None,
                'message': message.strip(),
                'severity': self._extract_severity(message),
                'source': 'journalctl'
            }
        return None
    
    def _extract_severity(self, message: str) -> str:
        """Extract severity level from log message."""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['error', 'err', 'failed', 'failure', 'exception']):
            return 'ERROR'
        elif any(keyword in message_lower for keyword in ['warn', 'warning']):
            return 'WARNING'
        elif any(keyword in message_lower for keyword in ['info', 'information']):
            return 'INFO'
        elif any(keyword in message_lower for keyword in ['debug', 'dbg']):
            return 'DEBUG'
        else:
            return 'UNKNOWN'
    
    def _extract_systemd_logs(self, lines: int = 50) -> List[Dict]:
        """Extract systemd service logs."""
        logs = []
        command = ['journalctl', '--no-pager', '-n', str(lines), '--output=short']
        
        output = self._run_command(command)
        if not output:
            return logs
        
        for line in output.split('\n'):
            if line.strip():
                parsed = self._parse_journalctl_line(line)
                if parsed:
                    parsed['category'] = 'systemd'
                    logs.append(parsed)
        
        return logs
    
    def _extract_kernel_logs(self, lines: int = 30) -> List[Dict]:
        """Extract kernel logs."""
        logs = []
        command = ['journalctl', '--no-pager', '-k', '-n', str(lines), '--output=short']
        
        output = self._run_command(command)
        if not output:
            return logs
        
        for line in output.split('\n'):
            if line.strip():
                parsed = self._parse_journalctl_line(line)
                if parsed:
                    parsed['category'] = 'kernel'
                    logs.append(parsed)
        
        return logs
    
    def _extract_auth_logs(self, lines: int = 30) -> List[Dict]:
        """Extract authentication logs."""
        logs = []
        command = ['journalctl', '--no-pager', '-u', 'sshd', '-n', str(lines), '--output=short']
        
        output = self._run_command(command)
        if not output:
            return logs
        
        for line in output.split('\n'):
            if line.strip():
                parsed = self._parse_journalctl_line(line)
                if parsed:
                    parsed['category'] = 'authentication'
                    logs.append(parsed)
        
        return logs
    
    def _extract_application_logs(self, lines: int = 30) -> List[Dict]:
        """Extract application-specific logs (e.g., Apache, Nginx, etc.)."""
        logs = []
        
        # Common services to check
        services = ['httpd', 'nginx', 'docker', 'postgresql', 'mysql', 'mariadb']
        
        for service in services:
            command = ['journalctl', '--no-pager', '-u', service, '-n', str(lines//len(services)), '--output=short']
            output = self._run_command(command)
            
            if output:
                for line in output.split('\n'):
                    if line.strip():
                        parsed = self._parse_journalctl_line(line)
                        if parsed:
                            parsed['category'] = 'application'
                            parsed['application'] = service
                            logs.append(parsed)
        
        return logs
    
    def extract_logs(self, categories: List[str] = None, lines_per_category: int = 50) -> Dict:
        """Extract logs from specified categories."""
        if categories is None:
            categories = list(self.log_sources.keys())
        
        extracted_logs = {
            'extraction_time': datetime.now().isoformat(),
            'hostname': subprocess.run(['hostname'], capture_output=True, text=True).stdout.strip(),
            'categories': {},
            'summary': {}
        }
        
        total_logs = 0
        
        for category in categories:
            if category in self.log_sources:
                print(f"Extracting {category} logs...", file=sys.stderr)
                category_logs = self.log_sources[category](lines_per_category)
                extracted_logs['categories'][category] = category_logs
                
                # Generate summary
                extracted_logs['summary'][category] = {
                    'total_entries': len(category_logs),
                    'severity_breakdown': self._get_severity_breakdown(category_logs),
                    'time_range': self._get_time_range(category_logs)
                }
                
                total_logs += len(category_logs)
        
        extracted_logs['summary']['total_logs'] = total_logs
        
        return extracted_logs
    
    def _get_severity_breakdown(self, logs: List[Dict]) -> Dict[str, int]:
        """Get breakdown of log severity levels."""
        breakdown = {}
        for log in logs:
            severity = log.get('severity', 'UNKNOWN')
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown
    
    def _get_time_range(self, logs: List[Dict]) -> Dict[str, str]:
        """Get time range of logs."""
        if not logs:
            return {'earliest': None, 'latest': None}
        
        timestamps = [log['timestamp'] for log in logs if log.get('timestamp')]
        if not timestamps:
            return {'earliest': None, 'latest': None}
        
        return {
            'earliest': min(timestamps),
            'latest': max(timestamps)
        }

def main():
    """Main function to run the log extractor."""
    parser = argparse.ArgumentParser(description='Extract Fedora system logs and output as JSON')
    parser.add_argument(
        '--categories', 
        nargs='+', 
        choices=['systemd', 'kernel', 'auth', 'application'],
        default=['systemd', 'kernel', 'auth', 'application'],
        help='Log categories to extract'
    )
    parser.add_argument(
        '--lines', 
        type=int, 
        default=50,
        help='Number of lines to extract per category'
    )
    parser.add_argument(
        '--output', 
        type=str,
        help='Output file (default: stdout)'
    )
    parser.add_argument(
        '--pretty', 
        action='store_true',
        help='Pretty print JSON output'
    )
    
    args = parser.parse_args()
    
    # Check if running as root for better log access
    if subprocess.run(['id', '-u'], capture_output=True, text=True).stdout.strip() != '0':
        print("Warning: Running as non-root user. Some logs may not be accessible.", file=sys.stderr)
    
    # Create extractor and extract logs
    extractor = FedoraLogExtractor()
    logs = extractor.extract_logs(args.categories, args.lines)
    
    # Output JSON
    json_output = json.dumps(logs, indent=2 if args.pretty else None)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_output)
        print(f"Logs extracted to {args.output}", file=sys.stderr)
    else:
        print(json_output)

if __name__ == '__main__':
    main()
