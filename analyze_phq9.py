from phq9_tools import summarize_results_folder, export_summary, character_item_detail
import os

RESULTS_DIR = "PHQ9 Conversation"
ANALYSIS_DIR = "analysis"

# Make sure the output folder exists
os.makedirs(ANALYSIS_DIR, exist_ok=True)

print("🔍 Analyzing PHQ-9 results...\n")

# Build summaries
df_summary = summarize_results_folder(RESULTS_DIR)
df_detail = character_item_detail(RESULTS_DIR)

# Define file paths
summary_csv = os.path.join(ANALYSIS_DIR, "phq9_summary.csv")
summary_xlsx = os.path.join(ANALYSIS_DIR, "phq9_summary.xlsx")
detail_csv = os.path.join(ANALYSIS_DIR, "phq9_detail.csv")
detail_xlsx = os.path.join(ANALYSIS_DIR, "phq9_detail.xlsx")

# Export results to the analysis folder
export_summary(df_summary, csv_path=summary_csv, xlsx_path=summary_xlsx)
export_summary(df_detail, csv_path=detail_csv, xlsx_path=detail_xlsx)

# Final confirmation
print("✅ Exports complete!")
print(f"- {summary_csv}")
print(f"- {summary_xlsx}")
print(f"- {detail_csv}")
print(f"- {detail_xlsx}")
