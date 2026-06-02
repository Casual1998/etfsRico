# =============================================================================
# main.py — Ficheiro principal: corre este para gerar todos os Excels
# =============================================================================
# Uso:
#   python main.py
#
# Gera:
#   - Um ficheiro Excel por ETF definido em config.py
#   - Um ficheiro de comparação entre todos os ETFs
#
# Para alterar ETFs, percentagens ou períodos → edita config.py
# Para alterar os cálculos → edita calculos.py
# Para alterar o formato dos Excels → edita este ficheiro
# =============================================================================

import os
import yfinance as yf
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

from config import (
    ETFS, FICHEIRO_COMPARACAO, PCTS, PERIODO, MONTH_NAMES
)
from calculos import (
    calcular_movimentos_mensais,
    calcular_monte_carlo,
    calcular_downside_deviation,
    calcular_recuperacao_por_mes
)


# =============================================================================
# FUNÇÕES AUXILIARES DE EXCEL
# =============================================================================

def escrever_cabecalho(ws, headers, widths, altura=30):
    """Escreve a linha de cabeçalho e define larguras das colunas."""
    ws.row_dimensions[1].height = altura
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(row=1, column=i, value=h)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w


def escrever_celula(ws, row, col, value, fmt=None, bold=False, align="right"):
    """Escreve um valor numa célula com formatação opcional."""
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name="Arial", bold=bold, size=10)
    c.alignment = Alignment(horizontal=align)
    if fmt and value not in ("Nunca atingido", "Dados insuficientes", "N/D", None):
        c.number_format = fmt
    return c


def escrever_bloco_movimentos(ws, er, col_start, res_dict):
    """
    Escreve 3 colunas por percentagem: valor alvo, data, dias.
    Usado tanto para quedas como para subidas.
    """
    col = col_start
    for pct in PCTS:
        # Coluna 1: preço alvo
        escrever_celula(ws, er, col, res_dict[pct]["alvo"][er - 2], fmt='#,##0.0000 "€"')
        col += 1

        # Coluna 2: data em que foi atingido
        data_val = res_dict[pct]["data"][er - 2]
        c = ws.cell(row=er, column=col, value=data_val)
        c.font = Font(name="Arial", size=10)
        c.alignment = Alignment(horizontal="right")
        if data_val != "Nunca atingido":
            c.number_format = "DD/MM/YYYY"
        col += 1

        # Coluna 3: número de dias
        escrever_celula(ws, er, col, res_dict[pct]["dias"][er - 2])
        col += 1

    return col


# =============================================================================
# FOLHA 1: MÉDIAS MENSAIS
# =============================================================================

