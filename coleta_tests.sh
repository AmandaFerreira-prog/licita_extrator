#!/bin/bash

set -x  # debug
set -e  # exit on error

START_DATE=${START_DATE:="2014-01-01"}
END_DATE=${END_DATE:="2024-12-31"}
ROOT_DIR="/workspaces/extrator_licita"
DATA_DIR="/workspaces/extrator_licita/data"
OUT_DIR="/workspaces/extrator_licita/data/out"
REPO_DIR="/workspaces/extrator_licita/data/qd"
DATA_COLLECTION_DIR=${REPO_DIR}/data_collection
QD_DOWNLOAD_DIR=${REPO_DIR}/data_collection/data/2500000
DOWNLOAD_DIR="/workspaces/extrator_licita/area_test"

mkdir -p ${DATA_DIR}
cd ${DATA_DIR}
mkdir -p ${DOWNLOAD_DIR}
mkdir -p ${OUT_DIR}

# Checando se o docker está rodando antes de iniciar a coleta.
docker ps > /dev/null

# Preparando ambiente para coleta.
cd ${REPO_DIR} || (git clone https://github.com/okfn-brasil/querido-diario qd && cd ${REPO_DIR})
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install setuptools
pip install wheel
pip install -r ${DATA_COLLECTION_DIR}/requirements-dev.txt

# Função para gerar 5 dias aleatórios por ano
generate_random_dates() {
    year=$1
    start_date="${year}-01-01"
    end_date="${year}-12-31"
    # Gerar 5 datas aleatórias dentro do ano
    for i in $(seq 1 5); do
        random_date=$(shuf -i $(date -d $start_date +%s)-$(date -d $end_date +%s) -n 1 | xargs -I {} date -d @{} +%Y-%m-%d)
        echo $random_date
    done
}

# Gerando dias aleatórios para cada ano no intervalo.
random_dates=()
for year in $(seq 2014 2024); do
    random_dates+=($(generate_random_dates $year))
done

# Coletando diários e movendo para a pasta de diários.
cd ${DATA_COLLECTION_DIR}
for random_date in "${random_dates[@]}"; do
    echo "Coletando diários para a data: ${random_date}"  # Para depuração
    scrapy crawl pb_federacao_municipios -a start_date=${random_date} -a end_date=${random_date} > ${OUT_DIR}/scrapy-${random_date}.out 2> ${OUT_DIR}/scrapy-${random_date}.err
done


for dir in `ls -da ${QD_DOWNLOAD_DIR}/*`
do
    # Importante pois algumas datas possuem mais de um diário (tem os extras).
    i=1
    for fpath in `ls -da ${dir}/*`
    do
        newname=`basename ${dir}-${i}.pdf`
        # Não apagamos o arquivo PDF, mas salvamos na pasta de destino
        cp ${fpath} ${DOWNLOAD_DIR}/${newname}
        i=$((i+1))
    done
done

# Finalizando e saindo do ambiente virtual.
cd ${REPO_DIR}

# Extraindo texto dos diários e segmentando diários.
cd ${DOWNLOAD_DIR}

# docker pull apache/tika:1.28.4
docker run -d -p 9998:9998 --rm --name tika apache/tika:1.28.4
sleep 10

for pdf in `ls -a *.pdf`
do
    fname=`basename -s .pdf ${pdf}`  # removendo extensão
    extraido="${fname}-extraido.txt"
    curl \
        -H "Accept: text/plain" -H "Content-Type: application/pdf" \
        -T ${pdf} \
        http://localhost:9998/tika > ${extraido}

    python3 ${ROOT_DIR}/extrair_diarios.py ${extraido}
    # Não apagamos o PDF
    rm -f ${fname}-proc*.txt
done

docker stop tika
