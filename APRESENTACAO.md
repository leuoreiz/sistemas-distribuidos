# Roteiro de defesa individual

O professor (Kuretzki) pergunta **individualmente** e a nota varia conforme a
resposta. Conteúdo abaixo alinhado ao material da disciplina (A01 a A05).

## Resumo de 30 segundos (decore a ideia)
"É um sistema distribuído de processamento de tarefas em microsserviços. O
usuário envia uma tarefa pela API; a API publica essa tarefa numa fila no Redis;
workers independentes consomem a fila em paralelo e gravam o resultado — ou seja,
os componentes se comunicam e coordenam suas ações apenas por troca de mensagens.
Tudo em contêineres Docker, publicado em nuvem pública (Render, modelo PaaS).
Localmente eu escalo réplicas da API atrás de um load balancer Nginx para
demonstrar escalabilidade e transparência."

## Premissas de SD e como provo cada uma (termos do material)

1. **Comunicação por troca de mensagens** — é a definição de SD do slide A01: os
   componentes "coordenam suas ações apenas enviando mensagens". API e workers
   nunca se chamam direto; só trocam mensagens pela fila do Redis (`LPUSH`/`BRPOP`).
2. **Concorrência** — clico em "Enviar 10" e vários workers processam ao mesmo
   tempo; o contador de "processadas" sobe em paralelo.
3. **Escalabilidade** — `docker compose up --scale api=3 --scale worker=3`. Uso
   replicação de serviços e caching (técnicas do slide A02). Adiciono nós sem
   mexer no código.
4. **Transparência** — o material lista vários tipos; mostro:
   - *de acesso*: recursos acessados por operações idênticas (a mesma API REST);
   - *de localização*: o cliente não sabe onde o nó está (campo "Atendido por");
   - *de replicação*: várias réplicas, número transparente ao usuário.
5. **Tolerância a falhas / Confiabilidade** — redundância: se um worker cai, a
   tarefa continua na fila e outro assume; heartbeats com TTL (`worker:<id>`,
   expira em 15s) detectam quem morreu. Demonstro com `docker stop <worker>`.
6. **Heterogeneidade** — Docker empacota tudo (código, libs, runtime); roda igual
   em qualquer SO/ambiente, local ou nuvem.
7. **Abertura (openness)** — API REST com interfaces publicadas (HTTP/JSON, padrão
   aberto); a documentação automática fica em `/docs`.
8. **Compartilhamento de recursos + Consistência** — o Redis é o recurso
   compartilhado; o total de processadas usa `INCR` (operação atômica), mantendo
   o estado consistente entre todos os nós.
9. **Acoplamento fraco + ausência de relógio global** — nós stateless, sem relógio
   comum; cada um decide com informação local (conceito do slide A02).

## Conceitos de nuvem (provável cobrança — termos do material)

- **Modelo de implantação:** nuvem **pública**.
- **Modelo de serviço:** **PaaS** (Plataforma como Serviço) — pela definição do
  professor: "fornecimento de ambiente, não tem acesso total ao servidor". O
  Render entrega o ambiente; eu não gerencio o servidor.
- **5 características essenciais (NIST):** auto-serviço sob demanda (deploy via
  Git), acesso amplo via rede (HTTPS), agrupamento de recursos, rápida
  elasticidade (escala réplicas), serviço de mensuração (pay as you go).
- **Vantagens (slide A03):** pay as you go, elasticidade automática,
  escalabilidade automática, alta disponibilidade — e o material cita **Docker/
  contêineres** nominalmente como vantagem de nuvem (é exatamente o que uso).

## Perguntas prováveis e respostas

- **"Por que não usou AWS, Azure ou Google (os do material)?"** O enunciado
  permite "nuvem de sua preferência". Escolhi o Render por ser PaaS de nuvem
  pública com plano gratuito e deploy direto do Docker — e ele **roda sobre a
  infraestrutura da AWS**. Avaliei os três grandes; seriam equivalentes, mas
  exigem mais configuração e cartão de crédito para a mesma demonstração.
- **"Qual a diferença de IaaS, PaaS e SaaS aqui?"** Usei **PaaS**: recebo o
  ambiente pronto e só publico o contêiner. IaaS (ex.: AWS EC2) eu teria que
  gerenciar o servidor; SaaS seria só consumir um software pronto (ex.: Gmail).
- **"Por que Redis?"** Cumpre três papéis: fila de mensagens (broker),
  recurso/estado compartilhado (contadores atômicos) e detecção de falhas
  (chaves com TTL). Simples e rápido para a demonstração.
- **"E se chegarem 1000 requisições?"** Viram itens na fila; os workers consomem
  no ritmo deles. A fila absorve picos (desacoplamento) e eu escalo workers.