def construir_folha_medias(wb, dados_df, dados_quadro, res_queda, res_subida):
    """
    Cria a folha 'Medias Mensais' com:
      - Média de fecho por mês
      - Data e dias para atingir -10% (compra)
      - Data e dias para atingir +10% a partir da compra (venda)
      - Lucro simulado de 100€
      - Previsão Monte Carlo a 30 dias
      - Downside Deviation a 90 dias
    """
    ws = wb.active
    ws.title = "Medias Mensais"

    # --- Definir colunas ---
    base_headers  = ["Ano", "Mes", "Media Mensal (€)", "Maximo Mensal (€)"]
    base_widths   = [8, 6, 18, 18]

    # Gera cabeçalhos dinamicamente para cada percentagem definida em config.py
    queda_headers  = []
    subida_headers = []
    for p in PCTS:
        queda_headers  += [f"-{p}% (€)", f"Data Compra -{p}%", f"Dias até Compra"]
        subida_headers += [f"+{p}% (€)", f"Data Venda +{p}%",  f"Dias Compra→Venda"]

    pct_widths = [14, 18, 14]

    # Coluna extra entre subidas e lucro: dias desde compra até atingir o máximo do mês
    maximo_headers = ["Dias Compra→Máximo"]
    maximo_widths  = [20]

    extra_headers = ["Lucro 100€ (€)", "Previsão MC 30d (€)", "Downside Dev. 90d (%)"]
    extra_widths  = [16, 20, 22]

    all_headers = base_headers + queda_headers + subida_headers + maximo_headers + extra_headers
    all_widths  = base_widths + pct_widths * len(PCTS) + pct_widths * len(PCTS) + maximo_widths + extra_widths

    escrever_cabecalho(ws, all_headers, all_widths)

    # Colunas fixas (calculadas uma vez)
    col_subidas_start  = len(base_headers) + len(PCTS) * 3 + 1
    col_dias_max       = len(base_headers) + len(PCTS) * 3 * 2 + 1  # após o bloco de subidas
    col_lucro          = col_dias_max + 1
    col_mc             = col_lucro + 1
    col_dd             = col_lucro + 2

    # --- Escrever dados linha a linha ---
    for r_idx, row in dados_quadro.iterrows():
        er = r_idx + 2
        media_val  = round(float(row["Media_Mensal"]), 4)
        inicio_mes = pd.Timestamp(year=int(row["Ano"]), month=int(row["Mes"]), day=1)

        # Ano e Mês
        escrever_celula(ws, er, 1, int(row["Ano"]), align="center")
        escrever_celula(ws, er, 2, MONTH_NAMES[int(row["Mes"])], align="center")

        # Média mensal
        escrever_celula(ws, er, 3, media_val, fmt='#,##0.0000 "€"')

        # Máximo mensal (maior preço de fecho atingido no mês)
        maximo_val = round(float(row["Maximo_Mensal"]), 4)
        escrever_celula(ws, er, 4, maximo_val, fmt='#,##0.0000 "€"')

        # Bloco de quedas (-10%)
        escrever_bloco_movimentos(ws, er, len(base_headers) + 1, res_queda)

        # Bloco de subidas (+10%, contadas desde a data de compra)
        escrever_bloco_movimentos(ws, er, col_subidas_start, res_subida)

        # Dias desde a compra (-10%) até atingir o máximo do mês
        pct = PCTS[0]
        dias_max = res_subida[pct]["dias_ate_maximo"][r_idx]
        escrever_celula(ws, er, col_dias_max, dias_max)

        # --- Lucro simulado de 100€ ---
        # Lógica: compra 100€ ao preço de -10%, vende ao preço de +10%
        pct = PCTS[0]
        preco_compra = res_queda[pct]["alvo"][r_idx]
        preco_venda  = res_subida[pct]["alvo"][r_idx]
        data_compra  = res_queda[pct]["data"][r_idx]
        data_venda   = res_subida[pct]["data"][r_idx]

        if data_compra == "Nunca atingido" or data_venda == "Nunca atingido":
            escrever_celula(ws, er, col_lucro, "Nunca atingido")
        else:
            unidades   = 100 / preco_compra
            lucro      = round(unidades * preco_venda - 100, 4)
            escrever_celula(ws, er, col_lucro, lucro, fmt='+#,##0.00 "€";-#,##0.00 "€"')

        # --- Monte Carlo: previsão do preço médio a 30 dias ---
        resultado_mc = calcular_monte_carlo(dados_df, inicio_mes)
        if resultado_mc is not None:
            escrever_celula(ws, er, col_mc, resultado_mc, fmt='#,##0.0000 "€"')
        else:
            escrever_celula(ws, er, col_mc, "Dados insuficientes")

        # --- Downside Deviation: risco de queda nos últimos 90 dias ---
        resultado_dd = calcular_downside_deviation(dados_df, inicio_mes)
        if resultado_dd is not None:
            escrever_celula(ws, er, col_dd, resultado_dd, fmt='0.0000"%"')
        else:
            escrever_celula(ws, er, col_dd, "Dados insuficientes")

    # --- Linha de total do lucro acumulado (soma apenas os valores numéricos) ---
    total_row = len(dados_quadro) + 2
    ws.cell(row=total_row, column=col_lucro - 1, value="TOTAL LUCRO:").font = Font(name="Arial", bold=True, size=10)
    lucro_col_letter = get_column_letter(col_lucro)
    formula = f'=SUMIF({lucro_col_letter}2:{lucro_col_letter}{total_row-1},"<>Nunca atingido",{lucro_col_letter}2:{lucro_col_letter}{total_row-1})'
    c = ws.cell(row=total_row, column=col_lucro, value=formula)
    c.number_format = '+#,##0.00 "€";-#,##0.00 "€"'
    c.font = Font(name="Arial", bold=True, size=10)
    c.alignment = Alignment(horizontal="right")

    return ws


