# Necessaire IA — Trabalho 1

API Web em Python que integra o Gemini para gerar um plano de maquiagem com os produtos disponíveis, considerando ocasião, estilo, experiência e tempo. Categoria: **Geração de Conteúdo**.

**Esta entrega e sua apresentação têm foco no backend. O consumo da API é demonstrado pelo Swagger.** A interface experimental em `static/` está preservada no repositório, mas não é necessária para acompanhar a demonstração do Trabalho 1. Não há deploy público: a execução é local.

## Arquitetura

Pedido JSON pelo Swagger → validação com Pydantic → prompt e consulta HTTP ao Gemini → validação do JSON retornado, produtos das etapas e tempo total → resposta HTTP.

- `main.py`: modelos, rotas, prompt, integração e tratamento de erros.
- `demo.py`: processo separado que simula falhas do provedor, usando o mesmo tratamento de erros.
- `test_api.py`: testes automatizados sem consultas reais ao Gemini.
- `exemplo.json`: pedido válido para a demonstração.
- `.env.example`: modelo de configuração sem segredos.
- `requirements.txt`: dependências com versões definidas.
- `static/`: interface experimental preservada, fora do foco desta apresentação.

Tecnologias: Python, FastAPI, Pydantic, HTTPX, Uvicorn e python-dotenv.

## Executar no Windows

Pré-requisitos: Python 3.11 ou superior (testado com 3.12 e 3.14), Git e acesso à API Gemini para as consultas reais.

