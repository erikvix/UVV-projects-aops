#!/usr/bin/env python3
"""Monta o relatorio da AOP3 (divulgacao para a comunidade) em PDF.

O script:
  1. sobe o site em um servidor local e tira prints de cada tela (evidencia de
     que o site publicado responde a todas as consultas do item II.d);
  2. junta esses prints com as fotos/prints que o grupo colocar em
     aop3/relatorio/evidencias/ (legendas opcionais em legendas.csv);
  3. gera aop3/relatorio/RELATORIO-AOP3.html e imprime em
     aop3/relatorio/RELATORIO-AOP3.pdf.

Antes de gerar a versao final, preencha o bloco DADOS DA ENTREGA abaixo.

Uso:  python3 aop3/scripts/gerar_relatorio.py
"""
from __future__ import annotations

import csv
import html
import shutil
import socket
import subprocess
import sys
import threading
import time
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ===========================================================================
# DADOS DA ENTREGA - preencha antes de gerar o PDF final
# ===========================================================================
INTEGRANTES = [
    # ("Nome completo do integrante", "Matrícula")
    ("[NOME COMPLETO DO INTEGRANTE 1]", "[MATRÍCULA]"),
    ("[NOME COMPLETO DO INTEGRANTE 2]", "[MATRÍCULA]"),
    ("[NOME COMPLETO DO INTEGRANTE 3]", "[MATRÍCULA]"),
    ("[NOME COMPLETO DO INTEGRANTE 4]", "[MATRÍCULA]"),
    ("[NOME COMPLETO DO INTEGRANTE 5]", "[MATRÍCULA]"),
]
DISCIPLINA = "Arquitetura de Dados Relacionais I"
PROFESSOR = "[NOME DO PROFESSOR]"
INSTITUICAO = "Universidade Vila Velha (UVV)"
CURSO = "Análise e Desenvolvimento de Sistemas"
CIDADE = "Vila Velha - ES"
SEMESTRE = "[SEMESTRE/ANO]"

# Endereco publico do site (ex.: GitHub Pages). Enquanto estiver vazio, o
# relatorio avisa que o endereco precisa ser preenchido.
URL_SITE = ""

# Onde e quando o site foi divulgado para a comunidade.
CANAIS_DE_DIVULGACAO = [
    # (canal / local, data, público alcancado, observacao)
    ("[Ex.: grupo de WhatsApp do bairro X]", "[dd/mm/aaaa]", "[nº de pessoas]", "[como foi feito]"),
    ("[Ex.: perfil do grupo no Instagram]", "[dd/mm/aaaa]", "[nº de visualizacoes]", "[link da publicacao]"),
    ("[Ex.: mural da associação de moradores]", "[dd/mm/aaaa]", "[público estimado]", "[cartaz com QR Code do site]"),
]
# ===========================================================================

RAIZ = Path(__file__).resolve().parents[2]
SITE = RAIZ / "aop3" / "site"
RELATORIO = RAIZ / "aop3" / "relatorio"
EVIDENCIAS = RELATORIO / "evidencias"
COLETAS = RAIZ / "dados" / "coletas.csv"
FONTE_TXT = RAIZ / "dados" / "fonte.txt"
SAIDA_HTML = RELATORIO / "RELATORIO-AOP3.html"
SAIDA_PDF = RELATORIO / "RELATORIO-AOP3.pdf"

TELAS = [
    ("painel-1", "site-consulta-1.png", 1500,
     "Consulta I - menor e maior preço de cada combustível, com posto, endereço, bairro, valor e data da coleta."),
    ("painel-2", "site-consulta-2.png", 1500,
     "Consulta II - preço médio e quantidade de amostras por posto e combustível, com filtros por combustível e bairro."),
    ("painel-3", "site-consulta-3.png", 1400,
     "Consulta III - preço mais recente de cada combustível em cada posto."),
    ("painel-4", "site-consulta-4.png", 1500,
     "Consulta IV - evolução do preço de um combustível em um posto, escolhidos pelo usuário."),
    ("painel-5", "site-graficos.png", 2000,
     "Gráficos do item II.e - evolução do preço médio de cada combustível na cidade e em cada posto."),
    ("painel-6", "site-planilhas.png", 1200,
     "Planilhas e dados abertos disponibilizados para download pela comunidade."),
]