# =============================================================================
# FOLHA 2: DADOS DIÁRIOS (com indicadores técnicos)
# =============================================================================

def construir_folha_diaria(wb, dados_df):
    """
    Cria a folha 'Dados Diarios' com:
      - Open, High, Low, Close, Volume
      - RSI(14): sobrecomprado >70, sobrevendido <30
      - MM50 e MM200: médias móveis de 50 e 200 dias
      - Sinal RSI: texto descritivo
    """
    ws = wb.create_sheet("Dados Diarios")

    # --- Calcular indicadores técnicos ---

    # RSI (Relative Strength Index) com período de 14 dias
    # Mede a força relativa dos movimentos de subida vs queda
    close = dados_df["Close"]
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()   # média dos dias positivos
    loss  = (-delta.clip(upper=0)).rolling(14).mean() # média dos dias negativos
    rs    = gain / loss.replace(0, float("nan"))
    dados_df["RSI"] = (100 - (100 / (1 + rs))).round(2)

    # Médias Móveis (preço médio dos últimos N dias)
    dados_df["MM50"]  = close.rolling(50).mean().round(4)
    dados_df["MM200"] = close.rolling(200).mean().round(4)

    def sinal_rsi(rsi):
        """Interpreta o valor do RSI em linguagem natural."""
        if pd.isna(rsi): return ""
        if rsi < 30:     return "Sobrevendido"   # boa altura para comprar
        if rsi > 70:     return "Sobrecomprado"  # possível correção em breve
        return "Neutro"

    headers = ["Data", "Open (€)", "High (€)", "Low (€)", "Close (€)",
               "Volume", "RSI (14)", "MM50 (€)", "MM200 (€)", "Sinal RSI"]
    widths  = [14, 12, 12, 12, 12, 14, 10, 14, 14, 16]

    escrever_cabecalho(ws, headers, widths)

    for r_idx, (date, row) in enumerate(dados_df.iterrows(), 2):
        escrever_celula(ws, r_idx, 1, date.date(), fmt="DD/MM/YYYY", align="center")
        for c_idx, col in enumerate(["Open", "High", "Low", "Close"], 2):
            v = row.get(col)
            escrever_celula(ws, r_idx, c_idx,
                            round(float(v), 4) if pd.notna(v) else None,
                            fmt='#,##0.0000 "€"')
        escrever_celula(ws, r_idx, 6, int(row.get("Volume", 0) or 0))

        rsi_val = row.get("RSI")
        escrever_celula(ws, r_idx, 7, float(rsi_val) if pd.notna(rsi_val) else None)

        mm50 = row.get("MM50")
        escrever_celula(ws, r_idx, 8, float(mm50) if pd.notna(mm50) else None, fmt='#,##0.0000 "€"')

        mm200 = row.get("MM200")
        escrever_celula(ws, r_idx, 9, float(mm200) if pd.notna(mm200) else None, fmt='#,##0.0000 "€"')

        escrever_celula(ws, r_idx, 10, sinal_rsi(rsi_val), align="center")

    return ws


# =============================================================================
# FOLHA 3: ESTATÍSTICAS MENSAIS (comparação por mês ao longo de 10 anos)
# =============================================================================

