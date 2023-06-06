import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

first_last_commit_df = pd.read_csv('first_last_commit.csv')

# Convert the 'First Commit Date' and 'Last Commit Date' columns to datetime
first_last_commit_df['First Commit Date'] = pd.to_datetime(first_last_commit_df['First Commit Date'])
first_last_commit_df['Last Commit Date'] = pd.to_datetime(first_last_commit_df['Last Commit Date'])

# Calculate the time it takes for an EIP to be passed in months
first_last_commit_df['Time to Pass'] = (first_last_commit_df['Last Commit Date'] - first_last_commit_df['First Commit Date']).dt.days / 30

# Remove outliers
Q1 = first_last_commit_df['Time to Pass'].quantile(0.25)
Q3 = first_last_commit_df['Time to Pass'].quantile(0.75)
IQR = Q3 - Q1
first_last_commit_df = first_last_commit_df[~((first_last_commit_df['Time to Pass'] < (Q1 - 1.5 * IQR)) | (first_last_commit_df['Time to Pass'] > (Q3 + 1.5 * IQR)))]

# Plot a histogram of the times
sns.histplot(first_last_commit_df['Time to Pass'], kde=False, bins=30)
plt.xlabel('Time to Pass (months)')
plt.ylabel('Number of EIPs')
plt.title('Histogram of Time to Pass for EIPs')
plt.savefig('histogram.png')
plt.close()

# Plot a box and whisker plot of the times
sns.boxplot(x=first_last_commit_df['Time to Pass'])
plt.xlabel('Time to Pass (months)')
plt.title('Box and Whisker Plot of Time to Pass for EIPs')
plt.savefig('boxplot.png')
plt.close()

# Calculate the average time it takes for an EIP to be passed
average_time_to_pass = np.mean(first_last_commit_df['Time to Pass'])
print(f"The average time it takes for an EIP to be passed is {average_time_to_pass} months.")
