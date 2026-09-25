const el = id => document.getElementById(id);
el('demo-form').addEventListener('submit', async event => {
  event.preventDefault();
  el('run').disabled = true;
  el('cenario').disabled = true;
  el('demo-result').hidden = true;
  el('demo-loading').hidden = false;
  el('demo-status').textContent = 'Simulação em andamento. Aguarde…';
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const check = await fetch('/demo-status', {signal:controller.signal});
    if (!check.ok || (await check.json()).simulacao !== true) throw new Error('Servidor incorreto');
    const resposta = await fetch('/maquiagens', {method:'POST', headers:{'Content-Type':'application/json','X-Demo-Scenario':el('cenario').value}, body:JSON.stringify({ocasiao:'Faculdade durante o dia',estilo:'Natural',nivel:'iniciante',tempo_minutos:5,produtos:['blush','batom rosa']}), signal:controller.signal});
    const dados = await resposta.json();
    el('code').textContent = `HTTP ${resposta.status} · SIMULADO`;
    el('message').textContent = typeof dados.detail === 'string' ? dados.detail : 'Resposta inesperada. Confira se abriu o servidor demo na porta 8001.';
    el('explanation').textContent = 'O servidor respondeu com uma mensagem legível e continua disponível. Você pode executar outro cenário.';
    el('demo-result').hidden = false;
    el('demo-status').textContent = 'Simulação concluída.';
  } catch {
    el('demo-status').textContent = 'Não foi possível concluir. Confira se o servidor de demonstração está rodando na porta 8001.';
  } finally {
    clearTimeout(timer);
    el('demo-loading').hidden = true;
    el('run').disabled = false;
    el('cenario').disabled = false;
  }
});
