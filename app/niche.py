import json
import os
from typing import Any, Dict, Iterable, List, Optional

from openai import OpenAI


DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _ensure_openai_client() -> OpenAI:
	api_key = os.getenv("OPENAI_API_KEY")
	if not api_key:
		raise RuntimeError("OPENAI_API_KEY is not set.")
	client = OpenAI(api_key=api_key)
	return client


def _chunk(items: List[Dict[str, Any]], chunk_size: int) -> Iterable[List[Dict[str, Any]]]:
	for i in range(0, len(items), max(1, chunk_size)):
		yield items[i : i + chunk_size]


def _build_prompt(niche: str, items: List[Dict[str, Any]]) -> str:
	lines = [
		"Você é um analista. Retorne APENAS um JSON array com licitações relevantes ao nicho informado.",
		"Cada item deve ter: titulo, orgao, modalidade, valor (número ou null), valor_texto (string ou null), link.",
		"Nicho alvo: " + niche,
		"Itens para avaliar:",
	]
	for item in items:
		lines.append(json.dumps(item, ensure_ascii=False))
	return "\n".join(lines)


def filter_by_niche_with_openai(
	licitacoes: List[Dict[str, Any]],
	niche: str,
	model: Optional[str] = None,
	chunk_size: int = 25,
	max_chunks: Optional[int] = None,
) -> List[Dict[str, Any]]:
	if not licitacoes:
		return []
	client = _ensure_openai_client()
	chosen_model = model or DEFAULT_MODEL
	final_results: List[Dict[str, Any]] = []

	for idx, subset in enumerate(_chunk(licitacoes, chunk_size)):
		if max_chunks is not None and idx >= max_chunks:
			break
		prompt = _build_prompt(niche, subset)
		resp = client.chat.completions.create(
			model=chosen_model,
			messages=[
				{"role": "system", "content": "Responda somente com JSON válido."},
				{"role": "user", "content": prompt},
			],
			temperature=0.2,
		)
		content = (resp.choices[0].message.content or "").strip()
		try:
			parsed = json.loads(content)
			if isinstance(parsed, list):
				final_results.extend(parsed)
			elif isinstance(parsed, dict) and "itens" in parsed and isinstance(parsed["itens"], list):
				final_results.extend(parsed["itens"])  # fallback
		except json.JSONDecodeError:
			continue

	return final_results