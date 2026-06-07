# Deploy na nuvem (Render) — passo a passo

A nuvem escolhida foi o **Render** por ter plano gratuito, deploy direto a
partir do Docker e geração automática de **link público com HTTPS**.

> Tempo estimado: ~10 minutos. Não precisa cartão de crédito no plano free.

## Pré-requisitos
- Conta no GitHub (gratuita)
- Conta no Render: https://render.com (pode entrar com o GitHub)

## Passo 1 — Subir o código para o GitHub

Dentro da pasta `sistema-distribuido`:

```bash
git init
git add .
git commit -m "Sistema distribuído de processamento de tarefas"
git branch -M main
git remote add origin https://github.com/<SEU_USUARIO>/sistema-distribuido.git
git push -u origin main
```

(Crie o repositório vazio antes em https://github.com/new)

## Passo 2 — Criar a infraestrutura no Render (via Blueprint)

1. Acesse https://dashboard.render.com
2. Clique em **New +** → **Blueprint**
3. Conecte o repositório que você acabou de subir
4. O Render lê o arquivo `render.yaml` e mostra os recursos que vai criar:
   - `sistema-distribuido` (serviço web)
   - `fila-redis` (Redis gerenciado)
5. Clique em **Apply**

O Render vai construir a imagem Docker e iniciar tudo. A variável `REDIS_URL`
é injetada automaticamente (definida no `render.yaml`).

## Passo 3 — Pegar o link público

Quando o serviço web ficar **"Live"**, o Render mostra a URL no topo, algo como:

```
https://sistema-distribuido.onrender.com
```

**Esse é o link que você entrega ao professor.** Abra para confirmar que o
sistema está operando na nuvem.

## Observações importantes (para a apresentação)

- **Cold start:** no plano gratuito o serviço "hiberna" após ~15 min sem uso e
  leva alguns segundos para acordar no primeiro acesso. **Abra o link ~1 minuto
  antes de apresentar** para já estar quente.
- **Worker na nuvem:** no plano free, API e worker rodam no mesmo serviço
  (`RUN_EMBEDDED_WORKER=true`), então o fluxo *produtor → fila → consumidor*
  funciona normalmente na nuvem.
- **Réplicas / load balancer:** para mostrar escalabilidade horizontal e
  balanceamento com vários nós de verdade, use a demonstração local
  (`docker compose ... --scale api=3 --scale worker=3`). Na nuvem isso exigiria
  plano pago (múltiplas instâncias). Vale citar isso na apresentação.

## Alternativas equivalentes
O mesmo projeto sobe em **Railway** (detecta o Dockerfile automaticamente) ou
**Fly.io** (`fly launch`) caso prefira — a arquitetura não muda.
