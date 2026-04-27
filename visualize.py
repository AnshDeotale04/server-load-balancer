import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import matplotlib.pyplot as plt
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

# Run proximity simulation
servers = [
    Server(id="Server-1", latency_ms=10),
    Server(id="Server-2", latency_ms=15),
    Server(id="Server-3", latency_ms=20),
    Server(id="Server-4", latency_ms=25),
]

lb = LoadBalancer(servers=servers)

# Simulate requests
current_time = 0.0
requests_per_batch = 15

for i in range(200):
    if i > 0 and i % requests_per_batch == 0:
        current_time += 1.0
    
    req = Request(id=f"REQ-{i+1}", arrival_time=current_time)
    assigned = lb.route(req)

# Process all requests
for server in servers:
    while server.queue:
        req = server.queue.popleft()
        req.completion_time = req.arrival_time + (server.latency_ms / 1000.0)
        server.processed.append(req)

# Get latencies
latencies = sorted([req.latency * 1000 for server in servers for req in server.processed])
p50 = latencies[len(latencies) // 2]
p95 = latencies[int(len(latencies) * 0.95)]
p99 = latencies[int(len(latencies) * 0.99)]

# Round-robin baseline
rr_processed = simulate_round_robin(servers, 200)
rr_latencies = sorted([req.latency * 1000 for req in rr_processed])
rr_p99 = rr_latencies[int(len(rr_latencies) * 0.99)]

# Create figure with 4 subplots
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Load Balancer Performance Analysis', fontsize=16, fontweight='bold')

# 1. Latency distribution (histogram)
ax1 = axs[0, 0]
ax1.hist(latencies, bins=20, color='steelblue', edgecolor='black', alpha=0.7, label='Proximity')
ax1.hist(rr_latencies, bins=20, color='coral', edgecolor='black', alpha=0.5, label='Round-Robin')
ax1.axvline(p99, color='steelblue', linestyle='--', linewidth=2, label=f'P99 (Proximity): {p99:.1f}ms')
ax1.axvline(rr_p99, color='coral', linestyle='--', linewidth=2, label=f'P99 (RR): {rr_p99:.1f}ms')
ax1.set_xlabel('Latency (ms)', fontweight='bold')
ax1.set_ylabel('Frequency', fontweight='bold')
ax1.set_title('Latency Distribution', fontweight='bold')
ax1.legend()
ax1.grid(alpha=0.3)

# 2. Requests per server (bar chart)
ax2 = axs[0, 1]
server_names = [s.id for s in servers]
request_counts = [len(s.processed) for s in servers]
colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
bars = ax2.bar(server_names, request_counts, color=colors, edgecolor='black', alpha=0.8)
ax2.set_ylabel('Number of Requests', fontweight='bold')
ax2.set_title('Requests Routed per Server', fontweight='bold')
ax2.grid(axis='y', alpha=0.3)
# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height,
             f'{int(height)}',
             ha='center', va='bottom', fontweight='bold')

# 3. Average latency per server (bar chart)
ax3 = axs[1, 0]
avg_latencies = []
for server in servers:
    if server.processed:
        avg = sum(req.latency * 1000 for req in server.processed) / len(server.processed)
        avg_latencies.append(avg)
    else:
        avg_latencies.append(0)

bars = ax3.bar(server_names, avg_latencies, color=colors, edgecolor='black', alpha=0.8)
ax3.set_ylabel('Average Latency (ms)', fontweight='bold')
ax3.set_title('Average Latency per Server', fontweight='bold')
ax3.grid(axis='y', alpha=0.3)
# Add value labels
for bar in bars:
    height = bar.get_height()
    if height > 0:
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.1f}ms',
                 ha='center', va='bottom', fontweight='bold')

# 4. Comparison: Proximity vs Round-Robin
ax4 = axs[1, 1]
metrics = ['P50', 'P95', 'P99', 'Average']
proximity_vals = [
    p50,
    latencies[int(len(latencies) * 0.95)],
    p99,
    sum(latencies) / len(latencies)
]
rr_vals = [
    rr_latencies[len(rr_latencies) // 2],
    rr_latencies[int(len(rr_latencies) * 0.95)],
    rr_p99,
    sum(rr_latencies) / len(rr_latencies)
]

x = range(len(metrics))
width = 0.35
bars1 = ax4.bar([i - width/2 for i in x], proximity_vals, width, label='Proximity', color='steelblue', edgecolor='black', alpha=0.8)
bars2 = ax4.bar([i + width/2 for i in x], rr_vals, width, label='Round-Robin', color='coral', edgecolor='black', alpha=0.8)

ax4.set_ylabel('Latency (ms)', fontweight='bold')
ax4.set_title('Algorithm Comparison', fontweight='bold')
ax4.set_xticks(x)
ax4.set_xticklabels(metrics)
ax4.legend()
ax4.grid(axis='y', alpha=0.3)

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                 f'{height:.1f}',
                 ha='center', va='bottom', fontsize=8, fontweight='bold')

plt.tight_layout()
plt.show()
