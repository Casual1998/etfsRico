import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def gerar_graficos_a_partir_excel(nome_ficheiro_excel):
    df = pd.read_excel(nome_ficheiro_excel, sheet_name="Resumo_Mensal")

    # Combinar Ano e Mês numa única coluna tipo "2024-06"
    df['AnoMes'] = pd.to_datetime(df['Ano'].astype(str) + '-' + df['Mes'].astype(str))

    # Gráfico 1: Média mensal
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x='AnoMes', y='Media_Mensal', marker='o')
    plt.title('📈 Média Mensal de Fecho')
    plt.xlabel('Data')
    plt.ylabel('Preço Médio')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Gráfico 2: Amplitude mensal
    plt.figure(figsize=(10, 5))
    sns.barplot(data=df, x='AnoMes', y='Amplitude', color='orange')
    plt.title('📊 Amplitude Mensal (Máx - Mín)')
    plt.xlabel('Data')
    plt.ylabel('Amplitude')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

    # Gráfico 3: Desvio padrão mensal
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=df, x='AnoMes', y='Desvio_Padrao', marker='o', color='red')
    plt.title('📉 Volatilidade Mensal (Desvio Padrão)')
    plt.xlabel('Data')
    plt.ylabel('Desvio Padrão')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
