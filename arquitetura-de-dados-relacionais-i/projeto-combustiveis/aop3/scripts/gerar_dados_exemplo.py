#!/usr/bin/env python3
"""Gera o arquivo dados/coletas.csv com o conjunto de coletas do projeto.

ATENCAO: este script produz um conjunto de DEMONSTRACAO, usado apenas para
deixar o site, as planilhas e os graficos funcionando de ponta a ponta.
Para publicar os dados reais, substitua dados/coletas.csv pelo resultado de
scripts/importar_anp.py (serie historica da ANP) ou pela sua propria coleta de
campo, mantendo exatamente as mesmas colunas.

Saida: dados/coletas.csv
Colunas: id_coleta,posto,bairro,endereco,bandeira,combustivel,data_coleta,preco
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "dados" / "coletas.csv"

# 5 postos distribuidos em 3 bairros de Vila Velha - ES (requisito: >= 2 bairros).
# Os nomes dos postos sao fictitios de propósito: como os precos abaixo sao de
# demonstracao, nenhum valor e atribuido a um estabelecimento real.
POSTOS = [
    # nome, bairro, endereco, bandeira, fator de preco do posto
    ("Posto Praia da Costa", "Praia da Costa", "Av. Estudante José Júlio de Souza, 1200", "Ipiranga", 1.015),
    ("Posto Itapoã", "Itapoã", "Av. Champagnat, 480", "Shell", 1.000),
    ("Posto Coqueiral", "Coqueiral de Itaparica", "Av. Central, 2350", "Petrobras", 0.992),
    ("Posto Cobilândia", "Cobilândia", "Rod. Carlos Lindenberg, 3900", "Bandeira Branca", 0.972),
    ("Posto Glória", "Glória", "Av. Carlos Lindenberg, 1750", "Ale", 0.985),
]

# combustivel, preco base na 1a coleta, tendencia por coleta (R$)
COMBUSTIVEIS = [
    ("Gasolina comum", 6.19, 0.035),
    ("Gasolina aditivada", 6.33, 0.033),
    ("Etanol", 4.59, 0.028),
    ("Diesel S10", 6.09, 0.018),
]

PRIMEIRA_COLETA = date(2025, 3, 8)
INTERVALO_DIAS = 14
NUM_COLETAS = 6  # requisito: minimo de 5 coletas por posto, em datas diferentes


def main() -> None:
    rnd = random.Random(20250308)  # semente fixa: o arquivo gerado e reproduzivel
    linhas = []
    id_coleta = 0
    for posto, bairro, endereco, bandeira, fator in POSTOS:
        for combustivel, base, tendencia in COMBUSTIVEIS:
            for i in range(NUM_COLETAS):
                data_coleta = PRIMEIRA_COLETA + timedelta(days=INTERVALO_DIAS * i)
                ruido = rnd.uniform(-0.05, 0.05)
                preco = (base + tendencia * i) * fator + ruido
                id_coleta += 1
                linhas.append(
                    {
                        "id_coleta": id_coleta,
                        "posto": posto,
                        "bairro": bairro,
                        "endereco": endereco,
                        "bandeira": bandeira,
                        "combustivel": combustivel,
                        "data_coleta": data_coleta.isoformat(),
                        "preco": f"{preco:.3f}",
                    }
                )

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with SAIDA.open("w", encoding="utf-8", newline="") as fp:
        escritor = csv.DictWriter(fp, fieldnames=list(linhas[0].keys()))
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"{len(linhas)} coletas gravadas em {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
