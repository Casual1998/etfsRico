# =============================================================================
# config.py — Configurações gerais do projeto
# =============================================================================
# Este é o ficheiro que deves editar para personalizar a análise.
# Não precisas de tocar nos outros ficheiros para a maioria das alterações.

# -----------------------------------------------------------------------------
# LISTA DE ETFs
# Chave: ticker do Yahoo Finance | Valor: nome do ficheiro Excel de saída
# Para adicionar um ETF novo, basta adicionar uma linha aqui.
# -----------------------------------------------------------------------------
ETFS = {
    "SXR8.DE": "sxr8_analise.xlsx",           # S&P 500 em Euros
    "VWCE.DE": "vwce_analise.xlsx",            # Todo o Mundo em Euros
    "SXRV.DE": "nasdaq100_analise.xlsx",       # NASDAQ 100
    "QDVE.DE": "sp500_tech_analise.xlsx",      # S&P 500 Tech
    "VVSM.DE": "semicondutores_analise.xlsx",  # Semicondutores
    "XMA7.DE": "momentum_analise.xlsx",        # Momentum
    "SXLE.DE": "energia_analise.xlsx",         # Petróleo e Gás
}

# -----------------------------------------------------------------------------
# FICHEIRO DE COMPARAÇÃO (gerado no final, compara todos os ETFs entre si)
# -----------------------------------------------------------------------------
FICHEIRO_COMPARACAO = "comparacao_etfs.xlsx"

# -----------------------------------------------------------------------------
# PERCENTAGEM DE ANÁLISE
# Define a % de queda para "comprar" e de subida para "vender".
# Exemplo: [10] significa comprar a -10% e vender a +10%.
# Podes colocar mais valores, ex: [5, 10] para comparar os dois cenários.
# -----------------------------------------------------------------------------
PCTS = [10]

# -----------------------------------------------------------------------------
# PERÍODO DE HISTÓRICO
# Quantos dias de histórico descarregar do Yahoo Finance.
# 3650 = ~10 anos | 1825 = ~5 anos | 730 = ~2 anos
# -----------------------------------------------------------------------------
PERIODO = "3650d"

# -----------------------------------------------------------------------------
# MONTE CARLO
# N_SIMULACOES: número de simulações (mais = mais preciso, mas mais lento)
# JANELA_MC_DIAS: quantos dias anteriores ao mês usar para calibrar o modelo
# HORIZONTE_MC_DIAS: quantos dias à frente simular
# -----------------------------------------------------------------------------
N_SIMULACOES    = 1000
JANELA_MC_DIAS  = 60
HORIZONTE_MC_DIAS = 30

# -----------------------------------------------------------------------------
# DOWNSIDE DEVIATION
# Quantos dias anteriores ao mês usar para calcular o risco de queda
# -----------------------------------------------------------------------------
JANELA_DD_DIAS = 90

# -----------------------------------------------------------------------------
# NOMES DOS MESES (em português)
# Podes alterar para outro idioma se quiseres
# -----------------------------------------------------------------------------
MONTH_NAMES = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago",
    9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}