import yfinance as yf
import pandas as pd

# Obter dados do ETF
etf = yf.Ticker("SXR8.DE")
dados = etf.history(period="730d")  # Últimos 2 anos

# Garantir que é um DataFrame
dados_df = pd.DataFrame(dados)
dados_df.index = dados_df.index.tz_localize(None)

# Adicionar colunas com Ano e Mês
dados_df['Ano'] = dados_df.index.year
dados_df['Mes'] = dados_df.index.month

# Agrupar por Ano e Mês e calcular média do fechamento
dados_quadro = dados_df.groupby(['Ano', 'Mes'])['Close'].mean().reset_index()
dados_quadro.rename(columns={'Close': 'Media_Mensal'}, inplace=True)

# Adicionar colunas com +10% e -10% da média
dados_quadro['Media_mais_10pct'] = dados_quadro['Media_Mensal'] * 1.10
dados_quadro['Media_menos_10pct'] = dados_quadro['Media_Mensal'] * 0.90

# Exportar para Excel com duas abas
with pd.ExcelWriter("sxr8_ultimos_2_anos.xlsx", engine="openpyxl", mode="w") as writer:
    dados_df.to_excel(writer, sheet_name="Dados com Condição", index=True)
    dados_quadro.to_excel(writer, sheet_name="dados_quadro", index=False)

print("Arquivo Excel exportado com sucesso!")
