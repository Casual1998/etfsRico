# =============================================================================
# calculos.py — Funções de cálculo e análise financeira
# =============================================================================
# Contém toda a matemática do projeto:
#   - encontrar_movimento(): quando o preço atingiu -X% ou +X%
#   - calcular_monte_carlo(): previsão de preço com simulações aleatórias
#   - calcular_downside_deviation(): risco de queda em percentagem
#   - calcular_movimentos_mensais(): junta tudo para cada mês da tabela
#   - calcular_recuperacao_por_mes(): média de dias para recuperar por mês
#
# Não precisas de editar este ficheiro a menos que queiras mudar
# a lógica dos cálculos em si.
# =============================================================================

import math
import numpy as np
import pandas as pd

from config import PCTS, N_SIMULACOES, JANELA_MC_DIAS, HORIZONTE_MC_DIAS, JANELA_DD_DIAS


# -----------------------------------------------------------------------------
# encontrar_movimento
# -----------------------------------------------------------------------------
# Dado um preço médio mensal, procura nos dados diários a primeira data
# em que o preço atingiu a variação pretendida (subida ou queda).
#
# Parâmetros:
#   dados_df — DataFrame com os dados diários (índice = datas)
#   media    — preço médio do mês a analisar
#   pct      — percentagem de variação (ex: 10 para ±10%)
#   inicio   — data a partir da qual procurar
#   subida   — True para procurar +pct%, False para -pct%
#
# Devolve: (preço_alvo, data_atingida, dias_desde_inicio)
#          Se nunca atingido: (preço_alvo, "Nunca atingido", "Nunca atingido")
# -----------------------------------------------------------------------------
def encontrar_movimento(dados_df, media, pct, inicio, subida=False):
    if subida:
        # Arredonda para baixo: facilita atingir o alvo de subida
        alvo = math.floor(media * (1 + pct / 100) * 100) / 100
        futuros = dados_df[dados_df.index >= inicio]
        hit = futuros[futuros["Close"] >= alvo]
    else:
        # Arredonda para cima: facilita atingir o alvo de queda
        alvo = math.ceil(media * (1 - pct / 100) * 100) / 100
        futuros = dados_df[dados_df.index >= inicio]
        hit = futuros[futuros["Close"] <= alvo]

    if hit.empty:
        return alvo, "Nunca atingido", "Nunca atingido"

    data_hit = hit.index[0]
    return alvo, data_hit.date(), (data_hit - inicio).days


# -----------------------------------------------------------------------------
# calcular_monte_carlo
# -----------------------------------------------------------------------------
# Usa os últimos N dias anteriores ao mês para estimar a distribuição
# de retornos diários, depois corre 1000 simulações de M dias à frente.
# Devolve a média dos preços finais simulados.
#
# Parâmetros:
#   dados_df   — DataFrame com os dados diários
#   inicio_mes — primeiro dia do mês a analisar
#
# Devolve: preço médio previsto (float) ou None se dados insuficientes
# -----------------------------------------------------------------------------
def calcular_monte_carlo(dados_df, inicio_mes):
    # Selecionar os últimos JANELA_MC_DIAS dias anteriores ao mês
    janela = dados_df[dados_df.index < inicio_mes].tail(JANELA_MC_DIAS)

    if len(janela) < 10:
        return None  # dados insuficientes para uma estimativa fiável

    # Calcular retornos diários (variação % de um dia para o outro)
    retornos = janela["Close"].pct_change().dropna()
    mu       = retornos.mean()   # retorno médio diário
    sigma    = retornos.std()    # volatilidade diária
    preco_base = janela["Close"].iloc[-1]  # último preço conhecido

    # Correr N_SIMULACOES simulações de HORIZONTE_MC_DIAS dias
    simulacoes = []
    for _ in range(N_SIMULACOES):
        # Gerar retornos aleatórios com a mesma média e desvio do histórico
        r = np.random.normal(mu, sigma, HORIZONTE_MC_DIAS)
        # Calcular o preço final acumulando os retornos
        preco_final = preco_base * (1 + r).prod()
        simulacoes.append(preco_final)

    return round(float(np.mean(simulacoes)), 4)


# -----------------------------------------------------------------------------
# calcular_downside_deviation
# -----------------------------------------------------------------------------
# Mede apenas a volatilidade dos dias de queda (retornos negativos).
# Ignora os dias de subida — foca no risco real de perda.
#
# Fórmula: raiz quadrada da média dos retornos negativos ao quadrado
# Resultado em percentagem (ex: 1.23 significa 1.23% de risco diário de queda)
#
# Parâmetros:
#   dados_df   — DataFrame com os dados diários
#   inicio_mes — primeiro dia do mês a analisar
#
# Devolve: percentagem (float) ou None se dados insuficientes
# -----------------------------------------------------------------------------
def calcular_downside_deviation(dados_df, inicio_mes):
    # Selecionar os últimos JANELA_DD_DIAS dias anteriores ao mês
    janela = dados_df[dados_df.index < inicio_mes].tail(JANELA_DD_DIAS)

    if len(janela) < 10:
        return None

    retornos = janela["Close"].pct_change().dropna()

    # Filtrar apenas os retornos negativos (dias de queda)
    retornos_negativos = retornos[retornos < 0]

    if len(retornos_negativos) == 0:
        return 0.0  # não houve quedas neste período

    # Calcular o desvio padrão apenas das quedas, converter para %
    dd = float((retornos_negativos ** 2).mean() ** 0.5) * 100
    return round(dd, 4)


