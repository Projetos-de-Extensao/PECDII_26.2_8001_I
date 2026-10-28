---
id: diagrama_de_sequencia
title: Diagramas de Sequência
---
# Diagramas de Sequência dos Fluxos Críticos

Os diagramas usam os perfis e IDs definidos no [levantamento de requisitos](levreq.md). Como o cenário deixa regras e entidades em branco, detalhes marcados como proposta precisam de validação do responsável pelo cenário. Os participantes representam responsabilidades lógicas; não afirmam a arquitetura de classes atual.

## Confirmar agendamento

**Ator:** Administrador. **Requisitos:** RF-03, RF-05. **Regras:** RN-01 a RN-04 e RN-06. **Resultado:** a sessão é confirmada integralmente ou a operação é recusada sem persistência parcial.

```plantuml
@startuml confirmar_agendamento
actor Administrador
boundary "Cliente/API REST" as API
control "Autorização" as Auth
control "AgendamentoService" as Agendamento
database "Banco relacional" as DB

Administrador -> API: POST /sessoes (serviço, profissional, início, fim, participantes)
API -> Auth: validar token e perfil
alt não autenticado ou perfil diferente de Administrador
  Auth --> API: acesso negado
  API --> Administrador: 401/403
else autorizado
  Auth --> API: autorizado
  API -> Agendamento: confirmar(dados)
  Agendamento -> Agendamento: validar payload, compatibilidade, disponibilidade, bloqueios, conflito e capacidade
  Agendamento -> DB: iniciar transação e bloquear recursos relevantes
  Agendamento -> DB: confirmar que as regras continuam válidas
  alt alguma validação falhou
    Agendamento -> DB: rollback, se a transação foi iniciada
    Agendamento --> API: 400 (payload) ou 409 (regra) + motivo
    API --> Administrador: mostrar erro e motivo
  else todas as validações passaram
    Agendamento -> DB: gravar sessão e participantes
    Agendamento -> DB: commit
    Agendamento --> API: sessão confirmada
    API --> Administrador: 201 + sessão
  end
end
@enduml
```

O bloco de validação cobre os campos obrigatórios e intervalo (400), compatibilidade do profissional (RN-04), bloqueio e sobreposição de horários (RN-01, RN-03) e capacidade máxima (RN-02). Uma falha informa o motivo específico e não grava uma sessão parcial. A confirmação usa transação para impedir que solicitações concorrentes ultrapassem a capacidade (RN-06).

**Decisões a confirmar:** qual é o limite de capacidade e se sessões podem ser em grupo (cliente/responsável pelo cenário). A disponibilidade e os bloqueios já foram definidos como gerais por profissional, compartilhados entre serviços; a compatibilidade do profissional com cada serviço é verificada separadamente.

## Finalizar relatório de treino

**Ator:** Treinador responsável. **Requisitos:** RF-01, RF-06, RF-07. **Regra:** RN-05. **Resultado:** relatório associado à sessão de Treino é finalizado apenas pelo Treinador autorizado e com os dados obrigatórios válidos. Para atendimentos de saúde, o Profissional de Saúde responsável registra presença/falta pelo fluxo UC-06.

```plantuml
@startuml finalizar_relatorio_treino
actor Treinador
boundary "Cliente/API REST" as API
control "Autorização" as Auth
control "RelatorioTreinoService" as Relatorio
database "Banco relacional" as DB

Treinador -> API: PUT /sessoes/{id}/relatorio (relatório, presenças)
API -> Auth: validar token e perfil
alt não autenticado ou perfil diferente de Treinador
  Auth --> API: acesso negado
  API --> Treinador: 401/403
else treinador autenticado
  Auth --> API: autorizado
  API -> Relatorio: finalizar(sessaoId, treinador, dados)
  Relatorio -> DB: carregar sessão e vínculo do profissional
  Relatorio -> Relatorio: validar sessão, vínculo, campos e presenças
  alt sessão inexistente, sem permissão ou dados inválidos
    Relatorio --> API: 404/403/400 + motivo
    API --> Treinador: mostrar erro e motivo
  else sessão, permissão e dados válidos
    Relatorio -> DB: iniciar transação
    Relatorio -> DB: persistir relatório e presenças
    Relatorio -> DB: marcar relatório como finalizado
    Relatorio -> DB: commit
    Relatorio --> API: relatório finalizado
    API --> Treinador: 200 + relatório
  end
end
@enduml
```

**Definições:** um relatório por sessão, com participantes vinculados à sessão; pode ser salvo como rascunho e finalizado após validação. Registra objetivo, exercícios executados, volume como valor + unidade e intensidade da sessão pela escala Borg CR10 (0–10). Para treino resistido, volume-carga pode ser calculado como séries × repetições × carga em kg; modalidades diferentes mantêm suas próprias unidades, sem somar medidas incompatíveis. Após finalização, o relatório é imutável e qualquer tentativa de edição deve ser recusada. Presença/falta também se aplica aos atendimentos de saúde, registrada pelo profissional responsável; esse fluxo é descrito no UC-06.

## Rastreabilidade

| Fluxo | Casos de Uso | Requisitos | Regras |
|---|---|---|---|
| Confirmar agendamento | UC-05 | RF-03, RF-05 | RN-01, RN-02, RN-03, RN-04, RN-06 |
| Finalizar relatório de treino | UC-07 | RF-01, RF-06, RF-07 | RN-05 |