def navegador() -> str | None:
    for caminho in (
        "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
        shutil.which("google-chrome"),
    ):
        if caminho and Path(caminho).exists():
            return caminho
    return None


def porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def cortar_margem(caminho: Path) -> None:
    """Remove a faixa vazia no rodape do print, quando o Pillow esta instalado."""
    try:
        from PIL import Image, ImageChops
    except ImportError:
        return
    with Image.open(caminho) as img:
        img = img.convert("RGB")
        fundo = Image.new("RGB", img.size, img.getpixel((img.width - 4, img.height - 4)))
        caixa = ImageChops.difference(img, fundo).getbbox()
        if caixa:
            img.crop((0, 0, img.width, min(img.height, caixa[3] + 24))).save(caminho)


def capturar_telas(chrome: str) -> list[tuple[Path, str]]:
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    porta = porta_livre()
    handler = partial(SimpleHTTPRequestHandler, directory=str(SITE))
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), handler)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    time.sleep(0.4)
    capturadas = []
    try:
        for painel, arquivo, altura, legenda in TELAS:
            destino = EVIDENCIAS / arquivo
            subprocess.run(
                [chrome, "--headless", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                 f"--window-size=1200,{altura}", "--virtual-time-budget=4000",
                 f"--screenshot={destino}",
                 f"http://127.0.0.1:{porta}/index.html?aba={painel}"],
                check=True, capture_output=True,
            )
            cortar_margem(destino)
            capturadas.append((destino, legenda))
    finally:
        servidor.shutdown()
    return capturadas


def evidencias_do_grupo() -> list[tuple[Path, str]]:
    """Imagens colocadas pelo grupo em aop3/relatorio/evidencias/ (exceto os
    prints gerados automaticamente). Legendas opcionais em legendas.csv:
    arquivo;legenda"""
    automaticas = {arquivo for _, arquivo, _, _ in TELAS}
    legendas = {}
    arquivo_legendas = EVIDENCIAS / "legendas.csv"
    if arquivo_legendas.exists():
        with arquivo_legendas.open(encoding="utf-8-sig", newline="") as fp:
            for linha in csv.reader(fp, delimiter=";"):
                if len(linha) >= 2 and not linha[0].startswith("#"):
                    legendas[linha[0].strip()] = linha[1].strip()
    imagens = []
    for caminho in sorted(EVIDENCIAS.glob("*")):
        if caminho.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            continue
        if caminho.name in automaticas:
            continue
        imagens.append((caminho, legendas.get(caminho.name, "Evidência da divulgação: " + caminho.stem)))
    return imagens


def dados_de_demonstracao() -> bool:
    """Le a marca deixada pelo gerador do site em aop3/site/js/dados.js."""
    arquivo = SITE / "js" / "dados.js"
    return arquivo.exists() and '"demo": true' in arquivo.read_text(encoding="utf-8")


def resumo_dados() -> dict:
    with COLETAS.open(encoding="utf-8", newline="") as fp:
        linhas = list(csv.DictReader(fp))
    datas = sorted(l["data_coleta"] for l in linhas)
    def br(iso):
        a, m, d = iso.split("-")
        return f"{d}/{m}/{a}"
    return {
        "coletas": len(linhas),
        "postos": sorted({l["posto"] for l in linhas}),
        "bairros": sorted({l["bairro"] for l in linhas}),
        "combustiveis": sorted({l["combustivel"] for l in linhas}),
        "inicio": br(datas[0]),
        "fim": br(datas[-1]),
    }


