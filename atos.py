import json
import re


def extrair(texto_diario: str):
    atos = []
    matches = re.findall(
        r"^[\s\S]*?Código Identificador:.*$(?:\n|)", texto_diario, re.MULTILINE)
    for match in matches:
        atos.append(AtoContratual(match.strip()))
    return atos


class AtoContratual:
    # Padrões para extrair informações de contratos
    #Todas as regex prontas para valores,partes contratadas e objeto do contrato
    #regexs criadas a partir de documento teste para 24 diarios diversificados de todos o periodo(2014-2023)
    re_valor = r"(?is)(?:Valor:\s*|- |VALOR TOTAL:\s*|valor global de\s*|,?\s*Valor Global do presente Contrato é de\s*|VALOR DO CONTRATO:\s*|Remuneração:\s*|VALOR TOTAL ESTIMADO:\s*|valor de (?:R\$)?\s*| VALOR GLOBAL:?\s*)R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:,\d{2})?)(?!.+valor global)"
    re_partes = r"(?is)(?:(?<!A\s)CONTRATANTE\s|CONTRATAD[oa]:?(?!\,| objeto:)\s?(?:\(A\):)?\s?|[–-] \d{2}\.\d{2}\.\d{2} [–-]|PB – |PARTES:\s.*?(?:\d{4}-\d{2} |\d{3}.\d{3}.\d{3}-\d{2} )e\s|E A(?:S)? EMPRESA(?:S)?:\s|e Pessoa Física:\s|R\$\s\d{1,3}\.\d{1,3}\,\d{1,2}(?:\;\s|\se\s))(.*?)(?:\,?\sCNPJ|\,?\.?\sCPF| - R\$|\.?\sCONTRATADA|- (?!.*?LTDA)|\.?\sFunção|– CONTRATO| –)" #falta pra 16,229que na vdd não necessita pois é nome de pessoas
    re_objeto = r"(?is)objeto:\s*(.*?)(?:\.?\s*valor|\,?\s*celebrado|\.?\s*fundamento legal|PROCEDIMENTO DE CONTRATAÇÃO DIRETA:)"
    re_contrato = r"(?i)(EXTRATO D[EO] CONTRATO|TERMO ADITIVO (?:AO|DE) CONTRATO|EXTRATO DE ADITIVO)[\s\S]*?"

    def __init__(self, texto: str):

        self.texto = texto
        self.partes_contratadas = []
        self.cod = self._extrai_cod(texto)
        self.valores = []
        self.objetos = []
        self.possui_contratos = self._possui_contratos()
        if self.possui_contratos:
            self._extrai_informacoes()



    def _extrai_cod(self, texto: str):
        matches = re.findall(r'Código Identificador:(.*)', texto)
        return matches[0].strip() if matches else None

    def _possui_contratos(self):
        return re.search(self.re_contrato, self.texto) is not None

    def _extrai_informacoes(self):
        # Extraindo valores
        valor_matches = re.findall(self.re_valor, self.texto)
        self.valores = [self.formatar_valor(valor) for valor in valor_matches]

        # Extraindo partes contratadas
        parte_matches = re.findall(self.re_partes, self.texto)
        for match in parte_matches:
            # match contém os nomes completos
            self.partes_contratadas.append(match.strip())

        # Extraindo objetos
        objeto_matches = re.findall(self.re_objeto, self.texto)
        self.objetos = [match.strip() for match in objeto_matches]

    def formatar_valor(self, valor: str) -> float:
        # Remove espaços e formata o valor para float
        valor = valor.replace('.', '').replace(',', '.')
        return float(valor)

    def __str__(self):
        return json.dumps(self.__dict__, indent=2, ensure_ascii=False)
