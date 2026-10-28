---
id: viabilidade_mvp
title: Viabilidade e Iterações do MVP
---
# Viabilidade do MVP e Plano de Iterações

## Base de planejamento

O cenário reserva as semanas 6–8 para Elaboração, 9–10 para Construção 1, 11–12 para Construção 2, 13–16 para Construção 3 e 17–18 para Transição. Ele lista Construção 3 em duas linhas iguais (13–14 e 15–16) e chama a entrega final de aplicativo, embora o produto seja um backend. A equipe deve confirmar essas duas inconsistências com o professor; este documento interpreta 13–16 como uma única iteração de quatro semanas e Transição como a entrega da API.

## Comparação com a implementação atual

Inspeção do código em 27/10/2026. “Parcial” indica que há algo correspondente, mas ainda não cumpre o critério do cenário.

| Iteração prevista | Entrega do cenário | Evidência atual no repositório | Estado |
|---|---|---|---|
| 1 — semanas 9–10 | Autenticação/perfis, cadastro de alunos, profissionais e serviços, migrações e testes de domínio. | Modelos e endpoints CRUD para `Aluno`, `Professor` e `Sessao`; migrações e workflow de testes existem. Não há modelo de Serviço nem autorização por três perfis nas viewsets. | Parcial; RF-01 e RF-02 não atendidos integralmente. |
| 2 — semanas 11–12 | Disponibilidade, bloqueios, agendamento, consulta de agenda e testes de conflito/capacidade. | Existe sessão com início/fim e endpoint de consulta de sessões pendentes. Não foram encontrados modelos ou validações de disponibilidade, bloqueios, capacidade ou conflitos. | Não implementada no recorte GAAP. |
| 3 — semanas 13–16 | Presença, aula ministrada, relatório de treino, dashboard simples, auditoria e documentação de endpoints. | Sessão tem status/observações e notificação automática por e-mail. Não há presença por aluno, relatório de treino, auditoria abrangente ou dashboard evidenciados no código consultado. | Parcial; notificação é exceção fora do escopo. RF-06 e RF-07 pendentes. |
| Transição — semanas 17–18 | Aceite, defeitos, demonstração, release e documentação coerente. | CI executa `check`, valida migrations e testes; deploy e documentação existem. Ainda não há aceite do MVP conforme os critérios do cenário. | Preparação existente; aceite pendente. |

## Plano de trabalho para concluir o MVP

| Etapa | Trabalho necessário | Dependências | Evidência de conclusão |
|---|---|---|---|
| Elaboração — semanas 6–8 | Validar glossário, requisitos, capacidade, autorização, modelo de domínio, sequência, protótipos, riscos e arquitetura. | Confirmações do responsável pelo cenário; decisões da equipe. | Critérios de saída abaixo aprovados; documentação sem lacunas críticas não registradas. |
| Construção 1 — semanas 9–10 | Autenticação e perfis; cadastros de aluno, profissional e serviço; testes. | RF-01/RF-02 e modelo de usuário/serviço validados. | Os três perfis têm operações autorizadas; dados de base podem ser cadastrados por API. |
| Construção 2 — semanas 11–12 | Disponibilidade, bloqueios, consultas de agenda, confirmação, conflito, capacidade, transações e testes concorrentes. | RF-03/RF-04/RF-05 e RN-01–RN-04/RN-06 definidos. | Casos válidos são confirmados; violações são recusadas sem persistência parcial; concorrência não excede capacidade. |
| Construção 3 — semanas 13–16 | Presença/falta por aluno em sessões e atendimentos; relatório de treino; autorização; documentação de endpoints; dashboard simples somente se confirmado no escopo. | RF-06/RF-07, métricas e ciclo de vida do relatório definidos. | Profissional responsável registra presença no compromisso autorizado; apenas Treinador autorizado finaliza relatório de treino; relatório finalizado é imutável; testes e documentação refletem as permissões. |
| Transição — semanas 17–18 | Testes de aceitação, defeitos, demonstração, release, retrospectiva. | Iterações anteriores concluídas e ambiente de demonstração disponível. | Critérios da seção 10 do cenário verificados e release reproduzível. |

## Riscos

