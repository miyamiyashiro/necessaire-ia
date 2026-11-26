# Necessaire IA — Trabalho 2

Aplicação web com frontend em HTML, CSS e JavaScript e API em Python (FastAPI + Gemini) que monta um passo a passo de maquiagem
personalizado a partir dos produtos que a pessoa já tem, da ocasião, do estilo,
do nível de experiência e do tempo disponível.

## Aplicação publicada

- **Site:** https://necessaire-ia.onrender.com
- **API/Swagger:** https://necessaire-ia.onrender.com/docs
- **Saúde:** https://necessaire-ia.onrender.com/saude
- **Categoria:** Geração e Produtividade.

O usuário preenche o formulário, acompanha o carregamento, recebe etapas organizadas e pode copiar o plano completo. O formulário orienta a correção de entradas inválidas e mostra mensagens de falha sem exigir uma recarga da página.

## Arquitetura

Navegador (HTML/CSS/JavaScript) → POST /maquiagens em JSON → FastAPI/Pydantic → consulta HTTPS ao Gemini com HTTPX → validação do plano → JSON → resultado na interface.

Frontend e backend são servidos pelo mesmo Web Service no Render. O navegador usa a rota relativa `/maquiagens`, sem endereço localhost fixo e sem precisar de CORS entre domínios diferentes. A chave é usada somente no backend. O texto gerado é inserido com `textContent`, sem executar HTML da IA.

Na parte 1, o foco era consumir a API pelo Swagger. Na parte 2, o fluxo inclui formulário, carregamento, erros visuais, cópia do resultado e hospedagem pública com HTTPS.

- `main.py`: modelos, rotas, prompt, integração e tratamento de erros.
- `demo.py`: processo separado que simula falhas do provedor, usando o mesmo tratamento de erros.
- `test_api.py`: testes automatizados sem consultas reais ao Gemini.
- `exemplo.json`: pedido válido para a demonstração.
- `.env.example`: modelo de configuração sem segredos.
- `requirements.txt`: dependências com versões definidas.
- `static/`: frontend da aplicação: formulário, estilos responsivos, consulta à API e cópia do plano.

Tecnologias: Python, FastAPI, Pydantic, HTTPX, Uvicorn e python-dotenv.

## Executar no Windows

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

Abra **http://127.0.0.1:8000/** para usar o site ou **http://127.0.0.1:8000/docs** para testar a API. Mantenha o terminal aberto; Ctrl+C encerra o servidor. Reinicie-o após alterar o `.env`. O parâmetro `--reload` é destinado ao desenvolvimento local.

## Deploy no Render

Crie um **Web Service** conectado a este repositório:

| Configuração | Valor |
|---|---|
| Branch | `main` |
| Runtime | Python 3 |
| Root Directory | Vazio (arquivos na raiz do repositório) |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Compute | Free |

Configure duas variáveis **separadas** em Environment Variables:

| Nome (KEY) | Conteúdo (VALUE) |
|---|---|
| `GEMINI_API_KEY` | Chave privada da API Gemini |
| `GEMINI_MODEL` | Nome do modelo habilitado na conta; nesta implantação, `gemini-3.1-flash-lite` |

O nome é o texto antes do `=` no `.env`; o valor é o texto depois. Não envie o arquivo `.env` ao GitHub. Salve as variáveis e aplique um novo deploy. A mensagem de configuração do código ainda menciona `.env`, mas na nuvem as variáveis da plataforma substituem esse arquivo.

O plano gratuito pode suspender o serviço por inatividade: o primeiro acesso pode demorar para carregar. Confira o site antes da apresentação. Quotas da hospedagem e do Gemini são independentes; o funcionamento depende de disponibilidade e quota do provedor.

## Rotas

| Método e rota | Função |
|---|---|
| GET `/saude` | Verifica se a API responde e se há uma chave não vazia configurada. Não valida a chave nem consulta o Gemini. |
| POST `/maquiagens` | Recebe o pedido, consulta o Gemini e retorna o plano validado. |
| GET `/docs` | Swagger: documentação interativa para testar as rotas. |
| GET `/openapi.json` | Especificação da API. |

`/saúde` foi mantido como alias de compatibilidade, fora do Swagger. A raiz `/` abre a interface usada na demonstração da aplicação completa.

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

A resposta 200 contém `titulo`, `proposta`, `etapas` (produto, instrução e minutos) `opcao_simples`, `orientacao_tempo` e `situacao_tempo`. O texto varia entre gerações. A aplicação confere os nomes dos produtos declarados nas etapas e se a soma dos minutos não ultrapassa o tempo solicitado.

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

