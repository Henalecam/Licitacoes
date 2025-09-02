import json
import os
from pathlib import Path
from typing import Any, List


def ensure_parent_directory_exists(file_path: str) -> None:
	parent = Path(file_path).expanduser().resolve().parent
	parent.mkdir(parents=True, exist_ok=True)


def save_json(file_path: str, data: Any) -> None:
	ensure_parent_directory_exists(file_path)
	with open(file_path, "w", encoding="utf-8") as file_obj:
		json.dump(data, file_obj, ensure_ascii=False, indent=2)


def load_json(file_path: str) -> Any:
	with open(file_path, "r", encoding="utf-8") as file_obj:
		return json.load(file_obj)


def default_output_path() -> str:
	return os.getenv("OUTPUT_PATH", "./data/licitacoes.json")