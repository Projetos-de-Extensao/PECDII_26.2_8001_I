---
id: prototipo_baixa_fidelidade
title: Protótipo de Baixa Fidelidade
---
# Protótipo de Baixa Fidelidade — GAAP

Este protótipo de navegação usa os perfis do cenário GAAP e os IDs RF do [levantamento](../Elaboracao/levreq.md). É uma proposta de telas para uma API consumida por cliente web; a interface não faz parte da entrega do backend. Campos ainda não definidos pelo cenário estão identificados como pendentes.

## Mapa das telas

| Tela | Perfil | Requisitos | Ações principais |
|---|---|---|---|
| Acesso | Todos | RF-01 | Autenticar; apresentar acesso negado. |
| Cadastros | Administrador | RF-02 | Manter aluno, profissional e serviço. |
| Visão geral e pendências | Administrador | RF-04, RF-09, RF-11 | Consultar a operação e as pendências; representar os filtros de RF-09 e o dashboard de RF-11 já definido. |
| Agenda e configuração | Administrador | RF-03, RF-04, RF-05 | Consultar disponibilidade/bloqueios e confirmar agendamento sem conflito do profissional ou do aluno. |
| Agenda pessoal | Treinador | RF-04, RF-10 | Consultar sessões sob sua responsabilidade e serviços vinculados; registrar se foram ministradas após o horário previsto. |
| Atendimentos | Profissional de Saúde | RF-04, RF-06, RF-10 | Consultar serviços e agenda atribuídos; registrar presença/falta por aluno e se o atendimento foi ministrado, em ações separadas. |
| Presença e relatório | Treinador; Profissional de Saúde (presença nos atendimentos) | RF-06, RF-07 | Registrar presença/falta em sessões e atendimentos; Treinador finaliza relatório de treino. |
| Aviso de sessão pendente | Treinador | RF-08 (fora do escopo) | Receber o aviso excepcional por e-mail. |

## Acesso — RF-01

```plantuml
@startsalt
{+
  {* <b>GAAP — Entrar}
  E-mail | "usuario@exemplo.com"
  Senha | "**************"
  [Entrar]
  ..
  Status | "Credencial inválida ou perfil sem permissão"
}
@endsalt
```

## Cadastros — Administrador — RF-02

```plantuml
@startsalt
{+
  {* <b>GAAP — Cadastros}
  [Alunos] | [Profissionais] | [Serviços]
  --
  Nome | "Digite o nome"
  E-mail/contato | "Digite e-mail ou telefone"
  Perfil profissional | "Selecionar perfil (Treinador ou Profissional de Saúde)"
  Serviço | "Selecionar serviço (Treino, Fisioterapia, Psicologia ou Nutrição)"
  [Salvar] | [Cancelar]
  Status | "Cadastro salvo ou campo obrigatório inválido"
}
@endsalt
```

## Visão geral e pendências — Administrador — RF-04, RF-09, RF-11

```plantuml
@startsalt
{+
  {* <b>GAAP — Visão geral}
  [Consultar agenda] | [Consultar pendências]
  <b>Pendências operacionais (RF-09)
  Presença/falta | "Compromissos encerrados sem registro"
  Relatório | "Sessões de Treino sem relatório ou com rascunho"
  ..
  <b>Dashboard simples (RF-11)
  Indicadores | "Quantidade por serviço e situação; mês atual por padrão"
}
@endsalt
```

Os critérios de RF-09 e RF-11 foram definidos no registro de decisões D-11, D-12 e D-15. O protótipo ainda precisa mostrar os filtros de pendência e os controles de período e agrupamento do dashboard.

## Agenda e confirmação — Administrador — RF-03, RF-04, RF-05

```plantuml
@startsalt
{+
  {* <b>GAAP — Agenda}
  Início do período | "dd/mm/aaaa"
  Fim do período | "dd/mm/aaaa"
  Serviço | "Todas as categorias de serviço"
  Profissional | "Selecionar profissional"
  [Consultar agenda]
  [Configurar disponibilidade]
  [Registrar bloqueio]
  --
  <b>Confirmar sessão/atendimento
  Data | "dd/mm/aaaa"
  Início | "hh:mm"
  Fim | "hh:mm"
  Serviço | "Selecionar serviço (Treino, Fisioterapia, Psicologia ou Nutrição)"
  Profissional | "Selecionar profissional"
  Participantes | "Selecionar de 1 a 6 alunos"
  [Validar e confirmar]
  Resultado | "Confirmado ou rejeitado com o motivo"
}
@endsalt
```

