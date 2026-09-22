# AOP3 — Divulgação do trabalho para a comunidade

Entrega da terceira etapa do Projeto de Extensão de **Arquitetura de Dados Relacionais I**:
os dados de preço de combustíveis de **Vila Velha/ES** publicados para a comunidade.

Opção de divulgação escolhida: **(a) criação de um website**, que responde às quatro
consultas obrigatórias do item II.d e disponibiliza as planilhas e os gráficos do item II.e.
Essa mesma entrega atende também ao trabalho de *Programação Web – Front End*.

## O que já está pronto

| Entregável | Onde está |
| --- | --- |
| Site público (4 consultas + 2 gráficos + downloads) | [`site/`](./site) — abra `site/index.html` |
| Planilha única com as consultas e os gráficos | [`planilhas/precos-combustiveis-vila-velha.xlsx`](./planilhas) |
| Uma planilha CSV por consulta | `planilhas/consulta-1.csv` … `consulta-4.csv` |
| Consultas SQL do item II.d | [`sql/consultas.sql`](./sql/consultas.sql) |
| Relatório de evidências em PDF | [`relatorio/RELATORIO-AOP3.pdf`](./relatorio) |
| Dados brutos (fonte única de tudo) | [`../dados/coletas.csv`](../dados/coletas.csv) |

Tudo é gerado a partir de **um único arquivo**: `dados/coletas.csv`. Trocou o arquivo,
rodou os dois scripts, site, planilhas e relatório saem atualizados.

> ⚠️ **Os preços que estão no repositório agora são de demonstração** — um conjunto
> gerado para validar o site de ponta a ponta. Substitua pelos dados reais antes de
> divulgar (passo 1 abaixo). Enquanto a marca de demonstração estiver ligada, o site
> exibe um aviso e o relatório traz um alerta em destaque.

## Passo a passo até a entrega

### 1. Colocar os dados reais

Opção A — coleta do grupo / exportação do banco da AOP2: gere um CSV com estas colunas e
salve em `dados/coletas.csv`:

```
id_coleta,posto,bairro,endereco,bandeira,combustivel,data_coleta,preco
1,Posto Exemplo,Praia da Costa,"Av. Exemplo, 100",Ipiranga,Gasolina comum,2025-03-08,6.19
```

`data_coleta` no formato `aaaa-mm-dd` e `preco` com ponto decimal.

Opção B — série histórica da ANP:

```bash
# baixe o arquivo semestral de revenda em
# https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis
python3 aop3/scripts/importar_anp.py ca-2025-01.csv --municipio "VILA VELHA"
```

Depois, em `aop3/scripts/gerar_site_e_planilhas.py`, troque
`DADOS_DE_DEMONSTRACAO = True` por `False` (isso remove o aviso do site e corrige o texto
da fonte dos dados).

### 2. Regerar site e planilhas

```bash
python3 aop3/scripts/gerar_site_e_planilhas.py
```

### 3. Publicar o site (GitHub Pages)

1. No GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a branch**,
   branch `main`, pasta `/ (root)`.
2. O endereço fica:
   `https://<seu-usuario>.github.io/<repositorio>/arquitetura-de-dados-relacionais-i/projeto-combustiveis/aop3/site/`
3. Abra o endereço no celular para conferir — a página foi feita para funcionar bem em tela pequena.

Para testar antes de publicar, sem servidor nenhum: abra `aop3/site/index.html` no navegador.
Para testar como servidor local: `python3 -m http.server 8000 --directory aop3/site`.

### 4. Divulgar de fato para a comunidade

Compartilhe o endereço e guarde as provas: prints das mensagens e publicações, fotos do
cartaz com o QR Code do site, conversas em grupos de bairro, etc. Salve cada imagem em
`aop3/relatorio/evidencias/` e, se quiser legendas próprias, descreva-as em
`aop3/relatorio/evidencias/legendas.csv` (`arquivo;legenda`).

### 5. Gerar o relatório em PDF

Preencha o bloco **DADOS DA ENTREGA** no topo de `aop3/scripts/gerar_relatorio.py`
(integrantes e matrículas, professor, semestre, endereço do site, canais de divulgação) e rode:

```bash
python3 aop3/scripts/gerar_relatorio.py
```

O script tira sozinho os prints das telas do site, junta as suas evidências e grava
`aop3/relatorio/RELATORIO-AOP3.pdf` — é esse arquivo que vai para o AVA.

## Requisitos e onde cada um é atendido

| Requisito do enunciado | Onde |
| --- | --- |
| II.d.I — menor e maior preço de cada combustível | Aba “Menor e maior preço” · `consulta-1.csv` · `sql/consultas.sql` |
| II.d.II — preço médio e nº de amostras por posto | Aba “Preço médio por posto” · `consulta-2.csv` |
| II.d.III — preço mais recente por posto | Aba “Preço mais recente” · `consulta-3.csv` |
| II.d.IV — evolução do preço por posto/combustível | Aba “Evolução por posto” · `consulta-4.csv` |
| II.e.I — gráfico do preço médio de cada combustível | Aba “Gráficos” · planilha, aba *Gráfico - cidade* |
| II.e.II — gráfico do preço médio por posto | Aba “Gráficos” · planilha, aba *Gráfico - postos* |
| III — relatório de evidências em PDF | `relatorio/RELATORIO-AOP3.pdf` |

## Dependências

Só para regerar planilhas e relatório (o site não depende de nada):

```bash
pip install openpyxl   # planilha .xlsx
pip install pillow     # opcional: corta a margem em branco dos prints
```

O relatório em PDF é impresso pelo Chrome/Chromium instalado na máquina.