def construir_folha_estatisticas(wb, dados_df):
    """
    Cria a folha 'Estatisticas Mensais' com:
      - Para cada mês do ano (Jan a Dez), uma linha
      - Para cada ano disponível, colunas com Mínimo, Máximo e Desvio Padrão
      - Média do desvio ao longo de todos os anos
      - Ranking de instabilidade (1 = mês mais instável do ano)
    """
    ws = wb.create_sheet("Estatisticas Mensais")

    # Calcular estatísticas por ano e mês
    stats_df = dados_df.groupby(["Ano", "Mes"])["Close"].agg(
        Minimo="min", Maximo="max", Desvio="std"
    ).reset_index()

    anos = sorted(stats_df["Ano"].unique())

    # Cabeçalho da primeira coluna (Mês)
    ws.cell(row=1, column=1, value="Mes").font = Font(name="Arial", bold=True, size=10)
    ws.cell(row=1, column=1).alignment = Alignment(horizontal="center")
    ws.column_dimensions["A"].width = 8

    # Uma grupo de 3 colunas por ano (Min, Max, Desvio)
    col = 2
    ano_col_map = {}
    for ano in anos:
        ano_col_map[ano] = col
        for label in [f"{ano} Min (€)", f"{ano} Max (€)", f"{ano} Desvio (€)"]:
            c = ws.cell(row=1, column=col, value=label)
            c.font = Font(name="Arial", bold=True, size=10)
            c.alignment = Alignment(horizontal="center", wrap_text=True)
            ws.column_dimensions[get_column_letter(col)].width = 14
            col += 1

    # Colunas finais: média do desvio e ranking
    col_media_desvio = col
    ws.cell(row=1, column=col_media_desvio, value="Média Desvio (€)").font = Font(name="Arial", bold=True, size=10)
    ws.cell(row=1, column=col_media_desvio).alignment = Alignment(horizontal="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(col_media_desvio)].width = 16

    col_rank = col + 1
    ws.cell(row=1, column=col_rank, value="Instabilidade").font = Font(name="Arial", bold=True, size=10)
    ws.cell(row=1, column=col_rank).alignment = Alignment(horizontal="center", wrap_text=True)
    ws.column_dimensions[get_column_letter(col_rank)].width = 14
    ws.row_dimensions[1].height = 35

    # Preencher uma linha por mês
    desvios_por_mes = {}
    for mes_num in range(1, 13):
        er = mes_num + 1
        ws.cell(row=er, column=1, value=MONTH_NAMES[mes_num]).font = Font(name="Arial", bold=True, size=10)
        ws.cell(row=er, column=1).alignment = Alignment(horizontal="center")

        desvios = []
        for ano in anos:
            col = ano_col_map[ano]
            subset = stats_df[(stats_df["Ano"] == ano) & (stats_df["Mes"] == mes_num)]
            if not subset.empty:
                r = subset.iloc[0]
                for offset, key in enumerate(["Minimo", "Maximo", "Desvio"]):
                    val = round(float(r[key]), 4) if pd.notna(r[key]) else None
                    escrever_celula(ws, er, col + offset, val, fmt='#,##0.0000 "€"')
                if pd.notna(r["Desvio"]):
                    desvios.append(float(r["Desvio"]))

        # Média do desvio padrão ao longo de todos os anos para este mês
        media_dev = round(sum(desvios) / len(desvios), 4) if desvios else None
        desvios_por_mes[mes_num] = media_dev
        c = ws.cell(row=er, column=col_media_desvio, value=media_dev)
        if media_dev is not None:
            c.number_format = '#,##0.0000 "€"'
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="right")

    # Ranking de instabilidade (1 = mês com maior desvio médio)
    meses_ordenados = sorted(
        [(m, v) for m, v in desvios_por_mes.items() if v is not None],
        key=lambda x: x[1], reverse=True
    )
    rank_map = {m: i + 1 for i, (m, _) in enumerate(meses_ordenados)}
    for mes_num in range(1, 13):
        er = mes_num + 1
        rank = rank_map.get(mes_num, "")
        c = ws.cell(row=er, column=col_rank, value=f"#{rank}" if rank else "")
        c.font = Font(name="Arial", size=10)
        c.alignment = Alignment(horizontal="center")

    return ws


