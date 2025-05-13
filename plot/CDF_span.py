# Plot the cumulative distribution function plot of library life spans

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
data = pd.read_csv('data/Exp1 - span per tag.csv')

# Extract the span in days
span_days = data['span per tag (days)']

# Calculate the CDF
sorted_data = np.sort(span_days)
cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)

# Find positions for all thresholds
def find_threshold(cdf_value):
    idx = np.where(cdf >= cdf_value)[0][0]
    return sorted_data[idx], cdf[idx]

x_50, y_50 = find_threshold(0.50)
x_90, y_90 = find_threshold(0.90)
x_99, y_99 = find_threshold(0.99)

# Create the plot
plt.figure(figsize=(12, 7))
plt.plot(sorted_data, cdf, marker='.', linestyle='none', linewidth=1, markersize=5, label='CDF', color='dimgrey')

# Add 50% threshold (median)
plt.hlines(y=0.50, xmin=0, xmax=x_50, colors='orange', linestyles='--', alpha=0.7)
plt.vlines(x=x_50, ymin=0, ymax=y_50, colors='orange', linestyles='--', alpha=0.7)
plt.plot(x_50, y_50, 'o', color='orange', markersize=5, label=f'Median: {x_50:.0f} days')

# Add 90% threshold
plt.hlines(y=0.90, xmin=0, xmax=x_90, colors='purple', linestyles='--', alpha=0.7)
plt.vlines(x=x_90, ymin=0, ymax=y_90, colors='purple', linestyles='--', alpha=0.7)
plt.plot(x_90, y_90, 'o', color='purple', markersize=5, label=f'90% interval is less than {x_90:.0f} days')

# Add 99% threshold
plt.hlines(y=0.99, xmin=0, xmax=x_99, colors='red', linestyles='--', alpha=0.7)
plt.vlines(x=x_99, ymin=0, ymax=y_99, colors='red', linestyles='--', alpha=0.7)
plt.plot(x_99, y_99, 'o', color='red', markersize=5, label=f'99% interval is less than {x_99:.0f} days')

# Set axis limits and labels
plt.xlim(0, max(sorted_data)*1.05)  # X from 0 to 5% beyond max value
plt.ylim(0, 1.05)                   # Y from 0 to 1.05
plt.xlabel('Update Interval (days)', fontsize=12)
plt.ylabel('Cumulative Percentage', fontsize=12)
plt.title('Cumulative Distribution Function of Library Update Intervals', fontsize=14)

# Add reference lines at 0.5, 0.9, 0.99
for y in [0.50, 0.90, 0.99]:
    plt.axhline(y=y, color='gray', linestyle=':', alpha=0.3)

# Customize grid and legend
plt.grid(True, which='both', alpha=0.2)
plt.legend(loc='lower right', fontsize=10, framealpha=1)
plt.tight_layout()

# Show the plot
plt.show()