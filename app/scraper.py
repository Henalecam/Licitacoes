import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from .filters import parse_brl_to_float


DEFAULT_BASE_URL = (
	"https://www.gov.br/compras/pt-br/assuntos/avisos-de-licitacoes?pagina={page}"
)


@dataclass
class SelectorProfile:
	list_selector: str
	title_selector: str
	orgao_selector: Optional[str]
	modalidade_selector: Optional[str]
	valor_selector: Optional[str]
	link_selector: str


DEFAULT_PROFILE = SelectorProfile(
	list_selector="article",
	title_selector="h2, h3, a[aria-current]",
	orgao_selector=".orgao, .portal-titulo, .subtitle, .subtitulo, .documentByLine",
	modalidade_selector=".modalidade, .label-modalidade, .tag",
	valor_selector=".valor, .price, .amount, .value",
	link_selector="a",
)


def _extract_first_text(element, selector: Optional[str]) -> Optional[str]:
	if not selector:
		return None
	found = element.select_one(selector)
	if not found:
		return None
	return found.get_text(strip=True)


def _extract_first_link(element, selector: str) -> Optional[str]:
	found = element.select_one(selector)
	if not found:
		return None
	if found.has_attr("href"):
		return found["href"]
	return None


def normalize_record(raw: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
	title = (raw.get("titulo") or "").strip()
	orgao = (raw.get("orgao") or "").strip()
	modalidade = (raw.get("modalidade") or "").strip()
	valor_texto = (raw.get("valor_texto") or "").strip()
	valor = parse_brl_to_float(valor_texto)
	return {
		"titulo": title,
		"orgao": orgao,
		"modalidade": modalidade,
		"valor": valor,
		"valor_texto": valor_texto or None,
		"link": raw.get("link"),
	}


def scrape_licitacoes(
	pages: int = 1,
	base_url_template: str = DEFAULT_BASE_URL,
	selector_profile: SelectorProfile = DEFAULT_PROFILE,
	timeout_seconds: int = 20,
	delay_seconds: float = 1.0,
	user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) PythonScraper/1.0",
) -> List[Dict]:
	results: List[Dict] = []
	session = requests.Session()
	session.headers.update({"User-Agent": user_agent})

	for page in range(1, max(1, pages) + 1):
		url = base_url_template.format(page=page)
		try:
			response = session.get(url, timeout=timeout_seconds)
		except requests.RequestException:
			time.sleep(max(0.0, delay_seconds))
			continue

		if response.status_code != 200 or not response.text:
			time.sleep(max(0.0, delay_seconds))
			continue

		soup = BeautifulSoup(response.text, "html.parser")
		items = soup.select(selector_profile.list_selector)

		for element in items:
			title = _extract_first_text(element, selector_profile.title_selector)
			orgao = _extract_first_text(element, selector_profile.orgao_selector)
			modalidade = _extract_first_text(element, selector_profile.modalidade_selector)
			valor_texto = _extract_first_text(element, selector_profile.valor_selector)
			link = _extract_first_link(element, selector_profile.link_selector)

			if not title and not link:
				continue

			raw = {
				"titulo": title,
				"orgao": orgao,
				"modalidade": modalidade,
				"valor_texto": valor_texto,
				"link": link,
			}
			results.append(normalize_record(raw))

		time.sleep(max(0.0, delay_seconds))

	return results