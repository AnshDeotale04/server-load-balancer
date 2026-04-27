from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque


@dataclass
class Request:
    """Represents a single request routed through the load balancer."""
    id: str
    arrival_time: float  # seconds
    assigned_server: Optional['Server'] = None
    completion_time: Optional[float] = None
    
    @property
    def latency(self) -> Optional[float]:
        """Calculate latency: time from arrival to completion."""
        if self.completion_time is None:
            return None
        return self.completion_time - self.arrival_time


@dataclass
class Server:
    """Represents a backend server with latency and request queue."""
    id: str
    latency_ms: float  # network latency in milliseconds
    queue: deque = field(default_factory=deque)  # pending requests
    processed: List[Request] = field(default_factory=list)  # completed requests
    health_status: str = "HEALTHY"
    
    @property
    def load_percent(self) -> float:
        """Current load as percentage (queue size relative to some capacity)."""
        # Simple model: 1 request per unit capacity, full at 100 requests
        capacity = 100
        return (len(self.queue) / capacity) * 100
    
    def add_request(self, request: Request) -> None:
        """Add request to queue."""
        request.assigned_server = self
        self.queue.append(request)
    
    def process_request(self, current_time: float) -> Optional[Request]:
        """
        Process next request in queue.
        Returns the completed request (with completion_time set).
        """
        if not self.queue:
            return None
        
        request = self.queue.popleft()
        # Completion time = arrival + network latency (in seconds)
        request.completion_time = current_time + (self.latency_ms / 1000.0)
        self.processed.append(request)
        return request


@dataclass
class LoadBalancer:
    """Routes requests to servers based on proximity and load."""
    servers: List[Server] = field(default_factory=list)
    routing_log: List[tuple] = field(default_factory=list)  # (request, server, reason)
    
    def route(self, request: Request) -> Server:
        """
        Route request to best server.
        Priority: closest server (latency) with load < 80%
        Fallback: least loaded server if all are full
        """
        # Sort servers by latency (closest first)
        sorted_servers = sorted(self.servers, key=lambda s: s.latency_ms)
        
        # Find first server with load < 80%
        for server in sorted_servers:
            if server.health_status == "HEALTHY" and server.load_percent < 80:
                server.add_request(request)
                self.routing_log.append((request, server, f"load={server.load_percent:.0f}%"))
                return server
        
        # Fallback: route to least loaded server when all are >= 80%
        least_loaded = min(self.servers, key=lambda s: s.load_percent)
        least_loaded.add_request(request)
        self.routing_log.append((request, least_loaded, f"OVERLOAD, least-loaded={least_loaded.id}"))
        return least_loaded
    
    def process_all_requests(self) -> None:
        """Process all queued requests across all servers."""
        for server in self.servers:
            while server.queue:
                server.process_request(0.0)  # Simple: all complete at time 0
    
    def get_all_latencies(self) -> List[float]:
        """Get all request latencies."""
        latencies = []
        for server in self.servers:
            for req in server.processed:
                if req.latency is not None:
                    latencies.append(req.latency * 1000)  # Convert to ms
        return sorted(latencies)
    
    def percentile(self, latencies: List[float], p: int) -> float:
        """Calculate percentile (e.g., P50, P95, P99)."""
        if not latencies:
            return 0.0
        idx = int(len(latencies) * (p / 100))
        return latencies[min(idx, len(latencies) - 1)]