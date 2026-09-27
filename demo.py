"""Servidor separado de demonstração. Nunca consulta o Gemini.
Execute: python -m uvicorn demo:app --host 127.0.0.1 --port 8001
"""
import asyncio
import os
from typing import Literal

# Somente neste processo: credenciais fictícias para passar pela validação inicial.
os.environ['GEMINI_API_KEY'] = 'simulacao-sem-chave-real'
os.environ['GEMINI_MODEL'] = 'modelo-simulado'

import httpx
from fastapi import Header
from fastapi.responses import FileResponse
from main import app, transporte_ia, STATIC_DIR

app.title = 'Necessaire IA - SIMULAÇÃO LOCAL'


def transporte_simulado(cenario: Literal['limite', 'demora', 'indisponivel'] = Header(default='limite', alias='X-Demo-Scenario')):

    async def responder(requisicao):
        # Este transporte intercepta a chamada: nenhum dado sai para o Gemini.
        await asyncio.sleep(2)
        if cenario == 'demora':
            raise httpx.ReadTimeout('Timeout simulado', request=requisicao)
        status = 429 if cenario == 'limite' else 503
        return httpx.Response(status, json={'error': {'message': 'Falha simulada'}}, request=requisicao)

    return httpx.MockTransport(responder)


app.dependency_overrides[transporte_ia] = transporte_simulado

# A dependência sobrescrita não aparece automaticamente no OpenAPI.
openapi_original = app.openapi

def openapi_demo():
    schema = openapi_original()
    parametros = schema['paths']['/maquiagens']['post'].setdefault('parameters', [])
    if not any(p['name'] == 'X-Demo-Scenario' for p in parametros):
        parametros.append({'name': 'X-Demo-Scenario', 'in': 'header', 'required': False,
                           'description': 'Cenário simulado; não consulta o Gemini.',
                           'schema': {'type': 'string', 'enum': ['limite', 'demora', 'indisponivel'], 'default': 'limite'}})
    return schema

app.openapi = openapi_demo


@app.get('/demonstracao', include_in_schema=False)
def demonstracao():
    return FileResponse(STATIC_DIR / 'demo.html')


@app.get('/demo-status', include_in_schema=False)
def demo_status():
    return {'simulacao': True}
