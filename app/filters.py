from typing import Iterable, List, Optional, Dict, Any


def parse_brl_to_float(value_text: Optional[str]) -> Optional[float]:
	if value_text is None:
		return None
	text = value_text.strip()
	if not text:
		return None
	text = text.replace("R$", "").replace("\u00A0", " ").strip()
	text = text.replace(".", "").replace(",", ".")
	try:
		return float(text)
	except ValueError:
		return None


def filter_licitacoes(
	licitacoes: Iterable[Dict[str, Any]],
	orgao: Optional[str] = None,
	modalidade: Optional[str] = None,
	valor_min: Optional[float] = None,
	valor_max: Optional[float] = None,
) -> List[Dict[str, Any]]:
	results: List[Dict[str, Any]] = []
	for item in licitacoes:
		item_orgao = (item.get("orgao") or "").strip().lower()
		item_modalidade = (item.get("modalidade") or "").strip().lower()
		value_float = item.get("valor")
		if value_float is None and "valor_texto" in item:
			value_float = parse_brl_to_float(item.get("valor_texto"))

		if orgao and orgao.strip().lower() not in item_orgao:
			continue
		if modalidade and modalidade.strip().lower() not in item_modalidade:
			continue
		if valor_min is not None and (value_float is None or value_float < valor_min):
			continue
		if valor_max is not None and (value_float is None or value_float > valor_max):
			continue

		results.append(item)
	return results