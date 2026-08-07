"""
Script de migração de questões para o DynamoDB.

Uso:
    python migrar_questoes.py                    # migra todas as certificações
    python migrar_questoes.py CLF-C02            # migra apenas CLF-C02
    python migrar_questoes.py CLF-C02 --force    # recria todos os itens (upsert)

O campo 'dificuldade' é preservado/migrado junto com cada questão.
PK = CERT#<codigo>   SK = Q#<id com 3 dígitos>
"""
import json
import sys
import time
import boto3
from decimal import Decimal

# ── Configuração ──────────────────────────────────────────────────────────────

dynamodb   = boto3.resource('dynamodb', region_name='us-east-1')
tabela     = dynamodb.Table('Simulados_AWS')

TODAS_CERTS = [
    'CLF-C02',
    'DVA-C02',
    'SAA-C03',
    'SAP-C02',
    'SCS-C02',
    'SOA-C02',
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def converter_float(obj):
    """
    Recursivamente converte floats para Decimal, pois o DynamoDB boto3
    não aceita float nativo.
    """
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: converter_float(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [converter_float(v) for v in obj]
    return obj


def carregar_json(nome_cert: str) -> list:
    caminho = f'{nome_cert}.json'
    try:
        with open(caminho, 'r', encoding='utf-8') as f:
            dados = json.load(f)
    except UnicodeDecodeError:
        with open(caminho, 'r', encoding='utf-8-sig') as f:
            dados = json.load(f)

    questoes = dados if isinstance(dados, list) else dados.get('questoes', [])
    return questoes


def migrar_cert(nome_cert: str, force: bool = False) -> int:
    """
    Migra as questões de uma certificação para o DynamoDB.
    Retorna o número de itens gravados.
    """
    pk = f'CERT#{nome_cert}'
    questoes = carregar_json(nome_cert)

    if not questoes:
        print(f'  [AVISO] Nenhuma questão encontrada para {nome_cert}.')
        return 0

    # Empacota em lotes de 25 (limite do BatchWriteItem)
    LOTE = 25
    total_gravado = 0

    for inicio in range(0, len(questoes), LOTE):
        lote = questoes[inicio:inicio + LOTE]
        itens = []

        for questao in lote:
            # Cria cópia para não modificar o original
            item = dict(questao)

            # Chaves DynamoDB
            item['PK'] = pk
            item['SK'] = f"Q#{str(item['id']).zfill(3)}"

            # Garante que dificuldade existe (fallback para questões sem campo)
            if 'dificuldade' not in item:
                item['dificuldade'] = 'Médio'

            # Remove o campo 'id' numérico — o SK já serve como identificador
            # (mantemos para compatibilidade com o frontend legado)
            # item.pop('id', None)

            # Converte floats → Decimal
            item = converter_float(item)

            itens.append({'PutRequest': {'Item': item}})

        # Chama batch_write com retry em UnprocessedItems
        tentativa = 0
        pendentes = {'Simulados_AWS': itens}

        while pendentes and tentativa < 5:
            resp     = dynamodb.meta.client.batch_write_item(RequestItems=pendentes)
            pendentes = resp.get('UnprocessedItems', {})
            if pendentes:
                tentativa += 1
                espera = 2 ** tentativa
                print(f'  Retrying {len(pendentes.get("Simulados_AWS", []))} itens não processados (espera {espera}s)...')
                time.sleep(espera)

        total_gravado += len(lote)
        print(f'  Lote {inicio // LOTE + 1}: {len(lote)} itens gravados (total: {total_gravado}/{len(questoes)})')

    return total_gravado


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args  = sys.argv[1:]
    force = '--force' in args
    certs = [a for a in args if not a.startswith('--')]

    if not certs:
        certs = TODAS_CERTS

    # Valida nomes
    invalidos = [c for c in certs if c not in TODAS_CERTS]
    if invalidos:
        print(f'Certificações inválidas: {invalidos}')
        print(f'Válidas: {TODAS_CERTS}')
        sys.exit(1)

    print(f'Iniciando migração: {certs}  (force={force})\n')

    for cert in certs:
        print(f'--- {cert} ---')
        try:
            n = migrar_cert(cert, force)
            print(f'  Concluído: {n} questões migradas.\n')
        except FileNotFoundError:
            print(f'  [ERRO] Arquivo {cert}.json não encontrado. Pulando.\n')
        except Exception as e:
            print(f'  [ERRO] Falha ao migrar {cert}: {e}\n')

    print('=== Migração finalizada ===')


if __name__ == '__main__':
    main()
