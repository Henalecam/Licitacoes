import argparse
import os
import time
from typing import List, Dict, Any

from dotenv import load_dotenv

from .storage import save_json, load_json, default_output_path
from .scraper import scrape_licitacoes
from .filters import filter_licitacoes
from .niche import filter_by_niche_with_openai


load_dotenv()


def _cmd_scrape(args: argparse.Namespace) -> None:
	def run_once() -> int:
		licitacoes = scrape_licitacoes(
			pages=args.pages,
			base_url_template=args.base_url,
			timeout_seconds=args.timeout,
			delay_seconds=args.delay,
		)
		output = args.output or default_output_path()
		save_json(output, licitacoes)
		print(f"Scraping concluído. {len(licitacoes)} itens salvos em: {output}")
		return len(licitacoes)

	if not args.loop:
		run_once()
		return

	while True:
		try:
			run_once()
		except Exception as exc:  # log and continue
			print(f"Erro no scraping: {exc}")
		finally:
			time.sleep(max(1, args.loop_interval))


def _cmd_filter(args: argparse.Namespace) -> None:
	licitacoes: List[Dict[str, Any]] = load_json(args.input)
	resultados = filter_licitacoes(
		licitacoes,
		orgao=args.orgao,
		modalidade=args.modalidade,
		valor_min=args.valor_min,
		valor_max=args.valor_max,
	)
	if args.output:
		save_json(args.output, resultados)
		print(f"Filtragem concluída. {len(resultados)} itens salvos em: {args.output}")
	else:
		print(resultados)


def _cmd_niche(args: argparse.Namespace) -> None:
	licitacoes: List[Dict[str, Any]] = load_json(args.input)
	filtradas = filter_by_niche_with_openai(
		licitacoes=licitacoes,
		niche=args.niche,
		model=args.model,
		chunk_size=args.chunk_size,
		max_chunks=args.max_chunks,
	)
	if args.output:
		save_json(args.output, filtradas)
		print(f"Nicho concluído. {len(filtradas)} itens salvos em: {args.output}")
	else:
		print(filtradas)


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Scraper e filtros de licitações (Railway-ready)",
	)
	sub = parser.add_subparsers(dest="command", required=True)

	p_scrape = sub.add_parser("scrape", help="Executa scraping")
	p_scrape.add_argument("--pages", type=int, default=1)
	p_scrape.add_argument(
		"--base-url",
		default="https://www.gov.br/compras/pt-br/assuntos/avisos-de-licitacoes?pagina={page}",
		help="Template de URL com {page}",
	)
	p_scrape.add_argument("--timeout", type=int, default=20)
	p_scrape.add_argument("--delay", type=float, default=1.0)
	p_scrape.add_argument("--output", default=None)
	p_scrape.add_argument("--loop", action="store_true", help="Roda continuamente")
	p_scrape.add_argument("--loop-interval", type=int, default=600, help="Intervalo entre execuções (segundos)")
	p_scrape.set_defaults(func=_cmd_scrape)

	p_filter = sub.add_parser("filter", help="Filtra a partir do JSON salvo")
	p_filter.add_argument("--input", required=True)
	p_filter.add_argument("--orgao", default=None)
	p_filter.add_argument("--modalidade", default=None)
	p_filter.add_argument("--valor-min", type=float, default=None)
	p_filter.add_argument("--valor-max", type=float, default=None)
	p_filter.add_argument("--output", default=None)
	p_filter.set_defaults(func=_cmd_filter)

	p_niche = sub.add_parser("niche", help="Filtra por nicho usando ChatGPT")
	p_niche.add_argument("--input", required=True)
	p_niche.add_argument("--niche", required=True)
	p_niche.add_argument("--chunk-size", type=int, default=25)
	p_niche.add_argument("--max-chunks", type=int, default=None)
	p_niche.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
	p_niche.add_argument("--output", default=None)
	p_niche.set_defaults(func=_cmd_niche)

	return parser


def main() -> None:
	parser = build_parser()
	args = parser.parse_args()
	args.func(args)


if __name__ == "__main__":
	main()