```powershell
git clone https://github.com/miyamiyashiro/necessaire-ia.git
cd necessaire-ia
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Na primeira configuração, copie `.env.example` para `.env`. **Se `.env` já existir, preserve-o.**

```powershell
Copy-Item .env.example .env
```

Preencha localmente:

```dotenv
GEMINI_API_KEY=sua_chave_privada
GEMINI_MODEL=gemini-3.1-flash-lite
```

O modelo acima funcionou nos testes de setembro de 2026. Disponibilidade, quotas e custos dependem do provedor e da conta. Obtenha sua própria chave no [Google AI Studio](https://aistudio.google.com/apikey). Não publique o `.env`, nem exponha a chave em prints, slides ou no código. O `.gitignore` exclui o `.env`, ambientes virtuais e caches.

Inicie o backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Abra **http://127.0.0.1:8000/docs**. Mantenha o terminal aberto; Ctrl+C encerra o servidor. Reinicie-o após alterar o `.env`. O parâmetro `--reload` é destinado ao desenvolvimento local.

## Rotas

| Método e rota | Função |
|---|---|
| GET `/saude` | Verifica se a API responde e se há uma chave não vazia configurada. Não valida a chave nem consulta o Gemini. |
| POST `/maquiagens` | Recebe o pedido, consulta o Gemini e retorna o plano validado. |
| GET `/docs` | Swagger: documentação interativa para testar as rotas. |
| GET `/openapi.json` | Especificação da API. |

`/saúde` foi mantido como alias de compatibilidade, fora do Swagger. A raiz `/` ainda abre a interface experimental, que não será usada na apresentação.

A aplicação não armazena planos. Por isso não possui operações de atualização ou exclusão de planos (PUT/DELETE).

## Pedido e resposta

No Swagger, expanda POST `/maquiagens`, clique em **Try it out**, use o exemplo e clique em **Execute**:

```json
{
  "ocasiao": "Festa à noite",
  "estilo": "Marcante",
  "nivel": "iniciante",
  "tempo_minutos": 15,
  "produtos": ["corretivo", "blush", "máscara de cílios", "batom vermelho"]
}
```

A resposta 200 contém `titulo`, `proposta`, `etapas` (produto, instrução e minutos) e `opcao_simples`. O texto varia entre gerações. A aplicação confere os nomes dos produtos declarados nas etapas e se a soma dos minutos não ultrapassa o tempo solicitado.

## Validações e erros

- `ocasiao` e `estilo`: textos de 1 a 100 caracteres; espaços nas pontas são removidos.
- `nivel`: exatamente `iniciante`, `intermediario` ou `avancado`.
- `tempo_minutos`: inteiro de 5 a 120; texto, booleano e número decimal são recusados.
- `produtos`: lista de 1 a 20 textos não vazios, até 100 caracteres cada.
- O literal `string` e textos compostos apenas por caracteres invisíveis são recusados nos campos de entrada textual.
- Campos extras, ausentes ou de tipo incorreto são recusados antes da consulta ao Gemini.
- O POST exige Content-Type JSON e limita o corpo a 16.000 bytes, inclusive quando recebido em partes.
- A resposta da IA precisa seguir a estrutura de `Plano`; textos vazios, campos extras, produtos de etapas fora da lista e tempo excedido são recusados.

| Código | Significado |
|---|---|
| 200 | Plano gerado e aprovado nas verificações implementadas. |
| 400 | Entrada inválida ou JSON malformado; a mensagem identifica os campos. |
| 404 | Rota inexistente. |
| 405 | Método HTTP inadequado para a rota. |
| 413 | Corpo maior que o permitido. |
| 415 | Tipo de conteúdo diferente de JSON. |
| 429 | O provedor informou limite de uso. |
| 500 | Falha interna inesperada, com mensagem genérica sem detalhes sensíveis no corpo HTTP. |
| 502 | Resposta inesperada/inválida da IA ou formato da consulta rejeitado pelo provedor. |
| 503 | Configuração ausente/inválida, acesso recusado, modelo ausente, conexão indisponível ou falha do serviço. |
| 504 | Timeout da consulta. Há limite total de 35 segundos e timeout HTTP de 30 segundos. |

Os códigos internos do provedor não são todos repassados diretamente: por exemplo, um 403 do Gemini indica problema na credencial do servidor, não uma proibição ao usuário da nossa API, e resulta em 503 com orientação.

## Testes automatizados

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Na revisão de 27/09/2026, **25 testes passaram**, vários contendo múltiplos casos. Cobrem entradas inválidas e limites, JSON/UTF-8 incorretos, corpo enviado em partes, respostas malformadas do provedor, rede, timeout HTTP e total, códigos de erro, proteção das mensagens e arquivos públicos. O provedor é simulado nesses testes.

Também foram observadas consultas reais bem-sucedidas: festa com quatro produtos em 15 minutos e faculdade com blush e batom rosa em cinco minutos. Uma tentativa de desviar o estilo para uma receita de bolo manteve a tarefa no exemplo testado; isso não garante resistência a qualquer ataque.

## Demonstrar falhas pelo Swagger

A API real trata 429, 503 e 504 quando eles ocorrem. Para apresentar o tratamento sem esgotar quotas ou depender de uma indisponibilidade real, use um processo separado. **A falha do provedor é simulada; o tratamento de erros é o mesmo da aplicação.**

Abra outro terminal nesta pasta:

```powershell
.\.venv\Scripts\python.exe -m uvicorn demo:app --host 127.0.0.1 --port 8001
```

Abra **http://127.0.0.1:8001/docs**, cujo título identifica a simulação. Expanda POST `/maquiagens`, clique em **Try it out** e envie um pedido válido. No campo de cabeçalho `X-Demo-Scenario`, escolha:

| Cenário | Falha simulada | Retorno esperado |
|---|---|---|
| `limite` | Gemini responde 429 | 429 |
| `demora` | Cliente HTTP gera ReadTimeout | 504 |
| `indisponivel` | Gemini responde 503 | 503 |

O transporte HTTPX é substituído por `MockTransport` somente no processo demo. Nenhuma chamada sai para o Gemini e são usadas credenciais fictícias. A espera é abreviada para dois segundos: não equivale a esperar o limite real de 35 segundos, que tem teste automatizado próprio. Reinicie o servidor demo ao alterar seu código.

Explique antes: “Vamos simular uma falha do provedor para verificar como nossa API responde.” Não apresente esses cenários como incidentes reais. A API normal permanece na porta 8000. Pedidos inválidos continuam sendo recusados antes da consulta simulada.

## Limites conhecidos

- Não existe um catálogo para validar semanticamente qualquer nome de cosmético. Bloquear `string` não resolve todo texto sem sentido.
- O prompt delimita a tarefa e orienta usos adequados, mas não garante ausência de alucinações ou resistência absoluta a prompt injection.
- A verificação de produtos examina os nomes declarados nas etapas; as instruções, proposta e alternativa simples continuam sendo texto livre e podem conter erros.
- Não há autenticação ou limite local por usuário/IP. O 429 é o limite informado pelo provedor, não uma contagem de cliques no Swagger.
- O projeto foi preparado para execução e demonstração locais; exposição pública exige adaptações.

## Apresentação do Trabalho 1 — 15 minutos

1. **Introdução (2 min):** problema, público e categoria Geração de Conteúdo.
2. **Arquitetura e prompt (3 min):** modelos de entrada/saída, regras, chave no ambiente e chamada ao Gemini.
3. **Demonstração (5 min):** GET de saúde e POST válido pelo Swagger, explicando pedido e resposta.
4. **Erros e limites (3 min):** entrada inválida na API real e falhas do provedor identificadas como simulações no Swagger da porta 8001.
5. **Perguntas (2 min):** decisões e limitações.

Entregar o link do repositório, este README e o material de apresentação. A demonstração real depende de internet e quota do Gemini. A interface experimental não faz parte deste roteiro.

## Referências

- [FastAPI: corpo do pedido](https://fastapi.tiangolo.com/tutorial/body/)
- [Gemini: chaves de API](https://ai.google.dev/gemini-api/docs/api-key)
- [Gemini: respostas estruturadas](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
