import json
import glob
import os
import pandas as pd
from collections import Counter

os.makedirs("./docs/site/dados", exist_ok=True)

# Dicionário que guarda dados para renderização da página inicial.
inicial = {}
geral = {
    "detalhe": {},
    "ranking_num_contratos": {},
    "ranking_gastos_totais": {},
    "ranking_objetos": {},
    "ranking_empresas": {}
}

# Função para arredondar valores para 2 casas decimais
def arredondar_valor(valor):
    return round(valor, 2)

# Para guardar os objetos e empresas para o cálculo do top 3 mensal e top 10 anual
for path in glob.glob("../data/diarios/*-atos.json"):
    with open(path, encoding="utf-8") as json_file:
        diarios = json.load(json_file)
        for diario in diarios:
            diario = json.loads(diario)
            id_municipio = diario["id"]
            nome_municipio = diario["municipio"]
            data_quebrada = diario["data_publicacao"].split("-")
            ano = int(data_quebrada[0])
            mes = int(data_quebrada[1])  # para uso futuro
            dia = int(data_quebrada[2])  # para uso futuro

            # Atualizando seção de detalhes do municipio
            dado_municipio = inicial.get(id_municipio, {})
            detalhe = dado_municipio.get("detalhe", {})
            detalhe_ano = detalhe.get(ano, {})
            detalhe_ano_resumo = detalhe_ano.get("resumo", {})
            detalhe_ano_mes = detalhe_ano.get(mes, {})
            detalhe_ano_resumo["num_diarios"] = detalhe_ano_resumo.get(
                "num_diarios", 0) + 1
            detalhe_ano_mes["num_diarios"] = detalhe_ano_mes.get(
                "num_diarios", 0) + 1
            empresas_mensais = []  # Lista para empresas mensais
            objetos_mensais = []  # Lista para objetos mensais

            for ato in diario["atos"]:
                ato = json.loads(ato)
                valores = ato["valores"]

                # Arredondando o total gasto
                total_gasto_ato = arredondar_valor(sum(valores))

                detalhe_ano_resumo["num_contratos"] = detalhe_ano_resumo.get(
                    "num_contratos", 0) + len(valores)
                detalhe_ano_resumo["total_gasto"] = detalhe_ano_resumo.get(
                    "total_gasto", 0) + total_gasto_ato
                detalhe_ano_mes["num_contratos"] = detalhe_ano_mes.get(
                    "num_contratos", 0) + len(valores)
                detalhe_ano_mes["total_gasto"] = detalhe_ano_mes.get(
                    "total_gasto", 0) + total_gasto_ato

                # Coletando empresas e objetos
                empresas_mensais.extend(ato["partes_contratadas"])
                objetos_mensais.extend(ato["objetos"])

            # Calculando os top 3 empresas e objetos do mês
            top_3_empresas = [item[0] for item in Counter(empresas_mensais).most_common(3)]
            top_3_objetos = [item[0] for item in Counter(objetos_mensais).most_common(3)]

            detalhe_ano_mes["top_3_empresas"] = top_3_empresas
            detalhe_ano_mes["top_3_objetos"] = top_3_objetos

            detalhe_ano[mes] = detalhe_ano_mes
            detalhe[ano] = detalhe_ano
            detalhe_ano["resumo"] = detalhe_ano_resumo
            nome_municipio = nome_municipio.title()
            nome_municipio = nome_municipio.replace(" De ", " de ")
            nome_municipio = nome_municipio.replace(" Da ", " da ")
            nome_municipio = nome_municipio.replace(" Do ", " do ")
            inicial[id_municipio] = {
                "id": id_municipio,
                "nome": nome_municipio,
                "detalhe": detalhe,
            }

            # Atualizando seção de detalhes geral.
            detalhe_geral = geral.get("detalhe", {})
            detalhe_geral_ano = detalhe_geral.get(ano, {
                "resumo": {
                    "num_diarios": 0,
                    "num_contratos": 0,
                    "total_gasto": 0
                }
            })
            detalhe_geral_ano_mes = detalhe_geral_ano.get(mes, {
                "num_diarios": 0,
                "num_contratos": 0,
                "total_gasto": 0,
            })

            detalhe_geral_ano_mes["num_diarios"] += 1
            for ato in diario["atos"]:
                ato = json.loads(ato)
                detalhe_geral_ano_mes["num_contratos"] += len(ato["valores"])
                detalhe_geral_ano_mes["total_gasto"] += sum(ato["valores"])
                detalhe_geral_ano["resumo"]["num_contratos"] += len(ato["valores"])
                detalhe_geral_ano["resumo"]["total_gasto"] += sum(ato["valores"])

            detalhe_geral_ano["resumo"]["num_diarios"] += 1
            detalhe_geral_ano[mes] = detalhe_geral_ano_mes
            detalhe_geral[ano] = detalhe_geral_ano

            inicial["geral"] = {
                "id": "geral",
                "detalhe": detalhe_geral,
            }

