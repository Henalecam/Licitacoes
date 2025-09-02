# Scraping de Licitações com ChatGPT (Railway-ready)

Projeto Python para coletar licitações do Compras.gov.br (adaptável), filtrar por critérios básicos e usar o ChatGPT para selecionar licitações por nicho. Preparado para rodar localmente e no Railway como job contínuo ou agendado.

## Requisitos
- Python 3.10+
- Variável de ambiente `OPENAI_API_KEY` (para recursos de nicho/ChatGPT)

## Instalação
```bash
pip install -r requirements.txt
```

## Comandos (CLI)
Todos os comandos são executados via módulo principal.

- Scraping (padrão: salva em `./data/licitacoes.json`):
```bash
python -m app.main scrape --pages 2 --output ./data/licitacoes.json
```

- Scraping contínuo (loop):
```bash
python -m app.main scrape --pages 2 --output ./data/licitacoes.json --loop --loop-interval 900
```

- Filtrar do JSON salvo:
```bash
python -m app.main filter --input ./data/licitacoes.json \
  --orgao "Ministério X" --modalidade "Pregão" --valor-min 10000 --valor-max 50000 \
  --output ./data/licitacoes_filtradas.json
```

- Buscar por nicho (via ChatGPT):
```bash
export OPENAI_API_KEY=...  # ou use um .env
python -m app.main niche --input ./data/licitacoes.json --niche "serviços de TI" \
  --chunk-size 25 --model gpt-4o-mini --output ./data/licitacoes_nicho.json
```

## Observações sobre o scraping
- O HTML do Compras.gov.br pode mudar. O `scraper` foi escrito de forma resiliente, mas você pode precisar ajustar seletores ou usar uma API pública (ex.: PNCP) definindo `--api-url` e mapeando campos.
- Para uso em escala, agende o job com páginas segmentadas (por exemplo, 2–5 páginas por execução) para respeitar limites do Railway.

## Railway
- O projeto já inclui um `Procfile` para rodar como worker contínuo:
```
worker: python -m app.main scrape --pages 2 --output ./data/licitacoes.json --loop --loop-interval 900
```
- Defina a variável de ambiente `OPENAI_API_KEY` no Railway.
- O filesystem é efêmero; o JSON é persistido apenas durante a execução. Se necessitar guardar histórico, integre um armazenamento externo (S3, DB, etc.).
- Para rodar on-demand como job, crie um novo job no Railway apontando para o mesmo comando sem `--loop`.

## Estrutura
```
app/
  __init__.py
  main.py        # CLI (scrape, filter, niche)
  scraper.py     # Scraping HTML/API com normalização
  filters.py     # Filtragem por órgão, modalidade e faixa de valores
  storage.py     # IO JSON seguro para Railway
  niche.py       # Integração com OpenAI (ChatGPT)
```

## Desenvolvimento local
- Use um `.env` (ver `.env.example`) para variáveis de ambiente.
- Rode com poucas páginas e valide a saída JSON antes de escalar.