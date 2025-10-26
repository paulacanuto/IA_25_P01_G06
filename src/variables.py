#variables.py
from parser import ler_ficheiro

def criar_variaveis_dominios(nome_ficheiro="dataset.txt"):
    # Lê os dados do ficheiro
    dados = ler_ficheiro(nome_ficheiro)
    if not dados:
        return None, None

    variables = []  # Lista de tuplos (turma, curso, aula_index)
    domains = {}    # Dicionário {variavel: lista de slots disponíveis}
    all_slots = list(range(1, 21))  # Blocos 1 a 20

    # Para cada turma e curso
    for turma, cursos in dados['cc'].items():
        for curso in cursos:
            # Determina número de aulas por semana
            n_aulas = 1 if curso in dados['olw'] else 2
            for aula_index in range(1, n_aulas + 1):
                var = (turma, curso, aula_index)
                variables.append(var)

                # Identifica o professor do curso
                prof = None
                for p, cursos_p in dados['dsd'].items():
                    if curso in cursos_p:
                        prof = p
                        break

                # Remove slots indisponíveis do professor
                indisponiveis = dados['tr'].get(prof, [])
                domain = [slot for slot in all_slots if slot not in indisponiveis]
                domains[var] = domain

    return variables, domains


# Função para testar a criação
if __name__ == "__main__":
    vars_, doms = criar_variaveis_dominios("dataset.txt")
    print("Variáveis:")
    for v in vars_:
        print(v)
    print("\nDomínios:")
    for k, d in doms.items():
        print(f"{k}: {d}")
