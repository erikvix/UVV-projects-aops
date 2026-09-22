#!/usr/bin/env python3
"""Monta dados/coletas.csv a partir da Serie Historica de Precos de Combustiveis da ANP.

Fonte: https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis

Dois modos de uso:

  # 1. baixa sozinho todos os arquivos do ano direto do portal da ANP
  python3 aop3/scripts/importar_anp.py --baixar-ano 2026 --municipio "VILA VELHA" --uf ES

  # 2. usa arquivos que voce ja baixou (mensais ou semestrais, na ordem que quiser)
  python3 aop3/scripts/importar_anp.py precos-*.csv --municipio "VILA VELHA" --uf ES

Depois rode: python3 aop3/scripts/gerar_site_e_planilhas.py

O script entende os dois layouts publicados pela ANP (o semestral ca-AAAA-S.csv,
em latin-1, e os mensais de dados abertos, em UTF-8), filtra o municipio, mantem
apenas os quatro combustiveis do projeto e escolhe os postos com mais coletas,
dando preferencia a postos de bairros diferentes para atender ao requisito II.c.
Grava tambem dados/fonte.txt, com a descricao da origem que o site e o relatorio
exibem para a comunidade.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "dados" / "coletas.csv"
FONTE = RAIZ / "dados" / "fonte.txt"

PAGINA_ANP = ("https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/"
              "serie-historica-de-precos-de-combustiveis")
NAVEGADOR = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
             "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")

# Como o produto aparece na ANP -> como aparece no projeto
PRODUTOS = {
    "GASOLINA": "Gasolina comum",
    "GASOLINA ADITIVADA": "Gasolina aditivada",
    "ETANOL": "Etanol",
    "DIESEL S10": "Diesel S10",
}

# Palavras que ficam em caixa baixa ao arrumar nomes em CAIXA ALTA
MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em", "a", "o"}
# Palavras curtas que NAO sao sigla (senao "RUA Moema" em vez de "Rua Moema")
NAO_SIGLAS = {"RUA", "AVE", "ROD", "TRV", "LTD", "LOT", "VIA", "SAO", "DOS", "DAS",
              "SOL", "MAR", "RIO", "LUZ", "PAZ", "SUL", "NOR", "VER", "SEM"}


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    ).strip().upper()


def arrumar_caixa(texto: str) -> str:
    """A ANP publica tudo em CAIXA ALTA; deixa legivel para quem le o site."""
    palavras = []
    for i, palavra in enumerate(texto.strip().split()):
        baixa = palavra.lower()
        if i and baixa in MINUSCULAS:
            palavras.append(baixa)
        elif (len(palavra) <= 3 and palavra.isalpha() and palavra.isupper()
              and palavra not in NAO_SIGLAS and baixa not in MINUSCULAS):
            palavras.append(palavra)  # siglas curtas: BR, RM, ABC
        else:
            palavras.append(baixa.capitalize())
    return " ".join(palavras)


def ler_csv(caminho: Path):
    """Le um CSV da ANP em qualquer um dos layouts/codificacoes publicados."""
    dados = caminho.read_bytes()
    for codificacao in ("utf-8-sig", "latin-1"):
        try:
            texto = dados.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    else:
        return
    yield from csv.DictReader(texto.splitlines(), delimiter=";")


def baixar_ano(ano: int, destino: Path) -> list[Path]:
    """Descobre na pagina da ANP os arquivos do ano e baixa os de combustiveis."""
    pagina = destino / "anp.html"
    subprocess.run(["curl", "-sSL", "-A", NAVEGADOR, "--max-time", "180", "-o", str(pagina), PAGINA_ANP],
                   check=True)
    urls = sorted(set(re.findall(rf'https://[^"]*/{ano}/[^"]*\.csv', pagina.read_text(errors="replace"))))
    urls = [u for u in urls if re.search(r"gasolina|diesel", u, re.I)]
    if not urls:
        print(f"nenhum arquivo de {ano} encontrado na pagina da ANP", file=sys.stderr)
        return []
    baixados = []
    for url in urls:
        arquivo = destino / url.rsplit("/", 1)[-1]
        print(f"  baixando {arquivo.name}")
        resultado = subprocess.run(
            ["curl", "-sS", "-A", NAVEGADOR, "--max-time", "300", "-o", str(arquivo), url],
            capture_output=True,
        )
        if resultado.returncode == 0 and arquivo.exists():
            baixados.append(arquivo)
        else:
            print(f"  falhou: {arquivo.name}", file=sys.stderr)
    return baixados


def coletas_do_arquivo(caminho: Path, municipio: str, uf: str):
    alvo = sem_acento(municipio)
    for linha in ler_csv(caminho):
        if sem_acento(linha.get("Municipio", "")) != alvo:
            continue
        if uf and sem_acento(linha.get("Estado - Sigla", linha.get("Estado", ""))) != sem_acento(uf):
            continue
        produto = PRODUTOS.get(sem_acento(linha.get("Produto", "")))
        if produto is None:
            continue
        try:
            data_coleta = datetime.strptime(linha["Data da Coleta"].strip(), "%d/%m/%Y").date()
            preco = float(linha["Valor de Venda"].replace(",", "."))
        except (KeyError, ValueError, AttributeError):
            continue
        rua = arrumar_caixa(linha.get("Nome da Rua", ""))
        numero = (linha.get("Numero Rua", "") or "").strip()
        yield {
            "posto": arrumar_caixa(linha["Revenda"]),
            "bairro": arrumar_caixa(linha.get("Bairro", "") or "Nao informado"),
            "endereco": f"{rua}, {numero}".strip(", "),
            "bandeira": arrumar_caixa(linha.get("Bandeira", "")),
            "combustivel": produto,
            "data_coleta": data_coleta.isoformat(),
            "preco": f"{preco:.3f}",
        }


def escolher_postos(coletas, quantidade: int, min_coletas: int) -> list[str]:
    """Postos com pelo menos `min_coletas` datas em cada combustivel, preferindo
    bairros diferentes (requisito II.c: os postos devem englobar >= 2 bairros)."""
    datas = defaultdict(lambda: defaultdict(set))
    bairro_do_posto = {}
    for c in coletas:
        datas[c["posto"]][c["combustivel"]].add(c["data_coleta"])
        bairro_do_posto[c["posto"]] = c["bairro"]

    elegiveis = [
        posto for posto, por_combustivel in datas.items()
        if len(por_combustivel) == len(PRODUTOS)
        and all(len(d) >= min_coletas for d in por_combustivel.values())
    ]
    # mais coletas primeiro
    elegiveis.sort(key=lambda p: (-min(len(d) for d in datas[p].values()), p))

    escolhidos, bairros_usados = [], set()
    for posto in elegiveis:  # primeira passada: um posto por bairro
        if len(escolhidos) == quantidade:
            break
        if bairro_do_posto[posto] not in bairros_usados:
            escolhidos.append(posto)
            bairros_usados.add(bairro_do_posto[posto])
    for posto in elegiveis:  # segunda passada: completa as vagas que sobraram
        if len(escolhidos) == quantidade:
            break
        if posto not in escolhidos:
            escolhidos.append(posto)
    return escolhidos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="*", type=Path, help="CSVs da ANP ja baixados")
    ap.add_argument("--baixar-ano", type=int, metavar="AAAA",
                    help="baixa sozinho os arquivos desse ano no portal da ANP")
    ap.add_argument("--municipio", default="VILA VELHA")
    ap.add_argument("--uf", default="ES", help="sigla do estado (evita municipios homonimos)")
    ap.add_argument("--postos", type=int, default=5, help="quantos postos manter (padrao 5)")
    ap.add_argument("--min-coletas", type=int, default=5,
                    help="minimo de datas por combustivel em cada posto (padrao 5)")
    args = ap.parse_args()

    if not args.arquivos and not args.baixar_ano:
        ap.error("informe arquivos CSV da ANP ou use --baixar-ano")

    with tempfile.TemporaryDirectory() as temporaria:
        arquivos = list(args.arquivos)
        if args.baixar_ano:
            print(f"buscando arquivos de {args.baixar_ano} no portal da ANP...")
            arquivos += baixar_ano(args.baixar_ano, Path(temporaria))

        coletas = []
        for arquivo in arquivos:
            if not arquivo.exists():
                print(f"arquivo nao encontrado: {arquivo}", file=sys.stderr)
                continue
            encontradas = list(coletas_do_arquivo(arquivo, args.municipio, args.uf))
            coletas += encontradas
            print(f"  {arquivo.name}: {len(encontradas)} coletas de {args.municipio}")

    if not coletas:
        print(f"nenhuma coleta encontrada para {args.municipio}/{args.uf}", file=sys.stderr)
        return 1

    escolhidos = escolher_postos(coletas, args.postos, args.min_coletas)
    if not escolhidos:
        print(f"nenhum posto de {args.municipio} tem {args.min_coletas} coletas em datas "
              "diferentes dos quatro combustiveis; use mais arquivos ou reduza --min-coletas",
              file=sys.stderr)
        return 1

    selecao = sorted(
        (c for c in coletas if c["posto"] in escolhidos),
        key=lambda c: (c["posto"], c["combustivel"], c["data_coleta"]),
    )
    bairros = sorted({c["bairro"] for c in selecao})
    datas = sorted(c["data_coleta"] for c in selecao)

    if len(bairros) < 2:
        print("aviso: os postos escolhidos cobrem apenas 1 bairro; o trabalho exige no minimo 2.",
              file=sys.stderr)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    campos = ["id_coleta", "posto", "bairro", "endereco", "bandeira", "combustivel", "data_coleta", "preco"]
    with SAIDA.open("w", encoding="utf-8", newline="") as fp:
        escritor = csv.DictWriter(fp, fieldnames=campos)
        escritor.writeheader()
        for i, c in enumerate(selecao, start=1):
            escritor.writerow({"id_coleta": i, **c})

    def br(iso: str) -> str:
        a, m, d = iso.split("-")
        return f"{d}/{m}/{a}"

    FONTE.write_text(
        "Serie Historica de Precos de Combustiveis da ANP (Agencia Nacional do Petroleo, "
        "Gas Natural e Biocombustiveis), levantamento de precos de revenda em "
        f"{args.municipio.title()}/{args.uf.upper()}, coletas de {br(datas[0])} a {br(datas[-1])}. "
        "Dados abertos disponiveis em " + PAGINA_ANP + ". "
        f"Selecao: {len(escolhidos)} postos em {len(bairros)} bairros, quatro combustiveis, "
        f"{len(selecao)} coletas.\n",
        encoding="utf-8",
    )

    print(f"\n{len(selecao)} coletas de {len(escolhidos)} postos em {len(bairros)} bairros "
          f"({br(datas[0])} a {br(datas[-1])}) gravadas em {SAIDA.relative_to(RAIZ)}")
    for posto in escolhidos:
        bairro = next(c["bairro"] for c in selecao if c["posto"] == posto)
        print(f"  - {posto} ({bairro})")
    print("\nAgora rode: python3 aop3/scripts/gerar_site_e_planilhas.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
