#!/usr/bin/env python3
"""Converte a Serie Historica de Precos de Combustiveis da ANP em dados/coletas.csv.

Como usar:

  1. Baixe um arquivo semestral de REVENDA no portal da ANP
     (https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis)
     Ex.: ca-2025-01.csv
  2. Rode:
       python3 aop3/scripts/importar_anp.py ca-2025-01.csv --municipio "VILA VELHA"
  3. Regere o site e as planilhas:
       python3 aop3/scripts/gerar_site_e_planilhas.py

O arquivo da ANP e CSV com separador ";", codificacao latin-1 e as colunas
"Revenda", "Bairro", "Nome da Rua", "Numero Rua", "Bandeira", "Produto",
"Data da Coleta" (dd/mm/aaaa) e "Valor de Venda" (virgula decimal).
O script filtra o municipio pedido, mantem apenas os 4 combustiveis do projeto
e seleciona os postos com mais coletas, respeitando os requisitos do trabalho
(minimo de postos, minimo de coletas por posto e pelo menos 2 bairros).
"""
from __future__ import annotations

import argparse
import csv
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "dados" / "coletas.csv"

# Como o produto aparece na ANP -> como aparece no projeto
PRODUTOS = {
    "GASOLINA": "Gasolina comum",
    "GASOLINA ADITIVADA": "Gasolina aditivada",
    "ETANOL": "Etanol",
    "DIESEL S10": "Diesel S10",
}


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    ).strip().upper()


def ler_anp(caminho: Path, municipio: str):
    alvo = sem_acento(municipio)
    with caminho.open(encoding="latin-1", newline="") as fp:
        for linha in csv.DictReader(fp, delimiter=";"):
            if sem_acento(linha.get("Municipio", "")) != alvo:
                continue
            produto = PRODUTOS.get(sem_acento(linha.get("Produto", "")))
            if produto is None:
                continue
            try:
                data_coleta = datetime.strptime(
                    linha["Data da Coleta"].strip(), "%d/%m/%Y"
                ).date()
                preco = float(linha["Valor de Venda"].replace(",", "."))
            except (KeyError, ValueError):
                continue
            endereco = " ".join(
                p for p in (linha.get("Nome da Rua", ""), linha.get("Numero Rua", "")) if p.strip()
            )
            yield {
                "posto": linha["Revenda"].strip(),
                "bairro": linha.get("Bairro", "").strip() or "Nao informado",
                "endereco": endereco.strip(),
                "bandeira": linha.get("Bandeira", "").strip(),
                "combustivel": produto,
                "data_coleta": data_coleta.isoformat(),
                "preco": f"{preco:.3f}",
            }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo_anp", type=Path, help="CSV semestral de revenda da ANP")
    ap.add_argument("--municipio", default="VILA VELHA")
    ap.add_argument("--postos", type=int, default=5, help="quantos postos manter (padrao 5)")
    ap.add_argument("--min-coletas", type=int, default=5, help="minimo de datas por posto (padrao 5)")
    args = ap.parse_args()

    if not args.arquivo_anp.exists():
        print(f"arquivo nao encontrado: {args.arquivo_anp}", file=sys.stderr)
        return 1

    registros = list(ler_anp(args.arquivo_anp, args.municipio))
    if not registros:
        print(f"nenhuma coleta encontrada para {args.municipio}", file=sys.stderr)
        return 1

    datas_por_posto = defaultdict(set)
    for r in registros:
        datas_por_posto[r["posto"]].add(r["data_coleta"])

    elegiveis = [p for p, datas in datas_por_posto.items() if len(datas) >= args.min_coletas]
    elegiveis.sort(key=lambda p: (-len(datas_por_posto[p]), p))
    escolhidos = elegiveis[: args.postos]

    if not escolhidos:
        print(
            f"nenhum posto de {args.municipio} tem {args.min_coletas} coletas em datas "
            "diferentes neste arquivo; tente outro semestre ou reduza --min-coletas",
            file=sys.stderr,
        )
        return 1

    selecao = [r for r in registros if r["posto"] in escolhidos]
    selecao.sort(key=lambda r: (r["posto"], r["combustivel"], r["data_coleta"]))

    bairros = {r["bairro"] for r in selecao}
    if len(bairros) < 2:
        print(
            f"aviso: os postos escolhidos cobrem apenas {len(bairros)} bairro(s); "
            "o trabalho exige no minimo 2. Ajuste --postos ou escolha os postos na mao.",
            file=sys.stderr,
        )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    campos = ["id_coleta", "posto", "bairro", "endereco", "bandeira", "combustivel", "data_coleta", "preco"]
    with SAIDA.open("w", encoding="utf-8", newline="") as fp:
        escritor = csv.DictWriter(fp, fieldnames=campos)
        escritor.writeheader()
        for i, r in enumerate(selecao, start=1):
            escritor.writerow({"id_coleta": i, **r})

    print(f"{len(selecao)} coletas de {len(escolhidos)} postos ({len(bairros)} bairros) "
          f"gravadas em {SAIDA.relative_to(RAIZ)}")
    print("postos:", ", ".join(escolhidos))
    print("Agora rode: python3 aop3/scripts/gerar_site_e_planilhas.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
