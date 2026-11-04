---
id: prototipo_alta_fidelidade
title: Protótipo de Alta Fidelidade
---
# Protótipo de Alta Fidelidade — GAAP

## Situação do artefato

O arquivo de alta fidelidade anterior apontava para uma única imagem repetida e continha telas de torneio, sem relação com o GAAP. Esse material foi substituído pelo protótipo atual. O [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade) contém seis telas principais desktop (1920 × 1080) e seis versões mobile (390 × 844), além de uma variante de recusa de agendamento em cada formato. As imagens exportadas estão incorporadas na página do [protótipo de baixa fidelidade](../Iniciacao/prototipo_baixa_fidelidade.md#referencia-visual--prototipo-de-alta-fidelidade). A existência das telas não significa que tenham sido validadas com usuários.

Os nomes dos quadros editáveis no Figma identificam os fluxos funcionais relacionados a cada tela. Os nomes dos quadros não significam que todos os estados e controles previstos já apareçam nas imagens.

Em 30/10/2026, o aviso de capacidade da tela "Novo agendamento" foi atualizado nos quadros desktop e mobile e nos respectivos exports: o professor informou limite máximo de **6 alunos por sessão**, conforme relato de Pedro Lucas. O limite vale para qualquer serviço e será uma constante no backend do MVP, sem configuração administrativa.

## Cobertura prevista e lacunas dos exports

| Tela a produzir | Perfil | Requisitos | Estados que precisam ser representados |
|---|---|---|---|
| Login | Todos | RF-01 | Sucesso, credenciais inválidas, perfil sem autorização. |
| Cadastros de aluno, profissional e serviço | Administrador | RF-02 | Lista, formulário, validação de campos e confirmação. |
| Visão geral e pendências | Administrador | RF-04, RF-09, RF-11 | Pendências com definição a confirmar; indicadores simples a definir com o responsável pelo cenário. |
| Agenda, disponibilidade e bloqueios | Administrador | RF-03, RF-04 | Agenda vazia, resultado, bloqueio e erro de intervalo. |
| Confirmação de agendamento | Administrador | RF-05 | Sucesso, conflito do profissional ou do aluno, bloqueio, capacidade excedida e serviço incompatível. |
| Agenda de sessões | Treinador | RF-04, RF-10 | Somente compromissos sob responsabilidade do Treinador e serviços vinculados; registrar realizado/não realizado após o horário previsto, separado da presença. |
| Agenda de atendimentos | Profissional de Saúde | RF-04, RF-06, RF-10 | Somente serviços e agenda atribuídos; registrar realizado/não realizado separado da presença/falta dos alunos. |
| Presença e relatório de treino | Treinador | RF-06, RF-07 | Presente/falta por aluno; um relatório por sessão, rascunho/finalizado, volume com unidade e intensidade Borg CR10 (0–10). |
| Notificação de sessão pendente | Treinador | RF-08 (fora do escopo) | Aviso por e-mail; classificado como exceção já implementada. |

## Regras de consistência visual

- Usar GAAP como nome do produto e os três perfis do cenário como nomenclatura.
- Usar “Serviço” para Treino, Fisioterapia, Psicologia e Nutrição; usar “Sessão” como ocorrência agendada e “Atendimento” para os serviços de saúde.
- Não incluir módulos financeiros, prontuário, dashboards analíticos, torneios, planos, responsáveis legais ou aula experimental sem nova decisão de escopo.
- Manter a distinção entre regra proposta e decisão confirmada; consultar as pendências do [levantamento de requisitos](levreq.md).
- A variante de recusa do agendamento foi acrescentada em desktop e mobile, com indisponibilidade, bloqueio, conflito do aluno e incompatibilidade. O desktop também mostra a capacidade excedida (7/6); no mobile aparece o limite geral de 6 alunos por sessão.
- Ainda faltam a configuração de horários e bloqueios e os estados de sucesso do agendamento; atualmente há apenas atalhos e um resumo das validações.
- A variante mostra a recusa por conflito de horário do aluno; essa verificação segue pendente de confirmação.
- Mostrar os estados salvo/erro da presença nos atendimentos e uma tela do relatório finalizado somente para leitura. Os exemplos atuais já mostram presença/falta, campos do relatório por sessão, rascunho, volume com unidade e intensidade Borg CR10.
- O filtro “Todos os serviços” da agenda do Treinador pode reunir mais de um serviço, conforme esclarecimento de Pedro Lucas em 03/11/2026; deve incluir somente os serviços vinculados ao profissional.
- Representar os estados realizado/não realizado de RF-10 nas agendas de Treinador e Profissional de Saúde, separadamente da presença/falta. RF-09 e RF-11 continuam dependendo das definições de pendências e indicadores.
- Validar a experiência com usuários; não há resultados de teste registrados.

## Dependências

- O [protótipo de baixa fidelidade](../Iniciacao/prototipo_baixa_fidelidade.md) representa os mesmos fluxos e IDs.
- A [tabela de rastreabilidade](rastreabilidade.md) deve apontar cada tela aos requisitos correspondentes.
