import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MemoryValidator:
    def __init__(self, log_file="db/memory_log.json", retention_days=7):
        self.log_file = log_file
        self.retention_days = retention_days
        self.memory_data = self._load_memory()

    def _load_memory(self):
        if not os.path.exists(self.log_file):
            return {"recent_topics": []}
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"recent_topics": []}

    def _save_memory(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory_data, f, indent=2)

    def validate_and_log(self, news_items: list) -> list:
        """
        Filters out news items that have been seen recently.
        Logs the new items.
        """
        self._cleanup_old_entries()
        
        valid_items = []
        # Create a set of existing IDs for fast lookup
        existing_ids = {item.get('id') for item in self.memory_data.get("recent_topics", []) if item.get('id')}
        
        for item in news_items:
            item_id = item.get('id')
            if not item_id:
                # If no ID, we can't reliably dedupe by ID. 
                # We could check headline similarity, but for now let's allow it 
                # or generate a hash. Let's assume the LLM follows instructions to generate IDs.
                valid_items.append(item)
                continue

            if item_id not in existing_ids:
                valid_items.append(item)
                # Add to memory immediately to prevent duplicates within the same batch
                self._add_to_memory(item)
                existing_ids.add(item_id)
            else:
                logger.info(f"Skipping duplicate news: {item.get('headline')} (ID: {item_id})")
        
        self._save_memory()
        return valid_items

    def _add_to_memory(self, item):
        entry = item.copy()
        entry['timestamp'] = datetime.now().isoformat()
        self.memory_data.setdefault("recent_topics", []).append(entry)

    def _cleanup_old_entries(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        recent = []
        for item in self.memory_data.get("recent_topics", []):
            ts_str = item.get('timestamp')
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts > cutoff:
                        recent.append(item)
                except ValueError:
                    pass # Drop invalid timestamps
        self.memory_data["recent_topics"] = recent
