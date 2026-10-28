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
| Agenda e configuração | Administrador | RF-03, RF-04, RF-05 | Consultar disponibilidade/bloqueios e confirmar agendamento. |
| Agenda pessoal | Treinador | RF-04 | Consultar sessões sob sua responsabilidade. |
| Atendimentos | Profissional de Saúde | RF-04, RF-06 | Consultar apenas serviço e agenda atribuídos; registrar presença/falta dos alunos atendidos. |
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
  Participantes | "Selecionar alunos, se aplicável"
  [Validar e confirmar]
  Resultado | "Confirmado ou rejeitado com o motivo"
}
@endsalt
```

## Agenda do Treinador — RF-04, RF-06, RF-07

```plantuml
@startsalt
{+
  {* <b>GAAP — Minha agenda}
  Data inicial | "dd/mm/aaaa"
  Data final | "dd/mm/aaaa"
  Serviço | "Todos os meus serviços"
  [Consultar]
  ..
  <b>Sessões do período
  09:00 | "Sessão 01 — Treino — Agendada"
  10:00 | "Sessão 02 — Treino — Realizada"
  [Abrir sessão]
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

## Atendimentos do Profissional de Saúde — RF-04, RF-06

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

## Referência visual — protótipo de alta fidelidade

As telas abaixo são os exports atuais de alta fidelidade. Os wireframes PlantUML acima continuam sendo a referência de baixa fidelidade; as imagens não alteram o escopo nem resolvem as decisões ainda pendentes. **Os exports ainda não mostram o registro de presença/falta nos atendimentos de saúde nem todos os campos e estados definidos para o relatório de treino.** O arquivo editável está no [Figma](https://www.figma.com/design/7a3PVqNYNlwLtSgN4sfiU4/GAAP-%E2%80%94-Prot%C3%B3tipo-de-alta-fidelidade).

=== "Desktop · 1920 × 1080"

    ### Acesso

    ![Protótipo desktop — Acesso](<../assets/Prototipo/desktop/1920×1080 · · Acesso.png>){ width="100%" }

    ### Visão geral

    ![Protótipo desktop — Visão geral](<../assets/Prototipo/desktop/1920×1080 · · Visão geral.png>){ width="100%" }

    ### Cadastros

    ![Protótipo desktop — Cadastros](<../assets/Prototipo/desktop/1920×1080 · · Cadastros.png>){ width="100%" }

    ### Novo agendamento

    ![Protótipo desktop — Novo agendamento](<../assets/Prototipo/desktop/1920×1080 · · Novo agendamento.png>){ width="100%" }

    ### Agenda do treinador

    ![Protótipo desktop — Agenda do treinador](<../assets/Prototipo/desktop/1920×1080 · · Agenda do treinador.png>){ width="100%" }

    ### Atendimentos de saúde

    ![Protótipo desktop — Atendimentos de saúde](<../assets/Prototipo/desktop/1920×1080 · · Atendimentos de saúde.png>){ width="100%" }

=== "Mobile · 390 × 844"

    ### Acesso

    ![Protótipo mobile — Acesso](<../assets/Prototipo/mobile/01 · Acesso · Mobile.png>){ width="390" }

    ### Visão geral

    ![Protótipo mobile — Visão geral](<../assets/Prototipo/mobile/02 · Visão geral · Mobile.png>){ width="390" }

    ### Cadastros

    ![Protótipo mobile — Cadastros](<../assets/Prototipo/mobile/03 · Cadastros · Mobile.png>){ width="390" }

    ### Novo agendamento

    ![Protótipo mobile — Novo agendamento](<../assets/Prototipo/mobile/04 · Novo agendamento · Mobile.png>){ width="390" }

    ### Agenda do treinador

    ![Protótipo mobile — Agenda do treinador](<../assets/Prototipo/mobile/05 · Agenda treinador · Mobile.png>){ width="390" }

    ### Atendimentos de saúde

    ![Protótipo mobile — Atendimentos de saúde](<../assets/Prototipo/mobile/06 · Atendimentos saúde · Mobile.png>){ width="390" }

## Decisões que afetam as telas

- Definir onde a capacidade é configurada e se sessões comportam múltiplos alunos.
- Após a finalização, o relatório fica bloqueado para edição; rascunhos podem ser alterados antes de finalizar.
- A interface é representativa; a experiência visual não foi validada com usuários.
- A notificação por e-mail é RF-08, uma exceção registrada fora do escopo no cenário GAAP.

## Referências

- [Glossário](../Elaboracao/glossario.md)
- [Documento de Visão](documento_de_visao.md)
- [Levantamento de Requisitos](../Elaboracao/levreq.md)
- [Casos de Uso](../Elaboracao/casos_de_uso.md)