Ao confirmar, a API também verifica se algum aluno participante já tem compromisso sobreposto e aplica o limite informado de 6 alunos por sessão. Essas verificações não são campos adicionais da tela.

## Agenda do Treinador — RF-04, RF-06, RF-07, RF-10

```plantuml
@startsalt
{+
  {* <b>GAAP — Minha agenda}
  Data inicial | "dd/mm/aaaa"
  Data final | "dd/mm/aaaa"
  Serviço | "Todos os serviços vinculados"
  [Consultar]
  ..
  <b>Sessões do período
  09:00 | "Sessão 01 — Treino — Agendada"
  10:00 | "Sessão 02 — Treino — Realizada"
  [Abrir sessão]
  [Marcar realizada] | [Marcar não realizada] (após o horário previsto)
  ..
  <b>Presença e relatório (sessão de Treino realizada)
  Presença do Aluno 01 | "Selecionar Presente ou Falta"
  Atletas participantes | "Associados à sessão"
  Data, horário e local | "Dados da sessão"
  Objetivo da sessão | "Descrever foco principal"
  Exercícios executados | "Descrever exercícios"
  Volume total | "Valor + unidade da modalidade"
  Intensidade da sessão | "Borg CR10 (0–10)"
  [Salvar rascunho] | [Finalizar relatório]
  Status | "Rascunho editável, finalizado somente leitura ou erro"
}
@endsalt
```

O registro de sessão ministrada é separado da presença/falta e só fica disponível após o horário previsto.

## Atendimentos do Profissional de Saúde — RF-04, RF-06, RF-10

```plantuml
@startsalt
{+
  {* <b>GAAP — Meus atendimentos}
  Data inicial | "dd/mm/aaaa"
  Data final | "dd/mm/aaaa"
  Serviço | "Serviços vinculados"
  [Consultar]
  ..
  <b>Atendimentos do período
  13:00 | "Fisioterapia — Aluno 01 — Agendado"
  14:00 | "Fisioterapia — Aluno 02 — Agendado"
  [Marcar realizado] | [Marcar não realizado] (após o horário previsto)
  ..
  <b>Registrar presença/falta
  Aluno 01 | "Selecionar Presente ou Falta"
  Aluno 02 | "Selecionar Presente ou Falta"
  [Salvar presença]
  Status | "Presença registrada, dados inválidos ou acesso negado"
  ..
  A consulta respeita serviço e agenda atribuídos.
}
@endsalt
```

O registro de atendimento ministrado é separado da presença/falta e só fica disponível após o horário previsto.

## Referência visual — protótipo de alta fidelidade

As telas abaixo são os exports atuais de alta fidelidade. Os wireframes PlantUML acima continuam sendo a referência de baixa fidelidade; as imagens ilustram o escopo e os critérios definidos, mas não cobrem todos os estados necessários. Os exports mostram exemplos de presença/falta em atendimentos e os campos definidos para o relatório de treino, com ações de rascunho e finalização. Foi acrescentada uma variante de recusa de agendamento para desktop e mobile: ambas mostram indisponibilidade, conflito, bloqueio e incompatibilidade; o desktop também explicita capacidade excedida, enquanto o mobile mostra o limite de seis alunos por sessão. **Ainda faltam estados de sucesso/erro para outros fluxos, uma visualização separada do relatório finalizado somente para leitura e as representações visuais de RF-10 e RF-11.** O arquivo editável está no [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Protótipo-de-alta-fidelidade).

| Export atual | IDs relacionados | Cobertura ainda necessária |
|---|---|---|
| Acesso | RF-01 | Estados de credencial inválida e acesso negado. |
| Visão geral | RF-04, RF-09, RF-11 | Pendências conforme critério definido; filtros de tipo, período e agrupamentos do dashboard por serviço/situação ainda precisam de representação visual. |
| Cadastros | RF-02 | Formulário, validação e confirmação. |
| Novo agendamento e recusa | RF-03, RF-05 | A variante desktop mostra capacidade excedida (7/6); ambas mostram indisponibilidade, bloqueio, conflito e incompatibilidade. A configuração de disponibilidade/bloqueios e o estado de sucesso ainda precisam de representação. |
| Agenda do Treinador | RF-04, RF-06, RF-07, RF-10 | Estado finalizado somente para leitura e erros; representação de realizado/não realizado separada da presença ainda falta. |
| Atendimentos de saúde | RF-04, RF-06, RF-10 | Estado salvo e erros da presença/falta; representação de realizado/não realizado separada da presença ainda falta. |

