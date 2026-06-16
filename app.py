#!/usr/bin/env python3
"""Interface web para consulta de processos STJ com origem no Paraná."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

from consulta_stj_parana import (
    FiltroDatas,
    buscar_por_numero,
    buscar_processos,
    processos_para_csv,
    processos_para_excel,
)

DESTAQUES_MOV = {848, 22}


def renderizar_detalhe_processo(proc) -> None:
    """Exibe cartão de detalhes e timeline de um processo."""
    with st.container(border=True):
        col_info, col_status = st.columns([1.2, 1], gap="large")

        with col_info:
            st.caption("Número do processo")
            st.markdown(
                f'<p class="processo-numero-inline">{proc.numero_formatado}</p>',
                unsafe_allow_html=True,
            )
            st.caption("Classe")
            st.write(proc.classe or "—")
            st.caption("Ajuizamento")
            st.write(proc.data_ajuizamento or "—")
            st.caption("Assuntos")
            if proc.assuntos:
                for assunto in proc.assuntos:
                    st.write(f"• {assunto}")
            else:
                st.write("—")

        with col_status:
            if proc.tem_transito_julgado:
                st.success(f"Trânsito em julgado — {proc.data_transito_julgado}")
            else:
                st.error("Sem trânsito em julgado")
            if proc.tem_baixa_definitiva:
                st.success(f"Baixa definitiva — {proc.data_baixa_definitiva}")
            else:
                st.error("Sem baixa definitiva")

    if proc.timeline:
        st.markdown("##### Histórico de movimentos")
        movimentos = list(reversed(proc.timeline))
        for idx, m in enumerate(movimentos):
            destaque = m.codigo in DESTAQUES_MOV
            icone = "🟢" if destaque else "🔵"
            titulo = f"{icone} **{m.nome}**"
            if destaque:
                titulo += ' <span class="mov-badge-inline">Destaque</span>'
            st.markdown(titulo, unsafe_allow_html=True)
            meta = m.data_formatada()
            if m.orgao:
                meta = f"{m.orgao} · {meta}"
            st.caption(meta)
            if idx < len(movimentos) - 1:
                st.divider()

# ─── Configuração da página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="STJ Paraná — Consulta Processual",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constantes ───────────────────────────────────────────────────────────────
MODO_OPCOES = {
    "ambos":     "Trânsito em julgado E baixa definitiva",
    "transito":  "Somente trânsito em julgado",
    "baixa":     "Somente baixa definitiva",
    "qualquer":  "Trânsito em julgado OU baixa definitiva",
}
MODO_OPCOES_CURTO = {
    "ambos":    "Trânsito + Baixa",
    "transito": "Só trânsito",
    "baixa":    "Só baixa",
    "qualquer": "Trânsito ou Baixa",
}
TIPO_DATA_OPCOES = {
    "movimentacao": "Data da movimentação (trânsito / baixa)",
    "ajuizamento":  "Data de ajuizamento do processo",
    "atualizacao":  "Data da última atualização",
}
TIPO_DATA_CURTO = {
    "movimentacao": "Movimentação",
    "ajuizamento":  "Ajuizamento",
    "atualizacao":  "Última atualização",
}
LINK_STJ = "https://processo.stj.jus.br/processo/pesquisa/?num_registro={numero}"

hoje = date.today()

MESES_PT = [
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]
ANOS_DISPONIVEIS = list(range(2008, hoje.year + 1))


def seletor_data_pt(rotulo: str, padrao: date, chave: str) -> date:
    """Seletor de data em português: dia, mês e ano em uma linha."""
    import calendar

    st.markdown(f"**{rotulo}**")
    c_dia, c_mes, c_ano = st.columns([1, 2, 1])
    with c_dia:
        dia = st.selectbox(
            "Dia", list(range(1, 32)),
            index=padrao.day - 1,
            key=f"{chave}_dia",
            label_visibility="collapsed",
        )
    with c_mes:
        mes_idx = st.selectbox(
            "Mês", list(range(12)),
            index=padrao.month - 1,
            format_func=lambda i: MESES_PT[i],
            key=f"{chave}_mes",
            label_visibility="collapsed",
        )
    with c_ano:
        idx_ano = ANOS_DISPONIVEIS.index(padrao.year) if padrao.year in ANOS_DISPONIVEIS else len(ANOS_DISPONIVEIS) - 1
        ano = st.selectbox(
            "Ano", ANOS_DISPONIVEIS,
            index=idx_ano,
            key=f"{chave}_ano",
            label_visibility="collapsed",
        )

    ultimo_dia = calendar.monthrange(ano, mes_idx + 1)[1]
    return date(ano, mes_idx + 1, min(dia, ultimo_dia))


def aplicar_atalho_periodo(atalho: str) -> tuple[date, date]:
    if atalho == "mes_atual":
        return date(hoje.year, hoje.month, 1), hoje
    if atalho == "ano_atual":
        return date(hoje.year, 1, 1), hoje
    if atalho == "ultimos_90":
        return hoje - timedelta(days=90), hoje
    if atalho == "ultimos_30":
        return hoje - timedelta(days=30), hoje
    return date(hoje.year, 1, 1), hoje

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Força tema claro em toda a aplicação */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: #f1f5f9 !important;
    color: #0f172a !important;
}

.main .block-container {
    padding-top: 1.5rem;
    max-width: 1100px;
}

/* ── Textos da área principal ── */
.main h1, .main h2, .main h3, .main h4, .main h5, .main h6,
.main p, .main li, .main span, .main label,
.main .stMarkdown, .main .stMarkdown p,
.main .stMarkdown li, .main .stMarkdown h1,
.main .stMarkdown h2, .main .stMarkdown h3,
.main .stMarkdown h4, .main .stMarkdown strong,
.main [data-testid="stMarkdownContainer"] p,
.main [data-testid="stMarkdownContainer"] li,
.main [data-testid="stMarkdownContainer"] h1,
.main [data-testid="stMarkdownContainer"] h2,
.main [data-testid="stMarkdownContainer"] h3,
.main [data-testid="stMarkdownContainer"] h4,
.main [data-testid="stCaptionContainer"] {
    color: #0f172a !important;
}

.main .stMarkdown code,
.main [data-testid="stMarkdownContainer"] code {
    background: #e2e8f0 !important;
    color: #0f4c81 !important;
    padding: 1px 6px;
    border-radius: 4px;
    font-size: .88em;
}

/* ── Abas ── */
.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #e2e8f0;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b !important;
    font-weight: 500 !important;
    border-radius: 7px !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: #eff6ff !important;
    color: #1565a8 !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: transparent !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── Inputs na área principal ── */
.main .stTextInput input,
.main .stTextArea textarea {
    background: #ffffff !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
.main [data-baseweb="select"] {
    background-color: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
.main [data-baseweb="select"] > div {
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
}
.main .stTextArea textarea {
    font-family: 'Courier New', monospace !important;
    font-size: .9rem !important;
    line-height: 1.6 !important;
}
.main label, .main .stTextInput label, .main .stTextArea label,
.main .stSelectbox label, .main .stMultiSelect label {
    color: #334155 !important;
    font-weight: 500 !important;
    font-size: .88rem !important;
}

/* ── Alertas ── */
.main [data-testid="stAlert"] {
    border-radius: 8px !important;
}
.main [data-testid="stAlert"] p,
.main [data-testid="stAlert"] div {
    color: inherit !important;
}

/* ── Hero ── */
.hero {
    background: linear-gradient(135deg, #0c2d4a 0%, #1565a8 100%);
    color: #ffffff;
    padding: 1.6rem 2rem;
    border-radius: 14px;
    margin-bottom: 1.4rem;
    box-shadow: 0 4px 20px rgba(12,45,74,.2);
}
.hero h1 { margin: 0 0 .3rem 0; font-size: 1.75rem; font-weight: 700; color: #ffffff !important; }
.hero p  { margin: 0; color: rgba(255,255,255,.92) !important; font-size: .95rem; }

/* ── Métricas ── */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: .8rem 1rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
div[data-testid="metric-container"] label {
    color: #475569 !important;
    font-size: .82rem !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* ── Sidebar clara — texto escuro, alta legibilidade ── */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid #e2e8f0 !important;
    min-width: 300px !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 1.2rem;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #0f2744 !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stCaption,
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #475569 !important;
    font-size: .88rem !important;
    line-height: 1.5 !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stSlider label {
    color: #334155 !important;
    font-size: .9rem !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stRadio label p {
    color: #1e293b !important;
    font-weight: 500 !important;
    font-size: .9rem !important;
}
/* Selectbox na sidebar — sem alterar divs internos */
section[data-testid="stSidebar"] [data-baseweb="select"] {
    background-color: #f8fafc !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 8px !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] span {
    color: #0f172a !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #e2e8f0 !important;
    margin: .8rem 0 !important;
}
section[data-testid="stSidebar"] .lbl-data {
    margin: 0 0 4px 0;
    font-size: .85rem;
    color: #475569;
    font-weight: 600;
}
section[data-testid="stSidebar"] .sidebar-hint {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 8px;
    padding: .55rem .75rem;
    font-size: .82rem;
    color: #1e40af;
    line-height: 1.45;
    margin: .3rem 0 .6rem 0;
}
section[data-testid="stSidebar"] .sidebar-periodo {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 8px;
    padding: .6rem .85rem;
    font-size: .92rem;
    font-weight: 600;
    color: #14532d;
    text-align: center;
    margin: .4rem 0;
}
section[data-testid="stSidebar"] .sidebar-footer {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: .7rem .85rem;
    font-size: .82rem;
    color: #475569;
    line-height: 1.55;
}
section[data-testid="stSidebar"] .sidebar-footer strong {
    color: #0f2744;
}
section[data-testid="stSidebar"] .sidebar-footer code {
    background: #dbeafe;
    color: #1d4ed8;
    padding: 1px 5px;
    border-radius: 4px;
    font-size: .8rem;
}

/* ── Botões ── */
.stButton > button[kind="primary"] {
    background: #1565a8 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    color: #0f172a !important;
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
}

/* ── Tabela ── */
.main [data-testid="stDataFrame"] {
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    overflow: hidden;
}

/* ── Expander ── */
.main details summary {
    font-weight: 500;
    color: #0f172a !important;
}

/* ── Timeline e detalhe do processo ── */
.processo-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin: .75rem 0 1rem;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.processo-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
}
@media (max-width: 700px) {
    .processo-grid { grid-template-columns: 1fr; }
}
.proc-label {
    font-size: .75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-top: .75rem;
}
.proc-label:first-child { margin-top: 0; }
.processo-numero,
.processo-numero-inline {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f2744 !important;
    font-family: 'Courier New', Courier, monospace;
    margin: 0;
    white-space: nowrap;
    overflow-x: auto;
    letter-spacing: 0.02em;
}
.mov-badge-inline {
    background: #dcfce7;
    color: #166534;
    font-size: .68rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
    text-transform: uppercase;
    vertical-align: middle;
    margin-left: .35rem;
}
.proc-valor {
    font-size: .92rem;
    color: #1e293b;
    margin-top: 2px;
    line-height: 1.4;
}
.proc-assuntos {
    margin: 4px 0 0 1.1rem;
    padding: 0;
    font-size: .9rem;
    color: #334155;
}
.status-ok {
    background: #f0fdf4;
    border-left: 4px solid #16a34a;
    padding: .65rem .9rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: .5rem;
    font-size: .88rem;
    color: #14532d;
    font-weight: 500;
}
.status-no {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    padding: .65rem .9rem;
    border-radius: 0 8px 8px 0;
    margin-bottom: .5rem;
    font-size: .88rem;
    color: #991b1b;
    font-weight: 500;
}
.link-stj {
    display: inline-block;
    margin-top: .6rem;
    padding: .45rem .9rem;
    background: #1565a8;
    color: #ffffff !important;
    border-radius: 7px;
    font-size: .85rem;
    font-weight: 600;
    text-decoration: none;
}
.link-stj:hover { background: #125189; }
.timeline-titulo {
    font-size: .95rem;
    font-weight: 700;
    color: #0f2744;
    margin: 1rem 0 .6rem;
}
.timeline-wrap {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: .75rem 1rem;
}
.timeline-linha {
    display: flex;
    gap: .85rem;
    align-items: flex-start;
    padding: .55rem 0;
    border-bottom: 1px solid #e8edf2;
}
.timeline-linha:last-child { border-bottom: none; }
.timeline-dot-verde {
    width: 11px; height: 11px; border-radius: 50%;
    background: #16a34a; margin-top: 5px; flex-shrink: 0;
    box-shadow: 0 0 0 3px #dcfce7;
}
.timeline-dot-azul {
    width: 9px; height: 9px; border-radius: 50%;
    background: #2563eb; margin-top: 6px; flex-shrink: 0;
}
.timeline-conteudo { flex: 1; min-width: 0; }
.timeline-topo {
    display: flex;
    align-items: center;
    gap: .5rem;
    flex-wrap: wrap;
}
.timeline-topo strong {
    font-size: .9rem;
    color: #0f172a;
}
.mov-badge-destaque {
    background: #dcfce7;
    color: #166534;
    font-size: .7rem;
    font-weight: 700;
    padding: 1px 7px;
    border-radius: 999px;
    text-transform: uppercase;
}
.timeline-orgao {
    font-size: .78rem;
    color: #64748b;
    margin-top: 2px;
}
.timeline-data {
    font-size: .78rem;
    color: #94a3b8;
    margin-top: 2px;
}

/* legado — manter compatibilidade */
.timeline-item {
    display: flex; gap: .8rem; align-items: flex-start;
    padding: .5rem 0; border-bottom: 1px solid #e2e8f0;
}
.timeline-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: #1565a8; margin-top: 5px; flex-shrink: 0;
}
.timeline-dot.destaque { background: #16a34a; width: 12px; height: 12px; }
.timeline-text { font-size: .85rem; line-height: 1.5; color: #1e293b !important; }
.timeline-text strong { color: #0f172a !important; font-weight: 600; }
.timeline-orgao { font-size: .76rem; color: #64748b !important; margin-top: 1px; }
.timeline-data { font-size: .76rem; color: #64748b !important; margin-top: 2px; }

/* ── Card de ajuda ── */
.help-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem 1.75rem;
    color: #0f172a;
    line-height: 1.7;
}
.help-card h2 { color: #0f2744 !important; margin-top: 0; }
.help-card h3 { color: #1565a8 !important; margin-top: 1.4rem; }
.help-card p, .help-card li { color: #334155 !important; }
.help-card code { background: #e2e8f0; color: #0f4c81; padding: 1px 6px; border-radius: 4px; }
.help-card table { width: 100%; border-collapse: collapse; margin: .5rem 0; }
.help-card th { background: #f1f5f9; color: #0f2744; padding: 8px 12px; text-align: left; border: 1px solid #e2e8f0; }
.help-card td { padding: 8px 12px; border: 1px solid #e2e8f0; color: #334155; }
</style>
""", unsafe_allow_html=True)

