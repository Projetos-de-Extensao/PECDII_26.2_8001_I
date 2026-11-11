---
id: revisao_cruzada
title: Revisão do Escopo GAAP
---
# Revisão do Escopo GAAP

Este documento organiza a conferência dos critérios de aceite da seção 10 do cenário GAAP e dos sete pontos do feedback AP1 (#56), além de registrar achados e decisões de escopo. A issue #63 não exige revisão por outros integrantes nem aprovação do escopo; ela é concluída com a revisão documental e o registro das decisões.

Os resultados abaixo foram reavaliados contra o código e a documentação do workspace em 11/11/2026. A suíte local passou com 167 testes do backend e 3 testes do cliente; o build de produção do cliente também passou. O resultado remoto do workflow e o estado do GitHub Project não foram verificados nesta revisão.

## Critérios de aceite do cenário GAAP

| # | Pergunta de revisão | Evidência/documento | Resultado (OK / ajustar / pendente) | Observação/decisão |
|---:|---|---|---|---|
| C1 | O projeto sobe localmente por instruções reproduzíveis e aplica migrations em banco relacional? | README, migrations, CI | OK no workspace: as instruções estão documentadas e a suíte cria o banco de teste aplicando as migrations. | A configuração de produção/VPS não foi verificada nesta revisão. |
| C2 | Administrador consegue cadastrar dados de base e configurar ao menos um serviço? | RF-02, API, casos de uso | OK: cadastros de aluno, profissional e serviço estão implementados com escrita administrativa. | |
| C3 | A API recusa agendamentos conflitantes, bloqueados ou acima da capacidade? | RF-05, RN-01–RN-03, sequência e testes | OK no backend: confirmação valida disponibilidade, bloqueios, compatibilidade, conflitos e capacidade de até seis participantes de forma atômica. | |
| C4 | Profissional autorizado consulta agenda, registra presença/falta no compromisso sob sua responsabilidade e o Treinador finaliza relatório? | RF-04, RF-06, RF-07, casos de uso | API aplica o fim previsto à presença e ao desfecho; relatório de Treino tem rascunho, validação e finalização imutável. O cliente web inicial já oferece login, cadastros administrativos e agenda; presença/relatório na interface e RF-09/RF-11 permanecem pendentes. | Completar os fluxos da interface e os demais requisitos da Construção 3. |
| C5 | Usuários sem permissão não acessam agendas/operações indevidas? | RF-01, RN-05, testes de autorização | OK para as operações implementadas: os três perfis têm escopo próprio de consulta e as escritas administrativas/responsáveis são restritas. | |
| C6 | Testes automatizados passam no pipeline e cobrem regras prioritárias? | Workflow de CI e resultados do pipeline | Parcial: 167 testes do backend e 3 do cliente passaram localmente em 11/11/2026; o build de produção do cliente passou. O estado do workflow remoto não foi consultado. | |
| C7 | Documentação, diagramas UML e GitHub Project refletem o que foi efetivamente entregue? | Artefatos e GitHub Project | Parcial: os documentos de implementação foram atualizados para distinguir código atual de modelo-alvo; protótipos têm lacunas e o GitHub Project não foi comparado. | |

## Sete pontos do feedback AP1

| # | Ponto | Checklist de revisão | Estado |
|---:|---|---|---|
| F1 | Revalidar problema e recorte | Problema, perfis, metas do MVP, fora de escopo e exceção RF-08 estão explícitos? | Recorte documentado; RF-08 registrada como exceção fora do escopo do cenário. |
| F2 | Consolidar glossário | Aluno, profissional, serviço, sessão/atendimento, agenda, presença e relatório têm definição comum? Termos antigos estão removidos ou justificados? | Glossário consolidado e alinhado às decisões D-03, D-07 e D-09. |
| F3 | Refazer requisitos | Cada RF/RN/RNF tem ID, prioridade, critério observável e cobertura dos três perfis? Bloqueio, capacidade, compatibilidade e autorização estão definidos/assinalados para confirmação? | IDs e critérios registrados; RN-01, RN-07, RF-09, RF-11 e RNF-06 têm decisões registradas (D-10 a D-16). |
| F4 | Alinhar artefatos | Visão, mapa, casos de uso, classes e protótipos usam os mesmos IDs? Matriz de rastreabilidade não esconde lacunas? | IDs e matriz atualizados na #62; esta revisão corrigiu descrições de cobertura desatualizadas. Lacunas visuais restantes estão listadas no registro do protótipo. |
| F5 | Modelar fluxos de risco | Sequências mostram conflito, capacidade, bloqueio, usuário sem permissão e payload inválido; finalizar relatório também cobre permissão e dados inválidos? | Fluxos preparados; RNF-06 definido para operações críticas com registro append-only e mensagem legível. |
| F6 | Revisar viabilidade | Implementação atual foi comparada ao cronograma? Riscos, dependências e critério do marco de Elaboração foram registrados? | Comparação e riscos registrados; Construção 2 concluída no backend; RF-07 e o limite temporal de RF-06/RF-10 foram implementados; consulta RF-09, dashboard RF-11, lembrete RF-12 e auditoria RNF-06 continuam pendentes. |
| F7 | Revisar os achados | Os achados, dúvidas e decisões relevantes estão registrados, com inconsistências corrigidas ou explicitamente mantidas como pendências? | Revisão documental registrada; decisões D-04 a D-09 concluídas nesta atualização. |

## Registro das revisões

| Revisor(a) | Artefatos revisados | Data | Achados | Decisões/dúvidas registradas em |
|---|---|---|---|---|
| Lucas Santos | Casos de uso, classes, sequência, glossário, rastreabilidade, viabilidade, visão, mapa mental e protótipos (exports desktop e mobile) | 28/10/2026 | 7 inconsistências entre documentos (A1–A7) e 4 pontos no protótipo (P1–P4); detalhes abaixo | D-07 a D-09 |
| Revisão assistida (Codex) | Reavaliação de A1–A7 e P1–P4 após PR #75; rastreabilidade, viabilidade e exports desktop/mobile | 03/11/2026 | A1–A6, P1, P2 e P4 corrigidos na #62; A7 e descrições desatualizadas corrigidas nesta revisão; decisões D-04 a D-09 registradas e P3 resolvido. | Pendências visuais e RF-09/RF-11/RNF-06 descritas nos artefatos |
| Atualização das decisões com Pedro Lucas | RN-07, RF-09, RF-11, RN-01, lembrete de relatório e auditoria | 04/11/2026 | D-10 a D-15 registraram regras de conflito, pendências, dashboard e lembrete. D-16 fechou a auditoria para cadastro de usuários, confirmação de agendamento, alteração de presença/falta e finalização de relatório, com mensagens humanas e sem credenciais. | Registro de decisões D-10 a D-16; LevReq, casos de uso, modelos e rastreabilidade |
| Revisão assistida (Codex) | Código em `backend/src/`, README e documentos de iniciação/elaboração | 11/11/2026 | A revisão iniciou com relatório, regra temporal e cliente web pendentes; nesta atualização, os itens #108–#110 foram implementados e testados localmente. | Viabilidade, rastreabilidade, 5W2H, Design Thinking, mapa mental e protótipos |

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
| D-07 | Quem marca a sessão/atendimento como realizado, e isso se confunde com presença? | O profissional responsável registra realizado/não realizado depois do horário previsto. É uma informação do compromisso, separada da presença/falta individual de cada aluno. D-19 fixa o limite no fim previsto. | Decisão de modelagem adotada nesta revisão | 03/11/2026 | LevReq, casos de uso, glossário, protótipos |
| D-08 | O relatório de treino se liga ao Treinador diretamente ou só pela sessão? | O relatório pertence somente à sessão (um por sessão), sem FK direta para o Treinador. O responsável atual controla o rascunho; se a sessão for reatribuída, a autorização acompanha o responsável atual e o relatório permanece ligado à sessão. Relatório finalizado permanece imutável. | Decisão de modelagem adotada nesta revisão | 03/11/2026 | LevReq, classes, DER, casos de uso |
| D-09 | Como representar Treinador e Profissional de Saúde e seus vínculos com serviços? | Usar uma entidade Usuario com campo de perfil (Administrador, Treinador ou Profissional de Saúde), sem tabelas de especialização. O vínculo profissional–serviço é N:N; Treinadores podem atuar em mais de um serviço, conforme confirmação de Pedro Lucas. | Modelagem adotada nesta revisão; Treinador multi-serviço confirmado por Pedro Lucas | 03/11/2026 | LevReq, classes, DER, glossário, protótipos |
| D-10 | O conflito de horário do aluno (RN-07) entra no MVP? | Sim. Um aluno não pode participar de compromissos ativos com horários sobrepostos; intervalos seguem `[início, fim)`, permitindo compromissos contíguos. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, classes, DER, sequência, rastreabilidade |
| D-11 | O que conta como pendência operacional na RF-09? | Compromisso com horário encerrado, exceto cancelado, e ao menos um participante sem presença/falta registrada; sessões de Treino sem relatório ou com relatório em rascunho também são pendentes. A consulta identifica o motivo e é exclusiva do Administrador. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, rastreabilidade, protótipo |
| D-12 | Quais indicadores compõem o dashboard simples da RF-11? | Para o período selecionado, mostrar quantidade de compromissos por serviço e situação (agendado, realizado, não realizado ou cancelado); o mês atual é o período padrão. A consulta é exclusiva do Administrador e não inclui análises adicionais. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, classes, DER, rastreabilidade, protótipo |
| D-13 | Como validar e acelerar a busca por conflito do profissional (RN-01)? | Impedir sobreposição entre compromissos não cancelados do profissional, em qualquer serviço. A API consulta antes de confirmar e retorna mensagem amigável; usar índice composto `(profissional_id, inicio, fim)` e verificar o plano de execução/ganho no banco adotado. Intervalos `[início, fim)` permitem compromissos contíguos. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, sequência, DER, rastreabilidade |
| D-14 | Como validar e acelerar a busca por conflito do aluno (RN-07)? | A API consulta conflitos antes de confirmar e retorna mensagem amigável; usar índices em `(aluno_id, sessao_id)` em `participacao` e `(inicio, fim)` em `sessao`, confirmando plano de execução/ganho no banco adotado. Intervalos `[início, fim)` permitem compromissos contíguos. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, sequência, DER, rastreabilidade |
| D-15 | Como apoiar o acompanhamento das pendências e a leitura do dashboard? | RF-09 inclui filtros por tipo, contador total no menu do Administrador e atalhos para detalhes, sem permitir que o Administrador altere presença ou relatório. RF-11 mantém o período visível, ordenação por total decrescente e exibição explícita de zeros; destaque por cores claras é opcional. Inclui-se RF-12: um lembrete único por e-mail ao Treinador 24 horas após sessão de Treino se o relatório estiver ausente ou em rascunho. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, classes, DER, rastreabilidade, protótipo, viabilidade |
| D-16 | Qual é o escopo da auditoria (RNF-06)? | Registrar criação de usuário, confirmação de agendamento, alteração de presença/falta e finalização de relatório. Cada registro contém autor, operação, entidade, data/hora e mensagem em linguagem humana; é append-only e não inclui senhas ou credenciais. | Pedro Lucas | 04/11/2026 | LevReq, casos de uso, classes, DER, rastreabilidade |
| D-17 | Quem pode cancelar uma sessão? | O Administrador e o profissional responsável pela própria sessão, mudando `status` para `CANCELADA`. Outro profissional não altera a sessão, e só o Administrador a remove. É o comportamento já implementado no #104. | Pedro Lucas e Lucas Santos | 11/11/2026 | README, casos de uso |
| D-18 | O que fazer quando uma disponibilidade é removida ou um bloqueio é criado sobre uma sessão já confirmada? | Recusar com `409` (RN-03) a remoção ou alteração de disponibilidade e a criação ou alteração de bloqueio que deixe uma sessão confirmada fora da agenda do profissional. Sessões canceladas não impedem a operação. Saiu da revisão do #100. | Pedro Lucas e Lucas Santos | 11/11/2026 | LevReq (RN-03), README |
| D-19 | Qual limite temporal vale para presença/falta e para o desfecho da sessão? | Ambas as operações só são aceitas a partir do fim previsto, inclusive no instante exato (`agora >= fim`). O fim da sessão marca o primeiro momento em que a presença/falta pode ser confirmada e o compromisso pode ser declarado realizado ou não realizado; são informações distintas. | Decisão de implementação para #108, coerente com RF-06/RF-10 | 11/11/2026 | LevReq, casos de uso, API, testes e README |

## Referências

- [Cenário GAAP — critérios de aceite](../Iniciacao/cenario.md#10-criterios-de-aceite-da-entrega)
- [Feedback AP1](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_I/issues/56)
- [Plano de viabilidade](viabilidade_mvp.md)
- [Rastreabilidade](rastreabilidade.md)
