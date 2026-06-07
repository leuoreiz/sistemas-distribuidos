"""
Módulo compartilhado: conexão com Redis e identidade da instância.

Redis é o ponto central da arquitetura distribuída:
  - Fila de mensagens (message broker)  -> comunicação produtor/consumidor
  - Estado compartilhado / contadores    -> consistência entre nós
  - Heartbeats com TTL                    -> detecção de falhas
"""
import os
import socket
import uuid

import redis

# URL do Redis (no Render vem da variável de ambiente; local usa docker-compose)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Identidade única desta instância/contêiner.
# Mostra "qual nó" atendeu cada requisição -> transparência e balanceamento de carga.
INSTANCE_ID = os.getenv("INSTANCE_ID") or f"{socket.gethostname()}-{uuid.uuid4().hex[:6]}"

# Nomes das chaves no Redis
QUEUE_KEY = "tarefas:fila"             # lista usada como fila FIFO
PROCESSED_KEY = "tarefas:processadas"  # contador atômico de tarefas concluídas
TASK_KEY = "tarefa:{}"                 # hash com o estado de cada tarefa
WORKER_KEY = "worker:{}"               # heartbeat de cada worker (com TTL)

# Pool de conexões reutilizável (decode_responses -> strings em vez de bytes)
_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)