# -----------------------------------------------------------------------------
# calcular_movimentos_mensais
# -----------------------------------------------------------------------------
# Para cada mês na tabela de médias, calcula:
#   1. Quando o preço caiu -pct% e quantos dias demorou desde o início do mês
#   2. A partir desse momento, quando subiu +pct% e quantos dias demorou
#
# Parâmetros:
#   dados_df     — DataFrame com os dados diários
#   dados_quadro — DataFrame com as médias mensais (Ano, Mes, Media_Mensal)
#
# Devolve: (res_queda, res_subida) — dicionários com os resultados por mês
# -----------------------------------------------------------------------------
def calcular_movimentos_mensais(dados_df, dados_quadro):
    # Estrutura de dados para guardar os resultados
    res_queda  = {pct: {"alvo": [], "data": [], "dias": []} for pct in PCTS}
    res_subida = {pct: {"alvo": [], "data": [], "dias": [], "data_compra": [], "dias_ate_maximo": []} for pct in PCTS}

    for _, row in dados_quadro.iterrows():
        inicio = pd.Timestamp(year=int(row["Ano"]), month=int(row["Mes"]), day=1)
        media  = float(row["Media_Mensal"])
        maximo = float(row["Maximo_Mensal"])  # máximo de fecho do mês

        for pct in PCTS:
            # --- Passo 1: Encontrar queda de -pct% ---
            alvo_q, data_q, dias_q = encontrar_movimento(dados_df, media, pct, inicio, subida=False)
            res_queda[pct]["alvo"].append(alvo_q)
            res_queda[pct]["data"].append(data_q)
            res_queda[pct]["dias"].append(dias_q)

            # --- Passo 2: A partir da data de compra, encontrar subida de +pct% ---
            # O alvo de venda é sempre +pct% da média original (não do preço de compra)
            alvo_s = math.floor(media * (1 + pct / 100) * 100) / 100
            res_subida[pct]["alvo"].append(alvo_s)

            if data_q == "Nunca atingido":
                # Se nunca caiu, também não há dados de recuperação
                res_subida[pct]["data"].append("Nunca atingido")
                res_subida[pct]["dias"].append("Nunca atingido")
                res_subida[pct]["data_compra"].append("Nunca atingido")
                res_subida[pct]["dias_ate_maximo"].append("Nunca atingido")
            else:
                # Procurar a subida apenas a partir do dia de compra
                data_compra = pd.Timestamp(data_q)
                res_subida[pct]["data_compra"].append(data_compra.date())
                futuros = dados_df[dados_df.index >= data_compra]

                # Subida até +pct% da média (alvo fixo)
                hit = futuros[futuros["Close"] >= alvo_s]
                if hit.empty:
                    res_subida[pct]["data"].append("Nunca atingido")
                    res_subida[pct]["dias"].append("Nunca atingido")
                else:
                    data_venda = hit.index[0]
                    res_subida[pct]["data"].append(data_venda.date())
                    res_subida[pct]["dias"].append((data_venda - data_compra).days)

                # Subida até ao máximo do mês (a partir da data de compra)
                hit_max = futuros[futuros["Close"] >= maximo]
                if hit_max.empty:
                    res_subida[pct]["dias_ate_maximo"].append("Nunca atingido")
                else:
                    data_max = hit_max.index[0]
                    res_subida[pct]["dias_ate_maximo"].append((data_max - data_compra).days)

    return res_queda, res_subida


# -----------------------------------------------------------------------------
# calcular_recuperacao_por_mes
# -----------------------------------------------------------------------------
# Agrega os dias de recuperação (Compra→Venda) por mês do ano,
# calculando a média ao longo de todos os anos disponíveis.
# Usado para a folha de comparação entre ETFs.
#
# Devolve: dicionário {mes_num: media_dias} (ex: {1: 145.3, 2: 98.0, ...})
# -----------------------------------------------------------------------------
def calcular_recuperacao_por_mes(dados_quadro, res_subida):
    recuperacao = {}
    for mes_num in range(1, 13):
        dias_list = []
        for i, row in dados_quadro.iterrows():
            if int(row["Mes"]) == mes_num:
                d = res_subida[10]["dias"][i]
                if d != "Nunca atingido" and isinstance(d, (int, float)):
                    dias_list.append(d)
        recuperacao[mes_num] = round(sum(dias_list) / len(dias_list), 1) if dias_list else None
    return recuperacao