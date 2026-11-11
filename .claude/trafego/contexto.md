# Contexto do Time de Tráfego Pago — Reis Imóveis

Todos os agentes de tráfego (`trafego-*`) leem este arquivo antes de trabalhar.
Atualize aqui quando mudar conta, empreendimento ou metas.

## Negócio
- **Quem:** Lucas Miguel — corretor de imóveis (Reis Imóveis), Mogi das Cruzes / Alto Tietê (SP).
- **Produto atual:** Green Village I (bairro Santo Ângelo, Mogi) — lotes de 250 a 406 m².
  - A partir de R$ 70 mil (250 m²) · R$ 112 mil (320 m²).
  - Negociação direta com proprietários, **sem banco e sem consulta ao Serasa**.
  - Entrada de R$ 20 mil; aceita carro ou moto como parte da entrada (mediante avaliação).
  - Escassez real: acompanhe quantos lotes restam em `green-village-video/legenda-instagram.md`.
- **Canal de conversão:** WhatsApp (11) 93700-4295 e direct do Instagram ("comenta EU QUERO").
- **Material existente:** vídeo Reels em `green-village-video/` (`green-village-reels.mp4`).

## Perfil do negócio (o Gestor pergunta o que estiver _pendente_ e preenche aqui)
- Ticket médio do que vende: lotes a partir de R$ 70 mil (Green Village I).
- Objetivo dos anúncios: mensagem no WhatsApp / direct. _(confirmar se também quer formulário)_
- Investimento em anúncios: R$ 50 para começar (teste inicial, nov/2026). Prefere gastar pouco.
- Meta de custo por lead (quanto aceita pagar por contato): _pendente_
- A conta de anúncios já foi bloqueada alguma vez? _pendente_
- CRECI (para identificação nos anúncios, se quiser): _pendente_

## Contas Meta Ads (via conector Meta — sem token, sem .env)
| Conta | ID | Observação |
|---|---|---|
| Lucas Miguel | 624644153259329 | **Conta padrão** — única com forma de pagamento |
| Lucas Miguel Corretor de Imóveis | 1754950432339329 | Sem forma de pagamento |
| (sem nome) | 951637804071439 | Sem empresa vinculada, sem pagamento |

Moeda: BRL. Orçamento diário mínimo: R$ 5,49.

## Métricas que importam (imóveis ≠ e-commerce)
Venda de imóvel não acontece dentro do Meta, então **ROAS não serve** como métrica principal.
Use, nesta ordem:
1. **CPL** — custo por lead (cadastro, conversa no WhatsApp ou mensagem no direct).
2. **Volume de leads** por dia/semana.
3. **CTR (link)** — meta > 1,5%; abaixo de 0,7% o criativo está fraco.
4. **CPM** — sobe muito = público pequeno/saturado.
5. **Frequência** — acima de 3 em 7 dias = criativo saturado.
6. **Qualidade do lead** — só o Lucas sabe; pergunte quando for decidir escala.

Referência inicial de CPL para lote econômico no interior de SP: R$ 5–25 (mensagem) e
R$ 15–50 (formulário). Ajuste com os dados reais da conta assim que houver histórico.

## Regras de segurança (valem para todos os agentes)
- **Nunca** criar, ativar, pausar, excluir ou mudar orçamento sem mostrar o plano e receber
  um "sim" explícito do Lucas na conversa.
- Anúncios novos são criados **pausados** até a aprovação final.
- Escalar no máximo **20% do orçamento por vez**, com 48 h entre aumentos.
- Nada de promessas proibidas pela Meta (crédito garantido, "aprovação sem análise") e
  sempre mantenha o asterisco das condições ("sujeito a negociação").
- Ao criar campanha, verifique se a Meta exige a **Categoria Especial de Anúncio (Habitação)**
  para a conta/país (use `ads_get_help_article` se tiver dúvida). Com ela, segmentação por
  idade, gênero e raio pequeno fica limitada — planeje o público considerando isso.
- Nunca peça nem grave tokens/senhas em arquivos.