| ID | Risco | Impacto | Resposta |
|---|---|---|---|
| R-01 | Cenário deixa quatro funcionalidades, entidades mínimas, RN01–RN03 e NFRs em branco. | Equipe implementa regras divergentes do que será avaliado. | Obter esclarecimentos; registrar decisão, responsável e data; manter hipótese identificada como proposta até validação. |
| R-02 | Cliente/cenário não define valor, entidade ou nível de configuração da capacidade. | Agendamento e teste concorrente ficam ambíguos. | Solicitar ao cliente/responsável pelo cenário o limite, onde se aplica e se sessões podem ser em grupo, antes da construção 2; não presumir a regra. |
| R-03 | Código atual usa nomes/modelos de domínio anteriores (`Professor`, sem Serviço e perfis do cenário). | Requisitos novos não correspondem às APIs e dados existentes; migração pode quebrar consumidores. | Planejar compatibilidade e migração como tarefa técnica da Construção 1. |
| R-04 | Presença por aluno em sessões e atendimentos e relatório de treino ainda não estão implementados. | Não há como cumprir os critérios de aceite da Construção 3. | RF-06 foi definido para os dois tipos de compromisso; relatório por sessão, rascunho, volume com unidade, intensidade Borg CR10 e imutabilidade após finalização foram definidos. Implementar autorização por vínculo. |
| R-05 | Notificação automática por e-mail é explicitamente fora do escopo, mas foi mantida por recomendação do professor. | Desvio do cenário e esforço extra. | Manter como exceção RF-08 documentada e solicitar confirmação de escopo. |
| R-06 | Protótipo de alta fidelidade anterior era repetição de uma imagem e tinha conteúdo de torneio. | Artefato visual não validava os fluxos atuais. | Figma e exports atuais foram criados; revisar se refletem presença em atendimentos de saúde e os campos de relatório agora definidos antes da revisão cruzada. |
| R-07 | Cronograma tem 18 semanas e uma linha duplicada de iteração 3. | Planejamento e entrega podem não caber no período denominado “quatro meses”. | Confirmar calendário e duração com o professor antes de aprovar o marco. |

## Dependências entre entregas

- #58 Glossário define a terminologia usada por #59 e pelos demais artefatos.
- #59 define IDs e regras; #62 depende explicitamente desses IDs.
- #60 usa os IDs de requisitos e regras definidos em #59.
- #61 usa o escopo de #58/#59 e a evidência do código para estimar as iterações.
- #63 revisa o conjunto resultante de #58–#62; revisão cruzada e aprovação não podem ser substituídas por uma auto-revisão.

## Critério para concluir o milestone “Elaboração”

Considerar Elaboração concluída somente quando:

1. Glossário, perfis e escopo do MVP estiverem coerentes com o cenário, e hipóteses críticas tiverem confirmação ou decisão explícita da equipe/professor.
2. Requisitos RF/RN/RNF tiverem IDs estáveis, critérios observáveis, prioridades e cobertura dos três perfis.
3. Casos de uso, classes, sequências, protótipos e tabela de rastreabilidade apontarem para os mesmos IDs e não preservarem fluxos antigos como se fossem escopo aprovado.
4. Modelo relacional e arquitetura estiverem revisados em relação aos requisitos e à implementação que será construída.
5. Riscos, dependências, iterações e critérios de aceite estiverem registrados.
6. Revisão cruzada pela equipe estiver registrada e o responsável pelo cenário tiver aprovado o escopo.

## Milestone do GitHub

Proposta de milestone: **Elaboração**. Descrição: “Concluir e validar os requisitos, o modelo de domínio, a arquitetura, os fluxos UML, os protótipos, os riscos e os critérios de saída da fase de Elaboração do GAAP.” A criação do milestone é uma configuração do GitHub e precisa ser feita na página **Issues → Milestones**; não há ferramenta GitHub disponível nesta sessão para criá-lo diretamente.

## Referências

- [Cenário GAAP](../Iniciacao/cenario.md)
- [Levantamento de Requisitos](levreq.md)
- [Glossário](glossario.md)
- [Rastreabilidade](rastreabilidade.md)
- [Revisão cruzada](revisao_cruzada.md)
