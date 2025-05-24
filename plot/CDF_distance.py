# Plot the cumulative distribution function plot of library life spans

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import PercentFormatter

# Load the data
data1 = pd.read_csv('data/hits_distance_to_latest.csv')
data2 = pd.read_csv('data/hits_distance_to_current.csv')

# Extract the distance values in years
distance1 = data1['distance (years)']
distance2 = data2['distance (years)']

# Create figure and axis
plt.figure(figsize=(10, 6))

# Calculate CDF for both datasets
def calculate_cdf(data):
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data)+1) / len(sorted_data)
    return sorted_data, cdf

x1, y1 = calculate_cdf(distance1)
x2, y2 = calculate_cdf(distance2)

# Plot both CDFs
plt.plot(x1, y1, label='UAL (average: 1.2)', color='blue')
plt.plot(x2, y2, label='UAC (average: 5.4)', color='orange')

# Add vertical lines at year=1 and year=5 with percentage labels
for year in [1, 5]:
    # Find the percentage for Dataset 1
    idx1 = np.searchsorted(x1, year, side='right') - 1
    if idx1 >= 0:
        percent1 = y1[idx1] * 100
        plt.vlines(year, 0, y1[idx1], color='blue', linestyle='--', alpha=0.5)
        plt.text(year, y1[idx1], f'{percent1:.1f}%', color='blue', 
                 ha='right', va='bottom', backgroundcolor='white')
    
    # Find the percentage for Dataset 2
    idx2 = np.searchsorted(x2, year, side='right') - 1
    if idx2 >= 0:
        percent2 = y2[idx2] * 100
        plt.vlines(year, 0, y2[idx2], color='orange', linestyle='--', alpha=0.5)
        plt.text(year, y2[idx2], f'{percent2:.1f}%', color='orange', 
                 ha='left', va='top', backgroundcolor='white')

# Add a vertical line at the year markers
plt.axvline(1, color='gray', linestyle=':', alpha=0.3)
plt.axvline(5, color='gray', linestyle=':', alpha=0.3)

# Format the plot
plt.title('Cumulative Distribution Function')
plt.xlabel('Year')
plt.ylabel('Cumulative Percentage')
plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
plt.grid(True, which='both', linestyle='--', alpha=0.5)
plt.legend()
plt.tight_layout()

plt.show()