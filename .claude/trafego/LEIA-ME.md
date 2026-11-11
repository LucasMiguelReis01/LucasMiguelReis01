# Time de Tráfego Pago (Meta Ads)

Adaptado do pacote "time-de-trafego-pago v1.1.1" para o Claude Code nativo:
- usa o **conector Meta** do Claude (sem token, sem `.env`, sem `node instalar.js`);
- métricas de **imóveis** (custo por lead) no lugar de ROAS de e-commerce;
- nada é alterado na conta sem a sua aprovação.

| Agente | Quem | Para quê |
|---|---|---|
| `trafego-analista` | Trace 📊 | Analisa campanhas (melhores, piores, período) |
| `trafego-orcamento` | Buck 💰 | Escalar, pausar, redistribuir verba |
| `trafego-criativos` | Cris 🎨 | Criativos bons, saturados e ruins |
| `trafego-relatorios` | Rex 📋 | Relatório semanal, mensal, resumo executivo |
| `trafego-copy` | Ada ✍️ | Textos de anúncio e variações A/B |
| `trafego-diretor-video` | Cleo 🎬 | Brief, ganchos e roteiro de Reels |

Skill: **`/auditoria-trafego`** — roda o time inteiro e entrega o relatório + plano.

## Como pedir (em português normal)
- "Analisa minhas campanhas da última semana"
- "Faz a auditoria de tráfego"
- "Cria 3 anúncios para o Green Village focando em sem Serasa"
- "Me dá 5 ganchos de Reels para os lotes"
- "Relatório do mês"

Contas, produto e metas ficam em `contexto.md` — edite ali quando algo mudar.
