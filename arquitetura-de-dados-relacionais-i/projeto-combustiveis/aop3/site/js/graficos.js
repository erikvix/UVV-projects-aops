/* Gráfico de linhas em SVG, sem bibliotecas externas.
   Usado nos dois gráficos exigidos no item II.e do projeto:
   evolução do preço médio de cada combustível (geral e por posto). */

(function (global) {
  "use strict";

  var NS = "http://www.w3.org/2000/svg";

  function el(nome, atributos) {
    var node = document.createElementNS(NS, nome);
    Object.keys(atributos || {}).forEach(function (k) { node.setAttribute(k, atributos[k]); });
    return node;
  }

  function moeda(valor) {
    return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL", minimumFractionDigits: 2 });
  }

  function dataCurta(iso) {
    var p = iso.split("-");
    return p[2] + "/" + p[1];
  }

  function dataLonga(iso) {
    var p = iso.split("-");
    return p[2] + "/" + p[1] + "/" + p[0];
  }

  /* Escala vertical com limites "redondos" e passo legível. */
  function escalaY(valores) {
    var min = Math.min.apply(null, valores);
    var max = Math.max.apply(null, valores);
    var folga = (max - min) * 0.25 || 0.5;
    var baixo = Math.max(0, min - folga);
    var alto = max + folga;
    var passo = Math.max(0.1, Math.ceil(((alto - baixo) / 4) * 10) / 10);
    baixo = Math.floor(baixo / passo) * passo;
    alto = Math.ceil(alto / passo) * passo;
    var marcas = [];
    for (var v = baixo; v <= alto + 1e-9; v += passo) marcas.push(Math.round(v * 1000) / 1000);
    return { min: baixo, max: alto, marcas: marcas };
  }

  /* config: { series: [{nome, cor, pontos: [{data, valor}]}], altura, rotularLinhas } */
  function linhas(container, config) {
    var dica = document.createElement("div");
    dica.className = "dica";
    dica.setAttribute("role", "status");
    container.classList.add("grafico");
    container.textContent = "";
    container.appendChild(dica);

    function desenhar() {
      var anterior = container.querySelector("svg");
      if (anterior) anterior.remove();

      var series = config.series.filter(function (s) { return s.pontos.length; });
      if (!series.length) return;

      var largura = Math.max(260, container.clientWidth || 320);
      var altura = config.altura || 300;
      var rotular = config.rotularLinhas !== false && largura >= 430;
      var margem = { topo: 16, direita: rotular ? 108 : 18, baixo: 34, esquerda: 52 };
      var larguraPlot = largura - margem.esquerda - margem.direita;
      var alturaPlot = altura - margem.topo - margem.baixo;

      var datas = [];
      series.forEach(function (s) {
        s.pontos.forEach(function (p) { if (datas.indexOf(p.data) === -1) datas.push(p.data); });
      });
      datas.sort();

      var valores = [];
      series.forEach(function (s) { s.pontos.forEach(function (p) { valores.push(p.valor); }); });
      var y = escalaY(valores);

      function posX(data) {
        var i = datas.indexOf(data);
        return datas.length === 1
          ? margem.esquerda + larguraPlot / 2
          : margem.esquerda + (larguraPlot * i) / (datas.length - 1);
      }
      function posY(valor) {
        return margem.topo + alturaPlot * (1 - (valor - y.min) / (y.max - y.min));
      }

      var svg = el("svg", {
        viewBox: "0 0 " + largura + " " + altura,
        width: largura, height: altura,
        role: "img",
        "aria-label": config.descricao || "Gráfico de evolução de preços"
      });

      /* grade e eixo Y - recessivos */
      y.marcas.forEach(function (valor) {
        var yy = posY(valor);
        svg.appendChild(el("line", {
          x1: margem.esquerda, x2: margem.esquerda + larguraPlot, y1: yy, y2: yy,
          stroke: "var(--border)", "stroke-width": 1
        }));
        var rotulo = el("text", {
          x: margem.esquerda - 8, y: yy + 4, "text-anchor": "end",
          fill: "var(--text-muted)", "font-size": 11
        });
        rotulo.textContent = "R$ " + valor.toFixed(2).replace(".", ",");
        svg.appendChild(rotulo);
      });

      /* eixo X - primeira, última e algumas datas intermediárias */
      var passoRotulo = Math.max(1, Math.ceil(datas.length / Math.max(2, Math.floor(larguraPlot / 64))));
      datas.forEach(function (data, i) {
        if (i % passoRotulo !== 0 && i !== datas.length - 1) return;
        var rotulo = el("text", {
          x: posX(data), y: altura - 12, "text-anchor": "middle",
          fill: "var(--text-muted)", "font-size": 11
        });
        rotulo.textContent = dataCurta(data);
        svg.appendChild(rotulo);
      });

      /* linhas, 2px, com marcadores nos pontos */
      series.forEach(function (s) {
        var d = s.pontos.map(function (p, i) {
          return (i ? "L" : "M") + posX(p.data).toFixed(1) + " " + posY(p.valor).toFixed(1);
        }).join(" ");
        svg.appendChild(el("path", {
          d: d, fill: "none", stroke: s.cor, "stroke-width": 2,
          "stroke-linejoin": "round", "stroke-linecap": "round"
        }));
        s.pontos.forEach(function (p) {
          svg.appendChild(el("circle", {
            cx: posX(p.data), cy: posY(p.valor), r: 3.2,
            fill: s.cor, stroke: "var(--surface-1)", "stroke-width": 2
          }));
        });
      });

      /* rótulos diretos no fim de cada linha, afastados para não colidirem */
      if (rotular) {
        var fins = series.map(function (s) {
          var ultimo = s.pontos[s.pontos.length - 1];
          return { nome: s.nome, cor: s.cor, y: posY(ultimo.valor) };
        }).sort(function (a, b) { return a.y - b.y; });
        for (var i = 1; i < fins.length; i++) {
          if (fins[i].y - fins[i - 1].y < 14) fins[i].y = fins[i - 1].y + 14;
        }
        fins.forEach(function (f) {
          var texto = el("text", {
            x: margem.esquerda + larguraPlot + 10,
            y: Math.min(altura - margem.baixo + 8, f.y + 4),
            fill: "var(--text-secondary)", "font-size": 11.5
          });
          texto.textContent = f.nome;
          svg.appendChild(texto);
          svg.appendChild(el("rect", {
            x: margem.esquerda + larguraPlot + 2,
            y: Math.min(altura - margem.baixo + 8, f.y + 4) - 8, width: 6, height: 6, rx: 2, fill: f.cor
          }));
        });
      }

      /* camada de interação: mira vertical + tooltip */
      var mira = el("line", {
        y1: margem.topo, y2: margem.topo + alturaPlot,
        stroke: "var(--text-muted)", "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0
      });
      svg.appendChild(mira);
      var realces = el("g", { opacity: 0 });
      svg.appendChild(realces);

      var area = el("rect", {
        x: margem.esquerda, y: margem.topo, width: larguraPlot, height: alturaPlot,
        fill: "transparent", style: "cursor: crosshair"
      });
      svg.appendChild(area);

      function mostrar(evento) {
        var caixa = svg.getBoundingClientRect();
        var toque = evento.touches && evento.touches[0];
        var x = ((toque || evento).clientX - caixa.left) * (largura / caixa.width);
        var proporcao = datas.length === 1 ? 0 : (x - margem.esquerda) / larguraPlot;
        var indice = Math.max(0, Math.min(datas.length - 1, Math.round(proporcao * (datas.length - 1))));
        var data = datas[indice];

        mira.setAttribute("x1", posX(data));
        mira.setAttribute("x2", posX(data));
        mira.setAttribute("opacity", 1);
        realces.textContent = "";
        realces.setAttribute("opacity", 1);

        var itens = [];
        series.forEach(function (s) {
          var ponto = s.pontos.filter(function (p) { return p.data === data; })[0];
          if (!ponto) return;
          itens.push({ nome: s.nome, cor: s.cor, valor: ponto.valor });
          realces.appendChild(el("circle", {
            cx: posX(data), cy: posY(ponto.valor), r: 5,
            fill: s.cor, stroke: "var(--surface-1)", "stroke-width": 2
          }));
        });
        if (!itens.length) return;

        itens.sort(function (a, b) { return b.valor - a.valor; });
        dica.innerHTML = '<div class="dica-data">' + dataLonga(data) + "</div><ul>" +
          itens.map(function (it) {
            return '<li><span class="nome"><span class="ponto" style="background:' + it.cor + '"></span>' +
              it.nome + "</span><b>" + moeda(it.valor) + "</b></li>";
          }).join("") + "</ul>";

        var escala = caixa.width / largura;
        var esquerda = posX(data) * escala + 14;
        if (esquerda + dica.offsetWidth > caixa.width) esquerda = posX(data) * escala - dica.offsetWidth - 14;
        dica.style.left = Math.max(0, esquerda) + "px";
        dica.style.top = Math.max(0, margem.topo * escala) + "px";
        dica.style.opacity = 1;
      }

      function esconder() {
        dica.style.opacity = 0;
        mira.setAttribute("opacity", 0);
        realces.setAttribute("opacity", 0);
      }

      area.addEventListener("mousemove", mostrar);
      area.addEventListener("mouseleave", esconder);
      area.addEventListener("touchstart", mostrar, { passive: true });
      area.addEventListener("touchmove", mostrar, { passive: true });
      area.addEventListener("touchend", esconder);

      container.appendChild(svg);
    }

    desenhar();
    if (global.ResizeObserver) {
      var largura0 = container.clientWidth;
      new ResizeObserver(function () {
        if (Math.abs(container.clientWidth - largura0) > 8) {
          largura0 = container.clientWidth;
          desenhar();
        }
      }).observe(container);
    } else {
      global.addEventListener("resize", desenhar);
    }
    return { redesenhar: desenhar };
  }

  global.Graficos = { linhas: linhas, moeda: moeda, dataLonga: dataLonga };
})(window);
