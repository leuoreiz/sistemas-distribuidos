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
- [ ] Abrir o link da nuvem ~1 min antes (evitar cold start do plano gratuito)
- [ ] Ter o Docker rodando localmente para a demo de escala/falha (plano B)
- [ ] Saber enviar uma tarefa e mostrar o resultado "processado por"
- [ ] Saber explicar 1 premissa apontando para o arquivo no código
- [ ] Saber dizer: nuvem pública + PaaS + 5 características do NIST
