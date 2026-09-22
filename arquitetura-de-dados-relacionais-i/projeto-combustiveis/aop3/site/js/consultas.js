/* As quatro consultas exigidas no item II.d do projeto, aplicadas sobre
   window.DADOS.coletas. Cada função devolve exatamente as mesmas linhas que a
   consulta SQL correspondente em aop3/sql/consultas.sql. */

(function (global) {
  "use strict";

  function porData(a, b) {
    return a.data < b.data ? -1 : a.data > b.data ? 1 : 0;
  }

  /* CONSULTA I - menor e maior preço de cada tipo de combustível.
     Em caso de empate no preço, vence a coleta mais recente. */
  function menoresEMaiores(coletas) {
    var porCombustivel = agrupar(coletas, function (c) { return c.combustivel; });
    var linhas = [];
    Object.keys(porCombustivel).forEach(function (combustivel) {
      var lista = porCombustivel[combustivel].slice();
      var menor = lista.reduce(function (m, c) {
        return c.preco < m.preco || (c.preco === m.preco && c.data > m.data) ? c : m;
      });
      var maior = lista.reduce(function (m, c) {
        return c.preco > m.preco || (c.preco === m.preco && c.data > m.data) ? c : m;
      });
      linhas.push({ combustivel: combustivel, tipo: "Menor preço", coleta: menor });
      linhas.push({ combustivel: combustivel, tipo: "Maior preço", coleta: maior });
    });
    return linhas;
  }

  /* CONSULTA II - preço médio e quantidade de amostras por posto e combustível. */
  function mediaPorPostoCombustivel(coletas) {
    var chaves = agrupar(coletas, function (c) { return c.posto + "\u0000" + c.combustivel; });
    return Object.keys(chaves).map(function (chave) {
      var lista = chaves[chave];
      var soma = lista.reduce(function (s, c) { return s + c.preco; }, 0);
      return {
        posto: lista[0].posto,
        bairro: lista[0].bairro,
        combustivel: lista[0].combustivel,
        precoMedio: soma / lista.length,
        qtdAmostras: lista.length
      };
    }).sort(function (a, b) {
      return a.combustivel.localeCompare(b.combustivel, "pt-BR") || a.precoMedio - b.precoMedio;
    });
  }

  /* CONSULTA III - preço mais recente de cada combustível em cada posto. */
  function precoMaisRecente(coletas) {
    var chaves = agrupar(coletas, function (c) { return c.posto + "\u0000" + c.combustivel; });
    return Object.keys(chaves).map(function (chave) {
      return chaves[chave].slice().sort(porData).pop();
    }).sort(function (a, b) {
      return a.combustivel.localeCompare(b.combustivel, "pt-BR") || a.preco - b.preco;
    });
  }

  /* CONSULTA IV - evolução do preço de um combustível em um posto, por data. */
  function evolucao(coletas, posto, combustivel) {
    return coletas.filter(function (c) {
      return c.posto === posto && c.combustivel === combustivel;
    }).sort(porData);
  }

  /* Série do preço médio de cada combustível por data (gráfico II.e.I).
     Opcionalmente restrita a um posto (gráfico II.e.II). */
  function mediaPorData(coletas, posto) {
    var base = posto ? coletas.filter(function (c) { return c.posto === posto; }) : coletas;
    var chaves = agrupar(base, function (c) { return c.combustivel + "\u0000" + c.data; });
    var porCombustivel = {};
    Object.keys(chaves).forEach(function (chave) {
      var lista = chaves[chave];
      var media = lista.reduce(function (s, c) { return s + c.preco; }, 0) / lista.length;
      var nome = lista[0].combustivel;
      (porCombustivel[nome] = porCombustivel[nome] || []).push({ data: lista[0].data, valor: media });
    });
    Object.keys(porCombustivel).forEach(function (nome) {
      porCombustivel[nome].sort(porData);
    });
    return porCombustivel;
  }

  function agrupar(lista, chaveDe) {
    return lista.reduce(function (acc, item) {
      var chave = chaveDe(item);
      (acc[chave] = acc[chave] || []).push(item);
      return acc;
    }, {});
  }

  global.Consultas = {
    menoresEMaiores: menoresEMaiores,
    mediaPorPostoCombustivel: mediaPorPostoCombustivel,
    precoMaisRecente: precoMaisRecente,
    evolucao: evolucao,
    mediaPorData: mediaPorData
  };
})(window);
