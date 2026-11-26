# Roteiro de ensaio — Trabalho 2

Este roteiro orienta a fala e a demonstração; não é um conjunto de slides.

## 00:00–02:00 — Problema e evolução

Explique o público: pessoas que precisam montar uma maquiagem com os produtos e o tempo disponíveis. Categoria: Geração e Produtividade.

Sugestão de fala: “Na primeira parte construímos a API e mostramos pelo Swagger. Agora o usuário preenche uma página, recebe um plano organizado e pode copiá-lo. Publicamos o sistema no Render.”

## 02:00–05:00 — Arquitetura e deploy

Mostre o fluxo: navegador → API FastAPI → Gemini → validação → resultado.

- HTML estrutura o formulário, CSS adapta o layout e JavaScript envia o JSON e mostra o resultado.
- O Render hospeda frontend e backend juntos. `/maquiagens` é uma rota do mesmo domínio.
- Pydantic valida o pedido antes da IA. HTTPX realiza a consulta externa.
- O prompt define escopo e orientações. O código verifica estrutura, produtos declarados nas etapas e soma do tempo.
- `GEMINI_API_KEY` e `GEMINI_MODEL` ficam no ambiente do servidor. Nunca abra os valores secretos durante a apresentação.
- Não treinamos um modelo: integramos um modelo existente.

## 05:00–10:00 — Demonstração pública

Abra https://necessaire-ia.onrender.com (não localhost).

1. Preencha o exemplo de festa, estilo marcante, iniciante, 15 minutos e quatro produtos.
2. Gere uma vez e mostre o carregamento e o bloqueio de novos envios durante a espera.
3. Explique título, proposta, produtos, minutos e opção simples. Confira a soma do tempo.
4. Clique em Copiar plano e cole em um editor vazio previamente aberto.
5. Se houver tempo, reduza a largura da janela e mostre a organização em coluna.

Uma geração completa é suficiente; reserve tempo para a espera da IA. Uma captura anterior pode servir de apoio caso o provedor falhe, mas identifique-a como resultado anterior.

## 10:00–13:00 — Resiliência, segurança e limites

Na página pública, envie `string` no estilo e mostre o aviso. Corrija o campo. Mostre também tempo abaixo de 5 ou campo obrigatório vazio. A recusa no navegador evita uma chamada desnecessária, mas o backend valida novamente porque a API pode ser acessada diretamente.

Se quiser demonstrar uma resposta HTTP real da validação, use o Swagger público e envie `tempo_minutos: 0`: o backend deve retornar 400.

Explique:

- 429: limite informado pelo Gemini, não quantidade de cliques contada pelo nosso site.
- 504: timeout; o limite total da consulta externa é 35 segundos.
- 503: falha de conexão, disponibilidade ou configuração.
- A tela mostra a mensagem e libera o formulário para tentar novamente.
- Há testes automatizados com respostas controladas para falhas do provedor. Não apresente simulações como erros reais ocorridos na nuvem.
- O demo.py é apoio local separado. Ele não é uma rota de simulação publicada no site principal.
- JSON válido não garante uma orientação perfeita: o texto da IA tem limitações.
- Não temos autenticação nem limite próprio por usuário/IP; isso é uma melhoria pendente para controlar abuso e quota.

Não provoque esgotamento de quota nem remova a chave do serviço público para fabricar um erro. Se usar o laboratório local como apoio, avise explicitamente que saiu da produção e está simulando.

## 13:00–15:00 — Encerramento e perguntas

Resumo de fala: “Entregamos o fluxo completo de uma ferramenta de geração: entrada validada, consulta à IA, resultado estruturado, cópia e acesso público.”

Perguntas para ensaiar:

- Por que frontend e backend juntos? Simplifica a hospedagem e a comunicação no mesmo domínio.
- Onde fica a chave? No ambiente do servidor; o navegador chama nossa API.
- Por que não há banco ou PUT/DELETE? O sistema gera planos e não mantém um cadastro de planos.
- Por que validar a resposta da IA? A geração pode produzir uma estrutura ou valores inadequados.
- O que acontece se o Render estiver dormindo? O primeiro acesso aguarda a retomada do serviço gratuito.
- Os testes chamam o Gemini? Os automatizados simulam o provedor; a geração pública foi testada separadamente.

## Antes da banca

- Testar a URL pública com antecedência e conferir a quota.
- Abrir site, Swagger, editor vazio e material de apoio.
- Fechar .env e telas com segredos ou informações pessoais.
- Conferir também em celular real e registrar o resultado.
- Ensaiar com cronômetro: demonstração aos 5 minutos e perguntas aos 13.
- Ambas as integrantes devem entender todo o fluxo, mesmo dividindo as falas.
