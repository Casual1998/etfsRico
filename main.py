import yfinance as yf
import pandas as pd
import math
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

ETFS = {

    # Os teus originais (A funcionar 100%)

    "SXR8.DE": "sxr8_analise.xlsx",          # S&P 500

    "VWCE.DE": "vwce_analise.xlsx",          # Todo o Mundo

    

    # Alta Volatilidade / Tecnológicas (A funcionar 100%)

    "SXRV.DE": "nasdaq100_analise.xlsx",     # NASDAQ 100

    "QDVE.DE": "sp500_tech_analise.xlsx",    # S&P 500 Tech

    "VVSM.DE": "semicondutores_analise.xlsx",# Semicondutores / Microchips

    

    # --- CORRIGIDOS PARA O YAHOO FINANCE ---

    

    # 1. Momentum (Substitído pelo equivalente exato da iShares, ultra estável no Yahoo)

    "IS3R.DE": "momentum_analise.xlsx",      # iShares Edge MSCI World Momentum UCITS €

    

    # Petróleo e Gás JUNTOS (Empresas)

    "EXV1.DE": "energia_europa_analise.xlsx", # Gigantes Europeias (Shell, BP...)

    "ZPDW.DE": "energia_eua_analise.xlsx",    # Gigantes Americanas (Exxon, Chevron)



    # --- PETRÓLEO E GÁS (Via Amesterdão/Londres em Euros) ---

    "CRUD.L": "petroleo_brent_analise.xlsx",  # WisdomTree Brent Crude (Cotado em EUR na bolsa de Londres)

    "NGAS.L": "gas_natural_analise.xlsx",     # WisdomTree Natural Gas (Cotado em EUR na bolsa de Londres)



}

PCTS = [10]  # percentagem a analisar

month_names = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
               7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}

def encontrar_movimento(dados_df, media, pct, inicio, subida=False):
    if subida:
        alvo = math.floor(media * (1 + pct / 100) * 100) / 100
        futuros = dados_df[dados_df.index >= inicio]
        hit = futuros[futuros["Close"] >= alvo]
    else:
        alvo = math.ceil(media * (1 - pct / 100) * 100) / 100
        futuros = dados_df[dados_df.index >= inicio]
        hit = futuros[futuros["Close"] <= alvo]
    if hit.empty:
        return alvo, "Nunca atingido", "Nunca atingido"
    data_hit = hit.index[0]
    return alvo, data_hit.date(), (data_hit - inicio).days

