---
id: revisao_cruzada
title: Revisão do Escopo GAAP
---
# Revisão do Escopo GAAP

Este documento organiza a conferência dos critérios de aceite da seção 10 do cenário GAAP e dos sete pontos do feedback AP1 (#56), além de registrar achados e decisões de escopo. A issue #63 não exige revisão por outros integrantes nem aprovação do escopo; ela é concluída com a revisão documental e o registro das decisões.

## Critérios de aceite do cenário GAAP

| # | Pergunta de revisão | Evidência/documento | Resultado (OK / ajustar / pendente) | Observação/decisão |
|---:|---|---|---|---|
| C1 | O projeto sobe localmente por instruções reproduzíveis e aplica migrations em banco relacional? | README, migrations, CI | Pendente | |
| C2 | Administrador consegue cadastrar dados de base e configurar ao menos um serviço? | RF-02, API, casos de uso | Pendente; serviço não está implementado no código atual | |
| C3 | A API recusa agendamentos conflitantes, bloqueados ou acima da capacidade? | RF-05, RN-01–RN-03, sequência e testes | Pendente; regras ausentes na implementação atual | |
| C4 | Profissional autorizado consulta agenda, registra presença/falta no compromisso sob sua responsabilidade e o Treinador finaliza relatório? | RF-04, RF-06, RF-07, casos de uso | Pendente; presença/relatório não estão implementados atualmente | |
| C5 | Usuários sem permissão não acessam agendas/operações indevidas? | RF-01, RN-05, testes de autorização | Pendente; autorização por três perfis ausente no código atual | |
| C6 | Testes automatizados passam no pipeline e cobrem regras prioritárias? | Workflow de CI e resultados do pipeline | Pendente de execução/revisão | |
| C7 | Documentação, diagramas UML e GitHub Project refletem o que foi efetivamente entregue? | Artefatos e GitHub Project | Pendente; não declarar conformidade antes da revisão | |

## Sete pontos do feedback AP1

| # | Ponto | Checklist de revisão | Estado |
|---:|---|---|---|
| F1 | Revalidar problema e recorte | Problema, perfis, metas do MVP, fora de escopo e exceção RF-08 estão explícitos? | Recorte documentado; RF-08 registrada como exceção fora do escopo do cenário. |
| F2 | Consolidar glossário | Aluno, profissional, serviço, sessão/atendimento, agenda, presença e relatório têm definição comum? Termos antigos estão removidos ou justificados? | Glossário consolidado e alinhado às decisões D-03, D-07 e D-09. |
| F3 | Refazer requisitos | Cada RF/RN/RNF tem ID, prioridade, critério observável e cobertura dos três perfis? Bloqueio, capacidade, compatibilidade e autorização estão definidos/assinalados para confirmação? | IDs e critérios registrados; RF-09, RF-11, RN-07 e RNF-06 permanecem identificados como propostas/definições pendentes. |
| F4 | Alinhar artefatos | Visão, mapa, casos de uso, classes e protótipos usam os mesmos IDs? Matriz de rastreabilidade não esconde lacunas? | IDs e matriz atualizados na #62; esta revisão corrigiu descrições de cobertura desatualizadas. Lacunas visuais restantes estão listadas no registro do protótipo. |
| F5 | Modelar fluxos de risco | Sequências mostram conflito, capacidade, bloqueio, usuário sem permissão e payload inválido; finalizar relatório também cobre permissão e dados inválidos? | Fluxos preparados; RN-07 e RNF-06 continuam marcadas como propostas onde aplicável. |
| F6 | Revisar viabilidade | Implementação atual foi comparada ao cronograma? Riscos, dependências e critério do marco de Elaboração foram registrados? | Comparação e riscos registrados; semanas 13–16 planejadas em duas etapas; pendências RF-09/RF-11/RNF-06 estão explícitas. |
| F7 | Revisar os achados | Os achados, dúvidas e decisões relevantes estão registrados, com inconsistências corrigidas ou explicitamente mantidas como pendências? | Revisão documental registrada; decisões D-04 a D-09 concluídas nesta atualização. |

## Registro das revisões

| Revisor(a) | Artefatos revisados | Data | Achados | Decisões/dúvidas registradas em |
|---|---|---|---|---|
| Lucas Santos | Casos de uso, classes, sequência, glossário, rastreabilidade, viabilidade, visão, mapa mental e protótipos (exports desktop e mobile) | 28/10/2026 | 7 inconsistências entre documentos (A1–A7) e 4 pontos no protótipo (P1–P4); detalhes abaixo | D-07 a D-09 |
| Revisão assistida (Codex) | Reavaliação de A1–A7 e P1–P4 após PR #75; rastreabilidade, viabilidade e exports desktop/mobile | 03/11/2026 | A1–A6, P1, P2 e P4 corrigidos na #62; A7 e descrições desatualizadas corrigidas nesta revisão; decisões D-04 a D-09 registradas e P3 resolvido. | Pendências visuais e RF-09/RF-11/RNF-06 descritas nos artefatos |

### Achados da revisão — Lucas Santos (28/10/2026)

Revisão original feita sobre a `main` após o PR #71. A situação abaixo registra a reavaliação em 03/11/2026, depois do PR #75 (#62).

| # | Artefato | Achado original | Situação após PR #75 |
|---|---|---|---|
| A1 | Casos de uso, UC-07 | Cita RN-06 e RNF-03, que tratam da atomicidade do agendamento e da capacidade, não do relatório de treino. | Corrigido: UC-07 referencia RF-07, RN-05 e requisitos não funcionais pertinentes. |
| A2 | Casos de uso, diagrama | O UC-08 não tem ator associado; a tabela indica o Treinador como ator primário. | Corrigido: o diagrama associa o Treinador ao UC-08. |
| A3 | Diagrama de classes | Não há associação entre o profissional (Usuario) e Servico, necessária para representar a habilitação prevista na RN-04. | Corrigido: associação Usuario–Servico está representada como habilitação proposta. |
| A4 | Sequência "Finalizar relatório de treino" | O texto diz que a edição de relatório finalizado deve ser recusada, mas o fluxo não tem esse caminho alternativo. | Corrigido: fluxo inclui recusa de edição de relatório finalizado. |
| A5 | Sequência "Finalizar relatório de treino" | A chamada envia relatório e presenças juntos, acoplando RF-06 (UC-06) a RF-07; o Profissional de Saúde registra presença sem relatório. | Corrigido: presença/falta é operação separada; UC-06 atende os dois perfis profissionais. |
| A6 | Glossário | Profissional de Saúde aparece só consultando atendimentos; D-03, LevReq e visão 2.3 incluem o registro de presença/falta. | Corrigido: glossário inclui registro de presença/falta nos atendimentos atribuídos. |
| A7 | Revisão cruzada, F4 | Diz que o protótipo de alta fidelidade está ausente, mas o Figma e os exports já existem (PR #68). | Corrigido nesta revisão: F4 reconhece Figma/exports e registra as lacunas atuais. |
| P1 | Protótipo, "Novo agendamento" | O botão "Salvar rascunho" do desktop cria um agendamento em rascunho sem requisito correspondente; não aparece no mobile. | Corrigido: o export atual não oferece rascunho de agendamento. |
| P2 | Protótipo, "Agenda do treinador" | Faltam objetivo, volume com unidade e intensidade Borg CR10 no relatório. | Corrigido: o export atual exemplifica participantes, objetivo, exercícios, volume com unidade e Borg CR10. |
| P3 | Protótipo, "Agenda do treinador" | Filtro "Todos os serviços" para o Treinador. Ver D-09. | Resolvido em 03/11/2026: Pedro Lucas confirmou que o Treinador pode atuar em mais de um serviço; o filtro pode agregar seus serviços vinculados. Não deve listar serviços sem vínculo com o profissional. |
| P4 | Protótipo, "Novo agendamento" | Não há estados de erro para conflito, bloqueio e capacidade. | Parcialmente corrigido: variante desktop/mobile mostra recusa por indisponibilidade, bloqueio, conflito e incompatibilidade; capacidade 7/6 aparece no desktop e o limite de seis no mobile. Estado de sucesso ainda falta. |

## Registro de decisões e dúvidas

| ID | Dúvida/achado | Decisão | Responsável pela decisão | Data | Artefatos afetados |
|---|---|---|---|---|---|
| D-01 | Qual é a capacidade máxima, a quais serviços se aplica e onde é configurada? | Máximo de 6 alunos por sessão, informado pelo professor conforme relato de Pedro Lucas. Aplica-se a qualquer serviço; no MVP, será uma constante de validação no backend, sem configuração administrativa. Decisão concluída. | Professor (valor); Pedro Lucas (abrangência e implementação no MVP) | 30/10/2026 (registro dos esclarecimentos) | LevReq, classes, sequência, DER, protótipos |
| D-02 | Quais campos e estados compõem o relatório de treino? | Um relatório imutável após finalização por sessão; inclui participantes, objetivo, exercícios, volume com valor/unidade e intensidade Borg CR10 (0–10); permite rascunho e finalização após validação. | Usuário/equipe | 28/10/2026 | LevReq, casos de uso, classes, protótipos |
| D-03 | Presença/falta se aplica apenas a sessão de Treino? | Não. Aplica-se também aos atendimentos de saúde; o profissional responsável registra por aluno participante, respeitando serviço e agenda atribuídos. | Usuário/equipe | 28/10/2026 | LevReq, casos de uso, classes, protótipos |
| D-04 | A notificação de e-mail deve permanecer apesar de constar fora do escopo? | Mantida como exceção já implementada, por recomendação do professor em 14/10/2026. Continua fora do escopo funcional do cenário e não é critério de aceite do MVP. | Equipe; recomendação do professor | 03/11/2026 (decisão registrada) | Visão, LevReq, casos de uso, viabilidade |
| D-05 | Como interpretar as duas linhas da Iteração 3 e a entrega chamada “aplicativo”? | Tratar as semanas 13–14 e 15–16 como duas etapas da mesma Construção 3 de quatro semanas; tratar “aplicativo” na Transição como a API REST GAAP, produto definido pelo grupo. | Interpretação de planejamento adotada nesta revisão | 03/11/2026 | Viabilidade, planejamento |
| D-06 | A disponibilidade e os bloqueios são definidos por serviço ou profissional? | Gerais por profissional e compartilhados entre os serviços habilitados; conflitos e bloqueios valem para a agenda toda. Compatibilidade com o serviço é validada separadamente. | Usuário/equipe | 28/10/2026 | LevReq, glossário, classes, sequência, protótipos |
| D-07 | Quem marca a sessão/atendimento como realizado, e isso se confunde com presença? | O profissional responsável registra realizado/não realizado depois do horário previsto. É uma informação do compromisso, separada da presença/falta individual de cada aluno. | Decisão de modelagem adotada nesta revisão | 03/11/2026 | LevReq, casos de uso, glossário, protótipos |
| D-08 | O relatório de treino se liga ao Treinador diretamente ou só pela sessão? | O relatório pertence somente à sessão (um por sessão), sem FK direta para o Treinador. O responsável atual controla o rascunho; se a sessão for reatribuída, a autorização acompanha o responsável atual e o relatório permanece ligado à sessão. Relatório finalizado permanece imutável. | Decisão de modelagem adotada nesta revisão | 03/11/2026 | LevReq, classes, DER, casos de uso |
| D-09 | Como representar Treinador e Profissional de Saúde e seus vínculos com serviços? | Usar uma entidade Usuario com campo de perfil (Administrador, Treinador ou Profissional de Saúde), sem tabelas de especialização. O vínculo profissional–serviço é N:N; Treinadores podem atuar em mais de um serviço, conforme confirmação de Pedro Lucas. | Modelagem adotada nesta revisão; Treinador multi-serviço confirmado por Pedro Lucas | 03/11/2026 | LevReq, classes, DER, glossário, protótipos |

## Referências

- [Cenário GAAP — critérios de aceite](../Iniciacao/cenario.md#10-criterios-de-aceite-da-entrega)
- [Feedback AP1](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_I/issues/56)
- [Plano de viabilidade](viabilidade_mvp.md)
- [Rastreabilidade](rastreabilidade.md)
