import yfinance as yf
import pandas as pd
from datetime import datetime

# Obter dados do ETF
etf = yf.Ticker("SXR8.DE")
dados = etf.history(period="730d")  # Últimos 2 anos

# Garantir que é um DataFrame e remover timezone
dados_df = pd.DataFrame(dados)
dados_df.index = pd.to_datetime(dados_df.index).tz_localize(None)

# Adicionar colunas com Ano e Mês
dados_df['Ano'] = dados_df.index.year
dados_df['Mes'] = dados_df.index.month

# Agrupar por Ano e Mês e calcular média do fechamento
dados_quadro = dados_df.groupby(['Ano', 'Mes'])['Close'].mean().reset_index()
dados_quadro.rename(columns={'Close': 'Media_Mensal'}, inplace=True)

# Calcular +10% e -10%
dados_quadro['Media_mais_10pct'] = dados_quadro['Media_Mensal'] * 1.10
dados_quadro['Media_menos_10pct'] = dados_quadro['Media_Mensal'] * 0.90

# Inicializar listas para datas
datas_atingiu_mais10 = []
datas_atingiu_menos10 = []

# Iterar por cada linha de dados_quadro
for idx, linha in dados_quadro.iterrows():
    ano_atual = int(linha['Ano'])
    mes_atual = int(linha['Mes'])

    # Data de referência (primeiro dia do mês)
    data_inicio = datetime(ano_atual, mes_atual, 1)

    # Limites
    limite_superior = linha['Media_mais_10pct']
    limite_inferior = linha['Media_menos_10pct']

    # Filtrar apenas dados após esse mês
    df_futuro = dados_df[dados_df.index > data_inicio]

    # Verificar a primeira data em que atinge os limites
    data_mais10 = df_futuro[df_futuro['Close'] >= limite_superior].index.min()
    data_menos10 = df_futuro[df_futuro['Close'] <= limite_inferior].index.min()

    datas_atingiu_mais10.append(data_mais10 if pd.notna(data_mais10) else pd.NaT)
    datas_atingiu_menos10.append(data_menos10 if pd.notna(data_menos10) else pd.NaT)

# Adicionar colunas ao quadro final
dados_quadro['Data_atingiu_+10%'] = datas_atingiu_mais10
dados_quadro['Data_atingiu_-10%'] = datas_atingiu_menos10

# Exportar para Excel com as duas folhas
with pd.ExcelWriter("sxr8_ultimos_2_anos.xlsx", engine="openpyxl", mode="w") as writer:
    dados_df.to_excel(writer, sheet_name="Dados com Condição", index=True)
    dados_quadro.to_excel(writer, sheet_name="dados_quadro", index=False)

print("✅ Arquivo Excel exportado com sucesso!")
