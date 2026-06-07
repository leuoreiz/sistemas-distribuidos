# Sistema Distribuído de Processamento de Tarefas

Aplicação de microsserviços que demonstra **todas as premissas de sistemas
distribuídos** e está pronta para publicação em nuvem pública (Render).

```
            ┌──────────────┐        publica tarefa         ┌─────────┐
 navegador ─► Load Balancer ─► API (N réplicas) ──────────► │  Redis  │
            │   (Nginx)    │ ◄── estatísticas/estado ─────  │ (fila + │
            └──────────────┘                                │ estado) │
                                                            └────┬────┘
                                          consome a fila    ┌────▼────────┐
                                          em paralelo  ◄──  │ Workers (N) │
                                                            └─────────────┘
```

## Premissas de sistemas distribuídos atendidas

Terminologia alinhada ao material da disciplina (linha Coulouris).

| Premissa | Onde está no código |
|---|---|
| **Comunicação por troca de mensagens** | produtor/consumidor só conversam via fila no Redis — a própria definição de SD do material |
| **Concorrência** | múltiplos workers consomem a fila em paralelo (`worker.py`) |
| **Escalabilidade** | `--scale api=N --scale worker=N` (replicação de serviços + caching no Redis) |
| **Transparência** (acesso, localização, replicação) | cliente acessa 1 endereço; não sabe qual nó respondeu (`INSTANCE_ID`) |
| **Tolerância a falhas / Confiabilidade** | tarefa permanece na fila se um worker cai; heartbeats com TTL detectam quedas |
| **Heterogeneidade** | contêineres Docker rodam em qualquer SO/ambiente |
| **Abertura (openness)** | API REST com interfaces publicadas (padrão aberto HTTP/JSON; `/docs`) |
| **Compartilhamento de recursos + Consistência** | estado e contadores atômicos (`INCR`) no Redis |
| **Acoplamento fraco + ausência de relógio global** | nós stateless decidem com informação local |
| **Balanceamento de carga** (técnica de escalabilidade) | `nginx/nginx.conf` distribui entre as réplicas (round-robin) |

## Rodar localmente (demonstração completa)

Pré-requisito: Docker Desktop.

```bash
cd sistema-distribuido
docker compose up --build --scale api=3 --scale worker=3
```

Acesse **http://localhost:8080**. Recarregue a página: o campo *"Atendido por"*
muda → o load balancer está alternando entre as réplicas da API.

**Demonstrar tolerância a falhas:** com tudo rodando, derrube um worker e veja
a fila continuar sendo consumida pelos demais:

```bash
docker compose ps                       # veja os nomes dos workers
docker stop <nome-de-um-worker>
```

## Publicar na nuvem

Veja o passo a passo em [DEPLOY.md](DEPLOY.md).

## Estrutura

```
sistema-distribuido/
├── app/
│   ├── main.py        API (produtor) + interface web
│   ├── worker.py      worker (consumidor)
│   ├── common.py      conexão Redis e identidade da instância
│   ├── Dockerfile
│   └── requirements.txt
├── nginx/nginx.conf   load balancer (uso local)
├── docker-compose.yml demonstração local multi-réplica
└── render.yaml        infraestrutura como código (deploy na nuvem)
```