# ─── Cabeçalho ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚖️ STJ Paraná — Consulta Processual</h1>
  <p>Monitore processos do STJ com origem no TJPR que possuem certidão de trânsito em julgado
     ou decisão de baixa dos autos à origem — via API pública do Datajud/CNJ.</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Filtros")

    modo = st.selectbox(
        "Tipo de movimentação",
        options=list(MODO_OPCOES.keys()),
        format_func=lambda k: MODO_OPCOES_CURTO[k],
        index=0,
    )
    st.markdown(f"<div class='sidebar-hint'>{MODO_OPCOES[modo]}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📅 Período")

    tipo_data = st.selectbox(
        "Filtrar por",
        options=list(TIPO_DATA_OPCOES.keys()),
        format_func=lambda k: TIPO_DATA_CURTO[k],
        index=0,
    )
    st.markdown(f"<div class='sidebar-hint'>{TIPO_DATA_OPCOES[tipo_data]}</div>", unsafe_allow_html=True)

    st.markdown("<p style='font-size:.85rem;font-weight:600;color:#334155;margin:.5rem 0 .2rem;'>Atalhos de período</p>", unsafe_allow_html=True)
    atalho = st.radio(
        "Atalho",
        options=["ano_atual", "mes_atual", "ultimos_30", "ultimos_90", "personalizado"],
        format_func=lambda k: {
            "personalizado": "Personalizado",
            "mes_atual": "Mês atual",
            "ano_atual": "Ano atual",
            "ultimos_30": "Últimos 30 dias",
            "ultimos_90": "Últimos 90 dias",
        }[k],
        index=0,
        label_visibility="collapsed",
    )

    if atalho == "personalizado":
        data_inicio = seletor_data_pt("Data inicial", date(hoje.year, 1, 1), "ini")
        data_fim = seletor_data_pt("Data final", hoje, "fim")
    else:
        data_inicio, data_fim = aplicar_atalho_periodo(atalho)
        st.markdown(
            f"<div class='sidebar-periodo'>📅 {data_inicio.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    limite = st.slider("Limite de resultados", min_value=10, max_value=2000, value=200, step=10)

    st.markdown("---")
    st.markdown(
        "<div class='sidebar-footer'>"
        "🔍 Apenas processos do <strong>Paraná</strong> "
        "(código <code>8.16</code> no número CNJ)<br>"
        "Fonte: <strong>API pública Datajud / CNJ</strong>"
        "</div>",
        unsafe_allow_html=True,
    )

# ─── Abas principais ──────────────────────────────────────────────────────────
aba_periodo, aba_numero, aba_ajuda = st.tabs([
    "🔎 Busca por período",
    "🔢 Busca por número",
    "📖 Como usar",
])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1: BUSCA POR PERÍODO
# ══════════════════════════════════════════════════════════════════════════════
with aba_periodo:
    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        buscar = st.button("Consultar processos", type="primary", width="stretch")
    with col_msg:
        st.info(
            f"Filtro atual: **{TIPO_DATA_OPCOES[tipo_data]}** de "
            f"**{data_inicio.strftime('%d/%m/%Y')}** a **{data_fim.strftime('%d/%m/%Y')}** — "
            f"critério: **{MODO_OPCOES[modo]}**"
        )

    if buscar:
        if data_inicio > data_fim:
            st.error("⛔ A data inicial não pode ser maior que a data final.")
            st.stop()

        filtro = FiltroDatas(data_inicio=data_inicio, data_fim=data_fim, tipo=tipo_data)
        total_anos = data_fim.year - data_inicio.year + 1

        status_box = st.empty()
        barra = st.progress(0.0)

        def cb_progresso(msg: str, pct: float) -> None:
            status_box.info(f"⏳ {msg}")
            barra.progress(min(pct, 0.97))

        try:
            processos = buscar_processos(
                modo=modo, limite=limite, filtro_datas=filtro, on_progress=cb_progresso
            )
        except Exception as exc:
            barra.empty()
            st.error(f"❌ Erro na consulta: {exc}")
            st.stop()

        barra.progress(1.0)
        status_box.empty()
        st.session_state["processos_periodo"] = processos
        st.session_state["filtro_periodo"] = filtro
        st.session_state.pop("sel_processos_tabela", None)

    processos = st.session_state.get("processos_periodo", [])
    filtro_salvo: FiltroDatas | None = st.session_state.get("filtro_periodo")

    if processos:
        # Cabeçalho dos resultados
        if filtro_salvo and filtro_salvo.ativo():
            st.success(
                f"✅ **{len(processos)} processos** encontrados — "
                f"{filtro_salvo.data_inicio.strftime('%d/%m/%Y')} a "
                f"{filtro_salvo.data_fim.strftime('%d/%m/%Y')} "
                f"({TIPO_DATA_OPCOES[filtro_salvo.tipo]})"
            )

        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", len(processos))
        m2.metric("Com trânsito em julgado", sum(1 for p in processos if p.tem_transito_julgado))
        m3.metric("Com baixa definitiva",    sum(1 for p in processos if p.tem_baixa_definitiva))
        m4.metric("Com ambos",               sum(1 for p in processos if p.tem_transito_julgado and p.tem_baixa_definitiva))

        # Gráfico por classe
        classes = {}
        for p in processos:
            classes[p.classe] = classes.get(p.classe, 0) + 1
        df_classes = pd.DataFrame(
            sorted(classes.items(), key=lambda x: x[1], reverse=True)[:10],
            columns=["Classe", "Qtd"]
        )
        with st.expander("📊 Distribuição por classe (top 10)", expanded=False):
            st.bar_chart(df_classes.set_index("Classe"), height=280)

        # Filtro na tabela
        st.markdown("#### Resultados")
        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            busca_texto = st.text_input("🔍 Filtrar na tabela", placeholder="Digite número, classe ou assunto...")
        with col_f2:
            status_filtro = st.multiselect(
                "Status",
                ["Com trânsito", "Com baixa", "Com ambos", "Sem trânsito", "Sem baixa"],
                default=[],
            )

        # Aplicar filtros na tabela
        proc_filtrados = processos[:]
        if busca_texto:
            t = busca_texto.lower()
            proc_filtrados = [
                p for p in proc_filtrados
                if t in p.numero_formatado.lower()
                or t in p.classe.lower()
                or any(t in a.lower() for a in p.assuntos)
            ]
        if "Com trânsito" in status_filtro:
            proc_filtrados = [p for p in proc_filtrados if p.tem_transito_julgado]
        if "Com baixa" in status_filtro:
            proc_filtrados = [p for p in proc_filtrados if p.tem_baixa_definitiva]
        if "Com ambos" in status_filtro:
            proc_filtrados = [p for p in proc_filtrados if p.tem_transito_julgado and p.tem_baixa_definitiva]
        if "Sem trânsito" in status_filtro:
            proc_filtrados = [p for p in proc_filtrados if not p.tem_transito_julgado]
        if "Sem baixa" in status_filtro:
            proc_filtrados = [p for p in proc_filtrados if not p.tem_baixa_definitiva]

        st.caption(
            f"Exibindo {len(proc_filtrados)} de {len(processos)} processos · "
            "clique em uma linha da tabela para ver os detalhes"
        )

        # Tabela
        linhas = []
        for p in proc_filtrados:
            linhas.append({
                "Número do processo":   p.numero_formatado,
                "Classe":               p.classe,
                "Assuntos":             " | ".join(p.assuntos[:2]) if p.assuntos else "—",
                "Ajuizamento":          p.data_ajuizamento,
                "Trânsito em julgado":  p.data_transito_julgado or "—",
                "Baixa definitiva":     p.data_baixa_definitiva or "—",
                "Última atualização":   p.data_ultima_atualizacao,
                "🔗 STJ":              LINK_STJ.format(numero=p.numero_processo),
            })
        df = pd.DataFrame(linhas)

        selecao = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=420,
            on_select="rerun",
            selection_mode="single-row",
            key="sel_processos_tabela",
            column_config={
                "🔗 STJ": st.column_config.LinkColumn("🔗 STJ", display_text="Abrir"),
                "Número do processo": st.column_config.TextColumn(width="medium"),
                "Classe":  st.column_config.TextColumn(width="large"),
                "Assuntos": st.column_config.TextColumn(width="large"),
            },
        )

        # Detalhes / timeline
        st.markdown("---")
        st.markdown("#### Detalhes e histórico de movimentos")
        linhas_sel = selecao.selection.rows if selecao.selection else []
        if linhas_sel:
            idx = linhas_sel[0]
            if 0 <= idx < len(proc_filtrados):
                renderizar_detalhe_processo(proc_filtrados[idx])
            else:
                st.info("Selecione um processo na tabela acima.")
        else:
            st.info("👆 Clique em um processo na tabela acima para ver o histórico de movimentos.")

        # Downloads
        st.markdown("---")
        nome_base = f"stj_parana_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.download_button(
                "⬇️ Baixar CSV",
                data=processos_para_csv(proc_filtrados),
                file_name=f"{nome_base}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with dc2:
            st.download_button(
                "📊 Baixar Excel",
                data=processos_para_excel(proc_filtrados),
                file_name=f"{nome_base}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with dc3:
            st.download_button(
                "📄 Baixar todos (CSV)",
                data=processos_para_csv(processos),
                file_name=f"{nome_base}_todos.csv",
                mime="text/csv",
                use_container_width=True,
            )
    elif buscar:
        st.warning("⚠️ Nenhum processo encontrado com os filtros selecionados.")

# ══════════════════════════════════════════════════════════════════════════════
# ABA 2: BUSCA POR NÚMERO
# ══════════════════════════════════════════════════════════════════════════════
with aba_numero:
    st.markdown("""
<div class="help-card" style="margin-bottom:1rem;">
  <h3 style="margin-top:0;color:#0f2744;">Busca por número de processo</h3>
  <p>Cole um ou mais números CNJ, <strong>um por linha</strong>. Aceita com ou sem formatação:</p>
  <p>
    <code>0040376-67.2020.8.16.0014</code> &nbsp;ou&nbsp;
    <code>00403766720208160014</code>
  </p>
</div>
""", unsafe_allow_html=True)

    numeros_input = st.text_area(
        "Números de processo",
        height=160,
        placeholder="0040376-67.2020.8.16.0014\n0000432-26.2022.8.16.0196\n...",
    )

    col_b, col_i = st.columns([1, 3])
    with col_b:
        buscar_num = st.button("Consultar números", type="primary", use_container_width=True, key="btn_num")
    with col_i:
        st.info("Busca individual em cada número. Não depende dos filtros de data da barra lateral.")

    if buscar_num:
        numeros_lista = [n.strip() for n in numeros_input.splitlines() if n.strip()]
        if not numeros_lista:
            st.warning("Informe ao menos um número de processo.")
        else:
            with st.spinner(f"Consultando {len(numeros_lista)} processo(s)..."):
                try:
                    resultados_num = buscar_por_numero(numeros_lista, modo=modo)
                except Exception as exc:
                    st.error(f"Erro: {exc}")
                    st.stop()

            st.session_state["processos_numero"] = resultados_num

    resultados_num = st.session_state.get("processos_numero", [])
    if resultados_num:
        st.success(f"✅ {len(resultados_num)} processo(s) encontrado(s).")
        for p in resultados_num:
            with st.expander(f"📂 {p.numero_formatado} — {p.classe}", expanded=True):
                renderizar_detalhe_processo(p)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3: AJUDA
# ══════════════════════════════════════════════════════════════════════════════
with aba_ajuda:
    st.markdown("""
<div class="help-card">
<h2>Como usar esta ferramenta</h2>

<h3>Aba "Busca por período"</h3>
<ol>
  <li>Na barra lateral, escolha o <strong>tipo de movimentação</strong> desejado.</li>
  <li>Defina o <strong>período</strong> (data inicial e final).</li>
  <li>Escolha <strong>por qual data</strong> filtrar: movimentação, ajuizamento ou última atualização.</li>
  <li>Ajuste o <strong>limite de resultados</strong> (padrão 200).</li>
  <li>Clique em <strong>Consultar processos</strong>.</li>
</ol>
<p><strong>Dica:</strong> para encontrar certidões de trânsito em julgado e baixas recentes,
use <em>Data da movimentação</em> com o período desejado (ex.: 01/01/2026 a hoje).</p>

<h3>Aba "Busca por número"</h3>
<ul>
  <li>Cole um ou mais números CNJ (um por linha) e clique em <strong>Consultar números</strong>.</li>
  <li>Funciona com ou sem formatação: <code>0040376-67.2020.8.16.0014</code></li>
  <li>Mostra a timeline completa de movimentos de cada processo.</li>
</ul>

<h3>Filtro na tabela de resultados</h3>
<ul>
  <li>Use o campo de texto para filtrar por número, classe ou assunto.</li>
  <li>Use o seletor de status para mostrar apenas processos com/sem trânsito ou baixa.</li>
</ul>

<h3>Downloads</h3>
<table>
  <tr><th>Botão</th><th>Conteúdo</th></tr>
  <tr><td>Baixar CSV</td><td>Resultados com filtros aplicados</td></tr>
  <tr><td>Baixar Excel</td><td>Mesmo conteúdo, formatado com cabeçalho colorido</td></tr>
  <tr><td>Baixar todos (CSV)</td><td>Todos os resultados sem filtro de texto/status</td></tr>
</table>

<h3>Identificação de processos do Paraná</h3>
<p>O número CNJ segue o padrão <code>NNNNNNN-DD.AAAA.J.TT.OOOO</code>:</p>
<table>
  <tr><th>Posição</th><th>Valor</th><th>Significado</th></tr>
  <tr><td><code>J</code></td><td><strong>8</strong></td><td>Justiça Estadual</td></tr>
  <tr><td><code>TT</code></td><td><strong>16</strong></td><td>Tribunal do Paraná (TJPR)</td></tr>
</table>
<p>Processos de outras origens (ex.: TRF4, TRT9) <strong>não são incluídos</strong> por padrão.</p>

<h3>Códigos de movimentação utilizados</h3>
<table>
  <tr><th>Código</th><th>Nome</th></tr>
  <tr><td><strong>848</strong></td><td>Trânsito em julgado</td></tr>
  <tr><td><strong>22</strong></td><td>Baixa definitiva (devolução à origem)</td></tr>
  <tr><td>123</td><td>Remessa</td></tr>
  <tr><td>132</td><td>Recebimento</td></tr>
</table>
<p>Fonte: <a href="https://www.cnj.jus.br/sgt/consulta_publica_movimentos.php" target="_blank">Tabelas Processuais Unificadas — CNJ</a></p>
</div>
""", unsafe_allow_html=True)
