# model.py
from constraint import Problem, AllDifferentConstraint
from variables import criar_variaveis_dominios
from collections import defaultdict
from parser import ler_ficheiro

# -------------------------------
# CONFIGURAÇÃO BASE
# -------------------------------
dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
horarios = ["09h-11h", "11h-13h", "14h-16h", "16h-18h"]

BLOCOS_POR_DIA = len(horarios)
DIAS_SEMANA = len(dias_semana)
TOTAL_TIMESLOTS = BLOCOS_POR_DIA * DIAS_SEMANA

# -------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------
def criar_quadro():
    """Cria estrutura do quadro horário vazio."""
    quadro = []
    for i in range(BLOCOS_POR_DIA):
        linha = []
        for j in range(DIAS_SEMANA):
            timeslot_index = j * BLOCOS_POR_DIA + i + 1
            linha.append(f"timeslot_{timeslot_index}")
        quadro.append(linha)
    return quadro


def visualizar_quadro(assignment):
    """Mostra visualmente o horário final (simplificado)."""
    print(f"{'':<12} | ", end="")
    for dia in dias_semana:
        print(f"{dia:<15} | ", end="")
    print()
    print("-" * 110)

    for i in range(BLOCOS_POR_DIA):
        print(f"{horarios[i]:<12} | ", end="")
        for j in range(DIAS_SEMANA):
            slot_index = j * BLOCOS_POR_DIA + i + 1
            aulas_no_slot = [
                f"{turma}-{curso}"
                for (turma, curso, _), s in assignment.items()
                if s == slot_index
            ]
            cell = ", ".join(aulas_no_slot) if aulas_no_slot else ""
            print(f"{cell:<15} | ", end="")
        print()
        print("-" * 110)


# -------------------------------
# FUNÇÃO DE CRIAÇÃO DO PROBLEMA
# -------------------------------
def criar_problema():
    problem = Problem()

    # Ler variáveis e domínios
    variables, domains = criar_variaveis_dominios("dataset.txt")
    if not variables:
        print("❌ Erro: não foi possível criar variáveis.")
        return None

    # Adicionar variáveis ao problema
    for var in variables:
        problem.addVariable(var, domains[var])

    dados = ler_ficheiro("dataset.txt")

    # -------------------------------
    # HARD CONSTRAINTS
    # -------------------------------
    # 1️⃣ Uma turma não pode ter mais de 3 aulas por dia
    def max_3_por_dia(*slots):
        count_por_dia = [0] * DIAS_SEMANA
        for s in slots:
            dia = (s - 1) // BLOCOS_POR_DIA
            count_por_dia[dia] += 1
            if count_por_dia[dia] > 3:
                return False
        return True
    problem.addConstraint(max_3_por_dia, variables)

    # 2️⃣ Disponibilidade do professor
    tr = dados.get("tr", {})
    dsd = dados.get("dsd", {})
    for professor, indisponiveis in tr.items():
        cursos_prof = dsd.get(professor, [])
        for var in variables:
            curso = var[1]
            if curso in cursos_prof:
                def disponivel(slot, indis=indisponiveis):
                    return slot not in indis
                problem.addConstraint(disponivel, [var])

    # -------------------------------
    # SOFT CONSTRAINTS
    # -------------------------------
    # Aulas do mesmo curso em dias distintos
    cursos_por_turma = defaultdict(list)
    for turma, curso, idx in variables:
        cursos_por_turma[(turma, curso)].append((turma, curso, idx))

    for aula_vars in cursos_por_turma.values():
        if len(aula_vars) > 1:
            def dias_diferentes(*slots):
                dias = [(s - 1) // BLOCOS_POR_DIA for s in slots]
                return len(dias) == len(set(dias))
            problem.addConstraint(dias_diferentes, aula_vars)

    # Cada turma prefere aulas em apenas 4 dias
    def preferir_4_dias(*slots):
        dias = set((s - 1) // BLOCOS_POR_DIA for s in slots)
        return len(dias) <= 4
    problem.addConstraint(preferir_4_dias, variables)

    # Aulas consecutivas no mesmo dia
    def aulas_consecutivas(*slots):
        slots_por_dia = defaultdict(list)
        for s in slots:
            dia = (s - 1) // BLOCOS_POR_DIA
            slots_por_dia[dia].append(s)
        for lista in slots_por_dia.values():
            lista.sort()
            for i in range(len(lista) - 1):
                if lista[i + 1] != lista[i] + 1:
                    return False
        return True
    problem.addConstraint(aulas_consecutivas, variables)

    return problem


# -------------------------------
# FUNÇÕES PARA MARCAR ONLINE
# -------------------------------
def preencher_quadro_com_solucao(solution, dados):
    """Preenche quadro com salas e marca Online de acordo com #oc"""
    quadro = []
    for i in range(BLOCOS_POR_DIA):
        linha = []
        for j in range(DIAS_SEMANA):
            timeslot_index = j * BLOCOS_POR_DIA + i + 1
            linha.append({
                "timeslot": timeslot_index,
                "aulas": [],
                "dia": dias_semana[j],
                "horario": horarios[i]
            })
        quadro.append(linha)

    for (turma, curso, aula_idx), timeslot in solution.items():
        linha = (timeslot - 1) % BLOCOS_POR_DIA
        coluna = (timeslot - 1) // BLOCOS_POR_DIA

        # Verifica se a aula é Online
        online_indices = dados.get("oc", {}).get(curso, [])
        if isinstance(online_indices, int):
            online_indices = [online_indices]
        sala = "Online" if aula_idx in online_indices else dados.get("rr", {}).get(curso, f"Room{turma[-1]}")

        aula_info = {"turma": turma, "curso": curso, "sala": sala}
        quadro[linha][coluna]["aulas"].append(aula_info)

    return quadro


def visualizar_quadro_com_aulas(quadro):
    """Mostra o quadro com indicação Online quando aplicável"""
    cabecalho = f"{'Horário':<12} |" + "".join([f" {dia:<15} |" for dia in dias_semana])
    print(cabecalho)
    print("-" * 110)

    for i in range(BLOCOS_POR_DIA):
        linha_str = f"{horarios[i]:<12} |"
        for j in range(DIAS_SEMANA):
            celula = quadro[i][j]
            if celula["aulas"]:
                aulas_texto = ", ".join([f"{aula['curso']}({aula['sala']})" for aula in celula["aulas"]])
            else:
                aulas_texto = ""
            linha_str += f" {aulas_texto:<15} |"
        print(linha_str)
        print("-" * 110)


# -------------------------------
# EXECUÇÃO DIRETA (TESTE)
# -------------------------------
if __name__ == "__main__":
    problem = criar_problema()
    if problem:
        solutions = problem.getSolutions()
        if solutions:
            print(f"{len(solutions)} soluções encontradas. Mostrando a primeira:\n")
            dados = ler_ficheiro("dataset.txt")
            quadro = preencher_quadro_com_solucao(solutions[0], dados)
            visualizar_quadro_com_aulas(quadro)
        else:
            print("⚠️ Nenhuma solução encontrada.")
