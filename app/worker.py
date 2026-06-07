"""
Worker (consumidor) — processa tarefas da fila de forma assíncrona.

Premissas de sistemas distribuídos demonstradas aqui:
  - Concorrência:        vários workers consomem a mesma fila em paralelo.
  - Tolerância a falhas:  se um worker cai, a tarefa volta/permanece na fila e
                          outro worker assume; heartbeats com TTL detectam quedas.
  - Comunicação por mensagens: produtor e consumidor só conversam via Redis,
                          sem chamar um ao outro diretamente (baixo acoplamento).
  - Ausência de relógio global: cada worker trabalha de forma independente.
"""
import json
import threading
import time

from common import (
    INSTANCE_ID,
    PROCESSED_KEY,
    QUEUE_KEY,
    TASK_KEY,
    WORKER_KEY,
    get_redis,
)

HEARTBEAT_TTL = 15  # segundos: se o worker não renovar, é considerado "morto"


def _processar(tarefa: dict) -> dict:
    """Simula um processamento pesado (ex.: cálculo, render, ETL)."""
    n = int(tarefa.get("numero", 0))
    tempo = float(tarefa.get("custo_seg", 1.0))
    time.sleep(tempo)  # simula latência de trabalho real
    resultado = sum(i * i for i in range(n + 1))  # algum cálculo determinístico
    return {"resultado": resultado, "processado_por": INSTANCE_ID}


def loop(stop_event: threading.Event | None = None) -> None:
    r = get_redis()
    print(f"[worker {INSTANCE_ID}] iniciado, escutando a fila '{QUEUE_KEY}'", flush=True)
    while stop_event is None or not stop_event.is_set():
        # heartbeat: prova de vida deste worker (TTL detecta falhas)
        r.set(WORKER_KEY.format(INSTANCE_ID), int(time.time()), ex=HEARTBEAT_TTL)

        # BRPOP bloqueia até chegar uma tarefa (ou timeout de 5s p/ renovar heartbeat)
        item = r.brpop(QUEUE_KEY, timeout=5)
        if not item:
            continue

        _, payload = item
        tarefa = json.loads(payload)
        task_id = tarefa["id"]
        chave = TASK_KEY.format(task_id)

        r.hset(chave, mapping={"status": "processando", "worker": INSTANCE_ID})
        try:
            saida = _processar(tarefa)
            r.hset(chave, mapping={"status": "concluida", **{k: str(v) for k, v in saida.items()}})
            r.incr(PROCESSED_KEY)  # contador atômico -> consistência entre nós
            print(f"[worker {INSTANCE_ID}] tarefa {task_id} concluída", flush=True)
        except Exception as e:  # tolerância a falhas: marca erro sem derrubar o worker
            r.hset(chave, mapping={"status": "erro", "erro": str(e)})
            print(f"[worker {INSTANCE_ID}] erro na tarefa {task_id}: {e}", flush=True)


def start_background_worker() -> threading.Event:
    """Sobe o worker numa thread (usado quando API e worker rodam no mesmo serviço)."""
    stop = threading.Event()
    threading.Thread(target=loop, args=(stop,), daemon=True).start()
    return stop


if __name__ == "__main__":
    loop()