Na execução local de 26/11/2026, **33 testes passaram**, vários contendo múltiplos casos. Cobrem entradas inválidas e limites, JSON/UTF-8 incorretos, corpo enviado em partes, respostas malformadas do provedor, rede, timeout HTTP e total, códigos de erro, proteção das mensagens e arquivos públicos. O provedor é simulado nesses testes.

Também foram observadas consultas reais bem-sucedidas: festa com quatro produtos em 15 minutos e faculdade com blush e batom rosa em cinco minutos. Uma tentativa de desviar o estilo para uma receita de bolo manteve a tarefa no exemplo testado; isso não garante resistência a qualquer ataque.

## Verificação em produção

Em 21/11/2026, a responsável pelo projeto confirmou manualmente na URL pública:

- Geração de plano com integração ao Gemini e apresentação do resultado.
- Cópia do plano e colagem em editor de texto.
- Recusa de `string`, campo vazio e tempo abaixo de 5 minutos.
- Nova geração após corrigir os dados inválidos.

A adaptação a janela estreita foi conferida anteriormente na execução local. A usuária também confirmou o funcionamento em celular real. Os testes automatizados e as simulações de falhas não equivalem a ter observado todos os erros em produção.

## Demonstrar falhas pelo Swagger (apoio local)

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

## Adequação do tempo

O tempo disponível é um teto, não uma meta a preencher. A IA avalia o acabamento e o nível de experiência. `situacao_tempo` distingue `adequado`, `tempo_de_sobra` e `insuficiente`.

Quando o pedido não cabe, a resposta 200 contém uma orientação e `etapas: []`: a tela mostra o aviso, convida a aumentar o tempo ou pedir um estilo mais simples e permite copiar a orientação. Não gera automaticamente outra maquiagem nem mostra zero minutos ou folga. Nos demais casos, etapas são obrigatórias e a soma deve caber no tempo. A interface e a cópia calculam a folga apenas para planos viáveis.

Falta de produtos não deve ser classificada como falta de tempo: a IA deve montar o plano possível com o estoque e explicar as limitações na proposta. Um item composto (ex.: sombra preta e batom vermelho escuro) mantém o nome inteiro nas etapas para preservar a validação de produtos.

A avaliação de viabilidade continua dependendo do modelo; muitos produtos disponíveis não obrigam seu uso. As vírgulas dentro de parênteses são preservadas no formulário (ex.: sombras (azul, roxo, brilho)).

Em 26/11/2026, uma consulta real com festa, estilo marcante, nível iniciante, 5 minutos e os produtos do caso relatado retornou aviso sem etapas. Os testes automatizados verificam o contrato e rejeitam combinações incoerentes de situação e etapas; não garantem todas as avaliações da IA.

Os campos ocasião, estilo e cada produto precisam conter pelo menos uma letra. Entradas como `3`, `123` ou apenas símbolos são bloqueadas no formulário e retornam 400 na API antes de consultar o Gemini. Nomes como `base cor 3` continuam válidos. Isso não substitui validação semântica de cosméticos.

## Limites conhecidos

- Não existe um catálogo para validar semanticamente qualquer nome de cosmético. Bloquear `string` não resolve todo texto sem sentido.
- O prompt delimita a tarefa e orienta usos adequados, mas não garante ausência de alucinações ou resistência absoluta a prompt injection.
- A verificação de produtos examina os nomes declarados nas etapas; as instruções, proposta e alternativa simples continuam sendo texto livre e podem conter erros.
- Não há autenticação ou limite local por usuário/IP. O 429 é o limite informado pelo provedor, não uma contagem de cliques no Swagger.
- A aplicação está publicada para demonstração acadêmica. Sem autenticação ou limitador próprio, a API pública pode consumir a quota compartilhada da chave; esse controle permanece uma melhoria pendente.
- Não há persistência de planos: recarregar a página remove o resultado da tela. Use Copiar plano para guardar o texto.

## Apresentação — 15 minutos

O roteiro detalhado está em [APRESENTACAO_PARTE_2.md](APRESENTACAO_PARTE_2.md).

1. Visão geral e evolução: 2 minutos.
2. Arquitetura full stack, deploy e prompt: 3 minutos.
3. Demonstração na URL pública: 5 minutos.
4. Resiliência, segurança e limites: 3 minutos.
5. Perguntas e encerramento: 2 minutos.

## Referências

- [FastAPI: corpo do pedido](https://fastapi.tiangolo.com/tutorial/body/)
- [Gemini: chaves de API](https://ai.google.dev/gemini-api/docs/api-key)
- [Gemini: respostas estruturadas](https://ai.google.dev/gemini-api/docs/generate-content/structured-output)
