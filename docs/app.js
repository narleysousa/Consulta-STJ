const API_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search";
const API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==";
const REPO_RAW = "https://raw.githubusercontent.com/narleysousa/Consulta-STJ/main/docs";
const REPO_API = "https://api.github.com/repos/narleysousa/Consulta-STJ";
const ACTION_URL = "https://github.com/narleysousa/Consulta-STJ/actions/workflows/consulta.yml";
const VERCEL_DEPLOY = "https://vercel.com/new/clone?repository-url=https://github.com/narleysousa/Consulta-STJ&project-name=consulta-stj&root-directory=.";
const VERCEL_SITE = "https://consulta-stj.vercel.app";
const TRANSITO = 848;
const BAIXA = 22;
const DESTAQUES = new Set([848, 22]);
const NOMES_MOV = { 848: "Trânsito em julgado", 22: "Baixa definitiva", 92: "Publicação", 54: "Acórdão" };

const MODO_LABELS = {
  ambos: "Trânsito em julgado E baixa definitiva",
  transito: "Somente trânsito em julgado",
  baixa: "Somente baixa definitiva",
  qualquer: "Trânsito em julgado OU baixa definitiva",
};
const TIPO_LABELS = {
  movimentacao: "Data da movimentação (trânsito / baixa)",
  ajuizamento: "Data de ajuizamento do processo",
  atualizacao: "Data da última atualização",
};

let processos = [];
let selecionado = null;
let cacheInfo = null;

function isGitHubPages() {
  return window.location.hostname.includes("github.io");
}

function isConsultaAoVivo() {
  const h = window.location.hostname;
  return h === "localhost" || h === "127.0.0.1" || h.includes("vercel.app");
}

