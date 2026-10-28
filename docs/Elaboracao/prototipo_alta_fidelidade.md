---
id: prototipo_alta_fidelidade
title: Protótipo de Alta Fidelidade
---
# Protótipo de Alta Fidelidade — GAAP

## Situação do artefato

O arquivo de alta fidelidade anterior apontava para uma única imagem repetida e continha telas de torneio, sem relação com o GAAP. Esse material foi substituído pelo protótipo atual. O [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade) contém seis telas desktop (1920 × 1080) e seis versões mobile (390 × 844); as imagens exportadas estão incorporadas na página do [protótipo de baixa fidelidade](../Iniciacao/prototipo_baixa_fidelidade.md#referencia-visual--prototipo-de-alta-fidelidade). A existência das telas não significa que tenham sido validadas com usuários.

## Cobertura prevista e lacunas dos exports

| Tela a produzir | Perfil | Requisitos | Estados que precisam ser representados |
|---|---|---|---|
| Login | Todos | RF-01, RNF-02 | Sucesso, credenciais inválidas, perfil sem autorização. |
| Cadastros de aluno, profissional e serviço | Administrador | RF-02 | Lista, formulário, validação de campos e confirmação. |
| Agenda, disponibilidade e bloqueios | Administrador | RF-03, RF-04 | Agenda vazia, resultado, bloqueio e erro de intervalo. |
| Confirmação de agendamento | Administrador | RF-05, RN-01 a RN-04 | Sucesso, conflito, bloqueio, capacidade excedida e serviço incompatível. |
| Agenda de sessões | Treinador | RF-04 | Somente compromissos sob responsabilidade do Treinador. |
| Agenda de atendimentos | Profissional de Saúde | RF-04, RF-06 | Somente serviço e agenda atribuídos; registrar presença/falta do aluno atendido. |
| Presença e relatório de treino | Treinador | RF-06, RF-07 | Presente/falta por aluno; um relatório por sessão, rascunho/finalizado, volume com unidade e intensidade Borg CR10 (0–10). |
| Notificação de sessão pendente | Treinador | RF-08 (fora do escopo) | Aviso por e-mail; classificado como exceção já implementada. |

## Regras de consistência visual

- Usar GAAP como nome do produto e os três perfis do cenário como nomenclatura.
- Usar “Serviço” para Treino, Fisioterapia, Psicologia e Nutrição; usar “Sessão” como ocorrência agendada e “Atendimento” para os serviços de saúde.
- Não incluir módulos financeiros, prontuário, dashboards analíticos, torneios, planos, responsáveis legais ou aula experimental sem nova decisão de escopo.
- Manter a distinção entre regra proposta e decisão confirmada; consultar as pendências do [levantamento de requisitos](levreq.md).
- Revisar a consistência dos estados de sucesso e erro com os requisitos e decisões ainda pendentes.
- Representar a configuração de horários e bloqueios e os erros de validação do agendamento; atualmente há apenas atalhos e um resumo das validações.
- Atualizar as telas exportadas para mostrar presença/falta nos atendimentos de saúde e o relatório por sessão com rascunho, volume com unidade, intensidade Borg CR10 e estado finalizado somente para leitura.
- Validar a experiência com usuários; não há resultados de teste registrados.

## Dependências

- O [protótipo de baixa fidelidade](../Iniciacao/prototipo_baixa_fidelidade.md) representa os mesmos fluxos e IDs.
- A [tabela de rastreabilidade](rastreabilidade.md) deve apontar cada tela aos requisitos correspondentes.
