"""Servidor separado de demonstração. Nunca consulta o Gemini.
Execute: python -m uvicorn demo:app --host 127.0.0.1 --port 8001
"""
import asyncio
import os

# Somente neste processo: credenciais fictícias para passar pela validação inicial.
os.environ['GEMINI_API_KEY'] = 'simulacao-sem-chave-real'
os.environ['GEMINI_MODEL'] = 'modelo-simulado'

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from main import app, transporte_ia, STATIC_DIR

app.title = 'Necessaire IA - SIMULAÇÃO LOCAL'


def transporte_simulado(request: Request):
    cenario = request.headers.get('X-Demo-Scenario', 'limite')
    if cenario not in {'limite', 'demora', 'indisponivel'}:
        raise HTTPException(400, 'Escolha um cenário válido de simulação.')

    async def responder(requisicao):
        # Este transporte intercepta a chamada: nenhum dado sai para o Gemini.
        await asyncio.sleep(2)
        if cenario == 'demora':
            raise httpx.ReadTimeout('Timeout simulado', request=requisicao)
        status = 429 if cenario == 'limite' else 503
        return httpx.Response(status, json={'error': {'message': 'Falha simulada'}}, request=requisicao)

    return httpx.MockTransport(responder)


app.dependency_overrides[transporte_ia] = transporte_simulado


@app.get('/demonstracao', include_in_schema=False)
def demonstracao():
    return FileResponse(STATIC_DIR / 'demo.html')


@app.get('/demo-status', include_in_schema=False)
def demo_status():
    return {'simulacao': True}
