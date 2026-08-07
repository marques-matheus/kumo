"""
Lambda: GetSimuladoDetalhes
Rota: GET /simulados/{simulado_id}

Retorna os detalhes completos de um simulado salvo (questões + respostas + gabarito).
Apenas o próprio aluno pode acessar seus simulados.

Resposta:
{
  "simulado_id": "2024-01-01T12:00:00Z#<uuid>",
  "cert": "CLF-C02",
  "data_iso": "...",
  "score": 85,
  "corretas": 34,
  "erradas": 6,
  "puladas": 0,
  "total": 40,
  "tempo_segundos": 1800,
  "questoes": [
    {
      "id": "Q#001",
      "pergunta": "...",
      "opcoes": [...],
      "temas": [...],
      "dificuldade": "Médio",
      "status": "correta",
      "resposta_usuario": [1],
      "resposta_correta": [1],
      "explicacao": "..."
    },
    ...
  ]
}
"""
import json
import boto3
from boto3.dynamodb.types import TypeDeserializer
from decimal import Decimal

# ── Utilitários ───────────────────────────────────────────────────────────────

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


_deserializer = TypeDeserializer()

def deserializar(item_raw: dict) -> dict:
    return {k: _deserializer.deserialize(v) for k, v in item_raw.items()}


# ── Conexões reutilizadas entre invocações ────────────────────────────────────

dynamodb = boto3.client('dynamodb', region_name='us-east-1')

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
}

DETALHES_TABLE  = 'Simulados_Detalhes'
SIMULADOS_TABLE = 'Simulados_AWS'


# ── Handler ───────────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    try:
        # Extrai claims do JWT (injetados pelo API Gateway HTTP API v2)
        claims = (event.get('requestContext', {})
                       .get('authorizer', {})
                       .get('jwt', {})
                       .get('claims', {}))

        aluno_id    = claims.get('sub', '')
        simulado_id = (event.get('pathParameters') or {}).get('simulado_id', '')

        if not simulado_id:
            return _resp(400, {'mensagem': "Parâmetro 'simulado_id' obrigatório na URL."})

        if not aluno_id:
            return _resp(401, {'mensagem': 'Token inválido ou ausente.'})

        print(f'Buscando simulado: aluno={aluno_id} simulado_id={simulado_id}')

        # 1. Busca o registro de detalhes na tabela Simulados_Detalhes
        resp_det = dynamodb.get_item(
            TableName=DETALHES_TABLE,
            Key={
                'PK': {'S': f'USER#{aluno_id}'},
                'SK': {'S': simulado_id},
            }
        )

        item_det = resp_det.get('Item')
        if not item_det:
            return _resp(404, {'mensagem': 'Simulado não encontrado.'})

        detalhe = deserializar(item_det)

        # Verificação de propriedade (defesa extra além do JWT)
        if detalhe.get('aluno_id') != aluno_id:
            return _resp(403, {'mensagem': 'Acesso negado.'})

        cert           = detalhe.get('cert', '')
        questoes_ids   = detalhe.get('questoes_ids', [])   # lista de SKs: ["Q#001", ...]
        respostas      = detalhe.get('respostas', {})       # {str(idx): [int, ...]}
        gabarito       = detalhe.get('gabarito', {})        # {SK: [int, ...]}

        if not questoes_ids:
            return _resp(404, {'mensagem': 'Simulado sem questões registradas.'})

        # 2. Busca o texto das questões via BatchGetItem
        keys = [
            {'PK': {'S': f'CERT#{cert}'}, 'SK': {'S': sk}}
            for sk in questoes_ids
        ]

        resp_batch = dynamodb.batch_get_item(
            RequestItems={SIMULADOS_TABLE: {'Keys': keys}}
        )

        # Trata UnprocessedKeys
        itens_raw = resp_batch['Responses'].get(SIMULADOS_TABLE, [])
        unprocessed = resp_batch.get('UnprocessedKeys', {})
        if unprocessed:
            retry = dynamodb.batch_get_item(RequestItems=unprocessed)
            itens_raw += retry['Responses'].get(SIMULADOS_TABLE, [])

        # Indexa por SK
        itens_db = {item['SK']['S']: deserializar(item) for item in itens_raw}

        # 3. Monta lista de questões com status e gabarito
        questoes_resp = []
        for idx, sk in enumerate(questoes_ids):
            item = itens_db.get(sk, {})
            resp_usuario = respostas.get(str(idx))
            resp_correta = gabarito.get(sk, [])

            # Determina status
            if resp_usuario is None:
                status = 'pulada'
            elif sorted(resp_usuario) == sorted(resp_correta):
                status = 'correta'
            else:
                status = 'errada'

            questoes_resp.append({
                'id':               sk,
                'pergunta':         item.get('pergunta', ''),
                'opcoes':           item.get('opcoes', []),
                'temas':            item.get('temas', []),
                'dificuldade':      item.get('dificuldade', ''),
                'status':           status,
                'resposta_usuario': resp_usuario,
                'resposta_correta': resp_correta,
                'explicacao':       item.get('explicacao', ''),
            })

        payload = {
            'simulado_id':    simulado_id,
            'cert':           cert,
            'data_iso':       detalhe.get('data_iso', ''),
            'score':          detalhe.get('score', 0),
            'corretas':       detalhe.get('corretas', 0),
            'erradas':        detalhe.get('erradas', 0),
            'puladas':        detalhe.get('puladas', 0),
            'total':          detalhe.get('total', 0),
            'tempo_segundos': detalhe.get('tempo_segundos'),
            'questoes':       questoes_resp,
        }

        return _resp(200, payload)

    except Exception as e:
        print(f'Erro crítico em GetSimuladoDetalhes: {e}')
        return _resp(500, {'mensagem': 'Erro interno ao buscar detalhes do simulado.'})


def _resp(status: int, body: dict) -> dict:
    return {
        'statusCode': status,
        'headers':    CORS_HEADERS,
        'body':       json.dumps(body, cls=DecimalEncoder, ensure_ascii=False),
    }
