# Necessaire IA

Assistente de maquiagem que cria um passo a passo com os produtos que a pessoa já possui, considerando ocasião, estilo, experiência e tempo. Projeto da categoria **Geração de Conteúdo**.

## Funcionalidades e validação

API Python implementada, com documentação interativa para experimentar no navegador. Integração Gemini confirmada em 24/09/2026 com uma consulta real: HTTP 200, quatro produtos informados e etapas somando 15 minutos. Novas instalações precisam configurar chave e modelo no .env. Testes usam respostas simuladas explicitamente; não comprovam a qualidade de uma IA real. Interface disponível em http://127.0.0.1:8000/, com formulário, carregamento, mensagens de erro e etapas organizadas.

## Entenda o caminho

Pessoa preenche pedido → FastAPI valida os campos → servidor envia pedido ao Gemini → servidor confere o JSON, os produtos das etapas e o tempo total → pessoa recebe o plano.

- `main.py`: campos, rotas, prompt e chamada à IA.
- `exemplo.json`: pedido pronto para testar.
- `.env`: configuração privada (você cria a partir de `.env.example`).
- `test_api.py`: testes locais sem gastar créditos de IA.

API é a parte que recebe pedidos e devolve respostas. Uma rota é um endereço dessa API. JSON é um formato de dados com campos e valores. Prompt é o conjunto de instruções que enviamos ao modelo.

## Executar no Windows

Com Python 3.11 ou superior instalado (testado também com Python 3.14 no Windows), obtenha o projeto:

```powershell
git clone https://github.com/miyamiyashiro/necessaire-ia.git
cd necessaire-ia
```

Crie o ambiente e instale as bibliotecas, uma linha de cada vez:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Se `.env` já existir, preserve-o. Abra esse arquivo localmente e preencha `GEMINI_API_KEY` com sua própria chave e `GEMINI_MODEL` com um modelo disponível na sua conta. Nos testes de 24/09/2026, usamos `gemini-3.1-flash-lite` com sucesso. Disponibilidade e quotas podem mudar.

Em seguida, inicie:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

Abra http://127.0.0.1:8000/ para usar o formulário. Mantenha o terminal aberto enquanto utiliza a aplicação. Alterações no `.env` exigem reiniciar o servidor.

Abra http://127.0.0.1:8000/docs. Essa é a página de testes da API. Expanda `POST /maquiagens`, clique em **Try it out**, cole o conteúdo de `exemplo.json` e clique em **Execute**.

Sem configurar a IA, esse pedido retorna 503 com uma orientação. Isso é esperado; a aplicação não finge que gerou conteúdo. `GET /saude` funciona sem chave. Pare o servidor com Ctrl+C.

## Conectar a IA

Obtenha sua chave no Google AI Studio e consulte os modelos disponíveis para sua conta. Confira quotas e custos antes de usar. No arquivo `.env`, preencha `GEMINI_API_KEY` e `GEMINI_MODEL`, depois reinicie o servidor. Não envie a chave em conversas, slides ou no GitHub.

Documentação oficial: https://ai.google.dev/gemini-api/docs/api-key

Saída estruturada usada nesta implementação: https://ai.google.dev/gemini-api/docs/generate-content/structured-output

FastAPI e validação do pedido: https://fastapi.tiangolo.com/tutorial/body/

## Rotas e variáveis

| Rota | O que faz |
|---|---|
| GET / | Abre a interface do Necessaire IA |
| GET /saude | Indica que o servidor responde e se existe uma chave configurada (não valida a chave) |
| POST /maquiagens | Gera um plano a partir do pedido |
| GET /docs | Documenta campos e permite fazer pedidos |

| Variável | Uso |
|---|---|
| GEMINI_API_KEY | Chave privada, apenas no servidor |
| GEMINI_MODEL | Identificador do modelo com suporte a saída estruturada |

## Regras e erros