def figura(caminho: Path, legenda: str, numero: int) -> str:
    relativo = caminho.relative_to(RELATORIO).as_posix()
    return (
        '<figure><img src="' + html.escape(relativo) + '" alt="' + html.escape(legenda) + '">'
        '<figcaption><b>Figura ' + str(numero) + '.</b> ' + html.escape(legenda) + "</figcaption></figure>"
    )


def montar_html(telas, extras, resumo) -> str:
    hoje = date.today().strftime("%d/%m/%Y")
    endereco = (
        '<a href="' + html.escape(URL_SITE) + '">' + html.escape(URL_SITE) + "</a>"
        if URL_SITE else
        '<span class="pendente">[PREENCHER: endereço público do site, ex. https://usuario.github.io/...]</span>'
    )

    integrantes = "".join(
        f"<tr><td>{html.escape(nome)}</td><td>{html.escape(matricula)}</td></tr>"
        for nome, matricula in INTEGRANTES
    )
    canais = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in linha) + "</tr>"
        for linha in CANAIS_DE_DIVULGACAO
    )

    aviso_demo = (
        '<p class="pendente">[ATENÇÃO: os preços publicados ainda são o conjunto de demonstração. '
        'Substitua <code>dados/coletas.csv</code> pela coleta real do grupo (ou pela importação da ANP), '
        'rode <code>gerar_site_e_planilhas.py</code> com <code>DADOS_DE_DEMONSTRACAO = False</code> e '
        'gere este relatório de novo antes de entregar.]</p>'
        if dados_de_demonstracao() else ""
    )

    origem = (
        FONTE_TXT.read_text(encoding="utf-8").strip()
        if FONTE_TXT.exists() and FONTE_TXT.read_text(encoding="utf-8").strip()
        else f"coleta realizada pelo grupo em postos de {CIDADE}."
    )

    numero = 0
    blocos_site = []
    for caminho, legenda in telas:
        numero += 1
        blocos_site.append(figura(caminho, legenda, numero))

    if extras:
        blocos_extras = []
        for caminho, legenda in extras:
            numero += 1
            blocos_extras.append(figura(caminho, legenda, numero))
        extras_html = "".join(blocos_extras)
    else:
        extras_html = (
            '<p class="pendente">[PENDENTE: coloque aqui as evidências da divulgação — prints das '
            'publicacoes, fotos do cartaz afixado, conversas de compartilhamento, lista de presenca. '
            'Basta salvar as imagens em <code>aop3/relatorio/evidencias/</code> (legendas opcionais em '
            '<code>legendas.csv</code>, no formato <code>arquivo;legenda</code>) e rodar este script de novo.]</p>'
        )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Relatório AOP3 - Divulgação para a comunidade</title>
