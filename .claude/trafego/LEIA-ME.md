# Time de Tráfego Pago (Meta Ads)

Adaptado do pacote "time-de-trafego-pago v1.1.1" + Gestor, para o Claude Code nativo:
- usa o **conector Meta** do Claude (sem token, sem `.env`, sem `node instalar.js`);
- métricas de **imóveis** (custo por lead) no lugar de ROAS de e-commerce;
- nada é alterado na conta sem a sua aprovação.

## Fale só com o Gestor
**`/gestor`** (ou só peça em português normal) — ele entende o pedido, chama o time na ordem
certa e devolve uma resposta só: RESUMO · O QUE FAZER AGORA · O QUE EU PREPAREI · POSSO EXECUTAR?

| Agente | Quem | Para quê |
|---|---|---|
| `trafego-analista` | Trace 📊 | Analisa campanhas (o que performa, o que queima dinheiro) |
| `trafego-orcamento` | Buck 💰 | Escalar, pausar, redistribuir verba |
| `trafego-criativos` | Cris 🎨 | Criativos bons, saturados e ruins |
| `trafego-relatorios` | Rex 📋 | Relatório semanal, mensal, resumo executivo |
| `trafego-copy` | Ada ✍️ | Textos de anúncio em 3 versões |
| `trafego-video` | Léo 🎬 | Ganchos e roteiros de Reels |
| `trafego-compliance` | Vera 🛡️ | Compliance em 4 camadas (regras gerais, nichos + imóveis, segmentação, saúde da conta) |

O Gestor é uma *skill* (e não um agente) porque no Claude Code um subagente não pode chamar
outros subagentes — só a conversa principal pode coordenar o time.

## Exemplos
- "Gestor, como estão meus anúncios?"
- "Faz a revisão da semana"
- "Tenho R$ 600 pra investir esse mês no Green Village, o que eu faço?"
- "Quero gravar um vídeo no terreno"
- "Meu anúncio foi reprovado"

Perfil do negócio, contas e metas ficam em `contexto.md`.
**Comandos prontos para copiar e colar: `comandos.md`.**

## Problemas de acesso (equivalência com o "Guia dos Erros da Meta")
O guia foi escrito para quem conecta a Meta com **token + app próprio no Facebook Developers**.
Aqui o acesso é pelo **conector Meta do Claude**, então a maior parte não se aplica:

| Erro do guia | Aqui |
|---|---|
| 1. Claude não encontra os agentes | Os agentes estão em `.claude/agents/` deste repositório. Abra a sessão com este repo; agentes novos aparecem a partir da sessão seguinte. |
| 2. Falta o token | **Não se aplica.** Não existe token; o conector já autentica. |
| 3. Pede o número da conta | Já configurado em `contexto.md` (padrão: 624644153259329). |
| 4. App em modo de desenvolvimento | **Não se aplica.** Não há app seu no Facebook Developers. |
| 5. Descrição do app | **Não se aplica.** |
| 6. Verificação pendente | **Não se aplica.** |
| 7. App reprovado | **Não se aplica.** Para **anúncio** reprovado, peça à Vera. |

Se algo travar no acesso:
- **Conector desconectado / erro de permissão** → reconecte o Meta em claude.ai → Configurações → Conectores.
- **Conta não aparece** → confira se seu perfil tem acesso a ela no Gerenciador de Negócios.
- **Anúncio não veicula** → a conta precisa de forma de pagamento (hoje só a "Lucas Miguel" tem).
- **Sem acesso nenhum** → mande print ou o relatório exportado do Gerenciador
  (Relatórios → Exportar); o Gestor analisa a partir dele.
