"""
API Gateway (produtor) + interface web.

Premissas de sistemas distribuídos demonstradas aqui:
  - Escalabilidade horizontal: várias réplicas desta API atrás de um load balancer.
  - Balanceamento de carga + transparência: cada resposta mostra qual INSTANCE_ID
    atendeu; o cliente não sabe (nem precisa saber) qual nó respondeu.
  - Comunicação por mensagens: a API só publica tarefas na fila do Redis.
  - Consistência: estatísticas vêm de contadores atômicos compartilhados no Redis.
"""
import json
import os
import time
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from common import (
    INSTANCE_ID,
    PROCESSED_KEY,
    QUEUE_KEY,
    TASK_KEY,
    WORKER_KEY,
    get_redis,
)
from worker import HEARTBEAT_TTL, start_background_worker

app = FastAPI(title="Sistema Distribuído de Processamento de Tarefas")
r = get_redis()

# No plano gratuito da nuvem rodamos API + worker no mesmo serviço (worker embutido).
# Local (docker-compose) os workers são contêineres separados e escaláveis.
if os.getenv("RUN_EMBEDDED_WORKER", "true").lower() == "true":
    start_background_worker()


class NovaTarefa(BaseModel):
    numero: int = 1000
    custo_seg: float = 1.0


@app.get("/health")
def health():
    """Health check usado pelo load balancer / nuvem para detectar falhas."""
    try:
        r.ping()
        return {"status": "ok", "instancia": INSTANCE_ID}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/api/info")
def info():
    return {"instancia": INSTANCE_ID}


@app.post("/api/tarefas")
def criar_tarefa(t: NovaTarefa):
    task_id = uuid.uuid4().hex[:8]
    tarefa = {"id": task_id, "numero": t.numero, "custo_seg": t.custo_seg}
    r.hset(TASK_KEY.format(task_id), mapping={"status": "na_fila", "recebido_por": INSTANCE_ID})
    r.lpush(QUEUE_KEY, json.dumps(tarefa))  # publica na fila (produtor)
    return {"id": task_id, "status": "na_fila", "recebido_por": INSTANCE_ID}


@app.get("/api/tarefas/{task_id}")
def status_tarefa(task_id: str):
    dados = r.hgetall(TASK_KEY.format(task_id))
    if not dados:
        raise HTTPException(status_code=404, detail="tarefa não encontrada")
    return {"id": task_id, **dados}


@app.get("/api/stats")
def stats():
    # Workers ativos = chaves de heartbeat ainda vivas (TTL não expirou)
    agora = int(time.time())
    workers = []
    for chave in r.scan_iter(match=WORKER_KEY.format("*")):
        visto = int(r.get(chave) or 0)
        workers.append({"id": chave.split("worker:")[1], "ha_segundos": agora - visto})
    return {
        "instancia_que_respondeu": INSTANCE_ID,
        "tarefas_na_fila": r.llen(QUEUE_KEY),
        "tarefas_processadas": int(r.get(PROCESSED_KEY) or 0),
        "workers_ativos": sorted(workers, key=lambda w: w["id"]),
        "heartbeat_ttl_seg": HEARTBEAT_TTL,
    }


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


