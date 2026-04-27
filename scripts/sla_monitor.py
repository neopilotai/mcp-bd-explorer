"""
Phase 4.3 - SLA Monitoring & Alerting System
Tracks pipeline health and sends alerts for SLA violations
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from enum import Enum
from dataclasses import dataclass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class SLAMetric:
    """Data class for SLA metrics"""
    name: str
    value: float
    target: float
    unit: str
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime


class SLAMonitor:
    """Monitors pipeline SLA and generates alerts"""
    
    # SLA Configuration
    SLA_TARGETS = {
        'completion_time': {
            'target': 4.0,  # hours
            'warning': 2.0,  # hours
            'critical': 3.5  # hours
        },
        'success_rate': {
            'target': 99.0,  # percent
            'warning': 95.0,  # percent
            'critical': 90.0  # percent
        },
        'error_rate': {
            'target': 1.0,  # percent
            'warning': 2.0,  # percent
            'critical': 5.0  # percent
        },
        'records_loaded': {
            'target': 1000,  # minimum records
            'warning': 500,  # minimum records
            'critical': 100  # minimum records
        },
        'throughput': {
            'target': 500,  # records/sec
            'warning': 300,  # records/sec
            'critical': 100  # records/sec
        }
    }
    
    def __init__(self, 
                 smtp_host: Optional[str] = None,
                 smtp_port: int = 587,
                 smtp_user: Optional[str] = None,
                 smtp_password: Optional[str] = None,
                 alert_recipients: Optional[List[str]] = None):
        """Initialize SLA monitor with email alerting"""
        self.smtp_config = {
            'host': smtp_host,
            'port': smtp_port,
            'user': smtp_user,
            'password': smtp_password
        }
        self.alert_recipients = alert_recipients or []
        self.metrics_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
    
    def evaluate_load_pipeline(self, pipeline_stats: Dict[str, Any]) -> List[str]:
        """
        Evaluate pipeline stats against SLA targets
        
        Args:
            pipeline_stats: Dictionary with load statistics
            
        Returns:
            List of alert messages
        """
        alerts = []
        
        # Calculate key metrics
        total_records = pipeline_stats.get('total_records', 0)
        inserted = pipeline_stats.get('inserted', 0)
        updated = pipeline_stats.get('updated', 0)
        failed = pipeline_stats.get('failed', 0)
        duration_seconds = pipeline_stats.get('duration_seconds', 0)
        start_time = pipeline_stats.get('start_time', datetime.utcnow())
        
        # Completion time (hours)
        completion_time = duration_seconds / 3600.0
        
        # Success rate (percent)
        success_count = inserted + updated
        success_rate = (success_count / total_records * 100.0) if total_records > 0 else 0
        
        # Error rate (percent)
        error_rate = (failed / total_records * 100.0) if total_records > 0 else 0
        
        # Throughput (records/sec)
        throughput = (total_records / duration_seconds) if duration_seconds > 0 else 0
        
        # Check completion time SLA
        if completion_time > self.SLA_TARGETS['completion_time']['critical']:
            alerts.append(self._create_alert(
                AlertLevel.CRITICAL,
                'Completion Time SLA Breach',
                f"Load pipeline exceeded SLA: {completion_time:.2f}h > {self.SLA_TARGETS['completion_time']['critical']}h",
                pipeline_stats
            ))
        elif completion_time > self.SLA_TARGETS['completion_time']['warning']:
            alerts.append(self._create_alert(
                AlertLevel.WARNING,
                'Completion Time Warning',
                f"Load pipeline approaching SLA: {completion_time:.2f}h > {self.SLA_TARGETS['completion_time']['warning']}h",
                pipeline_stats
            ))
        
        # Check success rate SLA
        if success_rate < self.SLA_TARGETS['success_rate']['critical']:
            alerts.append(self._create_alert(
                AlertLevel.CRITICAL,
                'Success Rate SLA Breach',
                f"Success rate below critical threshold: {success_rate:.2f}% < {self.SLA_TARGETS['success_rate']['critical']}%",
                pipeline_stats
            ))
        elif success_rate < self.SLA_TARGETS['success_rate']['warning']:
            alerts.append(self._create_alert(
                AlertLevel.WARNING,
                'Success Rate Warning',
                f"Success rate below warning threshold: {success_rate:.2f}% < {self.SLA_TARGETS['success_rate']['warning']}%",
                pipeline_stats
            ))
        
        # Check error rate SLA
        if error_rate > self.SLA_TARGETS['error_rate']['critical']:
            alerts.append(self._create_alert(
                AlertLevel.CRITICAL,
                'Error Rate SLA Breach',
                f"Error rate above critical threshold: {error_rate:.2f}% > {self.SLA_TARGETS['error_rate']['critical']}%",
                pipeline_stats
            ))
        elif error_rate > self.SLA_TARGETS['error_rate']['warning']:
            alerts.append(self._create_alert(
                AlertLevel.WARNING,
                'Error Rate Warning',
                f"Error rate above warning threshold: {error_rate:.2f}% > {self.SLA_TARGETS['error_rate']['warning']}%",
                pipeline_stats
            ))
        
        # Check minimum records loaded
        if total_records < self.SLA_TARGETS['records_loaded']['critical']:
            alerts.append(self._create_alert(
                AlertLevel.CRITICAL,
                'Minimum Records SLA Breach',
                f"Too few records loaded: {total_records} < {self.SLA_TARGETS['records_loaded']['critical']}",
                pipeline_stats
            ))
        elif total_records < self.SLA_TARGETS['records_loaded']['warning']:
            alerts.append(self._create_alert(
                AlertLevel.WARNING,
                'Minimum Records Warning',
                f"Below target record count: {total_records} < {self.SLA_TARGETS['records_loaded']['warning']}",
                pipeline_stats
            ))
        
        # Check throughput
        if throughput < self.SLA_TARGETS['throughput']['critical']:
            alerts.append(self._create_alert(
                AlertLevel.CRITICAL,
                'Throughput SLA Breach',
                f"Throughput below critical: {throughput:.2f} records/sec < {self.SLA_TARGETS['throughput']['critical']}",
                pipeline_stats
            ))
        elif throughput < self.SLA_TARGETS['throughput']['warning']:
            alerts.append(self._create_alert(
                AlertLevel.WARNING,
                'Throughput Warning',
                f"Throughput below target: {throughput:.2f} records/sec < {self.SLA_TARGETS['throughput']['warning']}",
                pipeline_stats
            ))
        
        # Store alerts
        self.alerts.extend(alerts)
        
        # Send email notifications
        if alerts:
            self._send_alerts(alerts)
        
        return [alert['message'] for alert in alerts]
    
    def _create_alert(self, level: AlertLevel, title: str, message: str, 
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert object"""
        return {
            'level': level.value,
            'title': title,
            'message': message,
            'timestamp': datetime.utcnow(),
            'context': context
        }
    
    def _send_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """Send alert emails"""
        if not self.alert_recipients or not self.smtp_config['host']:
            logger.warning("Email alerting not configured")
            return False
        
        try:
            # Group alerts by level
            critical_alerts = [a for a in alerts if a['level'] == AlertLevel.CRITICAL.value]
            warning_alerts = [a for a in alerts if a['level'] == AlertLevel.WARNING.value]
            
            if not critical_alerts and not warning_alerts:
                return True
            
            # Create email
            msg = MIMEMultipart('html')
            msg['Subject'] = f"MCP-BD Explorer SLA Alert - {len(critical_alerts)} Critical, {len(warning_alerts)} Warnings"
            msg['From'] = self.smtp_config['user']
            msg['To'] = ', '.join(self.alert_recipients)
            
            # Build HTML body
            html_body = self._build_alert_email_html(critical_alerts, warning_alerts)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['user'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"SLA alerts sent to {len(self.alert_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SLA alerts: {e}")
            return False
    
    def _build_alert_email_html(self, critical_alerts: List[Dict], 
                               warning_alerts: List[Dict]) -> str:
        """Build HTML email body"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .critical { background-color: #ffcccc; border-left: 4px solid #cc0000; }
                .warning { background-color: #ffffcc; border-left: 4px solid #ffcc00; }
                .title { font-weight: bold; margin-bottom: 5px; }
                .timestamp { font-size: 0.9em; color: #666; }
            </style>
        </head>
        <body>
            <h2>MCP-BD Explorer - SLA Alert Report</h2>
            <p>Pipeline SLA violations detected at {}</p>
        """.format(datetime.utcnow().isoformat())
        
        if critical_alerts:
            html += "<h3 style='color: #cc0000;'>Critical Alerts ({}):</h3>".format(len(critical_alerts))
            for alert in critical_alerts:
                html += f"""
                <div class='alert critical'>
                    <div class='title'>⚠️ {alert['title']}</div>
                    <div>{alert['message']}</div>
                    <div class='timestamp'>{alert['timestamp'].isoformat()}</div>
                </div>
                """
        
        if warning_alerts:
            html += "<h3 style='color: #ff9900;'>Warnings ({}):</h3>".format(len(warning_alerts))
            for alert in warning_alerts:
                html += f"""
                <div class='alert warning'>
                    <div class='title'>⚠️ {alert['title']}</div>
                    <div>{alert['message']}</div>
                    <div class='timestamp'>{alert['timestamp'].isoformat()}</div>
                </div>
                """
        
        html += """
        </body>
        </html>
        """
        return html
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts"""
        critical = [a for a in self.alerts if a['level'] == AlertLevel.CRITICAL.value]
        warnings = [a for a in self.alerts if a['level'] == AlertLevel.WARNING.value]
        
        return {
            'total_alerts': len(self.alerts),
            'critical_count': len(critical),
            'warning_count': len(warnings),
            'recent_alerts': self.alerts[-10:],
            'last_alert_time': self.alerts[-1]['timestamp'] if self.alerts else None
        }


# Usage example
if __name__ == "__main__":
    monitor = SLAMonitor(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="alerts@example.com",
        smtp_password="password",
        alert_recipients=["ops@example.com"]
    )
    
    # Simulate pipeline stats
    pipeline_stats = {
        'total_records': 50000,
        'inserted': 45000,
        'updated': 4500,
        'failed': 500,
        'duration_seconds': 180,  # 3 minutes
        'start_time': datetime.utcnow() - timedelta(seconds=180)
    }
    
    alerts = monitor.evaluate_load_pipeline(pipeline_stats)
    print(f"Generated {len(alerts)} alerts")
    for alert in alerts:
        print(f"- {alert}")
    
    print(f"\nSummary: {monitor.get_alert_summary()}")
