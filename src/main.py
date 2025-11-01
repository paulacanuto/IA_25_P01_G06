from parser import ler_ficheiro, mostrar_dados
from model import criar_problema, preencher_quadro_com_solucao, visualizar_horario_por_turma

if __name__ == "__main__":
    print("=" * 60)
    print("SISTEMA DE GESTÃO DE HORÁRIOS")
    print("=" * 60)

    # 1️⃣ Carregar dados do ficheiro
    caminho_ficheiro = r"..\data\data2.txt" or r"..\data\dataset.txt"  # Ajusta o caminho conforme necessário
    dados = ler_ficheiro(caminho_ficheiro)

    if dados:
        # 2️⃣ Mostrar dados carregados
        mostrar_dados(dados)

        print("\n" + "=" * 60)
        print("INICIANDO AGENDAMENTO AUTOMÁTICO")
        print("=" * 60)

        # 3️⃣ Criar e resolver problema de agendamento
        problem = criar_problema()
        if not problem:
            print("Não foi possível criar o problema de agendamento.")
        else:
            solution = problem.getSolution()
            if not solution:
                print(" Nenhuma solução encontrada!")
            else:
                # 4️⃣ Preencher o quadro com a solução e considerar aulas online
                quadro_preenchido = preencher_quadro_com_solucao(solution, dados)

                # 5️⃣ Visualizar horário final por turma
                visualizar_horario_por_turma(quadro_preenchido, dados)
    else:
        print("Não foi possível carregar os dados. Verifique o ficheiro dataset.txt")
