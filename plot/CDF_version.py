# Plot the cumulative distribution function plot of library life spans

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from matplotlib.ticker import PercentFormatter

# Load the data
df = pd.read_csv('data/version_hits_distribution.csv')


# Plot CDF for each column
plt.figure(figsize=(8, 6))

# for col in df.columns:
#     data = df[col].dropna().values  # Drop NaNs if any
#     sorted_data = np.sort(data)
#     cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
#     plt.plot(sorted_data, cdf, label=str(col))

for col in df.columns:
    data = df[col].dropna().values
    average = np.mean(data)
    kde = gaussian_kde(data)
    
    # Create a range of values to evaluate the CDF on
    x_vals = np.linspace(min(data), max(data), 500)
    cdf_vals = np.array([kde.integrate_box_1d(-np.inf, x) for x in x_vals])
    
    plt.plot(x_vals, cdf_vals, label=str(col) + f' (avg: {average:.1f} versions)')

# Custom ticks
# x_ticks = np.linspace(df.min().min(), df.max().max(), 11)  # 15 evenly spaced x-axis ticks
y_ticks = np.linspace(0.2, 1, 9)  # 21 evenly spaced y-axis ticks (0.0 to 1.0)

# plt.xticks(x_ticks)
plt.yticks(y_ticks)

# Plot settings
plt.title('CDF Curves for Each Column')
plt.xlabel('Number of Versions')
plt.ylabel('Library Cumulative Probability')

plt.xlim(0, 100)
plt.legend()
plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
# plt.axhline(0.9, color='gray', linestyle='-', alpha=0.5, label='0.9')
plt.grid(True)
plt.tight_layout()
plt.show()