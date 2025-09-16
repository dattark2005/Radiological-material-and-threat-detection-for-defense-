import psutil
import time
from datetime import datetime, timedelta
from models.database import SystemLog, AnalysisSession, ThreatAssessment, mongo
import logging

class SystemMonitor:
    """System monitoring and metrics collection service."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        
    def get_system_metrics(self):
        """Get current system performance metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network (if available)
            try:
                network = psutil.net_io_counters()
                network_stats = {
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                }
            except:
                network_stats = {}
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime_seconds': (datetime.utcnow() - self.start_time).total_seconds(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': network_stats
            }
        except Exception as e:
            logging.error(f"Error collecting system metrics: {str(e)}")
            return {}
    
    def get_application_metrics(self):
        """Get application-specific metrics from database."""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            last_hour = now - timedelta(hours=1)
            
            # Analysis metrics
            total_analyses = AnalysisSession.query.count()
            analyses_24h = AnalysisSession.query.filter(
                AnalysisSession.created_at >= last_24h
            ).count()
            analyses_1h = AnalysisSession.query.filter(
                AnalysisSession.created_at >= last_hour
            ).count()
            
            # Threat metrics
            total_threats = ThreatAssessment.query.count()
            threats_24h = ThreatAssessment.query.filter(
                ThreatAssessment.created_at >= last_24h
            ).count()
            
            high_threats_24h = ThreatAssessment.query.filter(
                ThreatAssessment.created_at >= last_24h,
                ThreatAssessment.threat_level.in_(['High', 'Very High'])
            ).count()
            
            # Success rates
            completed_analyses = AnalysisSession.query.filter(
                AnalysisSession.status == 'completed'
            ).count()
            
            success_rate = (completed_analyses / total_analyses * 100) if total_analyses > 0 else 0
            
            # Average processing time
            avg_processing_time = db.session.query(
                func.avg(AnalysisSession.processing_time)
            ).filter(
                AnalysisSession.status == 'completed',
                AnalysisSession.processing_time.isnot(None)
            ).scalar() or 0
            
            return {
                'timestamp': now.isoformat(),
                'analyses': {
                    'total': total_analyses,
                    'last_24h': analyses_24h,
                    'last_hour': analyses_1h,
                    'success_rate': round(success_rate, 2),
                    'avg_processing_time': round(float(avg_processing_time), 2)
                },
                'threats': {
                    'total': total_threats,
                    'last_24h': threats_24h,
                    'high_severity_24h': high_threats_24h
                }
            }
        except Exception as e:
            logging.error(f"Error collecting application metrics: {str(e)}")
            return {}
    
    def get_error_metrics(self):
        """Get error and log metrics."""
        try:
            now = datetime.utcnow()
            last_24h = now - timedelta(hours=24)
            
            # Error counts by level
            error_counts = db.session.query(
                SystemLog.level,
                func.count(SystemLog.id)
            ).filter(
                SystemLog.created_at >= last_24h
            ).group_by(SystemLog.level).all()
            
            error_stats = {level: count for level, count in error_counts}
            
            # Recent critical errors
            critical_errors = SystemLog.query.filter(
                SystemLog.level == 'ERROR',
                SystemLog.created_at >= last_24h
            ).order_by(SystemLog.created_at.desc()).limit(10).all()
            
            return {
                'timestamp': now.isoformat(),
                'error_counts_24h': error_stats,
                'recent_critical_errors': [
                    {
                        'timestamp': error.created_at.isoformat(),
                        'message': error.message,
                        'component': error.component
                    } for error in critical_errors
                ]
            }
        except Exception as e:
            logging.error(f"Error collecting error metrics: {str(e)}")
            return {}
    
    def get_health_status(self):
        """Get overall system health status."""
        try:
            system_metrics = self.get_system_metrics()
            app_metrics = self.get_application_metrics()
            error_metrics = self.get_error_metrics()
            
            # Health checks
            health_checks = {
                'database': self._check_database_health(),
                'disk_space': self._check_disk_space(system_metrics),
                'memory_usage': self._check_memory_usage(system_metrics),
                'error_rate': self._check_error_rate(error_metrics),
                'processing_performance': self._check_processing_performance(app_metrics)
            }
            
            # Overall status
            failed_checks = [check for check, status in health_checks.items() if not status['healthy']]
            overall_status = 'healthy' if not failed_checks else 'degraded' if len(failed_checks) <= 2 else 'unhealthy'
            
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'overall_status': overall_status,
                'health_checks': health_checks,
                'failed_checks': failed_checks
            }
        except Exception as e:
            logging.error(f"Error checking health status: {str(e)}")
            return {
                'overall_status': 'unknown',
                'error': str(e)
            }
    
    def _check_database_health(self):
        """Check database connectivity and performance."""
        try:
            # Simple query to test connection
            db.session.execute('SELECT 1')
            return {'healthy': True, 'message': 'Database connection OK'}
        except Exception as e:
            return {'healthy': False, 'message': f'Database error: {str(e)}'}
    
    def _check_disk_space(self, system_metrics):
        """Check available disk space."""
        if not system_metrics or 'disk' not in system_metrics:
            return {'healthy': False, 'message': 'Unable to check disk space'}
        
        disk_percent = system_metrics['disk']['percent']
        if disk_percent > 90:
            return {'healthy': False, 'message': f'Disk usage critical: {disk_percent:.1f}%'}
        elif disk_percent > 80:
            return {'healthy': True, 'message': f'Disk usage warning: {disk_percent:.1f}%', 'warning': True}
        else:
            return {'healthy': True, 'message': f'Disk usage OK: {disk_percent:.1f}%'}
    
    def _check_memory_usage(self, system_metrics):
        """Check memory usage."""
        if not system_metrics or 'memory' not in system_metrics:
            return {'healthy': False, 'message': 'Unable to check memory usage'}
        
        memory_percent = system_metrics['memory']['percent']
        if memory_percent > 90:
            return {'healthy': False, 'message': f'Memory usage critical: {memory_percent:.1f}%'}
        elif memory_percent > 80:
            return {'healthy': True, 'message': f'Memory usage warning: {memory_percent:.1f}%', 'warning': True}
        else:
            return {'healthy': True, 'message': f'Memory usage OK: {memory_percent:.1f}%'}
    
    def _check_error_rate(self, error_metrics):
        """Check error rate in last 24 hours."""
        if not error_metrics or 'error_counts_24h' not in error_metrics:
            return {'healthy': True, 'message': 'No error data available'}
        
        error_counts = error_metrics['error_counts_24h']
        critical_errors = error_counts.get('ERROR', 0)
        
        if critical_errors > 50:
            return {'healthy': False, 'message': f'High error rate: {critical_errors} errors in 24h'}
        elif critical_errors > 20:
            return {'healthy': True, 'message': f'Elevated error rate: {critical_errors} errors in 24h', 'warning': True}
        else:
            return {'healthy': True, 'message': f'Error rate OK: {critical_errors} errors in 24h'}
    
    def _check_processing_performance(self, app_metrics):
        """Check analysis processing performance."""
        if not app_metrics or 'analyses' not in app_metrics:
            return {'healthy': True, 'message': 'No processing data available'}
        
        success_rate = app_metrics['analyses']['success_rate']
        avg_time = app_metrics['analyses']['avg_processing_time']
        
        if success_rate < 80:
            return {'healthy': False, 'message': f'Low success rate: {success_rate}%'}
        elif avg_time > 300:  # 5 minutes
            return {'healthy': False, 'message': f'Slow processing: {avg_time:.1f}s average'}
        elif success_rate < 95 or avg_time > 120:  # 2 minutes
            return {'healthy': True, 'message': f'Performance warning: {success_rate}% success, {avg_time:.1f}s avg', 'warning': True}
        else:
            return {'healthy': True, 'message': f'Processing OK: {success_rate}% success, {avg_time:.1f}s avg'}

# Global monitor instance
system_monitor = SystemMonitor()
