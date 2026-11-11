# Instruções do projeto

## Time de tráfego pago (Meta Ads)
Quando o Lucas chamar um agente pelo nome (ex.: "Trace, analise…", "Ada, cria…"),
delegue para o subagente correspondente com a ferramenta Agent, passando o pedido completo:

| Nome | subagent_type |
|---|---|
| Trace | `trafego-analista` |
| Buck | `trafego-orcamento` |
| Cris | `trafego-criativos` |
| Rex | `trafego-relatorios` |
| Ada | `trafego-copy` |
| Léo | `trafego-video` |
| Vera | `trafego-compliance` |

- "Gestor, …", "rode o fluxo completo", "revisão da semana" ou qualquer pedido sobre anúncios
  sem nome de agente → use a skill **gestor**.
- Toda copy da Ada e todo roteiro do Léo passam pela Vera antes de ir ao ar.
- Nenhuma mudança na conta (pausar, ativar, orçamento, criar) sem o "sim" explícito do Lucas.
- Contexto do negócio, contas e metas: `.claude/trafego/contexto.md`.
- Comandos prontos: `.claude/trafego/comandos.md`.
