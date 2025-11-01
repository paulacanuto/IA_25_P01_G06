from constraint import Problem, AllDifferentConstraint
from model import BLOCOS_POR_DIA, DIAS_SEMANA, TOTAL_TIMESLOTS, dias_semana, horarios, criar_problema
from collections import defaultdict

def criar_quadro_horario_com_aulas():
    """Cria quadro horário vazio estruturado por dias e horários"""
    quadro = []
    for i in range(BLOCOS_POR_DIA):
        linha = []
        for j in range(DIAS_SEMANA):
            timeslot_index = j * BLOCOS_POR_DIA + i + 1
            linha.append({
                "timeslot": f"timeslot_{timeslot_index}",
                "aulas": [],
                "dia": dias_semana[j],
                "horario": horarios[i],
                "numero": timeslot_index
            })
        quadro.append(linha)
    return quadro


def atribuir_aulas_ao_horario(dados):
    """Cria e resolve o problema de agendamento com base nas restrições"""
    problem = Problem()
    variables = []
    dominio_timeslots = list(range(1, TOTAL_TIMESLOTS + 1))

    # Criar variáveis: turma_curso_aulaX
    for turma, cursos in dados["cc"].items():
        for curso in cursos:
            n_aulas = 1 if curso in dados.get("olw", []) else 2
            for aula_idx in range(1, n_aulas + 1):
                var_name = f"{turma}_{curso}_aula{aula_idx}"
                problem.addVariable(var_name, dominio_timeslots)
                variables.append(var_name)

    print(f"Total de aulas para agendar: {len(variables)}")

    # ---------------------------
    #       HARD CONSTRAINTS
    # ---------------------------

    # 1️⃣ Todas as aulas de uma turma em horários distintos
    for turma in dados["cc"].keys():
        turma_vars = [v for v in variables if v.startswith(f"{turma}_")]
        problem.addConstraint(AllDifferentConstraint(), turma_vars)

    # 2️⃣ Professor não pode dar duas aulas ao mesmo tempo
    for professor, cursos_prof in dados["dsd"].items():
        prof_vars = [v for v in variables if v.split("_")[1] in cursos_prof]
        if len(prof_vars) > 1:
            problem.addConstraint(AllDifferentConstraint(), prof_vars)

    # 3️⃣ Disponibilidade do professor
    for professor, indisponiveis in dados.get("tr", {}).items():
        cursos_prof = dados["dsd"].get(professor, [])
        for var in variables:
            curso = var.split("_")[1]
            if curso in cursos_prof:
                problem.addConstraint(lambda ts, indis=indisponiveis: ts not in indis, [var])

    # 4️⃣ Uma turma não pode ter mais de 3 aulas por dia
    for turma in dados["cc"].keys():
        turma_vars = [v for v in variables if v.startswith(f"{turma}_")]

        def max_3_por_dia(*slots):
            contagem = [0] * DIAS_SEMANA
            for s in slots:
                dia = (s - 1) // BLOCOS_POR_DIA
                contagem[dia] += 1
                if contagem[dia] > 3:
                    return False
            return True

        problem.addConstraint(max_3_por_dia, turma_vars)

    # ---------------------------
    #       SOFT CONSTRAINTS
    # ---------------------------

    # 1️⃣ Aulas do mesmo curso devem ser em dias distintos
    cursos_por_turma = defaultdict(list)
    for var in variables:
        turma, curso = var.split("_")[0], var.split("_")[1]
        cursos_por_turma[(turma, curso)].append(var)

    for grupo in cursos_por_turma.values():
        if len(grupo) > 1:
            def dias_diferentes(*slots):
                dias = [(s - 1) // BLOCOS_POR_DIA for s in slots]
                return len(dias) == len(set(dias))
            problem.addConstraint(dias_diferentes, grupo)

    # 2️⃣ Cada turma deve ter aulas em, se possível, apenas 4 dias
    for turma in dados["cc"].keys():
        turma_vars = [v for v in variables if v.startswith(f"{turma}_")]

        def preferir_4_dias(*slots):
            dias = set((s - 1) // BLOCOS_POR_DIA for s in slots)
            return len(dias) <= 4
        problem.addConstraint(preferir_4_dias, turma_vars)

    # 3️⃣ As aulas em cada dia devem ser consecutivas
    for turma in dados["cc"].keys():
        turma_vars = [v for v in variables if v.startswith(f"{turma}_")]

        def aulas_consecutivas(*slots):
            por_dia = defaultdict(list)
            for s in slots:
                dia = (s - 1) // BLOCOS_POR_DIA
                por_dia[dia].append(s)
            for lista in por_dia.values():
                lista.sort()
                for i in range(len(lista) - 1):
                    if lista[i + 1] != lista[i] + 1:
                        return False
            return True

        problem.addConstraint(aulas_consecutivas, turma_vars)

    # ---------------------------
    #       RESOLUÇÃO
    # ---------------------------
    print(" A resolver o problema de agendamento...")
    solution = problem.getSolution()

    if not solution:
        print(" Nenhuma solução encontrada!")
        return None

    print("Solução encontrada com sucesso!")
    return solution

def preencher_quadro_com_solucao(quadro, solution, dados):
    """Preenche o quadro horário com a solução encontrada, considerando aulas online."""
    for var_name, timeslot in solution.items():
        turma, curso, aula_str = var_name.split("_")
        aula_idx = int(aula_str.replace("aula", ""))  # número da aula do curso
        timeslot_idx = timeslot - 1

        # Calcular posição no quadro
        coluna = timeslot_idx // BLOCOS_POR_DIA  # dia
        linha = timeslot_idx % BLOCOS_POR_DIA    # horário

        # Índices de aulas online para este curso
        online_indices = dados.get("oc", {}).get(curso, [])
        if not isinstance(online_indices, list):
            online_indices = [online_indices]

        # Definir sala
        sala = "Online" if aula_idx in online_indices else dados.get("rr", {}).get(curso, f"Room{turma[-1]}")

        # Adicionar aula ao quadro
        aula_info = {"turma": turma, "curso": curso, "sala": sala}
        quadro[linha][coluna]["aulas"].append(aula_info)

    return quadro



def visualizar_horario_por_turma(quadro, dados):
    """Imprime o horário final organizado por turma"""
    for turma in dados["cc"].keys():
        print("\n" + "=" * 80)
        print(f"HORÁRIO DA TURMA {turma}")
        print("=" * 80)

        cabecalho = f"{'Horário':<12} |" + "".join([f" {dia:<20} |" for dia in dias_semana])
        print(cabecalho)
        print("-" * 140)

        for i in range(BLOCOS_POR_DIA):
            linha_str = f"{horarios[i]:<12} |"
            for j in range(DIAS_SEMANA):
                celula = quadro[i][j]
                conteudo = "---"
                for aula in celula["aulas"]:
                    if aula["turma"] == turma:
                        conteudo = f"{aula['curso']} {aula['sala']}"
                        break
                linha_str += f" {conteudo:<20} |"
            print(linha_str)
            print("-" * 140)


def verificar_restricoes(quadro, dados):
    """Verifica se todas as hard constraints estão a ser cumpridas"""
    problemas = []

    # 1️⃣ Aulas de uma turma em horários distintos
    for turma in dados["cc"].keys():
        slots_turma = []
        for i in range(BLOCOS_POR_DIA):
            for j in range(DIAS_SEMANA):
                for aula in quadro[i][j]["aulas"]:
                    if aula["turma"] == turma:
                        slots_turma.append(quadro[i][j]["numero"])
        if len(slots_turma) != len(set(slots_turma)):
            problemas.append(f" Turma {turma} tem aulas em horários repetidos!")

    # 2️⃣ Professores não podem dar duas aulas ao mesmo tempo
    for i in range(BLOCOS_POR_DIA):
        for j in range(DIAS_SEMANA):
            celula = quadro[i][j]
            profs = {}
            for aula in celula["aulas"]:
                prof = next((p for p, cursos in dados.get("dsd", {}).items() if aula["curso"] in cursos), None)
                if prof:
                    if prof in profs:
                        problemas.append(
                            f" Professor {prof} tem aulas simultâneas: {profs[prof]} e {aula['curso']} ({celula['dia']} {celula['horario']})"
                        )
                    profs[prof] = aula["curso"]

    # 3️⃣ Disponibilidade do professor
    for i in range(BLOCOS_POR_DIA):
        for j in range(DIAS_SEMANA):
            celula = quadro[i][j]
            for aula in celula["aulas"]:
                prof = next((p for p, cursos in dados.get("dsd", {}).items() if aula["curso"] in cursos), None)
                if prof and (celula["numero"] in dados.get("tr", {}).get(prof, [])):
                    problemas.append(
                        f" Professor {prof} não disponível em {celula['dia']} {celula['horario']} para curso {aula['curso']}"
                    )

    # 4️⃣ Máximo de 3 aulas por dia por turma
    for turma in dados["cc"].keys():
        for d in range(DIAS_SEMANA):
            aulas_no_dia = sum(
                1 for i in range(BLOCOS_POR_DIA)
                for aula in quadro[i][d]["aulas"]
                if aula["turma"] == turma
            )
            if aulas_no_dia > 3:
                problemas.append(f" Turma {turma} tem {aulas_no_dia} aulas na {dias_semana[d]} (máx. 3)")

    if problemas:
        print("\n PROBLEMAS DETETADOS:")
        for p in problemas:
            print(p)
    else:
        print("✅ Todas as hard constraints foram cumpridas!")

    return len(problemas) == 0


def main(dados):
    print(" INICIANDO AGENDAMENTO AUTOMÁTICO")
    
    # 1️⃣ Criar e resolver problema de agendamento
    problem = criar_problema()
    if not problem:
        print("Não foi possível criar o problema de agendamento.")
        return

    solution = problem.getSolution()
    if not solution:
        print(" Nenhuma solução encontrada!")
        return

    # 2️⃣ Criar quadro horário vazio
    quadro = criar_quadro_horario_com_aulas()

    # 3️⃣ Preencher o quadro com a solução, incluindo aulas online
    quadro_preenchido = preencher_quadro_com_solucao(quadro, solution, dados)

    # 4️⃣ Visualizar horário final por turma
    visualizar_horario_por_turma(quadro_preenchido, dados)
