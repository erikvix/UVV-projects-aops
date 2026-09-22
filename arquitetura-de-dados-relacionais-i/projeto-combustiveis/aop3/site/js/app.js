/* Monta a página a partir de window.DADOS (gerado de dados/coletas.csv). */

(function () {
  "use strict";

  var DADOS = window.DADOS;
  var COLETAS = DADOS.coletas;

  /* Ordem fixa das cores: cada combustível tem sempre a mesma cor,
     em qualquer gráfico, tabela ou filtro da página. */
  var CORES = ["var(--series-1)", "var(--series-2)", "var(--series-3)", "var(--series-4)"];
  var COMBUSTIVEIS = unicos(COLETAS.map(function (c) { return c.combustivel; }));
  var POSTOS = unicos(COLETAS.map(function (c) { return c.posto; }));
  var BAIRROS = unicos(COLETAS.map(function (c) { return c.bairro; }));
  var COR = {};
  COMBUSTIVEIS.forEach(function (nome, i) { COR[nome] = CORES[i % CORES.length]; });

  var DADOS_POSTO = {};
  COLETAS.forEach(function (c) { DADOS_POSTO[c.posto] = c; });

  function unicos(lista) {
    return lista.filter(function (v, i, a) { return a.indexOf(v) === i; })
                .sort(function (a, b) { return a.localeCompare(b, "pt-BR"); });
  }
  function moeda(v) { return Graficos.moeda(v); }
  function data(v) { return Graficos.dataLonga(v); }
  function q(sel) { return document.querySelector(sel); }
  function criar(tag, texto, classe) {
    var n = document.createElement(tag);
    if (texto !== undefined && texto !== null) n.textContent = texto;
    if (classe) n.className = classe;
    return n;
  }
  function marca(nome) {
    var span = criar("span", null, "marca");
    var ponto = criar("span", null, "ponto");
    ponto.style.background = COR[nome] || "var(--text-muted)";
    span.appendChild(ponto);
    span.appendChild(criar("span", nome));
    return span;
  }
  function tabela(destino, colunas, linhas) {
    destino.textContent = "";
    var rolagem = criar("div", null, "tabela-rolagem");
    var tab = document.createElement("table");
    var thead = document.createElement("thead");
    var tr = document.createElement("tr");
    colunas.forEach(function (col) {
      var th = criar("th", col.titulo, col.num ? "num" : null);
      tr.appendChild(th);
    });
    thead.appendChild(tr);
    tab.appendChild(thead);
    var tbody = document.createElement("tbody");
    if (!linhas.length) {
      var vazio = document.createElement("tr");
      var td = criar("td", "Nenhum resultado para os filtros selecionados.");
      td.colSpan = colunas.length;
      vazio.appendChild(td);
      tbody.appendChild(vazio);
    }
    linhas.forEach(function (linha) {
      var tr2 = document.createElement("tr");
      colunas.forEach(function (col) {
        var td = criar("td", null, col.num ? "num" : null);
        var valor = col.celula(linha);
        if (valor instanceof Node) td.appendChild(valor); else td.textContent = valor;
        tr2.appendChild(td);
      });
      tbody.appendChild(tr2);
    });
    tab.appendChild(tbody);
    rolagem.appendChild(tab);
    destino.appendChild(rolagem);
  }
  function opcoes(select, valores, rotuloTodos) {
    select.textContent = "";
    if (rotuloTodos) select.appendChild(new Option(rotuloTodos, ""));
    valores.forEach(function (v) { select.appendChild(new Option(v, v)); });
  }

  /* ---------------- cabeçalho, aviso e abas ---------------- */

  function cabecalho() {
    q("#cidade").textContent = DADOS.cidade + " - " + DADOS.uf;
    q("#resumo").textContent = COLETAS.length + " coletas | " + POSTOS.length + " postos | " +
      BAIRROS.length + " bairros | " + COMBUSTIVEIS.length + " combustíveis | período de " +
      data(DADOS.periodo.inicio) + " a " + data(DADOS.periodo.fim);
    if (DADOS.demo) q("#aviso").hidden = false;
    q("#fonte").textContent = DADOS.fonte;
    q("#atualizacao").textContent = data(DADOS.gerado_em);
  }

  function abas() {
    var botoes = [].slice.call(document.querySelectorAll("nav.abas button"));

    function abrir(botao) {
      botoes.forEach(function (outro) {
        var ativo = outro === botao;
        outro.setAttribute("aria-selected", ativo ? "true" : "false");
        q("#" + outro.dataset.painel).hidden = !ativo;
      });
      window.dispatchEvent(new Event("resize"));
    }

    botoes.forEach(function (botao) {
      botao.addEventListener("click", function () { abrir(botao); });
    });

    /* Link direto para uma aba: index.html?aba=painel-5
       (usado tambem pelo script que gera as evidencias do relatorio). */
    var pedida = new URLSearchParams(location.search).get("aba");
    if (pedida) {
      var alvo = botoes.filter(function (b) { return b.dataset.painel === pedida; })[0];
      if (alvo) abrir(alvo);
    }
  }

  function tema() {
    var botao = q("#alternar-tema");
    function aplicar(valor) {
      document.documentElement.setAttribute("data-theme", valor);
      botao.textContent = valor === "dark" ? "Tema claro" : "Tema escuro";
      botao.setAttribute("aria-label", "Alternar para tema " + (valor === "dark" ? "claro" : "escuro"));
    }
    var salvo = null;
    try { salvo = localStorage.getItem("tema"); } catch (e) { /* navegação privada */ }
    var inicial = salvo || (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    aplicar(inicial);
    botao.addEventListener("click", function () {
      var novo = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      aplicar(novo);
      try { localStorage.setItem("tema", novo); } catch (e) { /* ignora */ }
      window.dispatchEvent(new Event("resize"));
    });
  }

  /* ---------------- destaques (menor preço mais recente) ---------------- */

  function destaques() {
    var recentes = Consultas.precoMaisRecente(COLETAS);
    var destino = q("#destaques");
    destino.textContent = "";
    COMBUSTIVEIS.forEach(function (combustivel) {
      var lista = recentes.filter(function (r) { return r.combustivel === combustivel; });
      if (!lista.length) return;
      var melhor = lista.reduce(function (m, r) { return r.preco < m.preco ? r : m; });
      var tile = criar("div", null, "tile");
      var rotulo = criar("div", null, "rotulo");
      var ponto = criar("span", null, "ponto");
      ponto.style.background = COR[combustivel];
      rotulo.appendChild(ponto);
      rotulo.appendChild(criar("span", combustivel));
      tile.appendChild(rotulo);
      tile.appendChild(criar("div", moeda(melhor.preco), "valor"));
      tile.appendChild(criar("div", melhor.posto + " - " + melhor.bairro + " (" + data(melhor.data) + ")", "onde"));
      destino.appendChild(tile);
    });
  }

  /* ---------------- consulta I ---------------- */

  function consultaI() {
    var linhas = Consultas.menoresEMaiores(COLETAS).sort(function (a, b) {
      return a.combustivel.localeCompare(b.combustivel, "pt-BR") ||
             (a.tipo === "Menor preço" ? -1 : 1);
    });
    tabela(q("#tabela-1"), [
      { titulo: "Combustível", celula: function (l) { return marca(l.combustivel); } },
      { titulo: "", celula: function (l) {
          return criar("span", l.tipo, "etiqueta " + (l.tipo === "Menor preço" ? "menor" : "maior"));
        } },
      { titulo: "Posto", celula: function (l) { return l.coleta.posto; } },
      { titulo: "Endereço", celula: function (l) { return l.coleta.endereco; } },
      { titulo: "Bairro", celula: function (l) { return l.coleta.bairro; } },
      { titulo: "Preço", num: true, celula: function (l) { return moeda(l.coleta.preco); } },
      { titulo: "Data da coleta", num: true, celula: function (l) { return data(l.coleta.data); } }
    ], linhas);
  }

  /* ---------------- consulta II ---------------- */

  function consultaII() {
    var fCombustivel = q("#f2-combustivel");
    var fBairro = q("#f2-bairro");
    opcoes(fCombustivel, COMBUSTIVEIS, "Todos");
    opcoes(fBairro, BAIRROS, "Todos");

    function render() {
      var linhas = Consultas.mediaPorPostoCombustivel(COLETAS).filter(function (l) {
        return (!fCombustivel.value || l.combustivel === fCombustivel.value) &&
               (!fBairro.value || l.bairro === fBairro.value);
      });
      tabela(q("#tabela-2"), [
        { titulo: "Posto", celula: function (l) { return l.posto; } },
        { titulo: "Bairro", celula: function (l) { return l.bairro; } },
        { titulo: "Combustível", celula: function (l) { return marca(l.combustivel); } },
        { titulo: "Preço médio", num: true, celula: function (l) { return moeda(l.precoMedio); } },
        { titulo: "Amostras", num: true, celula: function (l) { return String(l.qtdAmostras); } }
      ], linhas);
    }
    fCombustivel.addEventListener("change", render);
    fBairro.addEventListener("change", render);
    render();
  }

  /* ---------------- consulta III ---------------- */

  function consultaIII() {
    var fCombustivel = q("#f3-combustivel");
    var fBairro = q("#f3-bairro");
    opcoes(fCombustivel, COMBUSTIVEIS, "Todos");
    opcoes(fBairro, BAIRROS, "Todos");

    function render() {
      var linhas = Consultas.precoMaisRecente(COLETAS).filter(function (l) {
        return (!fCombustivel.value || l.combustivel === fCombustivel.value) &&
               (!fBairro.value || l.bairro === fBairro.value);
      });
      tabela(q("#tabela-3"), [
        { titulo: "Posto", celula: function (l) { return l.posto; } },
        { titulo: "Bairro", celula: function (l) { return l.bairro; } },
        { titulo: "Combustível", celula: function (l) { return marca(l.combustivel); } },
        { titulo: "Preço", num: true, celula: function (l) { return moeda(l.preco); } },
        { titulo: "Data da coleta", num: true, celula: function (l) { return data(l.data); } }
      ], linhas);
    }
    fCombustivel.addEventListener("change", render);
    fBairro.addEventListener("change", render);
    render();
  }

  /* ---------------- consulta IV ---------------- */

  function consultaIV() {
    var fPosto = q("#f4-posto");
    var fCombustivel = q("#f4-combustivel");
    opcoes(fPosto, POSTOS);
    opcoes(fCombustivel, COMBUSTIVEIS);

    function render() {
      var linhas = Consultas.evolucao(COLETAS, fPosto.value, fCombustivel.value);
      var resumo = q("#resumo-4");
      if (linhas.length > 1) {
        var variacao = linhas[linhas.length - 1].preco - linhas[0].preco;
        var sinal = variacao >= 0 ? "+" : "-";
        resumo.textContent = "Do dia " + data(linhas[0].data) + " ao dia " +
          data(linhas[linhas.length - 1].data) + ", o preço variou " + sinal +
          moeda(Math.abs(variacao)).replace("R$", "R$ ").trim() + " (" +
          (variacao / linhas[0].preco * 100).toFixed(1).replace(".", ",") + "%).";
      } else {
        resumo.textContent = "";
      }

      Graficos.linhas(q("#grafico-4"), {
        altura: 300,
        descricao: "Evolução do preço de " + fCombustivel.value + " no " + fPosto.value,
        series: [{
          nome: fCombustivel.value,
          cor: COR[fCombustivel.value],
          pontos: linhas.map(function (c) { return { data: c.data, valor: c.preco }; })
        }]
      });

      tabela(q("#tabela-4"), [
        { titulo: "Posto", celula: function (l) { return l.posto; } },
        { titulo: "Bairro", celula: function (l) { return l.bairro; } },
        { titulo: "Combustível", celula: function (l) { return marca(l.combustivel); } },
        { titulo: "Preço", num: true, celula: function (l) { return moeda(l.preco); } },
        { titulo: "Data da coleta", num: true, celula: function (l) { return data(l.data); } }
      ], linhas);
    }
    fPosto.addEventListener("change", render);
    fCombustivel.addEventListener("change", render);
    render();
  }

  /* ---------------- gráficos do item II.e ---------------- */

  function legenda(destino, nomes) {
    destino.textContent = "";
    nomes.forEach(function (nome) {
      var item = criar("span", null, "item");
      var ponto = criar("span", null, "ponto");
      ponto.style.background = COR[nome];
      item.appendChild(ponto);
      item.appendChild(criar("span", nome));
      destino.appendChild(item);
    });
  }

  function series(medias) {
    return COMBUSTIVEIS.filter(function (nome) { return medias[nome]; }).map(function (nome) {
      return { nome: nome, cor: COR[nome], pontos: medias[nome] };
    });
  }

  function graficos() {
    legenda(q("#legenda-geral"), COMBUSTIVEIS);
    Graficos.linhas(q("#grafico-geral"), {
      altura: 340,
      descricao: "Evolução do preço médio de cada combustível em " + DADOS.cidade,
      series: series(Consultas.mediaPorData(COLETAS))
    });

    legenda(q("#legenda-postos"), COMBUSTIVEIS);
    var destino = q("#graficos-postos");
    destino.textContent = "";
    POSTOS.forEach(function (posto) {
      var cartao = criar("div", null, "cartao");
      var titulo = criar("h3", posto);
      var sub = criar("p", DADOS_POSTO[posto].bairro, "descricao");
      sub.style.margin = "-8px 0 10px";
      sub.style.fontSize = ".85rem";
      cartao.appendChild(titulo);
      cartao.appendChild(sub);
      var area = criar("div");
      cartao.appendChild(area);
      destino.appendChild(cartao);
      Graficos.linhas(area, {
        altura: 240,
        rotularLinhas: false,
        descricao: "Evolução do preço médio de cada combustível no " + posto,
        series: series(Consultas.mediaPorData(COLETAS, posto))
      });
    });
  }

  cabecalho();
  abas();
  tema();
  destaques();
  consultaI();
  consultaII();
  consultaIII();
  consultaIV();
  graficos();
})();
