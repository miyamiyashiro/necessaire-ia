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

    def test_placeholder_recusado_antes_da_ia(self):
        with patch('main.consultar_ia', new_callable=AsyncMock) as consulta:
            casos = [dict(PEDIDO, ocasiao='string'), dict(PEDIDO, estilo=' STRING '),
                     dict(PEDIDO, produtos=['batom', ' string '])]
            for pedido in casos:
                resposta = self.client.post('/maquiagens', json=pedido)
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('Substitua', resposta.json()['detail'])
            consulta.assert_not_called()

    def test_exemplo_swagger_valido(self):
        from main import Pedido
        schema = self.client.get('/openapi.json').json()
        exemplo = schema['components']['schemas']['Pedido']['examples'][0]
        self.assertEqual(Pedido.model_validate(exemplo).produtos[0], 'corretivo')

    def test_limite_corpo(self):
        self.assertEqual(self.client.post('/maquiagens', content=b'x' * 16001, headers={'Content-Type': 'application/json'}).status_code, 413)

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

class AuditoriaErros(unittest.TestCase):
    setUp = TestAPI.setUp
    resposta = TestAPI.resposta
    enviar = TestAPI.enviar
    def test_matriz_entradas_invalidas(self):
        casos = [
            ('nivel', 'Profissional'), ('nivel', None), ('nivel', 'Iniciante'),
            ('ocasiao', ''), ('ocasiao', ' '*10), ('ocasiao', 123),
            ('ocasiao', 'x'*101), ('ocasiao', '\u200b'), ('estilo', None),
            ('tempo_minutos', True), ('tempo_minutos', '15'), ('tempo_minutos', 5.5),
            ('tempo_minutos', 4), ('tempo_minutos', 121),
            ('produtos', 'blush'), ('produtos', [None]), ('produtos', ['']),
            ('produtos', ['x'*101]), ('produtos', ['blush']*21),
            ('produtos', [1]), ('produtos', ['\u200b']),
        ]
        with patch('main.consultar_ia', new_callable=AsyncMock) as consulta:
            for campo, valor in casos:
                with self.subTest(campo=campo, valor=valor):
                    r = self.client.post('/maquiagens', json=dict(PEDIDO, **{campo:valor}))
                    self.assertEqual(r.status_code, 400)
                    self.assertTrue(r.json()['erros'])
            consulta.assert_not_called()

    def test_campos_ausentes_extras_e_corpo_errado(self):
        with patch('main.consultar_ia', new_callable=AsyncMock) as consulta:
            for body in [{}, [], 'texto', dict(PEDIDO, desconhecido='valor')]:
                with self.subTest(body=body):
                    self.assertEqual(self.client.post('/maquiagens', json=body).status_code, 400)
            self.assertEqual(self.client.post('/maquiagens', content='', headers={'Content-Type':'application/json'}).status_code,400)
            consulta.assert_not_called()

    def test_limites_validos(self):
        from main import Pedido
        for tempo in [5,120]:
            self.assertEqual(Pedido.model_validate(dict(PEDIDO,tempo_minutos=tempo)).tempo_minutos,tempo)
        self.assertEqual(len(Pedido.model_validate(dict(PEDIDO,produtos=['batom']*20)).produtos),20)
        self.assertEqual(len(Pedido.model_validate(dict(PEDIDO,ocasiao='a'*100)).ocasiao),100)

    def test_nivel_mensagem_especifica(self):
        r=self.client.post('/maquiagens',json=dict(PEDIDO,nivel='Profissional'))
        self.assertIn('iniciante, intermediario ou avancado',r.json()['detail'])

    def test_content_type_e_utf8(self):
        for tipo in ['text/plain','application/x-www-form-urlencoded']:
            self.assertEqual(self.client.post('/maquiagens',content='{}',headers={'Content-Type':tipo}).status_code,415)
        r=self.client.post('/maquiagens',content=b'\xff',headers={'Content-Type':'application/json'})
        self.assertEqual(r.status_code,400)
        self.assertIn('UTF-8',r.json()['detail'])

    def test_corpo_em_blocos_sem_content_length(self):
        self.assertEqual(self.client.post('/maquiagens', content=iter([b'a'*8000,b'b'*8001]),headers={'Content-Type':'application/json'}).status_code,413)

    def test_envelopes_inesperados(self):
        casos=[[], None, {'candidates':[None]}, {'candidates':{}},
               {'candidates':[{'finishReason':'STOP','content':None}]},
               {'candidates':[{'finishReason':'STOP','content':{'parts':[None]}}]},
               {'candidates':[{'finishReason':'STOP','content':{'parts':[{'text':123}]}}]},
               {'candidates':[{'finishReason':'STOP','content':{'parts':[]}}]},
               {'candidates':[{'finishReason':'SAFETY'}]}]
        for body in casos:
            with self.subTest(body=body):
                self.assertEqual(self.enviar(httpx.Response(200, content=json.dumps(body))).status_code,502)
        self.assertEqual(self.enviar(httpx.Response(200,content='<html>falha</html>')).status_code,502)
        self.assertEqual(self.enviar(httpx.Response(302,headers={'Location':'https://example.com'})).status_code,502)

    def test_texto_vazio_extra_e_duracao_invalida_na_saida(self):
        casos=[dict(PLANO,proposta='   '), dict(PLANO,opcao_simples=' '), dict(PLANO,extra='surpresa'),
               dict(PLANO,etapas=[dict(PLANO['etapas'][0],instrucao=' ')]),
               dict(PLANO,etapas=[dict(PLANO['etapas'][0],minutos=True)]),
               dict(PLANO,etapas=[dict(PLANO['etapas'][0],minutos=0)])]
        for plano in casos:
            with self.subTest(plano=plano):
                self.assertEqual(self.enviar(self.resposta(plano=plano)).status_code,502)

    def test_nao_vaza_erro_do_provedor(self):
        r=self.enviar(httpx.Response(403,json={'error':{'message':'segredo-superprivado'}}))
        self.assertNotIn('segredo-superprivado',r.text)
        self.assertNotIn('chave-ficticia',r.text)

    def test_timeout_total(self):
        import asyncio
        timeout_original=asyncio.timeout
        async def lento(*args,**kwargs):
            await asyncio.sleep(0.2)
        with patch('main.asyncio.timeout', side_effect=lambda _: timeout_original(0.01)), patch('main.httpx.AsyncClient.post',side_effect=lento):
            self.assertEqual(self.client.post('/maquiagens',json=PEDIDO).status_code,504)

    def test_falha_inesperada_controlada(self):
        with patch('main.consultar_ia',side_effect=RuntimeError('segredo-superprivado')):
            with TestClient(app,raise_server_exceptions=False) as client:
                r=client.post('/maquiagens',json=PEDIDO)
                self.assertEqual(r.status_code,500)
                self.assertNotIn('segredo-superprivado',r.text)
                self.assertIn('erro interno',r.json()['detail'])

    def test_rotas_metodos_saude_e_configuracao(self):
        self.assertEqual(self.client.get('/saúde').status_code,200)
        self.assertEqual(self.client.get('/maquiagens').status_code,405)
        self.assertEqual(self.client.get('/nada').json()['detail'],'Rota não encontrada.')
        for chave,modelo in [('  ','modelo'),('teste',''),('teste','../modelo')]:
            with patch.dict(os.environ,{'GEMINI_API_KEY':chave,'GEMINI_MODEL':modelo}), patch('main.httpx.AsyncClient.post',new_callable=AsyncMock) as chamada:
                self.assertEqual(self.client.post('/maquiagens',json=PEDIDO).status_code,503)
                chamada.assert_not_called()
        with patch.dict(os.environ,{'GEMINI_API_KEY':'   '}):
            self.assertFalse(self.client.get('/saude').json()['ia_configurada'])


if __name__ == '__main__':
    unittest.main()