Textos: 1–100 caracteres, sem aceitar espaços vazios. Produtos: 1–20 itens. Tempo: inteiro de 5–120 minutos. Nível: iniciante, intermediario ou avancado. Corpo do pedido limitado a 16 KB, inclusive quando enviado em partes.

400: campos inválidos; 404: rota inexistente; 413: pedido grande demais; 429: limite do provedor; 502: resposta incompleta/inválida da IA; 503: configuração ausente ou IA indisponível; 504: tempo de espera excedido.

O prompt separa regras dos dados e limita a tarefa à maquiagem. A validação garante os nomes dos produtos nas etapas e o tempo total, mas não garante que todo o texto livre esteja correto. Revisão com pedidos reais, incluindo tentativas de desviar as instruções, ainda é necessária. Não fazemos diagnóstico de pele nem prometemos segurança para alergias.

## Testar

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Os testes simulam o provedor para verificar sucesso, erros, timeout e respostas incorretas. Para demonstrar essas falhas, execute os testes e explique que são simulações; não apresente isso como falha real do Gemini.

## Cenários verificados

- Consulta real: festa à noite, quatro produtos e 15 minutos; resposta 200.
- Consulta real: faculdade, blush e batom rosa, cinco minutos; resposta 200.
- Tempo zero: resposta 400, identificando tempo_minutos.
- Tentativa de mudar a tarefa para receita de bolo: manteve maquiagem no teste observado. Isso não garante resistência a qualquer prompt injection.
- Revisão do prompt após sugestão de usar batom como blush: novos exemplos respeitaram as regiões de aplicação. Conteúdo livre ainda pode conter erros.
- Laboratório local: 429, 503 e 504 reproduzidos sem consultar o Gemini.
- 11 testes automatizados da API e arquivos públicos, com provedor simulado.

O programa é executado localmente; publicar o código no GitHub não hospeda a aplicação. Cada pessoa que executar consultas reais precisa configurar seu acesso ao Gemini. Não há autenticação de usuários ou limitação local de requisições: o servidor está previsto para demonstração local, não para exposição pública sem adaptações.

## Roteiro de apresentação

2 min: problema e público. 3 min: fluxo da API, prompt e regras. 5 min: demonstração. 3 min: entradas inválidas e falhas simuladas identificadas. 2 min: perguntas. As duas integrantes devem entender o fluxo e a proteção da chave.

## Interface

Abra http://127.0.0.1:8000/ com o servidor rodando. Use Preencher com um exemplo e depois Criar meu passo a passo.

- `static/index.html`: estrutura do formulário e da área de resultado.
- `static/style.css`: cores, espaçamentos e adaptação para celular.
- `static/app.js`: monta o JSON, envia à mesma rota POST /maquiagens e apresenta a resposta.

A interface bloqueia envios duplicados durante o carregamento, mantém os campos após uma falha e apresenta o conteúdo da IA como texto (sem executar HTML). Não armazena a chave nem faz acesso direto ao Gemini.

## Demonstração reproduzível de falhas

Mantenha o servidor principal na porta 8000. Abra outro terminal nesta pasta e execute:

```powershell
.\.venv\Scripts\python.exe -m uvicorn demo:app --host 127.0.0.1 --port 8001
```

Abra http://127.0.0.1:8001/demonstracao. Escolha limite (429), demora (504) ou indisponibilidade (503). Todos os resultados são explicitamente simulados. O transporte HTTPX é substituído por MockTransport somente neste processo separado, sem acesso ao Gemini, usando credenciais fictícias. A mesma função consultar_ia trata o erro; o laboratório não retorna mensagens prontas por uma rota alternativa. O timeout é provocado após dois segundos para abreviar a apresentação, não representa uma espera real de 35 segundos. O timeout total continua coberto pelo limite no código; esta simulação exercita o tratamento de ReadTimeout.

Explique antes de executar: "Agora vamos simular falhas do provedor para demonstrar a resposta da nossa API." Mostre carregamento, código HTTP, mensagem legível e uma segunda execução para demonstrar que o servidor segue disponível. Ctrl+C encerra apenas o servidor do terminal selecionado.
