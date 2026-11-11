---
name: auditoria-trafego
description: Auditoria completa das campanhas Meta Ads do Lucas (corretor de imóveis). Roda o time de tráfego em sequência — análise de campanhas, revisão de criativos, plano de orçamento e relatório final. Use quando pedirem "auditoria", "revisão geral das campanhas", "como estão meus anúncios" ou a checagem semanal de segunda-feira.
---

# Auditoria de Tráfego Pago

1. Leia `.claude/trafego/contexto.md`. Período padrão: últimos 7 dias (ou o informado).
2. Rode **em paralelo** (Agent tool, mesmo período e mesma conta):
   - `trafego-analista` → análise de campanhas
   - `trafego-criativos` → revisão de criativos
3. Com o resultado da análise, rode `trafego-orcamento` pedindo **apenas o plano**
   (sem aplicar nada).
4. Passe os três resultados para `trafego-relatorios` consolidar o relatório final.
5. Mostre o relatório ao Lucas e salve em `.claude/trafego/relatorios/AAAA-MM-DD-auditoria.md`.
6. Termine perguntando quais ações do plano de orçamento ele aprova. Só aplique o que ele
   aprovar, explicitamente, nesta conversa.

Se a conta não tiver campanhas com entrega no período, diga isso e ofereça montar a primeira
campanha com `trafego-copy` + `trafego-diretor-video`.
