import pandas as pd
df = pd.read_csv("generated_files/new_custom.csv")

# Filter the DataFrame for issues assigned to Rishika
filtered_df = df[df['assignee'] == 'Rishika']

# Save the filtered DataFrame to output.csv
filtered_df.to_csv('generated_files/output.csv', index=False)
