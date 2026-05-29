import os
import pandas as pd
from dbfread import DBF

folder = r"C:\Users\Supreme Court\Desktop\allreportctms"
output_file = os.path.join(folder, "merged_output.xlsx")

all_data = []

# Loop through all DBF files in folder
for file in os.listdir(folder):
    if file.lower().endswith(".dbf"):
        file_path = os.path.join(folder, file)
        print(f"Reading: {file}")

        # Read DBF into DataFrame
        table = DBF(file_path, load=True)
        df = pd.DataFrame(iter(table))

        # Optional: add source file column (useful for tracking)
        df["source_file"] = file

        all_data.append(df)

# Merge all DataFrames
if all_data:
    merged_df = pd.concat(all_data, ignore_index=True)

    # Export to Excel
    merged_df.to_excel(output_file, index=False)

    print(f"\nDone! File saved at:\n{output_file}")
else:
    print("No DBF files found.")