function escapeHtml(v) {
  return String(v ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function corrigirTexto(t) {
  if (!t) return "";
  for (const [e, c] of [["PRESIDÃ NCIA", "PRESIDÊNCIA"], ["PRESIDÃNCIA", "PRESIDÊNCIA"]]) {
    t = t.split(e).join(c);
  }
  return t;
}

function formatarCnj(n) {
  n = String(n).padStart(20, "0");
  return `${n.slice(0, 7)}-${n.slice(7, 9)}.${n.slice(9, 13)}.${n[13]}.${n.slice(14, 16)}.${n.slice(16)}`;
}

function formatarDataBr(v) {
  if (!v) return "";
  v = String(v).trim();
  if (v.includes("T")) {
    const d = new Date(v);
    if (!isNaN(d)) return d.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }
  if (/^\d{8}/.test(v)) return `${v.slice(6, 8)}/${v.slice(4, 6)}/${v.slice(0, 4)}`;
  return v;
}

function parseData(v) {
  if (!v) return null;
  v = String(v).trim();
  if (v.includes("T")) {
    const d = new Date(v);
    return isNaN(d) ? null : d;
  }
  if (/^\d{8}/.test(v)) return new Date(+v.slice(0, 4), +v.slice(4, 6) - 1, +v.slice(6, 8));
  return null;
}

function parseDataBr(v) {
  const s = String(v || "");
  const m = s.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
  if (!m) return 0;
  return new Date(+m[3], +m[2] - 1, +m[1], +(m[4] || 0), +(m[5] || 0)).getTime();
}

function dataNoPeriodo(valor, ini, fim) {
  const d = parseData(valor);
  if (!d) return false;
  return d >= ini && d <= fim;
}

function atendeCriterio(tTrans, tBaixa, modo) {
  if (modo === "ambos") return tTrans && tBaixa;
  if (modo === "transito") return tTrans;
  if (modo === "baixa") return tBaixa;
  return tTrans || tBaixa;
}

function extrairAssuntos(raw) {
  const nomes = [];
  function coletar(item) {
    if (!item) return;
    if (typeof item === "string" && item.trim()) nomes.push(item.trim());
    else if (Array.isArray(item)) item.forEach(coletar);
    else if (typeof item === "object" && item.nome) nomes.push(corrigirTexto(String(item.nome)));
  }
  coletar(raw);
  return nomes;
}

function extrairMovs(movs, codigo) {
  return (movs || []).filter(m => m && m.codigo === codigo).map(m => ({
    codigo,
    nome: String(m.nome || ""),
    data_hora: String(m.dataHora || ""),
    orgao: corrigirTexto(String((m.orgaoJulgador || {}).nome || "")),
  }));
}

function extrairTimeline(movs) {
  const codes = new Set(Object.keys(NOMES_MOV).map(Number));
  return (movs || [])
    .filter(m => m && codes.has(m.codigo))
    .map(m => ({
      codigo: m.codigo,
      nome: String(m.nome || NOMES_MOV[m.codigo] || ""),
      data_hora: String(m.dataHora || ""),
      orgao: corrigirTexto(String((m.orgaoJulgador || {}).nome || "")),
    }))
    .sort((a, b) => a.data_hora.localeCompare(b.data_hora));
}

function processarHit(fonte, modo, filtro) {
  const movs = fonte.movimentos || [];
  const transitos = extrairMovs(movs, TRANSITO);
  const baixas = extrairMovs(movs, BAIXA);
  const temTrans = transitos.length > 0;
  const temBaixa = baixas.length > 0;
  if (!atendeCriterio(temTrans, temBaixa, modo)) return null;

  if (filtro && filtro.data_inicio && filtro.data_fim) {
    const ini = new Date(filtro.data_inicio + "T00:00:00");
    const fim = new Date(filtro.data_fim + "T23:59:59");
    if (filtro.tipo === "movimentacao") {
      const tp = transitos.some(m => dataNoPeriodo(m.data_hora, ini, fim));
      const bp = baixas.some(m => dataNoPeriodo(m.data_hora, ini, fim));
      if (!tp && !bp) return null;
    } else if (filtro.tipo === "ajuizamento") {
      if (!dataNoPeriodo(fonte.dataAjuizamento, ini, fim)) return null;
    } else if (filtro.tipo === "atualizacao") {
      if (!dataNoPeriodo(fonte.dataHoraUltimaAtualizacao, ini, fim)) return null;
    }
  }

  const ultT = transitos.sort((a, b) => b.data_hora.localeCompare(a.data_hora))[0];
  const ultB = baixas.sort((a, b) => b.data_hora.localeCompare(a.data_hora))[0];
  const classeRaw = Array.isArray(fonte.classe) ? fonte.classe[0] : fonte.classe;
  const timeline = extrairTimeline(movs);

  return {
    numero_processo: String(fonte.numeroProcesso || ""),
    numero_formatado: formatarCnj(fonte.numeroProcesso || ""),
    classe: corrigirTexto(String((classeRaw || {}).nome || "")),
    assuntos: extrairAssuntos(fonte.assuntos),
    data_ajuizamento: formatarDataBr(fonte.dataAjuizamento),
    data_ultima_atualizacao: formatarDataBr(fonte.dataHoraUltimaAtualizacao),
    tem_transito_julgado: temTrans ? "Sim" : "Não",
    data_transito_julgado: formatarDataBr(ultT?.data_hora || ""),
    tem_baixa_definitiva: temBaixa ? "Sim" : "Não",
    data_baixa_definitiva: formatarDataBr(ultB?.data_hora || ""),
    timeline: timeline.map(m => ({ ...m, data: formatarDataBr(m.data_hora) })),
  };
}

function procParaExibicao(p) {
  return {
    ...p,
    assuntos: Array.isArray(p.assuntos) ? p.assuntos.join(" | ") : (p.assuntos || ""),
  };
}

async function apiBuscar(body) {
  const payload = JSON.stringify(body);
  const tentativas = [];
  const noPages = window.location.hostname.includes("github.io");
  const local = ["localhost", "127.0.0.1"].includes(window.location.hostname);

  if (local || window.location.hostname.includes("vercel.app")) {
    tentativas.push(async () => {
      const r = await fetch(`${window.location.origin}/api/datajud`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      if (!r.ok) throw new Error(`Proxy local: HTTP ${r.status}`);
      return r.json();
    });
  }

  // Direto (funciona em localhost / Vercel com proxy local)
  if (!noPages && !local) {
    tentativas.push(async () => {
      const r = await fetch(API_URL, {
        method: "POST",
        headers: {
          Authorization: `APIKey ${API_KEY}`,
          "Content-Type": "application/json",
        },
        body: payload,
      });
      if (!r.ok) throw new Error(`API Datajud: HTTP ${r.status}`);
      return r.json();
    });
  }

  // Proxies (necessário no GitHub Pages — API bloqueia CORS)
  const proxies = [];
  proxies.push("https://consulta-stj.vercel.app/api/datajud");

  for (const url of proxies) {
    tentativas.push(async () => {
      const r = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      });
      if (!r.ok) throw new Error(`Proxy: HTTP ${r.status}`);
      return r.json();
    });
  }

  let ultimoErro;
  for (const fn of tentativas) {
    try {
      return await fn();
    } catch (e) {
      ultimoErro = e;
    }
  }
  const err = new Error(ultimoErro?.message || "Failed to fetch");
  err.cors = true;
  throw err;
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function ultimoCommitResultados() {
  try {
    const r = await fetch(`${REPO_API}/commits?path=docs/resultados.json&per_page=1`);
    if (!r.ok) return null;
    const [c] = await r.json();
    return c?.sha || null;
  } catch {
    return null;
  }
}

async function ultimaRunAction() {
  try {
    const r = await fetch(`${REPO_API}/actions/workflows/consulta.yml/runs?per_page=1`);
    if (!r.ok) return null;
    const j = await r.json();
    return j.workflow_runs?.[0] || null;
  } catch {
    return null;
  }
}

function aplicarJsonResultados(j) {
  if (!j?.processos?.length) return false;
  cacheInfo = { gerado_em: j.gerado_em, filtro: j.filtro, total: j.total };
  processos = j.processos.map(p => ({
    ...p,
    assuntos: typeof p.assuntos === "string" ? p.assuntos.split(" | ") : (p.assuntos || []),
  }));
  renderResultados();
  return true;
}

async function carregarJsonRaw() {
  for (const url of [`${REPO_RAW}/resultados.json?${Date.now()}`, `resultados.json?${Date.now()}`]) {
    try {
      const r = await fetch(url);
      if (!r.ok) continue;
      return await r.json();
    } catch { /* próxima */ }
  }
  return null;
}

function paramsActionHtml(filtro) {
  return `
    <table class="params-action">
      <tr><td>data_inicio</td><td><code>${filtro.data_inicio}</code></td></tr>
      <tr><td>data_fim</td><td><code>${filtro.data_fim}</code></td></tr>
      <tr><td>modo</td><td><code>${filtro.modo}</code></td></tr>
      <tr><td>tipo_data</td><td><code>${filtro.tipo}</code></td></tr>
      <tr><td>limite</td><td><code>${filtro.limite}</code></td></tr>
    </table>`;
}

async function atualizarViaGitHubAction(filtro) {
  const alerta = document.getElementById("alerta-periodo");
  const prog = document.getElementById("progresso");
  const progBar = document.getElementById("progresso-bar");
  const commitAntes = await ultimoCommitResultados();
  const runAntes = (await ultimaRunAction())?.id || 0;

  alerta.style.display = "block";
  alerta.className = "alert info";
  alerta.innerHTML = `
    <strong>No GitHub Pages a consulta roda no servidor do GitHub</strong> (não no navegador).<br><br>
    <strong>1.</strong> Abra a <a href="${ACTION_URL}" target="_blank" rel="noopener">Action Consulta STJ</a><br>
    <strong>2.</strong> Clique <strong>Run workflow</strong> e preencha:<br>
    ${paramsActionHtml(filtro)}
    <strong>3.</strong> Aguarde aqui — o site atualiza sozinho quando terminar (~1–2 min)<br><br>
    <em>Quer consulta instantânea com um clique?</em>
    <a href="${VERCEL_DEPLOY}" target="_blank" rel="noopener">Deploy grátis na Vercel</a> (2 min, uma vez só).`;

  prog.classList.remove("hidden");
  progBar.style.width = "5%";
  const limite = Date.now() + 12 * 60 * 1000;
  let ultimoStatus = "";

  while (Date.now() < limite) {
    await sleep(5000);
    const pct = Math.min(92, ((Date.now() - (limite - 12 * 60 * 1000)) / (12 * 60 * 1000)) * 100);
    progBar.style.width = `${pct}%`;

    const run = await ultimaRunAction();
    if (run && run.id !== runAntes) {
      if (run.status === "in_progress" || run.status === "queued") {
        ultimoStatus = "⏳ Consulta em andamento no GitHub...";
        alerta.className = "alert info";
        alerta.innerHTML = ultimoStatus + `<br><a href="${run.html_url}" target="_blank" rel="noopener">Ver progresso</a>`;
      } else if (run.conclusion === "failure") {
        alerta.className = "alert err";
        alerta.innerHTML = `❌ A consulta falhou no GitHub.
          <a href="${run.html_url}" target="_blank" rel="noopener">Ver o erro</a>.
          Tente período de 30 dias ou menos e limite até 50.
          ${processos.length ? `<br><em>Exibindo ${processos.length} processos do cache anterior.</em>` : ""}`;
        prog.classList.add("hidden");
        return;
      }
    }

    const commitNovo = await ultimoCommitResultados();
    if (commitNovo && commitNovo !== commitAntes) {
      const j = await carregarJsonRaw();
      if (aplicarJsonResultados(j)) {
        progBar.style.width = "100%";
        alerta.className = "alert ok";
        alerta.innerHTML = `✅ <strong>${processos.length} processos</strong> atualizados via GitHub Actions!`;
        setTimeout(() => prog.classList.add("hidden"), 1200);
        return;
      }
    }
  }

  alerta.className = "alert err";
  alerta.innerHTML = `Tempo esgotado. Confira a <a href="${ACTION_URL}" target="_blank" rel="noopener">Action</a>
    e recarregue a página (Cmd+Shift+R). Para consulta instantânea:
    <a href="${VERCEL_DEPLOY}" target="_blank" rel="noopener">deploy na Vercel</a>.`;
  prog.classList.add("hidden");
}

function montarQuery(ini, fim, tipoData, modo) {
  const must = [
    { wildcard: { numeroProcesso: "?????????????816????" } },
  ];
  if (modo === "ambos") {
    must.push({ term: { "movimentos.codigo": TRANSITO } });
    must.push({ term: { "movimentos.codigo": BAIXA } });
  } else if (modo === "transito") {
    must.push({ term: { "movimentos.codigo": TRANSITO } });
  } else if (modo === "baixa") {
    must.push({ term: { "movimentos.codigo": BAIXA } });
  } else {
    must.push({ terms: { "movimentos.codigo": [TRANSITO, BAIXA] } });
  }
  if (ini && fim) {
    const iso = (d, fimDia) => `${d}T${fimDia ? "23:59:59" : "00:00:00"}`;
    const aj = (d, fimDia) => d.replace(/-/g, "") + (fimDia ? "235959" : "000000");
    if (tipoData === "ajuizamento") {
      must.push({ range: { dataAjuizamento: { gte: aj(ini), lte: aj(fim, true) } } });
    } else if (tipoData === "atualizacao") {
      must.push({ range: { dataHoraUltimaAtualizacao: { gte: iso(ini), lte: iso(fim, true) } } });
    } else {
      must.push({ range: { "movimentos.dataHora": { gte: iso(ini), lte: iso(fim, true) } } });
    }
  }
  return must;
}

async function buscarPeriodo(filtro, modo, limite, onProg) {
  const resultados = [];
  const ini = filtro.data_inicio;
  const fim = filtro.data_fim;
  let offset = 0;
  const page = 500;

  while (resultados.length < limite) {
    const tam = Math.min(page, Math.max(limite - resultados.length, 100));
    if (onProg) onProg(`Buscando... ${resultados.length} encontrados`, resultados.length / limite);
    const body = {
      size: tam,
      from: offset,
      query: { bool: { must: montarQuery(ini, fim, filtro.tipo, modo) } },
      _source: ["numeroProcesso", "classe", "assuntos", "dataAjuizamento", "dataHoraUltimaAtualizacao", "movimentos"],
    };
    const dados = await apiBuscar(body);
    const hits = dados.hits?.hits || [];
    if (!hits.length) break;
    for (const h of hits) {
      const p = processarHit(h._source || {}, modo, filtro);
      if (p) resultados.push(p);
      if (resultados.length >= limite) break;
    }
    if (onProg && resultados.length) {
      onProg(`Buscando... ${resultados.length} encontrados`, resultados.length / limite, resultados.slice());
    }
    offset += tam;
    const total = dados.hits?.total?.value || 0;
    if (offset >= total || offset >= 10000) break;
  }
  return resultados;
}

async function buscarNumeros(numeros, modo) {
  const resultados = [];
  const limpos = numeros
    .map(raw => raw.replace(/[-.]/g, "").trim())
    .filter(Boolean);
  const concorrencia = 4;

  for (let i = 0; i < limpos.length; i += concorrencia) {
    const lote = limpos.slice(i, i + concorrencia);
    const loteResultados = await Promise.all(lote.map(async numero => {
      const dados = await apiBuscar({
        size: 1,
        query: { term: { numeroProcesso: numero } },
        _source: ["numeroProcesso", "classe", "assuntos", "dataAjuizamento", "dataHoraUltimaAtualizacao", "movimentos"],
      });
      const hits = dados.hits?.hits || [];
      if (!hits.length) return null;
      return processarHit(hits[0]._source || {}, modo);
    }));
    loteResultados.forEach(p => { if (p) resultados.push(p); });
  }
  return resultados;
}

function getFiltros() {
  const modo = document.getElementById("modo").value;
  const tipo = document.getElementById("tipo-data").value;
  const limite = +document.getElementById("limite").value;
  const atalho = document.querySelector('input[name="atalho"]:checked')?.value || "ano_atual";
  let ini, fim;
  const hoje = new Date();
  if (atalho === "personalizado") {
    ini = document.getElementById("data-ini").value;
    fim = document.getElementById("data-fim").value;
  } else if (atalho === "mes_atual") {
    ini = `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}-01`;
    fim = hoje.toISOString().slice(0, 10);
  } else if (atalho === "ultimos_30") {
    const d = new Date(hoje); d.setDate(d.getDate() - 30);
    ini = d.toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  } else if (atalho === "ultimos_90") {
    const d = new Date(hoje); d.setDate(d.getDate() - 90);
    ini = d.toISOString().slice(0, 10);
    fim = hoje.toISOString().slice(0, 10);
  } else {
    ini = `${hoje.getFullYear()}-01-01`;
    fim = hoje.toISOString().slice(0, 10);
  }
  return { modo, tipo, limite, data_inicio: ini, data_fim: fim };
}

function atualizarSidebar() {
  const modo = document.getElementById("modo").value;
  const tipo = document.getElementById("tipo-data").value;
  document.getElementById("hint-modo").textContent = MODO_LABELS[modo];
  document.getElementById("hint-tipo").textContent = TIPO_LABELS[tipo];
  document.getElementById("limite-val").textContent = document.getElementById("limite").value;

  const atalho = document.querySelector('input[name="atalho"]:checked')?.value;
  const custom = document.getElementById("datas-custom");
  const periodo = document.getElementById("sidebar-periodo");
  custom.classList.toggle("hidden", atalho !== "personalizado");
  periodo.classList.toggle("hidden", atalho === "personalizado");

  if (atalho !== "personalizado") {
    const f = getFiltros();
    periodo.textContent = `📅 ${f.data_inicio.split("-").reverse().join("/")} → ${f.data_fim.split("-").reverse().join("/")}`;
  }
  atualizarInfoFiltro();
}

function atualizarInfoFiltro() {
  const f = getFiltros();
  const el = document.getElementById("info-filtro");
  if (el) {
    const di = f.data_inicio.split("-").reverse().join("/");
    const df = f.data_fim.split("-").reverse().join("/");
    el.innerHTML = `Filtro atual: <strong>${TIPO_LABELS[f.tipo]}</strong> de <strong>${di}</strong> a <strong>${df}</strong> — critério: <strong>${MODO_LABELS[f.modo]}</strong>`;
  }
}

function filtrarLista(lista) {
  const t = document.getElementById("filtro-texto")?.value?.toLowerCase() || "";
  const status = document.getElementById("filtro-status")?.value || "";
  return lista.filter(p => {
    const numero = String(p.numero_formatado || "").toLowerCase();
    const classe = String(p.classe || "").toLowerCase();
    const assuntos = (Array.isArray(p.assuntos) ? p.assuntos.join(" | ") : String(p.assuntos || "")).toLowerCase();
    if (t && !numero.includes(t) && !classe.includes(t) && !assuntos.includes(t)) return false;
    const trans = p.tem_transito_julgado === "Sim";
    const baixa = p.tem_baixa_definitiva === "Sim";
    if (status === "Com trânsito" && !trans) return false;
    if (status === "Com baixa" && !baixa) return false;
    if (status === "Com ambos" && !(trans && baixa)) return false;
    if (status === "Sem trânsito" && trans) return false;
    if (status === "Sem baixa" && baixa) return false;
    return true;
  });
}

function ordenarLista(lista) {
  const ordem = document.getElementById("ordem-resultados")?.value || "transito_desc";
  return lista.slice().sort((a, b) => {
    if (ordem === "baixa_desc") return parseDataBr(b.data_baixa_definitiva) - parseDataBr(a.data_baixa_definitiva);
    if (ordem === "classe_asc") return (a.classe || "").localeCompare(b.classe || "", "pt-BR");
    if (ordem === "numero_asc") return (a.numero_formatado || "").localeCompare(b.numero_formatado || "");
    return parseDataBr(b.data_transito_julgado) - parseDataBr(a.data_transito_julgado);
  });
}

function atualizarHeroStats() {
  const el = document.getElementById("hero-stats");
  if (!el) return;
  if (!processos.length) {
    el.innerHTML = "<span>Consulta</span><strong>Aguardando busca</strong>";
    return;
  }
  const gerado = cacheInfo?.gerado_em ? `Atualizado em ${escapeHtml(cacheInfo.gerado_em)}` : "Dados carregados";
  el.innerHTML = `<span>${gerado}</span><strong>${processos.length} processos</strong>`;
}

function renderMetricas(lista) {
  const el = document.getElementById("metricas");
  const trans = lista.filter(p => p.tem_transito_julgado === "Sim").length;
  const baixa = lista.filter(p => p.tem_baixa_definitiva === "Sim").length;
  const ambos = lista.filter(p => p.tem_transito_julgado === "Sim" && p.tem_baixa_definitiva === "Sim").length;
  el.innerHTML = `
    <div class="metric"><div class="val">${lista.length}</div><div class="lbl">Total</div></div>
    <div class="metric"><div class="val">${trans}</div><div class="lbl">Com trânsito</div></div>
    <div class="metric"><div class="val">${baixa}</div><div class="lbl">Com baixa</div></div>
    <div class="metric"><div class="val">${ambos}</div><div class="lbl">Com ambos</div></div>`;
}

function renderGrafico(lista) {
  const el = document.getElementById("grafico-classes");
  const counts = {};
  lista.forEach(p => { counts[p.classe] = (counts[p.classe] || 0) + 1; });
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 10);
  if (!top.length) {
    el.innerHTML = '<div class="empty-state">Sem classes para os filtros atuais.</div>';
    return;
  }
  const max = top[0]?.[1] || 1;
  el.innerHTML = top.map(([c, n]) => `
    <div class="bar-row">
      <span title="${escapeHtml(c)}">${escapeHtml(c.length > 28 ? c.slice(0, 28) + "…" : c)}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(n / max) * 100}%"></div></div>
      <strong>${n}</strong>
    </div>`).join("");
}

function renderTabela(lista) {
  const wrap = document.getElementById("tabela-wrap");
  const det = document.getElementById("detalhe");
  if (!lista.length) {
    wrap.innerHTML = `<div class="empty-state">Nenhum processo encontrado com os filtros atuais.</div>`;
    det.innerHTML = "";
    return;
  }
  let html = `<table><thead><tr>
    <th>Número</th><th>Classe</th><th>Assuntos</th><th>Trânsito</th><th>Baixa</th>
  </tr></thead><tbody>`;
  lista.forEach((p, i) => {
    const pe = procParaExibicao(p);
    const transOk = pe.tem_transito_julgado === "Sim";
    const baixaOk = pe.tem_baixa_definitiva === "Sim";
    html += `<tr class="proc" data-i="${i}">
      <td class="num">${escapeHtml(pe.numero_formatado)}</td>
      <td>${escapeHtml(pe.classe || "—")}</td>
      <td class="assuntos-cell">${escapeHtml(pe.assuntos || "—")}</td>
      <td><span class="status-pill ${transOk ? "ok" : "no"}">${escapeHtml(pe.data_transito_julgado || "—")}</span></td>
      <td><span class="status-pill ${baixaOk ? "ok" : "no"}">${escapeHtml(pe.data_baixa_definitiva || "—")}</span></td>
    </tr>`;
  });
  html += "</tbody></table>";
  wrap.innerHTML = html;
  wrap.querySelectorAll("tr.proc").forEach(tr => {
    tr.addEventListener("click", () => {
      wrap.querySelectorAll("tr.proc").forEach(r => r.classList.remove("sel"));
      tr.classList.add("sel");
      selecionado = lista[+tr.dataset.i];
      renderDetalhe(selecionado);
    });
  });
}

function renderDetalhe(p) {
  const el = document.getElementById("detalhe");
  if (!p) { el.innerHTML = ""; return; }
  const assuntos = Array.isArray(p.assuntos) ? p.assuntos : (p.assuntos || "").split(" | ").filter(Boolean);
  const tl = (p.timeline || []).slice().reverse().map(m => {
    const dest = DESTAQUES.has(m.codigo) ? '<span class="destaque">Destaque</span>' : "";
    const highlight = DESTAQUES.has(m.codigo) ? " is-highlight" : "";
    const orgao = m.orgao ? `${escapeHtml(m.orgao)} · ` : "";
    return `<div class="timeline-item${highlight}"><strong>${escapeHtml(m.nome)}</strong>${dest}
      <div class="tl-meta">${orgao}${escapeHtml(m.data || m.data_hora || "")}</div></div>`;
  }).join("");
  el.innerHTML = `
    <h4>Detalhes e histórico de movimentos</h4>
    <div class="card"><div class="card-grid">
      <div>
        <div class="proc-label">Número do processo</div>
        <div class="processo-numero">${escapeHtml(p.numero_formatado)}</div>
        <div class="proc-label">Classe</div><div>${escapeHtml(p.classe || "—")}</div>
        <div class="proc-label">Ajuizamento</div><div>${escapeHtml(p.data_ajuizamento || "—")}</div>
        <div class="proc-label">Assuntos</div><div>${assuntos.map(a => `• ${escapeHtml(a)}`).join("<br>") || "—"}</div>
      </div>
      <div>
        <div class="status ${p.tem_transito_julgado === "Sim" ? "ok" : "no"}">Trânsito em julgado — ${escapeHtml(p.data_transito_julgado || "—")}</div>
        <div class="status ${p.tem_baixa_definitiva === "Sim" ? "ok" : "no"}">Baixa definitiva — ${escapeHtml(p.data_baixa_definitiva || "—")}</div>
      </div>
    </div>
    ${tl ? `<div class="timeline"><div class="proc-label">Histórico de movimentos</div>${tl}</div>` : ""}
    </div>`;
}

function renderResultados() {
  const filtrados = ordenarLista(filtrarLista(processos));
  document.getElementById("area-resultados").classList.toggle("hidden", !processos.length);
  document.getElementById("caption-tabela").textContent = `Exibindo ${filtrados.length} de ${processos.length} processos`;
  renderMetricas(filtrados);
  renderGrafico(filtrados);
  renderTabela(filtrados);
  atualizarHeroStats();
}

async function carregarCache() {
  const j = await carregarJsonRaw();
  if (j && aplicarJsonResultados(j)) return true;
  return false;
}

function mostrarAvisoGitHubPages() {
  if (!isGitHubPages()) return;
  const alerta = document.getElementById("alerta-periodo");
  const btnVercel = document.getElementById("btn-vercel");
  if (btnVercel) btnVercel.classList.remove("hidden");
  if (!alerta) return;
  alerta.style.display = "block";
  alerta.className = "alert info";
  alerta.innerHTML = `
    Você está no <strong>GitHub Pages</strong> (visualização). A consulta ao vivo não roda no navegador aqui.<br>
    · <strong>Atualizar dados:</strong> use o botão abaixo (roda no GitHub, ~1–2 min)<br>
    · <strong>Consulta instantânea:</strong> <a href="${VERCEL_DEPLOY}" target="_blank" rel="noopener">deploy grátis na Vercel</a> ou <code>./iniciar-site.sh</code> no computador`;
  const btn = document.getElementById("btn-consultar");
  if (btn) btn.textContent = "Atualizar dados (GitHub Actions)";
}

async function consultarPeriodo() {
  const btn = document.getElementById("btn-consultar");
  const prog = document.getElementById("progresso");
  const progBar = document.getElementById("progresso-bar");
  const alerta = document.getElementById("alerta-periodo");
  const f = getFiltros();
  if (f.data_inicio > f.data_fim) {
    alerta.style.display = "block";
    alerta.className = "alert err";
    alerta.textContent = "⛔ A data inicial não pode ser maior que a data final.";
    return;
  }

  if (isGitHubPages()) {
    btn.disabled = true;
    try {
      await atualizarViaGitHubAction(f);
    } finally {
      btn.disabled = false;
    }
    return;
  }

  btn.disabled = true;
  alerta.classList.remove("hidden");
  alerta.style.display = "block";
  alerta.className = "alert info";
  alerta.textContent = "⏳ Consultando API Datajud...";
  prog.classList.remove("hidden");
  let viaGitHub = false;
  let ultimoRenderParcial = 0;
  try {
    processos = await buscarPeriodo(
      { data_inicio: f.data_inicio, data_fim: f.data_fim, tipo: f.tipo },
      f.modo,
      f.limite,
      (msg, pct, parcial) => {
        alerta.textContent = `⏳ ${msg}`;
        progBar.style.width = `${Math.min(pct * 100, 97)}%`;
        if (parcial?.length && Date.now() - ultimoRenderParcial > 600) {
          ultimoRenderParcial = Date.now();
          processos = parcial;
          renderResultados();
        }
      }
    );
    progBar.style.width = "100%";
    alerta.className = "alert ok";
    const di = f.data_inicio.split("-").reverse().join("/");
    const df = f.data_fim.split("-").reverse().join("/");
    alerta.innerHTML = `✅ <strong>${processos.length} processos</strong> encontrados — ${di} a ${df} (${TIPO_LABELS[f.tipo]})`;
    cacheInfo = { gerado_em: new Date().toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" }) };
    renderResultados();
  } catch (e) {
    if (e.cors || String(e.message).toLowerCase().includes("fetch")) {
      viaGitHub = true;
      await atualizarViaGitHubAction(f);
      return;
    }
    alerta.style.display = "block";
    alerta.className = "alert err";
    alerta.textContent = `❌ Erro: ${e.message}`;
  } finally {
    btn.disabled = false;
    if (!viaGitHub) setTimeout(() => prog.classList.add("hidden"), 800);
  }
}

async function consultarNumeros() {
  const alerta = document.getElementById("alerta-numero");
  const area = document.getElementById("resultados-numero");
  const nums = document.getElementById("numeros-input").value.split("\n").filter(Boolean);
  const modo = document.getElementById("modo").value;
  if (!nums.length) {
    alerta.style.display = "block";
    alerta.className = "alert err";
    alerta.textContent = "Informe ao menos um número.";
    return;
  }
  alerta.classList.remove("hidden");
  alerta.style.display = "block";
  alerta.className = "alert info";
  alerta.textContent = `⏳ Consultando ${nums.length} processo(s)...`;
  try {
    const res = await buscarNumeros(nums, modo);
    alerta.className = "alert ok";
    alerta.textContent = `✅ ${res.length} processo(s) encontrado(s).`;
    area.innerHTML = res.map((p, i) => `<div class="numero-result-card">
        <div class="numero-result-head">
          <div>
            <div class="processo-numero">${escapeHtml(p.numero_formatado)}</div>
            <div>${escapeHtml(p.classe || "—")}</div>
          </div>
          <button class="btn-secondary" data-idx="${i}" type="button">Detalhes</button>
        </div>
        <div class="status ${p.tem_transito_julgado === "Sim" ? "ok" : "no"}">Trânsito: ${escapeHtml(p.data_transito_julgado || "—")}</div>
        <div class="status ${p.tem_baixa_definitiva === "Sim" ? "ok" : "no"}">Baixa: ${escapeHtml(p.data_baixa_definitiva || "—")}</div>
      </div>`).join("");
    area.querySelectorAll("button[data-idx]").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelector('.tab[data-tab="periodo"]').click();
        processos = res;
        renderResultados();
        renderDetalhe(res[+btn.dataset.idx]);
      });
    });
  } catch (e) {
    if (e.cors || String(e.message).toLowerCase().includes("fetch")) {
      alerta.style.display = "block";
      alerta.className = "alert err";
      alerta.innerHTML = `❌ Busca por número bloqueada pelo navegador (CORS).<br>
        Use a aba <strong>Busca por período</strong> com GitHub Actions, ou rode localmente: <code>./iniciar.sh</code>`;
      return;
    }
    alerta.className = "alert err";
    alerta.textContent = `❌ Erro: ${e.message}`;
  }
}