def process_etf(ticker, output_file):
    print(f"A obter dados de {ticker}...")
    etf = yf.Ticker(ticker)
    dados = etf.history(period="3650d")

    dados_df = pd.DataFrame(dados)
    dados_df.index = pd.to_datetime(dados_df.index).tz_localize(None)
    dados_df["Ano"] = dados_df.index.year
    dados_df["Mes"] = dados_df.index.month

    dados_quadro = dados_df.groupby(["Ano", "Mes"])["Close"].mean().reset_index()
    dados_quadro.rename(columns={"Close": "Media_Mensal"}, inplace=True)

    # Calcular para cada percentagem:
    # - data/dias até atingir -10% (desde início do mês)
    # - a partir dessa data, data/dias até atingir +10%
    res_queda  = {pct: {"alvo": [], "data": [], "dias": []} for pct in PCTS}
    res_subida = {pct: {"alvo": [], "data": [], "dias": [], "data_compra": []} for pct in PCTS}

    for _, row in dados_quadro.iterrows():
        inicio = pd.Timestamp(year=int(row["Ano"]), month=int(row["Mes"]), day=1)
        media  = float(row["Media_Mensal"])
        for pct in PCTS:
            # 1. Encontrar queda -10%
            alvo_q, data_q, dias_q = encontrar_movimento(dados_df, media, pct, inicio, subida=False)
            res_queda[pct]["alvo"].append(alvo_q)
            res_queda[pct]["data"].append(data_q)
            res_queda[pct]["dias"].append(dias_q)

            # 2. A partir da data de compra (-10%), procurar +10%
            alvo_s = math.floor(media * (1 + pct / 100) * 100) / 100
            res_subida[pct]["alvo"].append(alvo_s)

            if data_q == "Nunca atingido":
                res_subida[pct]["data"].append("Nunca atingido")
                res_subida[pct]["dias"].append("Nunca atingido")
                res_subida[pct]["data_compra"].append("Nunca atingido")
            else:
                data_compra = pd.Timestamp(data_q)
                res_subida[pct]["data_compra"].append(data_compra.date())
                futuros = dados_df[dados_df.index >= data_compra]
                hit = futuros[futuros["Close"] >= alvo_s]
                if hit.empty:
                    res_subida[pct]["data"].append("Nunca atingido")
                    res_subida[pct]["dias"].append("Nunca atingido")
                else:
                    data_venda = hit.index[0]
                    res_subida[pct]["data"].append(data_venda.date())
                    res_subida[pct]["dias"].append((data_venda - data_compra).days)

    wb = Workbook()

    # ── Folha 1: Médias Mensais ──────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Medias Mensais"

    # Construir cabeçalhos: base + queda + subida (a partir da compra)
    base_headers = ["Ano", "Mes", "Media Mensal (€)"]
    base_widths   = [8, 6, 18]

    queda_headers  = []
    subida_headers = []
    pct_widths     = [14, 18, 14]

    for pct in PCTS:
        queda_headers  += [f"-{pct}% (€)", f"Data Compra -{pct}%", f"Dias até Compra"]
        subida_headers += [f"+{pct}% (€)", f"Data Venda +{pct}%", f"Dias Compra→Venda"]

    lucro_headers = ["Lucro 100€ (€)"]
    lucro_widths  = [16]

    mc_headers = ["Previsão MC 30d (€)"]
    mc_widths  = [20]

    all_headers = base_headers + queda_headers + subida_headers + lucro_headers + mc_headers
    all_widths  = base_widths  + pct_widths * len(PCTS) + pct_widths * len(PCTS) + lucro_widths + mc_widths

    ws1.row_dimensions[1].height = 30
    for i, (h, w) in enumerate(zip(all_headers, all_widths), 1):
        c = ws1.cell(row=1, column=i, value=h)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        ws1.column_dimensions[get_column_letter(i)].width = w

    def escrever_bloco(ws, er, col_start, res_dict):
        col = col_start
        for pct in PCTS:
            alvo_val = res_dict[pct]["alvo"][er - 2]
            c_alvo = ws.cell(row=er, column=col, value=alvo_val)
            c_alvo.number_format = '#,##0.0000 "€"'
            col += 1

            data_val = res_dict[pct]["data"][er - 2]
            c_data = ws.cell(row=er, column=col)
            if data_val == "Nunca atingido":
                c_data.value = "Nunca atingido"
            else:
                c_data.value = data_val
                c_data.number_format = "DD/MM/YYYY"
            col += 1

            ws.cell(row=er, column=col, value=res_dict[pct]["dias"][er - 2])
            col += 1
        return col

    col_subidas_start = len(base_headers) + len(PCTS) * 3 + 1

    for r_idx, row in dados_quadro.iterrows():
        er = r_idx + 2
        media_val = round(float(row["Media_Mensal"]), 4)

        ws1.cell(row=er, column=1, value=int(row["Ano"]))
        ws1.cell(row=er, column=2, value=month_names[int(row["Mes"])])
        c3 = ws1.cell(row=er, column=3, value=media_val)
        c3.number_format = '#,##0.0000 "€"'

        escrever_bloco(ws1, er, len(base_headers) + 1, res_queda)
        escrever_bloco(ws1, er, col_subidas_start, res_subida)

        # Coluna lucro: 100€ investidos ao preço de compra (-10%), vendidos ao preço de venda (+10%)
        col_lucro = len(all_headers)
        pct = PCTS[0]
        preco_compra = res_queda[pct]["alvo"][r_idx]
        preco_venda  = res_subida[pct]["alvo"][r_idx]
        data_venda   = res_subida[pct]["data"][r_idx]

        c_lucro = ws1.cell(row=er, column=col_lucro)
        if data_venda == "Nunca atingido" or res_queda[pct]["data"][r_idx] == "Nunca atingido":
            c_lucro.value = "Nunca atingido"
        else:
            unidades = 100 / preco_compra
            valor_venda = unidades * preco_venda
            lucro = round(valor_venda - 100, 4)
            c_lucro.value = lucro
            c_lucro.number_format = '+#,##0.00 "€";-#,##0.00 "€"'

        # Monte Carlo: 60 dias anteriores ao início do mês → prever 30 dias
        col_mc = len(all_headers)
        inicio_mes = pd.Timestamp(year=int(row["Ano"]), month=int(row["Mes"]), day=1)
        janela = dados_df[dados_df.index < inicio_mes].tail(60)
        c_mc = ws1.cell(row=er, column=col_mc)
        if len(janela) >= 10:
            retornos = janela["Close"].pct_change().dropna()
            mu    = retornos.mean()
            sigma = retornos.std()
            preco_base = janela["Close"].iloc[-1]
            N_SIM = 1000
            import numpy as np
            simulacoes = []
            for _ in range(N_SIM):
                r = np.random.normal(mu, sigma, 30)
                preco_final = preco_base * (1 + r).prod()
                simulacoes.append(preco_final)
            media_mc = round(float(np.mean(simulacoes)), 4)
            c_mc.value = media_mc
            c_mc.number_format = '#,##0.0000 "€"'
        else:
            c_mc.value = "Dados insuficientes"

        for c in range(1, len(all_headers) + 1):
            cell = ws1.cell(row=er, column=c)
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center" if c <= 2 else "right")

    # Linha de total do lucro acumulado
    total_row = len(dados_quadro) + 2
    total_col = len(all_headers)
    ws1.cell(row=total_row, column=total_col - 1, value="TOTAL LUCRO:").font = Font(name="Arial", bold=True, size=10)
    ws1.cell(row=total_row, column=total_col - 1).alignment = Alignment(horizontal="right")
    # Somar apenas células numéricas na coluna lucro
    first_data_row = 2
    last_data_row  = total_row - 1
    lucro_col_letter = get_column_letter(total_col)
    ws1.cell(row=total_row, column=total_col,
             value=f'=SUMIF({lucro_col_letter}{first_data_row}:{lucro_col_letter}{last_data_row},"<>Nunca atingido",{lucro_col_letter}{first_data_row}:{lucro_col_letter}{last_data_row})')
    ws1.cell(row=total_row, column=total_col).number_format = '+#,##0.00 "€";-#,##0.00 "€"'
    ws1.cell(row=total_row, column=total_col).font = Font(name="Arial", bold=True, size=10)
    ws1.cell(row=total_row, column=total_col).alignment = Alignment(horizontal="right")

    # ── Calcular indicadores técnicos ───────────────────────────────────────
    close = dados_df["Close"]

    # RSI(14)
    delta = close.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, float("nan"))
    dados_df["RSI"] = (100 - (100 / (1 + rs))).round(2)

    # Médias Móveis
    dados_df["MM50"]  = close.rolling(50).mean().round(4)
    dados_df["MM200"] = close.rolling(200).mean().round(4)

    def sinal_rsi(rsi):
        if pd.isna(rsi):    return ""
        if rsi < 30:        return "Sobrevendido"
        if rsi > 70:        return "Sobrecomprado"
        return "Neutro"

    # ── Folha 2: Dados Diários ───────────────────────────────────────────────
    ws2 = wb.create_sheet("Dados Diarios")
    raw_headers = ["Data", "Open (€)", "High (€)", "Low (€)", "Close (€)", "Volume",
                   "RSI (14)", "MM50 (€)", "MM200 (€)", "Sinal RSI"]
    raw_widths   = [14, 12, 12, 12, 12, 14, 10, 14, 14, 16]

    for i, (h, w) in enumerate(zip(raw_headers, raw_widths), 1):
        c = ws2.cell(row=1, column=i, value=h)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        ws2.column_dimensions[get_column_letter(i)].width = w
    ws2.row_dimensions[1].height = 30

    for r_idx, (date, row) in enumerate(dados_df.iterrows(), 2):
        ws2.cell(row=r_idx, column=1, value=date.date()).number_format = "DD/MM/YYYY"
        for c_idx, col in enumerate(["Open","High","Low","Close"], 2):
            v = row.get(col)
            cell = ws2.cell(row=r_idx, column=c_idx, value=round(float(v), 4) if pd.notna(v) else None)
            cell.number_format = '#,##0.0000 "€"'
        ws2.cell(row=r_idx, column=6, value=int(row.get("Volume", 0) or 0))

        # RSI
        rsi_val = row.get("RSI")
        ws2.cell(row=r_idx, column=7, value=float(rsi_val) if pd.notna(rsi_val) else None)

        # MM50
        mm50_val = row.get("MM50")
        c_mm50 = ws2.cell(row=r_idx, column=8, value=float(mm50_val) if pd.notna(mm50_val) else None)
        c_mm50.number_format = '#,##0.0000 "€"'

        # MM200
        mm200_val = row.get("MM200")
        c_mm200 = ws2.cell(row=r_idx, column=9, value=float(mm200_val) if pd.notna(mm200_val) else None)
        c_mm200.number_format = '#,##0.0000 "€"'

        # Sinal RSI
        ws2.cell(row=r_idx, column=10, value=sinal_rsi(rsi_val))

        for c in range(1, 11):
            cell = ws2.cell(row=r_idx, column=c)
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center" if c in (1, 10) else "right")


    # ── Folha 3: Estatísticas por Mês (10 anos) ───────────────────────────
    ws3 = wb.create_sheet("Estatisticas Mensais")

    stats_df = dados_df.groupby(["Ano", "Mes"])["Close"].agg(
        Minimo="min", Maximo="max", Desvio="std"
    ).reset_index()

    anos = sorted(stats_df["Ano"].unique())

    # Linha 1: cabeçalho fixo + grupos por ano
    ws3.cell(row=1, column=1, value="Mes").font = Font(name="Arial", bold=True, size=10)
    ws3.cell(row=1, column=1).alignment = Alignment(horizontal="center")
    ws3.column_dimensions["A"].width = 8

    col = 2
    ano_col_map = {}
    for ano in anos:
        ano_col_map[ano] = col
        for label in [f"{ano} Min (€)", f"{ano} Max (€)", f"{ano} Desvio (€)"]:
            c = ws3.cell(row=1, column=col, value=label)
            c.font = Font(name="Arial", bold=True, size=10)
            c.alignment = Alignment(horizontal="center", wrap_text=True)
            ws3.column_dimensions[get_column_letter(col)].width = 14
            col += 1

    # Colunas finais: média do desvio e ranking
    col_media_desvio = col
    c = ws3.cell(row=1, column=col_media_desvio, value="Média Desvio (€)")
    c.font = Font(name="Arial", bold=True, size=10)
    c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws3.column_dimensions[get_column_letter(col_media_desvio)].width = 16

    col_rank = col + 1
    c = ws3.cell(row=1, column=col_rank, value="Instabilidade")
    c.font = Font(name="Arial", bold=True, size=10)
    c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws3.column_dimensions[get_column_letter(col_rank)].width = 14

    ws3.row_dimensions[1].height = 35

    # Uma linha por mês (1-12)
    desvios_por_mes = {}
    for mes_num in range(1, 13):
        er = mes_num + 1
        ws3.cell(row=er, column=1, value=month_names[mes_num])
        ws3.cell(row=er, column=1).font = Font(name="Arial", bold=True, size=10)
        ws3.cell(row=er, column=1).alignment = Alignment(horizontal="center")

        desvios = []
        for ano in anos:
            col = ano_col_map[ano]
            subset = stats_df[(stats_df["Ano"] == ano) & (stats_df["Mes"] == mes_num)]
            if subset.empty:
                ws3.cell(row=er, column=col).value = None
                ws3.cell(row=er, column=col+1).value = None
                ws3.cell(row=er, column=col+2).value = None
            else:
                r = subset.iloc[0]
                for offset, key in enumerate(["Minimo", "Maximo", "Desvio"]):
                    val = round(float(r[key]), 4) if pd.notna(r[key]) else None
                    cell = ws3.cell(row=er, column=col+offset, value=val)
                    cell.number_format = '#,##0.0000 "€"'
                    cell.font = Font(name="Arial", size=10)
                    cell.alignment = Alignment(horizontal="right")
                if pd.notna(r["Desvio"]):
                    desvios.append(float(r["Desvio"]))

        media_dev = round(sum(desvios) / len(desvios), 4) if desvios else None
        desvios_por_mes[mes_num] = media_dev
        cell = ws3.cell(row=er, column=col_media_desvio, value=media_dev)
        cell.number_format = '#,##0.0000 "€"'
        cell.font = Font(name="Arial", bold=True, size=10)
        cell.alignment = Alignment(horizontal="right")

    # Ranking de instabilidade (1 = mais instável)
    meses_ordenados = sorted(
        [(m, v) for m, v in desvios_por_mes.items() if v is not None],
        key=lambda x: x[1], reverse=True
    )
    rank_map = {m: i+1 for i, (m, _) in enumerate(meses_ordenados)}
    for mes_num in range(1, 13):
        er = mes_num + 1
        rank = rank_map.get(mes_num, "")
        cell = ws3.cell(row=er, column=col_rank, value=f"#{rank}" if rank else "")
        cell.font = Font(name="Arial", size=10)
        cell.alignment = Alignment(horizontal="center")

    wb.save(output_file)
    print(f"✅ {output_file} criado!")

    # Devolver dias de recuperação por mês (para comparação)
    # Para cada mês calcula a média dos dias Compra→Venda ao longo dos anos
    recuperacao = {}  # mes_num -> media_dias
    for mes_num in range(1, 13):
        dias_list = []
        for i, row in dados_quadro.iterrows():
            if int(row["Mes"]) == mes_num:
                d = res_subida[10]["dias"][i]
                if d != "Nunca atingido" and isinstance(d, (int, float)):
                    dias_list.append(d)
        recuperacao[mes_num] = round(sum(dias_list) / len(dias_list), 1) if dias_list else None
    return recuperacao


