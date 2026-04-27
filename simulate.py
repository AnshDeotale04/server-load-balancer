import sys
from pathlib import Path

# Add src folder to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from load_balancer import Request, Server, LoadBalancer

def simulate_round_robin(servers, num_requests):
    """Simulate with simple round-robin (baseline)."""
    processed = []
    current_time = 0.0
    requests_per_batch = 15
    rr_index = 0
    
    for i in range(num_requests):
        if i > 0 and i % requests_per_batch == 0:
            current_time += 1.0
        
        req = Request(id=f"RR-{i+1}", arrival_time=current_time)
        server = servers[rr_index % len(servers)]
        rr_index += 1
        
        req.assigned_server = server
        req.completion_time = current_time + (server.latency_ms / 1000.0)
        processed.append(req)
    
    return processed

# Create 4 servers
servers = [
    Server(id="Server-1", latency_ms=10),
    Server(id="Server-2", latency_ms=15),
    Server(id="Server-3", latency_ms=20),
    Server(id="Server-4", latency_ms=25),
]

lb = LoadBalancer(servers=servers)

# ========== ROUND-ROBIN BASELINE (FIRST) ==========
print("="*60)
print("=== ROUND-ROBIN BASELINE ===\n")

rr_processed = simulate_round_robin(servers, 200)
rr_latencies = sorted([req.latency * 1000 for req in rr_processed])

rr_p50 = rr_latencies[len(rr_latencies) // 2]
rr_p95 = rr_latencies[int(len(rr_latencies) * 0.95)]
rr_p99 = rr_latencies[int(len(rr_latencies) * 0.99)]

print(f"P50: {rr_p50:.2f}ms")
print(f"P95: {rr_p95:.2f}ms")
print(f"P99: {rr_p99:.2f}ms")
print(f"Average: {sum(rr_latencies)/len(rr_latencies):.2f}ms\n")

for server in servers:
    rr_count = sum(1 for req in rr_processed if req.assigned_server == server)
    print(f"{server.id}: {rr_count:3d} requests")

# ========== PROXIMITY ALGORITHM (SECOND) ==========
print(f"\n{'='*60}")
print("=== PROXIMITY ALGORITHM ===\n")

# Reset servers for proximity simulation
for server in servers:
    server.queue = __import__('collections').deque()
    server.processed = []

# Simulate 200 requests over time
current_time = 0.0
requests_per_batch = 15

for i in range(200):
    if i > 0 and i % requests_per_batch == 0:
        current_time += 1.0
    
    req = Request(id=f"REQ-{i+1}", arrival_time=current_time)
    assigned = lb.route(req)
    
    # Print sample of first 15 and last 10
    if i < 15 or i >= 190:
        print(f"REQ-{i+1:3d} @ {current_time:.1f}s -> {assigned.id} (latency: {assigned.latency_ms}ms, load: {assigned.load_percent:5.1f}%)")
    elif i == 15:
        print("... [routing continues] ...\n")

# Process all requests
print(f"\n[Processing requests...]\n")
for server in servers:
    while server.queue:
        req = server.queue.popleft()
        req.completion_time = req.arrival_time + (server.latency_ms / 1000.0)
        server.processed.append(req)

# Calculate metrics
latencies = []
for server in servers:
    for req in server.processed:
        latencies.append(req.latency * 1000)
latencies.sort()

p50 = latencies[len(latencies) // 2] if latencies else 0
p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0

print(f"P50: {p50:.2f}ms")
print(f"P95: {p95:.2f}ms")
print(f"P99: {p99:.2f}ms")
print(f"Average: {sum(latencies)/len(latencies):.2f}ms\n")

for server in servers:
    total_latency = sum(req.latency * 1000 for req in server.processed)
    avg_latency = total_latency / len(server.processed) if server.processed else 0
    print(f"{server.id}: {len(server.processed):3d} requests | avg latency: {avg_latency:6.2f}ms")

# ========== COMPARISON ==========
avg_all = sum(latencies) / len(latencies)
rr_avg = sum(rr_latencies) / len(rr_latencies)

print(f"\n{'='*60}")
print("=== COMPARISON ===\n")
print(f"Metric      | Round-Robin | Proximity | Improvement")
print(f"-" * 55)
print(f"P50         | {rr_p50:11.2f}ms | {p50:9.2f}ms | {((rr_p50-p50)/rr_p50*100):+.1f}%")
print(f"P95         | {rr_p95:11.2f}ms | {p95:9.2f}ms | {((rr_p95-p95)/rr_p95*100):+.1f}%")
print(f"P99         | {rr_p99:11.2f}ms | {p99:9.2f}ms | {((rr_p99-p99)/rr_p99*100):+.1f}%")
print(f"Average     | {rr_avg:11.2f}ms | {avg_all:9.2f}ms | {((rr_avg-avg_all)/rr_avg*100):+.1f}%")