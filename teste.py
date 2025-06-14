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

# Inicializar listas para guardar as datas encontradas
datas_atingiu_mais10 = []
datas_atingiu_menos10 = []

# Iterar por cada mês na tabela de médias
for i in range(len(dados_quadro)):
    linha = dados_quadro.iloc[i]
    
    ano = int(linha['Ano'])
    mes = int(linha['Mes'])
    media_mensal = linha['Media_Mensal']
    limite_mais10 = linha['Media_mais_10pct']
    limite_menos10 = linha['Media_menos_10pct']
    
    # Data de início para procurar (primeiro dia do mês)
    data_inicio = datetime(ano, mes, 1)
    
    # Filtrar apenas os dados após esse mês
    df_futuro = dados_df[dados_df.index > data_inicio]
    
    # Inicializar datas como "não encontradas"
    data_mais10 = pd.NaT
    data_menos10 = pd.NaT

    # Iterar linha por linha do DataFrame futuro
    for data, row in df_futuro.iterrows():
        preco = row['Close']

        # Verificar +10%
        if pd.isna(data_mais10) and preco >= limite_mais10:
            data_mais10 = data

        # Verificar -10%
        if pd.isna(data_menos10) and preco <= limite_menos10:
            data_menos10 = data

        # Se já encontrou as duas datas, pode parar o loop
        if pd.notna(data_mais10) and pd.notna(data_menos10):
            break
    1
    datas_atingiu_mais10.append(data_mais10)
    datas_atingiu_menos10.append(data_menos10)

# Adicionar as datas ao DataFrame de resumo
dados_quadro['Data_atingiu_+10%'] = datas_atingiu_mais10
dados_quadro['Data_atingiu_-10%'] = datas_atingiu_menos10

# Exportar para Excel com as duas folhas
with pd.ExcelWriter("sxr8_ultimos_2_anos.xlsx", engine="openpyxl", mode="w") as writer:
    dados_df.to_excel(writer, sheet_name="Dados com Condição", index=True)
    dados_quadro.to_excel(writer, sheet_name="dados_quadro", index=False)

print("✅ Arquivo Excel exportado com sucesso!")
