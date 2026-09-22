# Projeto de Extensão — Preços de Combustíveis (Vila Velha/ES)

Projeto de Extensão da disciplina **Arquitetura de Dados Relacionais I** (UVV):
um banco de dados relacional que armazena preços de combustíveis coletados na região
e divulga essas informações para a comunidade.

| Etapa | Conteúdo | Pasta |
| --- | --- | --- |
| AOP1 | Projeto conceitual (modelo ER) | _a incluir_ |
| AOP2 | Projeto lógico (3FN) e físico (SGBD) | _a incluir_ |
| AOP3 | Divulgação para a comunidade — **website + planilhas + relatório** | [`aop3/`](./aop3) |

## Estrutura

```
projeto-combustiveis/
├── dados/coletas.csv        # fonte única: uma linha por coleta de preço
└── aop3/
    ├── site/                # site público (HTML/CSS/JS, sem dependências)
    ├── planilhas/           # .xlsx com gráficos + um CSV por consulta
    ├── sql/consultas.sql    # as 4 consultas do item II.d
    ├── relatorio/           # RELATORIO-AOP3.pdf + evidências
    ├── scripts/             # geração dos artefatos e importação da ANP
    └── README.md            # passo a passo da entrega da AOP3
```

Comece por [`aop3/README.md`](./aop3/README.md).
