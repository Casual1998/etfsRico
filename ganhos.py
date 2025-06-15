def calcular_ganhos():
    try:
        preco_compra = float(input("📉 Insere o preço de compra por unidade (€): ").replace(',', '.'))
        preco_venda = float(input("📈 Insere o preço de venda por unidade (€): ").replace(',', '.'))
        valor_investido = float(input("💰 Insere o valor investido (€): ").replace(',', '.'))

        # Quantidade de unidades compradas
        unidades = valor_investido / preco_compra

        # Valor final ao vender todas as unidades
        valor_final = unidades * preco_venda

        # Ganho
        lucro = valor_final - valor_investido
        percentagem = (lucro / valor_investido) * 100

        print(f"\n📊 Resultados:")
        print(f"🔹 Unidades compradas: {unidades:.4f}")
        print(f"🔹 Valor final: {valor_final:.2f} €")
        print(f"🔹 Lucro obtido: {lucro:.2f} €")
        print(f"🔹 Rentabilidade: {percentagem:.2f}%")
    except Exception as e:
        print("⚠️ Erro ao inserir os dados:", e)

if __name__ == "__main__":
    calcular_ganhos()