<style>
  @page {{ size: A4; margin: 18mm 16mm; }}
  body {{ font-family: Georgia, "Times New Roman", serif; color: #14140f; font-size: 11.5pt; line-height: 1.55; margin: 0; }}
  h1, h2, h3 {{ font-family: Helvetica, Arial, sans-serif; color: #10233d; }}
  h1 {{ font-size: 20pt; margin: 0 0 6px; }}
  h2 {{ font-size: 13pt; margin: 22px 0 8px; border-bottom: 1px solid #ccc7ba; padding-bottom: 4px; }}
  h3 {{ font-size: 11.5pt; margin: 16px 0 6px; }}
  p {{ margin: 0 0 10px; text-align: justify; }}
  .capa {{ text-align: center; padding: 38mm 0 0; page-break-after: always; }}
  .capa .inst {{ font-size: 12pt; text-transform: uppercase; letter-spacing: .06em; }}
  .capa .curso {{ margin-top: 4px; color: #4a4a42; }}
  .capa h1 {{ margin: 46mm 0 8px; font-size: 22pt; }}
  .capa .sub {{ font-size: 13pt; color: #3a3a33; }}
  .capa table {{ margin: 20mm auto 0; width: 84%; }}
  .capa .rodape-capa {{ margin-top: 30mm; font-size: 11pt; }}
  table {{ width: 100%; border-collapse: collapse; margin: 8px 0 14px; font-family: Helvetica, Arial, sans-serif; font-size: 10pt; }}
  th, td {{ border: 1px solid #ccc7ba; padding: 6px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #eef2f7; }}
  figure {{ margin: 14px 0 18px; page-break-inside: avoid; }}
  figure img {{ width: 100%; border: 1px solid #ccc7ba; border-radius: 4px; }}
  figcaption {{ font-family: Helvetica, Arial, sans-serif; font-size: 9pt; color: #45453c; margin-top: 5px; text-align: left; }}
  ul, ol {{ margin: 0 0 10px; padding-left: 20px; }}
  li {{ margin-bottom: 4px; }}
  code {{ font-family: "DejaVu Sans Mono", Consolas, monospace; font-size: 9.5pt; background: #f1f0eb; padding: 1px 4px; border-radius: 3px; }}
  .pendente {{ background: #fdf4dc; border-left: 3px solid #d79a00; padding: 8px 10px; font-family: Helvetica, Arial, sans-serif; font-size: 10pt; }}
  .secao {{ page-break-before: always; }}
</style>
</head>
<body>

<div class="capa">
  <div class="inst">{html.escape(INSTITUICAO)}</div>
  <div class="curso">{html.escape(CURSO)}</div>
  <div class="curso">{html.escape(DISCIPLINA)}</div>

  <h1>Projeto de Extensão — Preços de Combustíveis</h1>
  <div class="sub">AOP3 — Relatório de divulgação do trabalho para a comunidade</div>
  <div class="sub">{html.escape(CIDADE)}</div>

  <table>
    <thead><tr><th>Integrante</th><th>Matrícula</th></tr></thead>
    <tbody>{integrantes}</tbody>
  </table>

  <div class="rodape-capa">
    Professor(a): {html.escape(PROFESSOR)}<br>
    Semestre: {html.escape(SEMESTRE)}<br>
    {hoje}
  </div>
</div>

<h2>1. Objetivo</h2>
<p>Este relatório apresenta as evidências da terceira etapa (AOP3) do Projeto de Extensão da
disciplina {html.escape(DISCIPLINA)}: a divulgação, para a comunidade de {html.escape(CIDADE)}, das
informações de preço de combustíveis armazenadas no banco de dados relacional construido nas
etapas anteriores (AOP1 — projeto conceitual; AOP2 — projeto lógico e físico).</p>
<p>A base publicada reúne <b>{resumo['coletas']} coletas</b> de preço realizadas em
<b>{len(resumo['postos'])} postos</b> distribuídos por <b>{len(resumo['bairros'])} bairros</b>
({html.escape(', '.join(resumo['bairros']))}), para <b>{len(resumo['combustiveis'])} combustíveis</b>
({html.escape(', '.join(resumo['combustiveis']))}), entre {resumo['inicio']} e {resumo['fim']}.
Cada posto tem coletas em datas diferentes, atendendo aos requisitos do item II do enunciado.</p>
{aviso_demo}

<h2>2. Forma de divulgação escolhida</h2>
<p>Entre as opções previstas no enunciado, o grupo adotou a <b>opção (a): criação de um website</b>
aberto ao público, no qual qualquer pessoa — sem conhecimento técnico e sem instalar nada — consulta
os preços coletados diretamente do navegador do celular ou do computador.</p>
<p>A escolha se justifica por três motivos: (i) o site responde a todas as consultas exigidas no item
II.d de forma interativa, com filtros por combustível, bairro e posto; (ii) permanece disponível
permanentemente, podendo ser atualizado a cada nova coleta, diferentemente de um cartaz; e (iii)
o endereço pode ser compartilhado em grupos de mensagens e redes sociais do bairro, ampliando o
alcance da ação de extensão.</p>
<p><b>Endereço público do site:</b> {endereco}</p>

<h2>3. O que a comunidade encontra no site</h2>
<p>A página inicial destaca o menor preço atual de cada combustível e organiza o conteúdo em seis
seções: as quatro consultas obrigatórias, os gráficos de evolução e a área de download das planilhas
e dos dados abertos. As figuras a seguir registram o site publicado e em funcionamento.</p>
{''.join(blocos_site)}

<h2 class="secao">4. Evidências da divulgação junto a comunidade</h2>
<p>Além da publicacao do site, o grupo divulgou o endereço nos canais listados abaixo. As imagens
seguintes comprovam essa divulgação.</p>
<table>
  <thead><tr><th>Canal / local</th><th>Data</th><th>Público alcancado</th><th>Observação</th></tr></thead>
  <tbody>{canais}</tbody>
</table>
{extras_html}

<h2>5. Retorno da comunidade</h2>
<p class="pendente">[PREENCHER: comentários, dúvidas e sugestões recebidas; numero de acessos ao
site, se houver medição; relato de moradores que usaram a consulta antes de abastecer.]</p>

<h2>6. Conclusão</h2>
<p>A etapa cumpriu o objetivo de levar a informação produzida no banco de dados para fora da sala de
aula: os preços coletados deixaram de ser um conjunto de tabelas e passaram a ser uma consulta
publica, gratuita e de leitura simples, capaz de ajudar o morador a decidir onde abastecer. O mesmo
material tambem ficou disponível em planilha, para quem preferir analisar os números por conta
própria.</p>

<h2>7. Como os dados e os artefatos foram produzidos</h2>
<ul>
  <li><b>Origem dos dados:</b> {html.escape(origem)} Os registros ficam em
      <code>dados/coletas.csv</code>, no mesmo formato exportado pelo banco relacional da AOP2;
      a importação da série da ANP é feita por <code>aop3/scripts/importar_anp.py</code>.</li>
  <li><b>Site:</b> <code>aop3/site/</code> — HTML, CSS e JavaScript sem dependências externas; as quatro
      consultas do item II.d são executadas sobre os mesmos dados do banco, e as consultas SQL
      equivalentes ficam visíveis em cada secao da página.</li>
  <li><b>Planilhas e gráficos:</b> <code>aop3/scripts/gerar_site_e_planilhas.py</code> gera os arquivos de
      <code>aop3/planilhas/</code>, incluindo a planilha única com as quatro consultas e os dois gráficos
      exigidos no item II.e.</li>
  <li><b>Este relatório:</b> <code>aop3/scripts/gerar_relatorio.py</code>, que captura automaticamente as
      telas do site publicado e reúne as evidências da divulgação.</li>
</ul>

<p style="margin-top:18px; font-size:9.5pt; color:#55554c;">Relatório gerado em {hoje}.</p>

</body>
</html>
"""


def main() -> int:
    chrome = navegador()
    if chrome is None:
        print("Chromium/Chrome não encontrado: instale um deles para gerar os prints e o PDF.",
              file=sys.stderr)
        return 1

    RELATORIO.mkdir(parents=True, exist_ok=True)
    telas = capturar_telas(chrome)
    extras = evidencias_do_grupo()
    SAIDA_HTML.write_text(montar_html(telas, extras, resumo_dados()), encoding="utf-8")

    subprocess.run(
        [chrome, "--headless", "--no-sandbox", "--disable-gpu",
         "--no-pdf-header-footer", "--virtual-time-budget=8000",
         f"--print-to-pdf={SAIDA_PDF}", SAIDA_HTML.as_uri()],
        check=True, capture_output=True,
    )

    print(f"{len(telas)} telas do site capturadas em {EVIDENCIAS.relative_to(RAIZ)}/")
    print(f"{len(extras)} evidencia(s) do grupo incluida(s)")
    print(f"relatorio -> {SAIDA_PDF.relative_to(RAIZ)}")
    if not URL_SITE or any("[" in nome for nome, _ in INTEGRANTES):
        print("\nATENÇÃO: ainda há campos entre colchetes no relatório "
              "(integrantes, endereço do site, canais de divulgação). "
              "Preencha o bloco DADOS DA ENTREGA em aop3/scripts/gerar_relatorio.py e rode de novo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
