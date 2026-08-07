import json
import re
from pathlib import Path
from typing import Any


class KnowledgeBaseService:
    def __init__(self, file_path: Path | None = None) -> None:
        path = file_path or Path(__file__).parents[1] / "data" / "knowledge_base.json"
        self.entries: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))

    def search(self, query: str) -> dict[str, Any] | None:
        normalized_query = self._normalize(query)
        padded_query = f" {normalized_query} "
        best_entry = None
        best_score = 0

        for entry in self.entries:
            terms = [entry["title"], *entry["keywords"]]
            normalized_terms = filter(None, (self._normalize(term) for term in terms))
            matches = [term for term in normalized_terms if f" {term} " in padded_query]
            score = max((len(term.split()) * 10 + len(term) for term in matches), default=0)
            if score > best_score:
                best_entry, best_score = entry, score

        return best_entry

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9\s]", " ", value.lower()).strip()


knowledge_base_service = KnowledgeBaseService()