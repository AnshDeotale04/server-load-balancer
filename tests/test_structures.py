import time
from load_balancer import Request, Server, LoadBalancer

# Create 4 servers with different latencies
servers = [
    Server(id="Server-1", latency_ms=10),
    Server(id="Server-2", latency_ms=15),
    Server(id="Server-3", latency_ms=20),
    Server(id="Server-4", latency_ms=25),
]

# Create load balancer
lb = LoadBalancer(servers=servers)

# Simulate arrival of 10 requests
current_time = 0.0
for i in range(10):
    req = Request(id=f"REQ-{i+1}", arrival_time=current_time)
    assigned = lb.route(req)
    print(f"[{current_time:.1f}s] REQ-{i+1} → {assigned.id} (latency: {assigned.latency_ms}ms, load: {assigned.load_percent:.0f}%)")
    current_time += 0.1

print("\n--- Server Queues After Routing ---")
for server in servers:
    print(f"{server.id}: {len(server.queue)} queued | Load: {server.load_percent:.0f}%")

print("\n--- Routing Log ---")
for req, server, reason in lb.routing_log:
    print(f"{req.id} → {server.id} ({reason})")
