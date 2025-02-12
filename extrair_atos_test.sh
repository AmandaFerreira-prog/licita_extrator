#!/bin/bash

set -x  # Ativa o modo debug para exibir os comandos sendo executados
set -e  # Faz o script parar em caso de erro

ROOT_DIR=${PWD}  # Define o diretório raiz como o diretório atual
DATA_DIR=${ROOT_DIR}/area_teste/diarios  # Muda o diretório de dados para test_data

cd ${DATA_DIR}  # Navega para a pasta test_data

# Loop para processar cada arquivo JSON na pasta test_data que segue o padrão *-resumo-extracao.json
for resultado in *-resumo-extracao.json
do
    python3 ${ROOT_DIR}/extrair_atos.py ${resultado}  # Executa o script Python para cada arquivo
done