# Função para calcular o Top 10 de objetos e empresas por ano
def calcular_top10(tipo):
    # Utiliza Counter para contar as ocorrências
    todos = []
    for id_municipio, dado in inicial.items():
        if id_municipio == "geral": 
            continue
        for ano, detalhe in dado["detalhe"].items():
            for mes, dados_mes in detalhe.items():
                if mes == "resumo": 
                    continue
                if tipo == "objetos":
                    todos.extend(dados_mes.get("top_3_objetos", []))
                elif tipo == "empresas":
                    todos.extend(dados_mes.get("top_3_empresas", []))
    # Retorna os 10 mais comuns
    return dict(Counter(todos).most_common(10))

# Atualizando ranking de objetos e empresas no dicionário geral
geral["ranking_objetos"] = calcular_top10(tipo="objetos")
geral["ranking_empresas"] = calcular_top10(tipo="empresas")

# Atualizando seção de resumo
for id_municipio, dado in inicial.items():
    num_diarios = 0
    num_contratos = 0
    total_gasto = 0

    todas_empresas = []
    todos_objetos = []

    for ano, detalhe in dado["detalhe"].items():
        resumo = detalhe.get("resumo", {})
        num_diarios += resumo.get("num_diarios", 0)
        total_gasto += resumo.get("total_gasto", 0)
        num_contratos += resumo.get("num_contratos", 0)
    
    # Coletando dados para ranking de empresas e objetos
        for mes, dados_mes in detalhe.items():
            if mes == "resumo":
                continue
            todas_empresas.extend(dados_mes.get("top_3_empresas", []))
            todos_objetos.extend(dados_mes.get("top_3_objetos", []))

    # Calculando o Top 5 de empresas e objetos
    top_5_empresas = dict(Counter(todas_empresas).most_common(5))
    top_5_objetos = dict(Counter(todos_objetos).most_common(5))

    inicial[id_municipio]["resumo"] = {
        "num_diarios": num_diarios,
        "num_contratos": num_contratos,
        "total_gasto": arredondar_valor(total_gasto),
        "top_5_empresas": top_5_empresas,
        "top_5_objetos": top_5_objetos,
    }

# Analisando municípios que mais contrataram e gastaram
def top5(arg):
    df = pd.DataFrame.from_dict(inicial, orient='index')
    df = df[df["id"] != 'geral']
    df = df.sort_values(by=['resumo'], ascending=False,
                        key=lambda x: x.str.get(arg))
    top_5 = df.head(5)
    ranking = {}
    municipios = []
    for index, (municipio, row) in enumerate(top_5.iterrows()):
        ranking[index + 1] = {
            "nome": row["nome"],
            "num": row["resumo"][arg]
        }
        municipios.append(municipio)

    return ranking

inicial['geral']['ranking_contratos'] = top5("num_contratos")
inicial['geral']['ranking_gastos_totais'] = top5("total_gasto")
inicial['geral']['ranking_objetos'] = geral["ranking_objetos"]
inicial['geral']['ranking_empresas'] = geral["ranking_empresas"]

# Salvando dados para renderização da página inicial.
for id_municipio, dado in inicial.items():
    with open(f"./docs_test/site/dados/{id_municipio}.json", "w", encoding="utf-8") as json_file:
        json.dump(dado, json_file, indent=2, default=str, ensure_ascii=False)
