"""
Server Info Module
Provides server statistics and system information
"""
from datetime import datetime
from typing import Dict, Any, Optional
import platform
import psutil
import logging

logger = logging.getLogger(__name__)


class ServerInfo:
    """Server information and statistics"""
    
    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get basic system information"""
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "timestamp": datetime.utcnow()
        }
    
    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "cpu_count_physical": psutil.cpu_count(logical=False),
                "cpu_freq_current": cpu_freq.current if cpu_freq else None,
                "cpu_freq_min": cpu_freq.min if cpu_freq else None,
                "cpu_freq_max": cpu_freq.max if cpu_freq else None,
                "load_avg": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get CPU info: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow()}
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_used": memory.used,
                "memory_percent": memory.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get memory info: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow()}
    
    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk information"""
        try:
            disk = psutil.disk_usage('/')
            
            return {
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_percent": disk.percent,
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get disk info: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow()}
    
    @staticmethod
    def get_network_info() -> Dict[str, Any]:
        """Get network information"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
                "connections_count": len(net_connections),
                "timestamp": datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow()}
