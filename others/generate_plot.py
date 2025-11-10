import matplotlib.pyplot as plt
import numpy as np

# Example data
log_length = np.array([25, 50, 75, 100, 125, 150, 175, 200, 225, 250])

evaluation_times = np.array([
    [0.5, 1, 2, 5, 10, 20, 40, 80, 160, 320],
    [0.6, 1.2, 2.4, 4.8, 9.6, 15, 25, 35, 50, 70],
    [0.5, 1, 2, 4, 8, 20, 50, 100, 200, 400],
    [1, 10, 100, 500, 1000, 2000, 3000, 5000, 8000, 10000],
    [0.5, 2, 5, 10, 20, 40, 70, 100, 150, 200],
    [0.4, 0.8, 1.2, 2, 3, 5, 8, 12, 16, 20],
    [0.5, 2, 6, 15, 30, 50, 80, 120, 180, 250],
    [0.3, 0.6, 1, 1.5, 2, 3, 5, 7, 10, 13]
])

labels = [
    "Lookup Consistency",
    "Value Consistency",
    "Value Freshness",
    "Key Consistency",
    "Find Node Lookup Consistency",
    "Responsibility Transfer",
    "Membership Guarantee",
    "Reachability"
]

# Plot
for i, label in enumerate(labels):
    plt.plot(log_length, evaluation_times[i], marker='o', label=label)

plt.yscale("log")
plt.xlabel("Log Length")
plt.ylabel("Evaluation Time (s)")
plt.title("Evaluation Time vs Log Length (5 nodes)")
plt.legend()
plt.grid(True, which="both", linestyle="--", linewidth=0.5)

# Save as high-quality PDF
plt.tight_layout()
plt.savefig("plot.pdf", format="pdf", bbox_inches="tight")
plt.close()
