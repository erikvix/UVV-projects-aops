-- ---------------------------------------------------------------------------
-- Projeto de Extensao - Arquitetura de Dados Relacionais I
-- AOP3 - consultas exibidas no site de divulgacao (requisito II.d)
--
-- As mesmas consultas da AOP2. O site reproduz exatamente estes resultados em
-- JavaScript, a partir do arquivo dados/coletas.csv exportado do banco.
-- Dialeto: PostgreSQL (funciona tambem no MySQL 8+ / SQL Server 2012+,
-- que suportam funcoes de janela).
--
-- Modelo usado (AOP2):
--   posto(id_posto PK, nome, endereco, id_bairro FK, bandeira)
--   bairro(id_bairro PK, nome, id_cidade FK)
--   combustivel(id_combustivel PK, nome)
--   coleta(id_coleta PK, id_posto FK, id_combustivel FK, data_coleta, preco)
-- ---------------------------------------------------------------------------


-- ===========================================================================
-- CONSULTA I - Menor e maior preco de cada tipo de combustivel
-- Retorna: nome do posto, endereco, bairro, combustivel, valor e data da coleta
-- ===========================================================================
WITH precos AS (
    SELECT c.id_combustivel,
           cb.nome        AS combustivel,
           p.nome         AS posto,
           p.endereco     AS endereco,
           b.nome         AS bairro,
           c.preco        AS preco,
           c.data_coleta  AS data_coleta,
           RANK() OVER (PARTITION BY c.id_combustivel ORDER BY c.preco ASC,  c.data_coleta DESC) AS pos_menor,
           RANK() OVER (PARTITION BY c.id_combustivel ORDER BY c.preco DESC, c.data_coleta DESC) AS pos_maior
      FROM coleta c
      JOIN posto p        ON p.id_posto        = c.id_posto
      JOIN bairro b       ON b.id_bairro       = p.id_bairro
      JOIN combustivel cb ON cb.id_combustivel = c.id_combustivel
)
SELECT combustivel,
       CASE WHEN pos_menor = 1 THEN 'Menor preco' ELSE 'Maior preco' END AS tipo,
       posto,
       endereco,
       bairro,
       preco,
       data_coleta
  FROM precos
 WHERE pos_menor = 1 OR pos_maior = 1
 ORDER BY combustivel, tipo DESC, preco;


-- ===========================================================================
-- CONSULTA II - Preco medio e quantidade de amostras por posto e combustivel
-- Retorna: nome do posto, bairro, combustivel, preco medio, qtd. de amostras
-- ===========================================================================
SELECT p.nome                  AS posto,
       b.nome                  AS bairro,
       cb.nome                 AS combustivel,
       ROUND(AVG(c.preco), 3)  AS preco_medio,
       COUNT(*)                AS qtd_amostras
  FROM coleta c
  JOIN posto p        ON p.id_posto        = c.id_posto
  JOIN bairro b       ON b.id_bairro       = p.id_bairro
  JOIN combustivel cb ON cb.id_combustivel = c.id_combustivel
 GROUP BY p.nome, b.nome, cb.nome
 ORDER BY cb.nome, preco_medio;


-- ===========================================================================
-- CONSULTA III - Preco mais recente de cada combustivel em cada posto
-- Retorna: nome do posto, bairro, combustivel, valor e data da coleta
-- ===========================================================================
WITH ultima AS (
    SELECT c.*,
           ROW_NUMBER() OVER (PARTITION BY c.id_posto, c.id_combustivel
                              ORDER BY c.data_coleta DESC, c.id_coleta DESC) AS ordem
      FROM coleta c
)
SELECT p.nome        AS posto,
       b.nome        AS bairro,
       cb.nome       AS combustivel,
       u.preco       AS preco,
       u.data_coleta AS data_coleta
  FROM ultima u
  JOIN posto p        ON p.id_posto        = u.id_posto
  JOIN bairro b       ON b.id_bairro       = p.id_bairro
  JOIN combustivel cb ON cb.id_combustivel = u.id_combustivel
 WHERE u.ordem = 1
 ORDER BY cb.nome, u.preco;


-- ===========================================================================
-- CONSULTA IV - Evolucao do preco de UM combustivel em UM posto, por data
-- Retorna: nome do posto, bairro, combustivel, valor e data da coleta
-- (no site, :posto e :combustivel sao escolhidos pelo usuario nos seletores)
-- ===========================================================================
SELECT p.nome        AS posto,
       b.nome        AS bairro,
       cb.nome       AS combustivel,
       c.preco       AS preco,
       c.data_coleta AS data_coleta
  FROM coleta c
  JOIN posto p        ON p.id_posto        = c.id_posto
  JOIN bairro b       ON b.id_bairro       = p.id_bairro
  JOIN combustivel cb ON cb.id_combustivel = c.id_combustivel
 WHERE p.nome  = :posto
   AND cb.nome = :combustivel
 ORDER BY c.data_coleta;
