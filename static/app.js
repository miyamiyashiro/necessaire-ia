// O navegador coleta os campos. A chave da IA permanece somente no servidor.
const $ = (id) => document.getElementById(id);
const form = $('make-form');
let planoAtual = null;
function textoValido(valor) {
  const texto = valor.trim();
  return texto.length > 0 && texto.length <= 100 && texto.toLowerCase() !== 'string' && /\p{L}/u.test(texto);
}
function separarProdutos(texto) {
  const itens = []; let atual = ''; let parenteses = 0;
  for (const c of texto) {
    if (c === '(') parenteses++;
    if (c === ')') parenteses = Math.max(0, parenteses - 1);
    if (c === '\n' || (c === ',' && parenteses === 0)) {
      if (atual.trim()) itens.push(atual.trim());
      atual = ''; if (c === '\n') parenteses = 0;
    } else atual += c;
  }
  if (atual.trim()) itens.push(atual.trim());
  return itens;
}
function resumoTempo(total, disponivel) {
  const folga = disponivel - total;
  return `Disponível: ${disponivel} min · Plano estimado: ${total} min. ` +
    (folga > 0 ? `Folga estimada: ${folga} min. Não é necessário ocupar todo o tempo disponível.` :
      'O plano ocupa o tempo disponível estimado; o ritmo de aplicação pode variar.');
}
function textoDoPlano(plano) {
  if (plano.situacao_tempo === 'insuficiente') {
    return [plano.titulo, plano.proposta, plano.orientacao_tempo,
      `Tempo disponível: ${plano.tempo_disponivel} minutos`, plano.opcao_simples,
      'Avaliação estimada por IA; o tempo varia com a prática.'].join('\n\n');
  }
  const total = plano.etapas.reduce((soma, etapa) => soma + etapa.minutos, 0);
  return [plano.titulo, plano.proposta, `Tempo estimado: ${total} minutos`,
    ...(plano.orientacao_tempo ? [`Sobre o seu tempo: ${plano.orientacao_tempo}`] : []),
    resumoTempo(total, plano.tempo_disponivel),
    ...plano.etapas.map((etapa, i) => `${i + 1}. ${etapa.produto} (${etapa.minutos} min)\n${etapa.instrucao}`),
    `Opção simples\n${plano.opcao_simples}`,
    'Sugestão gerada por IA. Os tempos são estimados; siga as indicações dos produtos.'
  ].join('\n\n');
}
$('copy-plan').addEventListener('click', async () => {
  if (!planoAtual) return;
  const planoCopiado = planoAtual;
  const texto = textoDoPlano(planoCopiado);
  $('copy-plan').disabled = true;
  try {
    await navigator.clipboard.writeText(texto);
    if (planoAtual === planoCopiado) {
      $('copy-status').textContent = 'Plano copiado! Agora é só colar onde quiser.';
      $('manual-copy').hidden = true;
    }
  } catch {
    if (planoAtual === planoCopiado) {
      $('copy-status').textContent = 'A cópia automática não está disponível. Copie o texto selecionado abaixo.';
      $('copy-text').value = texto;
      $('manual-copy').hidden = false;
      $('copy-text').focus();
      $('copy-text').select();
    }
  } finally {
    $('copy-plan').disabled = false;
  }
});
$('example').addEventListener('click', () => {
  $('ocasiao').value = 'Festa à noite';
  $('estilo').value = 'Marcante';
  $('nivel').value = 'iniciante';
  $('tempo').value = '15';
  $('produtos').value = 'corretivo, blush, máscara de cílios, batom vermelho';
  $('produtos').setCustomValidity('');
  $('ocasiao').focus();
});
for (const id of ['ocasiao', 'estilo', 'produtos']) {
  $(id).addEventListener('input', () => $(id).setCustomValidity(''));
}
function mostrarErro(message) {
  $('error').textContent = message;
  $('error').hidden = false;
  $('empty').hidden = true;
}
function mostrarPlano(plano, tempoDisponivel) {
  planoAtual = {...plano, tempo_disponivel: tempoDisponivel};
  // textContent trata a resposta como texto, sem executar HTML vindo da IA.
  $('title').textContent = plano.titulo;
  $('proposal').textContent = plano.proposta;
  $('simple-text').textContent = plano.opcao_simples;
  const total = plano.etapas.reduce((sum, etapa) => sum + etapa.minutos, 0);
  $('time-guidance').textContent = plano.orientacao_tempo || 'Os tempos são estimados e variam com sua prática.';
  const insuficiente = plano.situacao_tempo === 'insuficiente';
  $('time-summary').textContent = insuficiente ? `Tempo disponível: ${tempoDisponivel} min. Aumente o tempo ou peça um estilo mais simples.` : resumoTempo(total, tempoDisponivel);
  $('steps').hidden = insuficiente;
  $('simple-box').hidden = insuficiente;
  $('copy-plan').textContent = insuficiente ? 'Copiar orientação' : 'Copiar plano';
  $('duration').textContent = `${total} MIN ESTIMADOS · ${plano.etapas.length} ETAPAS`;
  if (insuficiente) $('duration').textContent = 'TEMPO INSUFICIENTE PARA O PEDIDO';
  $('steps').replaceChildren();
  for (const etapa of plano.etapas) {
    const li = document.createElement('li');
    const head = document.createElement('div'); head.className = 'step-head';
    const title = document.createElement('h4'); title.textContent = etapa.produto;
    const time = document.createElement('span'); time.className = 'step-time'; time.textContent = `${etapa.minutos} min`;
    const text = document.createElement('p'); text.textContent = etapa.instrucao;
    head.append(title, time); li.append(head, text); $('steps').append(li);
  }
  $('result').hidden = false;
  $('status').textContent = insuficiente ? 'Confira a orientação sobre o tempo disponível.' : 'Seu passo a passo está pronto.';
  $('result').focus({preventScroll: true});
}
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if ($('fields').disabled) return;
  for (const id of ['ocasiao', 'estilo']) {
    if (!textoValido($(id).value)) {
      $(id).setCustomValidity('Informe um texto com letras, de até 100 caracteres. Não use apenas números ou símbolos nem o exemplo string.'); $(id).reportValidity(); return;
    }
  }
  const produtos = separarProdutos($('produtos').value);
  if (!produtos.length || produtos.length > 20 || produtos.some(p => !textoValido(p))) {
    $('produtos').setCustomValidity('Informe de 1 a 20 produtos com nomes de até 100 caracteres e pelo menos uma letra (ex.: base cor 3). Não use apenas números ou símbolos nem o exemplo string.');
    $('produtos').reportValidity(); return;
  }
  const pedido = {ocasiao: $('ocasiao').value.trim(), estilo: $('estilo').value.trim(), nivel: $('nivel').value, tempo_minutos: Number($('tempo').value), produtos};
  $('fields').disabled = true;
  planoAtual = null;
  $('copy-status').textContent = '';
  $('manual-copy').hidden = true;
  $('copy-text').value = '';
  $('result-region').setAttribute('aria-busy', 'true');
  for (const id of ['empty', 'result', 'error']) $(id).hidden = true;
  $('loading').hidden = false;
  $('status').textContent = 'Preparando sua maquiagem. Aguarde.';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45000);
  try {
    const resposta = await fetch('/maquiagens', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(pedido), signal: controller.signal});
    let dados;
    try { dados = await resposta.json(); } catch { throw new Error('O servidor enviou uma resposta inesperada. Tente novamente.'); }
    if (!resposta.ok) throw new Error(typeof dados.detail === 'string' ? dados.detail : 'Não foi possível gerar o plano. Confira os campos e tente novamente.');
    if (!dados || !Array.isArray(dados.etapas) || (!dados.etapas.length && dados.situacao_tempo !== 'insuficiente')) throw new Error('O plano recebido está incompleto. Tente novamente.');
    mostrarPlano(dados, pedido.tempo_minutos);
  } catch (error) {
    const message = error.name === 'AbortError' ? 'A resposta demorou demais. Aguarde um pouco e tente novamente.' : error instanceof TypeError ? 'Não foi possível conectar ao serviço. Confira sua conexão e tente novamente em instantes.' : error.message;
    mostrarErro(message);
    $('status').textContent = 'Não foi possível concluir. Confira a mensagem de erro.';
  } finally {
    clearTimeout(timer);
    $('loading').hidden = true;
    $('fields').disabled = false;
    $('result-region').setAttribute('aria-busy', 'false');
  }
});