# =============================================================================
# FUNÇÃO PRINCIPAL: processar um ETF e gerar o seu Excel
# =============================================================================

def process_etf(ticker, output_file):
    """
    Descarrega os dados do ticker, calcula todos os indicadores
    e gera o ficheiro Excel com 3 folhas.
    Devolve o dicionário de recuperação por mês (usado na comparação).
    """
    print(f"\n📥 A obter dados de {ticker}...")
    etf   = yf.Ticker(ticker)
    dados = etf.history(period=PERIODO)

    # Preparar DataFrame base
    dados_df = pd.DataFrame(dados)
    dados_df.index = pd.to_datetime(dados_df.index).tz_localize(None)
    dados_df["Ano"] = dados_df.index.year
    dados_df["Mes"] = dados_df.index.month

    # Calcular médias e máximos mensais
    dados_quadro = dados_df.groupby(["Ano", "Mes"]).agg(
        Media_Mensal=("Close", "mean"),
        Maximo_Mensal=("Close", "max")
    ).reset_index()

    # Calcular movimentos de preço (quedas e recuperações)
    res_queda, res_subida = calcular_movimentos_mensais(dados_df, dados_quadro)

    # Criar o workbook e as 3 folhas
    wb = Workbook()
    construir_folha_medias(wb, dados_df, dados_quadro, res_queda, res_subida)
    construir_folha_diaria(wb, dados_df)
    construir_folha_estatisticas(wb, dados_df)

    wb.save(output_file)
    print(f"✅ {output_file} criado!")

    # Calcular e devolver os dias médios de recuperação por mês
    return calcular_recuperacao_por_mes(dados_quadro, res_subida)


# =============================================================================
# FUNÇÃO DE COMPARAÇÃO: gerar o Excel com todos os ETFs lado a lado
# =============================================================================

