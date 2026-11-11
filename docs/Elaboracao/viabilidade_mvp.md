---
id: viabilidade_mvp
title: Viabilidade e Iterações do MVP
---
# Viabilidade do MVP e Plano de Iterações

## Base de planejamento

O cenário reserva as semanas 6–8 para Elaboração, 9–10 para Construção 1, 11–12 para Construção 2, 13–16 para Construção 3 e 17–18 para Transição. As duas linhas da Construção 3 (13–14 e 15–16) são tratadas como etapas consecutivas da mesma iteração de quatro semanas: primeiro presença, compromisso ministrado e relatório; depois integração, dashboard, auditoria e documentação. “Aplicativo” na Transição é interpretado como a entrega da API REST GAAP, produto definido pelo grupo.

## Comparação com a implementação atual

Inspeção do código em 11/11/2026. “Parcial” indica que há algo correspondente, mas ainda não cumpre o critério do cenário.

| Iteração prevista | Entrega do cenário | Evidência atual no repositório | Estado |
|---|---|---|---|
| 1 — semanas 9–10 | Autenticação/perfis, cadastro de alunos, profissionais e serviços, migrações e testes de domínio. | Existem autenticação, perfis `Usuario`, cadastros de `Aluno`, profissionais e serviços, permissões por perfil e vínculo N:N profissional-serviço. A migração 0012 converte professores existentes em Treinadores e preserva os vínculos das sessões; o campo da API passa de `professor` para `profissional`. | Concluída nas issues #78, #79, #80, #85 e #88. Os desvios que restam entre o DER e as migrações estão registrados no [DER](der.md#desvios-em-relacao-as-migracoes-atuais). |
| 2 — semanas 11–12 | Disponibilidade, bloqueios, agendamento, consulta de agenda e testes de conflito/capacidade, incluindo o conflito do aluno definido na RN-07. | Disponibilidade e bloqueios por profissional (migração 0013, #100). Participação dos alunos e serviço da sessão (migração 0014, #101). Confirmação pelo `POST /api/sessoes/`, exclusiva do Administrador, que grava sessão e participantes numa transação, recusa mais de 6 alunos (RN-02) e tem teste concorrente (#102). Ainda faltam as validações de habilitação, disponibilidade, bloqueio e conflitos (RN-01, RN-03, RN-04, RN-07) e a consulta da agenda por perfil. | Parcial. Pendentes: #97 e #98 (validações), #91, #95 e #96 (consulta da agenda) e #92, que fecha a confirmação depois da #97 e da #98. |
| 3 — semanas 13–16 | Presença, compromisso ministrado, relatório de treino, dashboard simples, lembrete de relatório, auditoria e documentação de endpoints. | O profissional responsável registra presença ou falta por aluno (RF-06) e marca a sessão como realizada ou não realizada; outros profissionais recebem `403` (RF-10, RN-05, #104). Sessão tem notificação automática por e-mail. Não há relatório de treino, consulta de pendências, dashboard, lembrete de relatório nem auditoria no código. | Parcial; RF-07/RF-09/RF-11/RF-12 e RNF-06 pendentes de implementação. Na RF-10 falta decidir se o registro só vale depois do início ou do fim da sessão. A notificação RF-08 é uma exceção fora do escopo. |
| Transição — semanas 17–18 | Aceite, defeitos, demonstração, release e documentação coerente. | CI executa `check`, valida migrations e testes; deploy e documentação existem. Ainda não há aceite do MVP conforme os critérios do cenário. | Preparação existente; aceite pendente. |

## Plano de trabalho para concluir o MVP

| Etapa | Trabalho necessário | Dependências | Evidência de conclusão |
|---|---|---|---|
| Elaboração — semanas 6–8 | Validar glossário, requisitos, capacidade, autorização, modelo de domínio, sequência, protótipos, riscos e arquitetura. | Confirmações do responsável pelo cenário; decisões da equipe. | Critérios de saída abaixo aprovados; documentação sem lacunas críticas não registradas. |
| Construção 1 — semanas 9–10 | Autenticação e perfis; cadastros de aluno, profissional e serviço; testes. | RF-01/RF-02 e modelo de usuário/serviço validados. | Os três perfis têm operações autorizadas; dados de base podem ser cadastrados por API. |
| Construção 2 — semanas 11–12 | Disponibilidade, bloqueios, consultas de agenda, confirmação, conflitos do profissional e do aluno, capacidade, transações e testes concorrentes. | RF-03/RF-04/RF-05; RN-01–RN-04/RN-06/RN-07. | Casos válidos são confirmados; violações são recusadas sem persistência parcial; concorrência não excede capacidade. |
| Construção 3A — semanas 13–14 | Presença/falta por aluno em sessões e atendimentos; estado realizado/não realizado do compromisso; relatório de treino. | RF-06, RF-07 e RF-10; métricas e ciclo de vida do relatório definidos. | Profissional responsável registra presença e estado do compromisso em ações distintas; Treinador finaliza relatório imutável. |
| Construção 3B — semanas 15–16 | Integrar fluxos, concluir documentação de endpoints e desenvolver consulta de pendências, dashboard, lembrete de relatório e auditoria. | RF-09, RF-11, RF-12 e RNF-06 definidos. | Integração e documentação atualizadas; testes e critérios de aceite cobrem os fluxos definidos. |
| Transição — semanas 17–18 | Testes de aceitação, defeitos, demonstração, release, retrospectiva. | Iterações anteriores concluídas e ambiente de demonstração disponível. | Critérios da seção 10 do cenário verificados e release reproduzível. |

## Riscos

| ID | Risco | Impacto | Resposta |
|---|---|---|---|
| R-01 | Cenário deixa quatro funcionalidades, entidades mínimas, RN01–RN03 e NFRs em branco. | Equipe implementa regras divergentes do que será avaliado. | Obter esclarecimentos; registrar decisão, responsável e data; manter hipótese identificada como proposta até validação. |
| R-02 | O limite de 6 alunos por sessão vale para qualquer serviço e será uma constante no backend do MVP, sem configuração administrativa. | Risco resolvido. | Implementado no #102: a confirmação recusa com `409` uma sessão com 7 alunos, sem gravar sessão nem participantes. Como os participantes são definidos na confirmação e não podem ser alterados depois, requisições concorrentes não somam alunos na mesma sessão. |
| R-03 | A API anterior expunha `Professor` e sessões com o campo `professor`. | Clientes que dependam dos nomes antigos precisam acompanhar a mudança. | Na Construção 1, a migração 0012 converte os registros para `Usuario`/Treinador, reponta as sessões e substitui `/api/professores/` e o campo `professor` pelos recursos/campo de profissional. A mudança de contrato está documentada no README. |
| R-04 | O relatório de treino ainda não está implementado. | Não há como cumprir todos os critérios de aceite da Construção 3. | A presença por aluno nos dois tipos de compromisso foi implementada no #104, com autorização pelo profissional responsável. O relatório por sessão, com rascunho, volume com unidade, intensidade Borg CR10 e imutabilidade após finalização, já está definido e falta implementar. |
| R-05 | Notificação automática por e-mail é explicitamente fora do escopo, mas foi mantida por recomendação do professor. | Desvio do cenário e esforço extra. | Manter como exceção RF-08 já implementada e documentada; ela não integra o aceite funcional do MVP. |
| R-06 | Protótipo de alta fidelidade anterior era repetição de uma imagem e tinha conteúdo de torneio. | Artefato visual não validava os fluxos atuais. | Figma e exports foram refeitos; #62 acrescentou presença nos atendimentos, campos completos do relatório e variante de recusa do agendamento. Permanecem pendentes estados de sucesso/configuração da agenda, presença salva/erro, relatório finalizado somente para leitura e representação de RF-10. A visão geral ainda precisa refletir os indicadores definidos para RF-11. A cobertura está registrada em `prototipo_alta_fidelidade.md`. |
| R-07 | Cronograma tem 18 semanas e repete o rótulo da Iteração 3 nas semanas 13–14 e 15–16. | Se as duas etapas não forem planejadas em sequência, pode haver lacunas na Construção 3. | Planejar as duas linhas como etapas consecutivas da Construção 3; usar o período total de 18 semanas do cenário. A entrega da Transição é a API REST. |

## Dependências entre entregas

- #58 Glossário define a terminologia usada por #59 e pelos demais artefatos.
- #59 define IDs e regras; #62 depende explicitamente desses IDs.
- #60 usa os IDs de requisitos e regras definidos em #59.
- #61 usa o escopo de #58/#59 e a evidência do código para estimar as iterações.
- #63 registra a conferência do conjunto resultante de #58–#62 e as decisões de escopo correspondentes; não depende de revisão de outros integrantes nem de aprovação do escopo.

## Critério para concluir o milestone “Elaboração”

Considerar Elaboração concluída somente quando:

1. Glossário, perfis e escopo do MVP estiverem coerentes com o cenário, e hipóteses críticas tiverem confirmação ou decisão explícita da equipe/professor.
2. Requisitos RF/RN/RNF tiverem IDs estáveis, critérios observáveis, prioridades e cobertura dos três perfis.
3. Casos de uso, classes, sequências, protótipos e tabela de rastreabilidade apontarem para os mesmos IDs e não preservarem fluxos antigos como se fossem escopo aprovado.
4. Modelo relacional e arquitetura estiverem revisados em relação aos requisitos e à implementação que será construída.
5. Riscos, dependências, iterações e critérios de aceite estiverem registrados.
6. A revisão documental e as decisões de escopo estiverem registradas. A aprovação formal do escopo, prevista separadamente no cenário da disciplina, não faz parte da conclusão da issue #63.

## Milestone do GitHub

O milestone [Elaboração](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_I/milestone/3) já existe no GitHub e está associado à issue #61. Sua existência organiza o trabalho; a conclusão do marco depende dos seis critérios de saída acima. A aprovação do escopo citada no cenário da disciplina continua sendo um critério do milestone, separado da issue #63.

## Referências

- [Cenário GAAP](../Iniciacao/cenario.md)
- [Levantamento de Requisitos](levreq.md)
- [Glossário](glossario.md)
- [Rastreabilidade](rastreabilidade.md)
- [Revisão cruzada](revisao_cruzada.md)