=== "Desktop · 1920 × 1080"

    ### Acesso — RF-01

    ![Protótipo desktop — Acesso](<../assets/Prototipo/desktop/1920×1080 · · Acesso.png>){ width="100%" }

    ### Visão geral — RF-04, RF-09, RF-11 (parcial)

    ![Protótipo desktop — Visão geral](<../assets/Prototipo/desktop/1920×1080 · · Visão geral.png>){ width="100%" }

    ### Cadastros — RF-02 (parcial)

    ![Protótipo desktop — Cadastros](<../assets/Prototipo/desktop/1920×1080 · · Cadastros.png>){ width="100%" }

    ### Novo agendamento — RF-03, RF-05

    ![Protótipo desktop — Novo agendamento](<../assets/Prototipo/desktop/1920×1080 · · Novo agendamento.png>){ width="100%" }

    ### Recusa do agendamento (variante)

    ![Protótipo desktop — Recusa do agendamento](<../assets/Prototipo/desktop/1920×1080 · Agendamento recusado · RF-05.png>){ width="100%" }

    ### Agenda do treinador — RF-04, RF-06, RF-07, RF-10 (parcial)

    ![Protótipo desktop — Agenda do treinador](<../assets/Prototipo/desktop/1920×1080 · · Agenda do treinador.png>){ width="100%" }

    ### Atendimentos de saúde — RF-04, RF-06, RF-10 (parcial)

    ![Protótipo desktop — Atendimentos de saúde](<../assets/Prototipo/desktop/1920×1080 · · Atendimentos de saúde.png>){ width="100%" }

=== "Mobile · 390 × 844"

    ### Acesso — RF-01

    ![Protótipo mobile — Acesso](<../assets/Prototipo/mobile/01 · Acesso · Mobile.png>){ width="390" }

    ### Visão geral — RF-04, RF-09, RF-11 (parcial)

    ![Protótipo mobile — Visão geral](<../assets/Prototipo/mobile/02 · Visão geral · Mobile.png>){ width="390" }

    ### Cadastros — RF-02 (parcial)

    ![Protótipo mobile — Cadastros](<../assets/Prototipo/mobile/03 · Cadastros · Mobile.png>){ width="390" }

    ### Novo agendamento — RF-03, RF-05

    ![Protótipo mobile — Novo agendamento](<../assets/Prototipo/mobile/04 · Novo agendamento · Mobile.png>){ width="390" }

    ### Recusa do agendamento (variante)

    ![Protótipo mobile — Recusa do agendamento](<../assets/Prototipo/mobile/07 · Agendamento recusado · Mobile · RF-05.png>){ width="390" }

    ### Agenda do treinador — RF-04, RF-06, RF-07, RF-10 (parcial)

    ![Protótipo mobile — Agenda do treinador](<../assets/Prototipo/mobile/05 · Agenda treinador · Mobile.png>){ width="390" }

    ### Atendimentos de saúde — RF-04, RF-06, RF-10 (parcial)

    ![Protótipo mobile — Atendimentos de saúde](<../assets/Prototipo/mobile/06 · Atendimentos saúde · Mobile.png>){ width="390" }

## Decisões que afetam as telas

- O professor informou capacidade máxima de 6 alunos por sessão, válida para qualquer serviço conforme esclarecimento de Pedro Lucas; no MVP, a validação usará uma constante no backend, sem configuração administrativa.
- Após a finalização, o relatório fica bloqueado para edição; rascunhos podem ser alterados antes de finalizar.
- A interface é representativa; a experiência visual não foi validada com usuários.
- A notificação por e-mail é RF-08, uma exceção registrada fora do escopo no cenário GAAP.

## Referências

- [Glossário](../Elaboracao/glossario.md)
- [Documento de Visão](documento_de_visao.md)
- [Levantamento de Requisitos](../Elaboracao/levreq.md)
- [Casos de Uso](../Elaboracao/casos_de_uso.md)
