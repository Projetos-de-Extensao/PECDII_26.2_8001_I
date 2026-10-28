---
id: revisao_cruzada
title: Checklist de Revisão Cruzada
---
# Checklist de Revisão Cruzada do Escopo

Este documento transforma os critérios de aceite da seção 10 do cenário GAAP e os sete pontos do feedback AP1 (#56) em uma checklist para revisão entre integrantes. **A checklist está preparada; a revisão de outros integrantes, o registro de decisões e a aprovação do escopo continuam pendentes.** Não marque uma linha como concluída sem evidência ou registro da equipe.

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
| F1 | Revalidar problema e recorte | Problema, perfis, metas do MVP, fora de escopo e exceção RF-08 estão explícitos? | Artefato preparado; revisar com a equipe |
| F2 | Consolidar glossário | Aluno, profissional, serviço, sessão/atendimento, agenda, presença e relatório têm definição comum? Termos antigos estão removidos ou justificados? | Artefato preparado; revisar com a equipe |
| F3 | Refazer requisitos | Cada RF/RN/RNF tem ID, prioridade, critério observável e cobertura dos três perfis? Bloqueio, capacidade, compatibilidade e autorização estão definidos/assinalados para confirmação? | Artefato preparado; decisões críticas pendentes |
| F4 | Alinhar artefatos | Visão, mapa, casos de uso, classes e protótipos usam os mesmos IDs? Matriz de rastreabilidade não esconde lacunas? | Matriz criada; protótipo visual de alta fidelidade ainda ausente |
| F5 | Modelar fluxos de risco | Sequências mostram conflito, capacidade, bloqueio, usuário sem permissão e payload inválido; finalizar relatório também cobre permissão e dados inválidos? | Diagramas preparados; validar regras propostas |
| F6 | Revisar viabilidade | Implementação atual foi comparada ao cronograma? Riscos, dependências e critério do marco de Elaboração foram registrados? | Análise preparada; cronograma precisa de confirmação |
| F7 | Revisão cruzada | Outros integrantes revisaram artefatos, registraram decisões/dúvidas e obtiveram aprovação do escopo? | Pendente — ação humana da equipe e validação do professor |

## Registro das revisões

| Revisor(a) | Artefatos revisados | Data | Achados | Decisões/dúvidas registradas em |
|---|---|---|---|---|
| A preencher pela equipe | | | | |
| A preencher pela equipe | | | | |
| A preencher pela equipe | | | | |

## Registro de decisões e dúvidas

| ID | Dúvida/achado | Decisão | Responsável pela decisão | Data | Artefatos afetados |
|---|---|---|---|---|---|
| D-01 | Qual é a capacidade máxima, a que nível se aplica e sessões podem ser em grupo? | Pendente de definição pelo cliente/responsável pelo cenário; a equipe não deve presumir valor ou regra. | Cliente/responsável pelo cenário | | LevReq, classes, sequência, protótipos |
| D-02 | Quais campos e estados compõem o relatório de treino? | Um relatório imutável após finalização por sessão; inclui participantes, objetivo, exercícios, volume com valor/unidade e intensidade Borg CR10 (0–10); permite rascunho e finalização após validação. | Usuário/equipe | 28/10/2026 | LevReq, casos de uso, classes, protótipos |
| D-03 | Presença/falta se aplica apenas a sessão de Treino? | Não. Aplica-se também aos atendimentos de saúde; o profissional responsável registra por aluno participante, respeitando serviço e agenda atribuídos. | Usuário/equipe | 28/10/2026 | LevReq, casos de uso, classes, protótipos |
| D-04 | A notificação de e-mail deve permanecer apesar de constar fora do escopo? | Mantida no código por recomendação de 14/10; confirmar aprovação formal | Equipe/professor | | Visão, LevReq, casos de uso |
| D-05 | Cronograma duplicou a iteração 3 e usa “aplicativo” na entrega de backend? | Interpretado como uma iteração de 4 semanas e API; confirmar com professor | | | Viabilidade, cenário |
| D-06 | A disponibilidade e os bloqueios são definidos por serviço ou profissional? | Gerais por profissional e compartilhados entre os serviços habilitados; conflitos e bloqueios valem para a agenda toda. Compatibilidade com o serviço é validada separadamente. | Usuário/equipe | 28/10/2026 | LevReq, glossário, classes, sequência, protótipos |

## Aprovação do escopo

**Estado: pendente.** Após a revisão cruzada, registrar aqui quem aprovou, a data, a versão dos documentos e quaisquer condições. A emissão do pedido de aprovação ao responsável pelo cenário deve ser feita pela equipe.

| Aprovador(a) | Data | Versão/referência do PR | Condições |
|---|---|---|---|
| Pendente | | | |

## Referências

- [Cenário GAAP — critérios de aceite](../Iniciacao/cenario.md#10-criterios-de-aceite-da-entrega)
- [Feedback AP1](https://github.com/Projetos-de-Extensao/PECDII_26.2_8001_I/issues/56)
- [Plano de viabilidade](viabilidade_mvp.md)
- [Rastreabilidade](rastreabilidade.md)