dados_recuperacao = {}
for ticker, filename in ETFS.items():
    dados_recuperacao[ticker] = process_etf(ticker, filename)

print("\nAmbos os ficheiros Excel foram gerados!")


def gerar_comparacao(dados_recuperacao, output_file="comparacao_etfs.xlsx"):
    print("A gerar comparacao entre ETFs...")
    tickers = list(ETFS.keys())

    # --- recolher desvio e recuperacao para cada ticker ---
    medias_desvio   = {}   # ticker -> {mes -> valor}
    for ticker in tickers:
        etf   = yf.Ticker(ticker)
        dados = etf.history(period="3650d")
        df    = pd.DataFrame(dados)
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df["Mes"] = df.index.month
        medias_desvio[ticker] = {}
        for m in range(1, 13):
            sub = df[df["Mes"] == m]["Close"].std()
            medias_desvio[ticker][m] = round(float(sub), 4) if pd.notna(sub) else None

    # --- construir a folha ---
    wb = Workbook()
    ws = wb.active
    ws.title = "Comparacao"

    # Secções de colunas
    # A: Mes
    # B...: Desvio medio por ticker
    # depois: Ranking desvio por ticker (dentro do proprio ETF)
    # depois: Mais Instavel (entre ETFs)
    # depois: Dias recuperacao por ticker
    # depois: Recupera mais rapido (entre ETFs)

    n = len(tickers)
    col_desvio_start  = 2
    col_rank_start    = col_desvio_start + n
    col_instavel      = col_rank_start + n
    col_rec_start     = col_instavel + 1
    col_rapido        = col_rec_start + n

    headers = (
        ["Mes"]
        + [f"{t}" for t in tickers]           # desvio
        + [f"Rank {t}" for t in tickers]      # ranking interno
        + ["Mais Instavel"]
        + [f"{t}" for t in tickers]           # dias recuperacao
        + ["Recupera Mais Rapido"]
    )
    # Row 1: group labels; Row 2: column labels
    ws.merge_cells(start_row=1, start_column=col_desvio_start,
                   end_row=1,   end_column=col_desvio_start + n - 1)
    ws.cell(row=1, column=col_desvio_start, value="Desvio Medio Mensal (€)")

    ws.merge_cells(start_row=1, start_column=col_rank_start,
                   end_row=1,   end_column=col_rank_start + n - 1)
    ws.cell(row=1, column=col_rank_start, value="Ranking Interno (1=mais instavel)")

    ws.cell(row=1, column=col_instavel, value="Mais Instavel")

    ws.merge_cells(start_row=1, start_column=col_rec_start,
                   end_row=1,   end_column=col_rec_start + n - 1)
    ws.cell(row=1, column=col_rec_start, value="Media Dias Recuperacao (compra -10% → venda +10%)")

    ws.cell(row=1, column=col_rapido, value="Recupera Mais Rapido")

    for col in range(1, col_rapido + 1):
        c = ws.cell(row=1, column=col)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True, vertical="center")
    ws.row_dimensions[1].height = 35

    # Row 2: sub-headers
    ws.cell(row=2, column=1, value="Mes")
    for i, t in enumerate(tickers):
        ws.cell(row=2, column=col_desvio_start + i, value=t)
        ws.cell(row=2, column=col_rank_start   + i, value=t)
        ws.cell(row=2, column=col_rec_start    + i, value=t)
    ws.cell(row=2, column=col_instavel, value="")
    ws.cell(row=2, column=col_rapido,   value="")
    for col in range(1, col_rapido + 1):
        c = ws.cell(row=2, column=col)
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    ws.row_dimensions[2].height = 30

    # Column widths
    ws.column_dimensions["A"].width = 8
    for col in range(2, col_rapido + 1):
        ws.column_dimensions[get_column_letter(col)].width = 18

    # Ranking interno por ETF (ordenado pelos 12 meses)
    rankings = {}
    for ticker in tickers:
        vals = sorted(
            [(m, v) for m, v in medias_desvio[ticker].items() if v is not None],
            key=lambda x: x[1], reverse=True
        )
        rankings[ticker] = {m: i+1 for i, (m, _) in enumerate(vals)}

    # Escrever dados (linha 3 em diante)
    for mes_num in range(1, 13):
        er = mes_num + 2

        c = ws.cell(row=er, column=1, value=month_names[mes_num])
        c.font = Font(name="Arial", bold=True, size=10)
        c.alignment = Alignment(horizontal="center")

        # Desvio medio
        vals_desvio = []
        for i, ticker in enumerate(tickers):
            val = medias_desvio[ticker].get(mes_num)
            cell = ws.cell(row=er, column=col_desvio_start + i, value=val if val is not None else "N/D")
            if val is not None:
                cell.number_format = '#,##0.0000 "€"'
                vals_desvio.append((ticker, val))
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="right")

        # Ranking interno
        for i, ticker in enumerate(tickers):
            rank = rankings[ticker].get(mes_num)
            cell = ws.cell(row=er, column=col_rank_start + i,
                           value=f"#{rank}" if rank is not None else "N/D")
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center")

        # Mais instavel entre ETFs
        if vals_desvio:
            mais_instavel = max(vals_desvio, key=lambda x: x[1])[0]
            c_mi = ws.cell(row=er, column=col_instavel, value=mais_instavel)
            c_mi.font = Font(name="Arial", bold=True, size=10)
            c_mi.alignment = Alignment(horizontal="center")

        # Dias de recuperacao
        vals_rec = []
        for i, ticker in enumerate(tickers):
            dias = dados_recuperacao.get(ticker, {}).get(mes_num)
            cell = ws.cell(row=er, column=col_rec_start + i,
                           value=round(dias, 1) if dias is not None else "N/D")
            cell.font = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="right")
            if dias is not None:
                vals_rec.append((ticker, dias))

        # Recupera mais rapido
        if vals_rec:
            mais_rapido = min(vals_rec, key=lambda x: x[1])[0]
            c_rap = ws.cell(row=er, column=col_rapido, value=mais_rapido)
            c_rap.font = Font(name="Arial", bold=True, size=10)
            c_rap.alignment = Alignment(horizontal="center")

    wb.save(output_file)
    print(f"✅ {output_file} criado!")

gerar_comparacao(dados_recuperacao)