function initTabs() {
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById("panel-" + tab.dataset.tab).classList.add("active");
    });
  });
}

function init() {
  const hoje = new Date().toISOString().slice(0, 10);
  document.getElementById("data-ini").value = `${new Date().getFullYear()}-01-01`;
  document.getElementById("data-fim").value = hoje;

  ["modo", "tipo-data", "limite", "data-ini", "data-fim"].forEach(id => {
    document.getElementById(id)?.addEventListener("change", atualizarSidebar);
    document.getElementById(id)?.addEventListener("input", atualizarSidebar);
  });
  document.querySelectorAll('input[name="atalho"]').forEach(r => r.addEventListener("change", atualizarSidebar));
  document.getElementById("btn-consultar").addEventListener("click", consultarPeriodo);
  document.getElementById("btn-numero").addEventListener("click", consultarNumeros);
  document.getElementById("filtro-texto")?.addEventListener("input", renderResultados);
  document.getElementById("filtro-status")?.addEventListener("change", renderResultados);
  document.getElementById("ordem-resultados")?.addEventListener("change", renderResultados);
  document.getElementById("btn-limpar-filtros")?.addEventListener("click", () => {
    document.getElementById("filtro-texto").value = "";
    document.getElementById("filtro-status").value = "";
    document.getElementById("ordem-resultados").value = "transito_desc";
    renderResultados();
  });

  initTabs();
  atualizarSidebar();
  carregarCache().finally(() => {
    atualizarHeroStats();
    if (isGitHubPages()) mostrarAvisoGitHubPages();
  });
}

document.addEventListener("DOMContentLoaded", init);
