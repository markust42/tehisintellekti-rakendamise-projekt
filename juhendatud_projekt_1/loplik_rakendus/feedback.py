import csv
import os

from config import LOG_FILE


def log_feedback(timestamp, prompt, filters, context_ids, context_names,
                 response, rating, error_category):
    file_exists = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Aeg", "Kasutaja päring", "Filtrid", "Leitud ID-d",
                "Leitud ained", "LLM Vastus", "Hinnang", "Veatüüp",
            ])
        writer.writerow([
            timestamp, prompt, filters,
            str(context_ids), str(context_names),
            response, rating, error_category,
        ])
