#parser.py
def ler_ficheiro(nome="dataset.txt"):
    dados = {
        'cc': {},   # Cursos por turma
        'olw': [],  # Cursos com uma aula por semana
        'dsd': {},  # Cursos por professor
        'tr': {},   # Restrições de horário dos professores
        'rr': {},   # Cursos e respetivas salas
        'oc': {}    # Cursos e respetivos índices de aula
    }

    try:
        with open(nome, 'r', encoding='utf-8') as ficheiro:
            linhas = ficheiro.readlines()

        secao_atual = None

        for linha in linhas:
            linha = linha.strip()

            # Ignorar linhas vazias ou comentários
            if not linha or linha.startswith('#head'):
                continue

            # Detetar secções
            if linha.startswith('#cc'):
                secao_atual = 'cc'
                continue
            elif linha.startswith('#olw'):
                secao_atual = 'olw'
                continue
            elif linha.startswith('#dsd'):
                secao_atual = 'dsd'
                continue
            elif linha.startswith('#tr'):
                secao_atual = 'tr'
                continue
            elif linha.startswith('#rr'):
                secao_atual = 'rr'
                continue
            elif linha.startswith('#oc'):
                secao_atual = 'oc'
                continue

            # Processar dados baseado na secção atual
            if secao_atual == 'cc':
                partes = linha.split()
                if len(partes) >= 2:
                    turma = partes[0]
                    cursos = partes[1:]
                    dados['cc'][turma] = cursos

            elif secao_atual == 'olw':
                cursos = linha.split()
                if cursos:
                    dados['olw'].extend(cursos)

            elif secao_atual == 'dsd':
                partes = linha.split()
                if len(partes) >= 2:
                    professor = partes[0]
                    cursos = partes[1:]
                    dados['dsd'][professor] = cursos

            elif secao_atual == 'tr':
                partes = linha.split()
                if len(partes) >= 2:
                    professor = partes[0]
                    slots = list(map(int, partes[1:]))
                    dados['tr'][professor] = slots

            elif secao_atual == 'rr':
                partes = linha.split()
                if len(partes) == 2:
                    curso, sala = partes
                    dados['rr'][curso] = sala

            elif secao_atual == 'oc':
                partes = linha.split()
                if len(partes) >= 2:
                    curso = partes[0]
                    # Suportar múltiplos índices de aula
                    indices = list(map(int, partes[1:]))
                    dados['oc'][curso] = indices 

        return dados

    except FileNotFoundError:
        print(f"Erro: Ficheiro '{nome}' não encontrado!")
        return None
    except Exception as e:
        print(f"Erro ao ler ficheiro: {e}")
        return None


def mostrar_dados(dados):
    if not dados:
        print("Nenhum dado para mostrar!")
        return

    print("\nCURSOS POR TURMA (#cc):")
    for turma, cursos in dados['cc'].items():
        print(f"{turma}: {', '.join(cursos)}")

    print("\nCURSOS COM UMA AULA POR SEMANA (#olw):")
    if dados['olw']:
        print(', '.join(dados['olw']))
    else:
        print("Nenhum curso com uma aula por semana")

    print("\nCURSOS POR PROFESSOR (#dsd):")
    for professor, cursos in dados['dsd'].items():
        print(f"{professor}: {', '.join(cursos)}")

    print("\nRESTRIÇÕES DE HORÁRIO DOS PROFESSORES (#tr):")
    for professor, slots in dados['tr'].items():
        print(f"{professor}: slots {', '.join(map(str, slots))}")

    print("\nRESTRIÇÕES DE SALA (#rr):")
    for curso, sala in dados['rr'].items():
        print(f"{curso}: {sala}")

    print("\nAULAS ONLINE (#oc):")
    for curso, indices in dados['oc'].items():
        if isinstance(indices, list):
            print(f"{curso}: aulas {', '.join(map(str, indices))} são online")
        else:
            print(f"{curso}: aula {indices} é online")
