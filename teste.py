import yfinance as yf
import pandas as pd
from datetime import datetime
import numpy as np

def processar_etf(ticker_simbolo, nome_ficheiro_excel):
    # Obter dados do ticker (ETF ou ação)
    etf = yf.Ticker(ticker_simbolo)
    dados = etf.history(period="1500d")

    # Garantir que é DataFrame e normalizar o índice
    dados_df = pd.DataFrame(dados)
    dados_df.index = pd.to_datetime(dados_df.index).tz_localize(None)

    # Adicionar colunas de ano e mês
    dados_df['Ano'] = dados_df.index.year
    dados_df['Mes'] = dados_df.index.month

    # Calcular estatísticas mensais
    dados_quadro = dados_df.groupby(['Ano', 'Mes'])['Close'].agg(
        Media_Mensal='mean',
        Minimo_Mensal='min',
        Maximo_Mensal='max',
        Desvio_Padrao='std'
    ).reset_index()

    # Calcular amplitude (flutuação no mês)
    dados_quadro['Amplitude'] = dados_quadro['Maximo_Mensal'] - dados_quadro['Minimo_Mensal']

    # Calcular limites de +10% e -10%
    dados_quadro['Media_mais_10pct'] = dados_quadro['Media_Mensal'] * 1.10
    dados_quadro['Media_menos_10pct'] = dados_quadro['Media_Mensal'] * 0.90

    # Inicializar listas para as datas de atingimento dos limites
    datas_atingiu_mais10 = []
    datas_atingiu_menos10 = []

    for i in range(len(dados_quadro)):
        linha = dados_quadro.iloc[i]
        ano = int(linha['Ano'])
        mes = int(linha['Mes'])
        limite_mais10 = linha['Media_mais_10pct']
        limite_menos10 = linha['Media_menos_10pct']
        data_inicio = datetime(ano, mes, 1)

        # Filtrar os dados futuros a partir do mês atual
        df_futuro = dados_df[dados_df.index > data_inicio]

        data_mais10 = pd.NaT
        data_menos10 = pd.NaT

        for data, row in df_futuro.iterrows():
            preco = row['Close']
            if pd.isna(data_mais10) and preco >= limite_mais10:
                data_mais10 = data
            if pd.isna(data_menos10) and preco <= limite_menos10:
                data_menos10 = data
            if pd.notna(data_mais10) and pd.notna(data_menos10):
                break

        datas_atingiu_mais10.append(data_mais10)
        datas_atingiu_menos10.append(data_menos10)

    dados_quadro['Data_atingiu_+10%'] = datas_atingiu_mais10
    dados_quadro['Data_atingiu_-10%'] = datas_atingiu_menos10

    # Exportar para Excel
    with pd.ExcelWriter(nome_ficheiro_excel, engine="openpyxl", mode="w") as writer:
        dados_df.to_excel(writer, sheet_name="Dados_Diarios", index=True)
        dados_quadro.to_excel(writer, sheet_name="Resumo_Mensal", index=False)

    print(f"✅ Ficheiro '{nome_ficheiro_excel}' exportado com sucesso!")

# Exemplo: usar para NVIDIA
processar_etf("NVDA", "nvda_ultimos_2_anos.xlsx")

# Exemplo: usar para S&P 500 (ETF europeu como SXR8.DE)
processar_etf("SXR8.DE", "sp500_ultimos_2_anos.xlsx")