HTML = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sistema Distribuído de Tarefas</title>
<style>
  :root{color-scheme:dark}
  body{font-family:system-ui,Segoe UI,Roboto,sans-serif;margin:0;background:#0f1226;color:#e8eaf6}
  header{padding:24px;background:#1a1f3a;border-bottom:1px solid #2b3160}
  h1{margin:0;font-size:20px} .sub{color:#9aa3d0;font-size:13px;margin-top:4px}
  main{max-width:880px;margin:0 auto;padding:24px;display:grid;gap:20px}
  .card{background:#171b34;border:1px solid #2b3160;border-radius:12px;padding:20px}
  .grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
  .stat{background:#10142b;border-radius:10px;padding:14px;text-align:center}
  .stat b{display:block;font-size:28px;color:#7c9cff} .stat span{font-size:12px;color:#9aa3d0}
  button{background:#5468ff;color:#fff;border:0;padding:10px 16px;border-radius:8px;cursor:pointer;font-size:14px}
  button:hover{background:#6a7bff} label{font-size:13px;color:#9aa3d0;margin-right:6px}
  input{background:#10142b;border:1px solid #2b3160;color:#e8eaf6;border-radius:6px;padding:6px;width:70px}
  table{width:100%;border-collapse:collapse;font-size:13px} td,th{padding:6px;border-bottom:1px solid #2b3160;text-align:left}
  .tag{font-family:monospace;background:#10142b;padding:2px 6px;border-radius:5px;color:#7c9cff}
  .ok{color:#56d364}.proc{color:#e3b341}.fila{color:#9aa3d0}
</style></head>
<body>
<header>
  <h1>🌐 Sistema Distribuído de Processamento de Tarefas</h1>
  <div class="sub">Atendido por: <span id="inst" class="tag">...</span> — recarregue: o nó pode mudar (balanceamento de carga)</div>
</header>
<main>
  <div class="card">
    <div class="grid">
      <div class="stat"><b id="fila">0</b><span>na fila</span></div>
      <div class="stat"><b id="proc">0</b><span>processadas</span></div>
      <div class="stat"><b id="wk">0</b><span>workers ativos</span></div>
    </div>
  </div>
  <div class="card">
    <label>Tamanho do cálculo (n):</label><input id="numero" type="number" value="50000">
    <label>Custo (s):</label><input id="custo" type="number" step="0.5" value="2">
    <button onclick="enviar()">➕ Enviar tarefa</button>
    <button onclick="enviarMuitas()">⚡ Enviar 10 (ver concorrência)</button>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Workers ativos (heartbeats)</h3>
    <table id="tw"><tr><th>worker</th><th>visto há</th></tr></table>
  </div>
  <div class="card">
    <h3 style="margin-top:0">Tarefas recentes</h3>
    <table id="tt"><tr><th>id</th><th>status</th><th>processada por</th></tr></table>
  </div>
</main>
<script>
const vistas = [];
async function tick(){
  const s = await (await fetch('/api/stats')).json();
  document.getElementById('inst').textContent = s.instancia_que_respondeu;
  document.getElementById('fila').textContent = s.tarefas_na_fila;
  document.getElementById('proc').textContent = s.tarefas_processadas;
  document.getElementById('wk').textContent = s.workers_ativos.length;
  document.getElementById('tw').innerHTML = '<tr><th>worker</th><th>visto há</th></tr>' +
    s.workers_ativos.map(w=>`<tr><td class="tag">${w.id}</td><td>${w.ha_segundos}s</td></tr>`).join('');
  for(const id of vistas.slice(-8)){
    const t = await (await fetch('/api/tarefas/'+id)).json();
    const cls = t.status==='concluida'?'ok':(t.status==='processando'?'proc':'fila');
    document.getElementById('row-'+id).innerHTML =
      `<td class="tag">${id}</td><td class="${cls}">${t.status}</td><td>${t.processado_por||'-'}</td>`;
  }
}
async function enviar(){
  const numero = +document.getElementById('numero').value;
  const custo_seg = +document.getElementById('custo').value;
  const r = await (await fetch('/api/tarefas',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({numero,custo_seg})})).json();
  vistas.push(r.id);
  const tr = document.createElement('tr'); tr.id='row-'+r.id;
  tr.innerHTML=`<td class="tag">${r.id}</td><td class="fila">na_fila</td><td>-</td>`;
  document.getElementById('tt').appendChild(tr);
}
async function enviarMuitas(){ for(let i=0;i<10;i++) await enviar(); }
setInterval(tick, 1500); tick();
</script>
</body></html>
"""