- **"E se o Redis cair?"** É o ponto central de coordenação; em produção usaria
  Redis replicado/cluster (Sentinel) para alta disponibilidade. No trabalho, o
  Redis gerenciado do Render já cuida disso.
- **"Isso é monolito ou microsserviço?"** Microsserviços: API (produtor) e worker
  (consumidor) são serviços independentes, escaláveis e implantáveis separadamente
  (acoplamento fraco).
- **"Diferença para uma aplicação tradicional (on-premises)?"** Arquitetura em
  contêineres, escalabilidade e disponibilidade sob demanda, sem comprar/gerenciar
  hardware próprio (comparação do slide A02-C1/A03).

## Checklist do dia da apresentação
- [ ] Abrir o link da nuvem ~2 min antes (evitar cold start do plano gratuito)
- [ ] Link no ar: https://sistema-distribuido-tdt8.onrender.com
- [ ] Ter o Docker rodando localmente para a demo de escala/falha (plano B)
- [ ] Saber enviar uma tarefa e mostrar o resultado "processado por"
- [ ] Saber explicar 1 premissa apontando para o arquivo no código
- [ ] Saber dizer: nuvem pública + PaaS + 5 características do NIST

---

## Respostas para os 3 pontos que podem pegar (alinhar com o material)

**1) "Por que não usou Azure, Google ou AWS, que são os do material (A05)?"**
O material apresenta os 3 grandes e o critério de seleção de fornecedor de IaaS.
Escolhi o Render porque: (a) o enunciado permite a nuvem de preferência; (b) é
**PaaS**, que é o modelo mais adequado ao meu caso — só publico o contêiner, não
gerencio servidor; (c) o Render **roda sobre a infraestrutura da AWS**, então
indiretamente uso um dos fornecedores do material; (d) tem plano gratuito e deploy
direto do Docker, sem cartão de crédito. Se fosse exigido IaaS num dos três, o
equivalente seria subir o mesmo contêiner numa instância **EC2 (AWS)** — a
arquitetura não mudaria.

**2) "E a segurança?" (A01 e A02 cobram)**
A comunicação usa **HTTPS (TLS)** fornecido pelo Render, então os dados trafegam
criptografados — atende ao "selar informações enviadas pela rede" do slide A01.
Além disso, o **Redis não fica exposto à internet** (`ipAllowList: []` no
`render.yaml`): só os serviços internos do Render o acessam. Em produção eu
adicionaria **autenticação na API** (token/chave) e **ACL no Redis**. No escopo do
trabalho, o foco foram as premissas de distribuição; segurança em profundidade
seria o próximo passo.

**3) "O que é SLA?" (A02-C1)**
SLA (Service Level Agreement / Acordo de Nível de Serviço) é o **contrato** que
define tempos de atendimento e resolução por severidade. O material reforça:
**SLA ≠ disponibilidade** — o SLA é a promessa contratual; a disponibilidade é o
quanto o sistema fica de fato no ar. Uso o plano **gratuito** do Render, que não
tem SLA garantido (inclusive hiberna após inatividade). Num plano pago haveria
SLA de uptime (ex.: 99,9%), e minha arquitetura já ajuda a cumprir disponibilidade:
réplicas da API + workers redundantes + Redis gerenciado.

---

## Roteiro cronometrado (~5 minutos)

**0:00–0:30 — Abertura.** Dizer o resumo de 30s (lá no topo deste arquivo).

**0:30–1:30 — Mostrar funcionando na nuvem.** Abrir o link, apontar o campo
"Atendido por" (transparência), clicar em **"Enviar tarefa"** e mostrar o contador
*processadas* subir de 0 → 1. Clicar em **"Enviar 10"** e mostrar várias sendo
processadas (concorrência). Recarregar a página e comentar que o nó pode mudar.

**1:30–3:00 — Explicar a arquitetura.** Desenhar/descrever o fluxo:
*você → API (produtor) → fila no Redis → workers (consumidores)*. Frase-chave:
"a API e os workers nunca se chamam direto, só trocam mensagens pela fila — é a
definição de sistema distribuído do slide A01". Apontar 3 premissas: comunicação
por mensagens, concorrência e tolerância a falhas (heartbeats com TTL).

**3:00–4:00 — Parte de nuvem.** Dizer: **nuvem pública**, modelo **PaaS** (Render
entrega o ambiente, eu não gerencio servidor — definição do A04), as **5
características do NIST** (auto-serviço, acesso via rede, agrupamento, elasticidade,
mensuração) e citar **Docker** como vantagem de nuvem (slide A03 cita nominalmente).

**4:00–5:00 — Fechamento e perguntas.** Resumir: "sistema distribuído de
microsserviços, comunicação por mensagens, escalável e tolerante a falhas, rodando
em nuvem pública PaaS". Estar pronto para as 3 perguntas acima.
