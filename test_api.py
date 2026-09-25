import json
import os
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi.testclient import TestClient
from main import app

PEDIDO = {'ocasiao': 'festa', 'estilo': 'simples', 'nivel': 'iniciante', 'tempo_minutos': 10, 'produtos': ['batom']}
PLANO = {'titulo': 'Batom em destaque', 'proposta': 'Uma proposta simples.', 'etapas': [{'produto': 'batom', 'instrucao': 'Aplique nos labios.', 'minutos': 2}], 'opcao_simples': 'Use uma camada leve do batom.'}

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.env = patch.dict(os.environ, {'GEMINI_API_KEY': 'chave-ficticia', 'GEMINI_MODEL': 'modelo-teste'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def resposta(self, status=200, plano=None):
        return httpx.Response(status, json={'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(plano or PLANO)}]}}]})

    def enviar(self, response):
        with patch('main.httpx.AsyncClient.post', new_callable=AsyncMock, return_value=response) as chamada:
            resultado = self.client.post('/maquiagens', json=PEDIDO)
            config = chamada.call_args.kwargs['json']['generationConfig']
            self.assertEqual(config['responseMimeType'], 'application/json')
            self.assertIn('responseJsonSchema', config)
            self.assertNotIn('responseFormat', config)
            return resultado

    def test_sucesso(self):
        r = self.enviar(self.resposta())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['etapas'][0]['produto'], 'batom')

    def test_entrada_invalida_nao_consulta_ia(self):
        with patch('main.consultar_ia', new_callable=AsyncMock) as consulta:
            for dados in [dict(PEDIDO, produtos=[]), dict(PEDIDO, ocasiao='   '), dict(PEDIDO, tempo_minutos=0), dict(PEDIDO, nivel='outro')]:
                self.assertEqual(self.client.post('/maquiagens', json=dados).status_code, 400)
            consulta.assert_not_called()

    def test_limite_corpo(self):
        self.assertEqual(self.client.post('/maquiagens', content=b'x' * 16001).status_code, 413)

    def test_json_invalido(self):
        self.assertEqual(self.client.post('/maquiagens', content='{', headers={'Content-Type': 'application/json'}).status_code, 400)

    def test_sem_chave(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            self.assertEqual(self.client.post('/maquiagens', json=PEDIDO).status_code, 503)

    def test_erros_provedor(self):
        for recebido, esperado in [(429, 429), (500, 503), (403, 503), (401, 503), (404, 503), (400, 502)]:
            self.assertEqual(self.enviar(self.resposta(recebido)).status_code, esperado)

    def test_timeout_e_rede(self):
        for erro, status in [(httpx.ReadTimeout('timeout'), 504), (httpx.ConnectError('rede'), 503)]:
            with patch('main.httpx.AsyncClient.post', new_callable=AsyncMock, side_effect=erro):
                self.assertEqual(self.client.post('/maquiagens', json=PEDIDO).status_code, status)

    def test_produto_e_tempo_invalidos(self):
        for etapa in [dict(PLANO['etapas'][0], produto='base'), dict(PLANO['etapas'][0], minutos=11)]:
            self.assertEqual(self.enviar(self.resposta(plano=dict(PLANO, etapas=[etapa]))).status_code, 502)

    def test_resposta_malformada(self):
        self.assertEqual(self.enviar(httpx.Response(200, json={'candidates': []})).status_code, 502)
        self.assertEqual(self.enviar(self.resposta(plano={'titulo': 'incompleto'})).status_code, 502)

    def test_interface_e_arquivos_publicos(self):
        self.assertIn('text/html', self.client.get('/').headers['content-type'])
        for path in ['/static/style.css', '/static/app.js']:
            self.assertEqual(self.client.get(path).status_code, 200)
        self.assertEqual(self.client.get('/static/../.env').status_code, 404)
        self.assertEqual(self.client.get('/.env').status_code, 404)
        respostas = self.client.get('/openapi.json').json()['paths']['/maquiagens']['post']['responses']
        self.assertIn('400', respostas)
        self.assertIn('503', respostas)

    def test_saude_docs_e_404(self):
        self.assertEqual(self.client.get('/saude').status_code, 200)
        self.assertEqual(self.client.get('/docs').status_code, 200)
        self.assertEqual(self.client.get('/inexistente').status_code, 404)

if __name__ == '__main__':
    unittest.main()