def gerar_comparacao(dados_recuperacao, output_file=FICHEIRO_COMPARACAO):
    """
    Gera o ficheiro de comparação entre todos os ETFs com:
      - Desvio médio mensal por ETF
      - Ranking interno de instabilidade por ETF
      - Qual ETF é mais instável em cada mês
      - Dias médios de recuperação por ETF
      - Qual ETF recupera mais rápido em cada mês
    """
    print(f"\n📊 A gerar comparação entre ETFs...")
    tickers = list(ETFS.keys())

    # Descarregar e calcular desvio mensal para cada ETF
    medias_desvio = {}
    for ticker in tickers:
        etf   = yf.Ticker(ticker)
        dados = etf.history(period=PERIODO)
        df    = pd.DataFrame(dados)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df["Mes"] = df.index.month
        medias_desvio[ticker] = {}
        for m in range(1, 13):
            sub = df[df["Mes"] == m]["Close"].std()
            medias_desvio[ticker][m] = round(float(sub), 4) if pd.notna(sub) else None

    # Calcular ranking interno (por ETF, ordenado pelos 12 meses)
    rankings = {}
    for ticker in tickers:
        vals = sorted(
            [(m, v) for m, v in medias_desvio[ticker].items() if v is not None],
            key=lambda x: x[1], reverse=True
        )
        rankings[ticker] = {m: i + 1 for i, (m, _) in enumerate(vals)}

    # --- Construir o Excel ---
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparacao"

    n = len(tickers)
    col_desvio_start = 2
    col_rank_start   = col_desvio_start + n
    col_instavel     = col_rank_start + n
    col_rec_start    = col_instavel + 1
    col_rapido       = col_rec_start + n

    # Linha 1: títulos dos grupos
    grupos = {
        col_desvio_start: ("Desvio Medio Mensal (€)", n),
        col_rank_start:   ("Ranking Interno (1=mais instavel)", n),
        col_rec_start:    ("Media Dias Recuperacao (compra -10% → venda +10%)", n),
    }
    for col_start, (titulo, span) in grupos.items():
        ws.merge_cells(start_row=1, start_column=col_start,
                       end_row=1,   end_column=col_start + span - 1)
        c = ws.cell(row=1, column=col_start, value=titulo)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True, vertical="center")

    for col_single in [col_instavel, col_rapido]:
        c = ws.cell(row=1, column=col_single,
                    value="Mais Instavel" if col_single == col_instavel else "Recupera Mais Rapido")
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 35

    # Linha 2: sub-cabeçalhos com os tickers
    ws.cell(row=2, column=1, value="Mes").font = Font(name="Arial", bold=True, size=10)
    for i, t in enumerate(tickers):
        for col in [col_desvio_start + i, col_rank_start + i, col_rec_start + i]:
            c = ws.cell(row=2, column=col, value=t)
            c.font = Font(name="Arial", bold=True, size=10)
            c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.row_dimensions[2].height = 30

    # Larguras das colunas
    ws.column_dimensions["A"].width = 8
    for col in range(2, col_rapido + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18

    # Linhas de dados (linha 3 em diante, uma por mês)
    for mes_num in range(1, 13):
        er = mes_num + 2
        c = ws.cell(row=er, column=1, value=MONTH_NAMES[mes_num])
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center")

        # Desvio médio e qual é o mais instável
        vals_desvio = []
        for i, ticker in enumerate(tickers):
            val = medias_desvio[ticker].get(mes_num)
            escrever_celula(ws, er, col_desvio_start + i,
                            val if val is not None else "N/D",
                            fmt='#,##0.0000 "€"')
            if val is not None:
                vals_desvio.append((ticker, val))

        # Ranking interno
        for i, ticker in enumerate(tickers):
            rank = rankings[ticker].get(mes_num)
            escrever_celula(ws, er, col_rank_start + i,
                            f"#{rank}" if rank is not None else "N/D",
                            align="center")

        # Mais instável entre os ETFs neste mês
        if vals_desvio:
            mais_instavel = max(vals_desvio, key=lambda x: x[1])[0]
            escrever_celula(ws, er, col_instavel, mais_instavel, bold=True, align="center")

        # Dias de recuperação e qual recupera mais rápido
        vals_rec = []
        for i, ticker in enumerate(tickers):
            dias = dados_recuperacao.get(ticker, {}).get(mes_num)
            escrever_celula(ws, er, col_rec_start + i,
                            round(dias, 1) if dias is not None else "N/D")
            if dias is not None:
                vals_rec.append((ticker, dias))

        if vals_rec:
            mais_rapido = min(vals_rec, key=lambda x: x[1])[0]
            escrever_celula(ws, er, col_rapido, mais_rapido, bold=True, align="center")

    wb.save(output_file)
    print(f"✅ {output_file} criado!")


# =============================================================================
# PONTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  Análise de ETFs — a iniciar")
    print("=" * 50)

    # Criar pasta de destino se não existir
    PASTA_SAIDA = "Ficheiros_Analise"
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    print(f"📁 Ficheiros serão guardados em: {PASTA_SAIDA}/")

    # Processar cada ETF individualmente
    dados_recuperacao = {}
    for ticker, filename in ETFS.items():
        caminho = os.path.join(PASTA_SAIDA, filename)
        dados_recuperacao[ticker] = process_etf(ticker, caminho)

    print("\n✅ Todos os ficheiros individuais gerados!")

    # Gerar o ficheiro de comparação entre todos os ETFs
    gerar_comparacao(dados_recuperacao, output_file=os.path.join(PASTA_SAIDA, FICHEIRO_COMPARACAO))

    print("\n🎉 Concluído! Ficheiros gerados em", PASTA_SAIDA + ":")
    for filename in ETFS.values():
        print(f"   - {filename}")
    print(f"   - {FICHEIRO_COMPARACAO}")