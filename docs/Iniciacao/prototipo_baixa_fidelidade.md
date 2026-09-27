---
id: prototipobaixa
title: Protótipo Baixa Fidelidade
---
## Introdução

<p align = "justify">
O protótipo de baixa fidelidade é uma representação simples e rápida da solução, usada para validar fluxos e funcionalidades antes da implementação. Como o sistema da PKZ Lab é unicamente back-end, o protótipo não representa telas, e sim a API: quais endpoints existem, o que cada request recebe, o que responde e quais erros podem acontecer. Ele serve de base para os casos de uso, para o diagrama de classes e para a implementação em Django.
</p>

## Metodologia

A equipe definiu os fluxos a partir dos requisitos elicitados no [Brainstorm](Brainstorm.md) (BS01 a BS10) e do escopo da [Pesquisa](pesquisa.md), priorizando o que é central para o problema da PKZ Lab: cadastro, alocação de sessão sem conflito, cancelamento/remarcação e consulta de agenda. Para cada fluxo foram identificados os endpoints, as entradas, as respostas de sucesso e os erros esperados. Os fluxos foram desenhados em PlantUML como diagramas de sequência entre o cliente da API e o sistema, no nível de requests HTTP (sem detalhar classes internas, o que fica para os diagramas de sequência da Elaboração).

## Protótipo de Baixa Fidelidade

### Versão 1.0

### Fluxos representados

| Fluxo | Descrição | Requisito(s) |
| -- | -- | -- |
| 1. Autenticação | Login e obtenção do token de acesso por perfil | BS03 |
| 2. Cadastro de aluno e responsável | Cadastro do aluno, com responsável e consentimento quando menor | BS01, BS02 |
| 3. Cadastros da coordenação | Espaços, professores/instrutores e atividades | BS03, BS04, BS05 |
| 4. Agendamento de sessão | Alocação de espaço + horário + profissional com verificação de conflito e capacidade | BS06, BS07, BS09 |
| 5. Cancelamento e remarcação | Alteração de sessão com histórico | BS08 |
| 6. Consulta de agenda | Agenda por perfil com filtros | BS10 |

### Endpoints principais

| Método | Endpoint | Descrição | Perfil |
| -- | -- | -- | -- |
| POST | `/api/auth/login/` | Autentica o usuário e retorna o token | Todos |
| POST | `/api/alunos/` | Cadastra aluno | Coordenação |
| GET | `/api/alunos/{id}/` | Consulta aluno | Coordenação, Responsável |
| POST | `/api/responsaveis/` | Cadastra responsável legal e vincula a um ou mais alunos | Coordenação |
| POST | `/api/alunos/{id}/consentimento/` | Registra a autorização do responsável (LGPD) | Responsável |
| POST / GET / PUT | `/api/espacos/` | Cadastra, lista e atualiza espaços | Coordenação |
| POST / GET / PUT | `/api/profissionais/` | Cadastra, lista e atualiza professores/instrutores e disponibilidades | Coordenação |
| POST / GET / PUT | `/api/atividades/` | Cadastra, lista e atualiza atividades | Coordenação |
| POST | `/api/sessoes/` | Agenda sessão regular ou aula experimental | Coordenação |
| POST | `/api/sessoes/{id}/remarcacao/` | Remarca sessão | Coordenação, Aluno, Responsável |
| POST | `/api/sessoes/{id}/cancelamento/` | Cancela sessão | Coordenação, Aluno, Responsável |
| POST | `/api/sessoes/{id}/registro/` | Registra presença e observações da sessão | Professor |
| GET | `/api/agenda/` | Consulta agenda com filtros | Todos |

### Respostas e erros padrão

| Código | Quando ocorre |
| -- | -- |
| 200 OK | Consulta ou atualização realizada |
| 201 Created | Recurso criado (cadastro, sessão, alteração) |
| 400 Bad Request | Dados obrigatórios ausentes ou em formato inválido |
| 401 Unauthorized | Token ausente, inválido ou expirado |
| 403 Forbidden | Perfil sem permissão para a operação (ex.: aluno tentando cadastrar espaço) |
| 404 Not Found | Recurso inexistente (aluno, espaço, sessão...) |
| 409 Conflict | Conflito de espaço, de profissional ou de capacidade |
| 422 Unprocessable Entity | Regra de negócio violada (menor sem consentimento, sessão já realizada, fora da antecedência mínima) |

### Fluxo 1 - Autenticação

```plantuml
@startuml fluxo_autenticacao
actor "Usuário" as U
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

U -> API : POST /api/auth/login/\n{ email, senha }
API -> DB : buscar usuário por e-mail
DB --> API : usuário
alt credenciais válidas
  API --> U : 200 OK\n{ token, perfil }
else credenciais inválidas
  API --> U : 401 Unauthorized\n{ erro: "E-mail ou senha inválidos" }
end
@enduml
```

### Fluxo 2 - Cadastro de aluno e responsável legal

```plantuml
@startuml fluxo_cadastro_aluno
actor "Coordenação" as C
actor "Responsável Legal" as R
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

C -> API : POST /api/alunos/\n{ nome, data_nascimento, telefone, email }
alt dados inválidos
  API --> C : 400 Bad Request\n{ campos com erro }
else aluno maior de idade
  API -> DB : salvar aluno
  API --> C : 201 Created\n{ id, nome, situacao: "ativo" }
else aluno menor de 18 anos
  API -> DB : salvar aluno
  API --> C : 201 Created\n{ id, nome, situacao: "aguardando_responsavel" }
  C -> API : POST /api/responsaveis/\n{ nome, cpf, telefone, email, alunos: [id] }
  API -> DB : salvar responsável e vínculo
  API --> C : 201 Created\n{ id, alunos, consentimento: "pendente" }
  R -> API : POST /api/alunos/{id}/consentimento/\n{ autorizado: true }
  alt responsável vinculado ao aluno
    API -> DB : registrar consentimento (data/hora)
    API --> R : 201 Created\n{ aluno, situacao: "ativo" }
  else responsável sem vínculo
    API --> R : 403 Forbidden
  end
end
@enduml
```

### Fluxo 3 - Cadastros da coordenação (espaço, profissional e atividade)

```plantuml
@startuml fluxo_cadastros_coordenacao
actor "Coordenação" as C
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

C -> API : POST /api/espacos/\n{ nome, capacidade }
alt capacidade <= 0 ou nome duplicado
  API --> C : 400 Bad Request
else válido
  API -> DB : salvar espaço
  API --> C : 201 Created\n{ id, nome, capacidade }
end

C -> API : POST /api/profissionais/\n{ nome, contato, especialidades,\n  disponibilidades: [{ dia, inicio, fim }] }
alt horário final antes do inicial
  API --> C : 400 Bad Request
else válido
  API -> DB : salvar profissional
  API --> C : 201 Created\n{ id, nome, especialidades }
end

C -> API : POST /api/atividades/\n{ nome, duracao_min, modalidade,\n  profissionais: [id], espacos: [id] }
alt profissional ou espaço inexistente
  API --> C : 404 Not Found
else válido
  API -> DB : salvar atividade e vínculos
  API --> C : 201 Created\n{ id, nome, modalidade }
end

note over C, API
  Qualquer outro perfil que tente
  esses endpoints recebe 403 Forbidden
end note
@enduml
```

### Fluxo 4 - Agendamento de sessão com verificação de conflito

```plantuml
@startuml fluxo_agendamento_sessao
actor "Coordenação" as C
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

C -> API : POST /api/sessoes/\n{ data, inicio, fim, atividade, espaco,\n  profissional, alunos: [id], tipo: "regular" | "experimental" }
API -> DB : buscar atividade, espaço, profissional e alunos
alt algum recurso inexistente
  API --> C : 404 Not Found
else profissional não habilitado ou espaço inadequado
  API --> C : 422 Unprocessable Entity
else aluno menor sem consentimento
  API --> C : 422 Unprocessable Entity\n{ erro: "Aluno sem autorização do responsável" }
else recursos válidos
  API -> DB : sessões do espaço no intervalo
  API -> DB : sessões e disponibilidade do profissional
  alt espaço ocupado
    API --> C : 409 Conflict\n{ erro: "Espaço ocupado no horário" }
  else profissional ocupado ou indisponível
    API --> C : 409 Conflict\n{ erro: "Profissional indisponível no horário" }
  else alunos > capacidade do espaço
    API --> C : 409 Conflict\n{ erro: "Capacidade do espaço excedida" }
  else sem conflito
    API -> DB : salvar sessão (situacao: "agendada")
    API --> C : 201 Created\n{ id, data, inicio, fim, atividade,\n  espaco, profissional, alunos, tipo }
  end
end
@enduml
```

### Fluxo 5 - Cancelamento e remarcação de sessão

```plantuml
@startuml fluxo_cancelamento_remarcacao
actor "Aluno / Responsável /\nCoordenação" as U
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

== Cancelamento ==
U -> API : POST /api/sessoes/{id}/cancelamento/\n{ motivo }
API -> DB : buscar sessão
alt sessão inexistente
  API --> U : 404 Not Found
else usuário sem vínculo com a sessão
  API --> U : 403 Forbidden
else sessão já realizada ou fora da antecedência mínima
  API --> U : 422 Unprocessable Entity
else permitido
  API -> DB : atualizar situação e liberar recursos
  API -> DB : registrar alteração no histórico
  API --> U : 200 OK\n{ id, situacao: "cancelada" }
end

== Remarcação ==
U -> API : POST /api/sessoes/{id}/remarcacao/\n{ nova_data, novo_inicio, novo_fim, motivo }
API -> DB : buscar sessão
alt sessão já realizada ou fora da antecedência mínima
  API --> U : 422 Unprocessable Entity
else conflito no novo horário
  API --> U : 409 Conflict\n{ erro: motivo do conflito }
else permitido
  API -> DB : atualizar horário e liberar o anterior
  API -> DB : registrar alteração no histórico
  API --> U : 200 OK\n{ id, data, inicio, fim, situacao: "remarcada" }
end
@enduml
```

### Fluxo 6 - Consulta de agenda

```plantuml
@startuml fluxo_consulta_agenda
actor "Usuário" as U
participant "API PKZ Lab" as API
database "Banco de Dados" as DB

U -> API : GET /api/agenda/?data_inicio=&data_fim=\n&atividade=&espaco=&profissional=&aluno=
alt filtro inválido (data final antes da inicial)
  API --> U : 400 Bad Request
else válido
  API -> API : restringir pelo perfil do token
  note right of API
    Aluno: suas sessões
    Responsável: sessões dos alunos vinculados
    Professor: sessões em que está alocado
    Coordenação: todas
  end note
  API -> DB : buscar sessões filtradas
  DB --> API : sessões
  API --> U : 200 OK\n[ { data, inicio, fim, atividade, profissional,\n    espaco, alunos*, situacao, historico } ]
end
@enduml
```

\* A lista de alunos da sessão só é retornada para professor e coordenação.

## Conclusão

<p align = "justify">
A elaboração do protótipo de baixa fidelidade permitiu definir, antes da implementação, os endpoints da API da PKZ Lab, o formato das entradas e respostas e os erros esperados em cada fluxo. Isso deixou claras as regras centrais do sistema, como a verificação de conflito de espaço, profissional e capacidade e a exigência de consentimento do responsável para alunos menores, e serve de referência para os casos de uso, o diagrama de classes e a construção da API.
</p>

## Referências

> PlantUML Sequence Diagram. Disponível em: https://plantuml.com/sequence-diagram

> MDN Web Docs. HTTP response status codes. Disponível em: https://developer.mozilla.org/pt-BR/docs/Web/HTTP/Status

> Protótipo de Baixa Fidelidade. Disponível em: https://jonh-carvalho.github.io/PECDII_26.2_8001/Iniciacao/prototipo_baixa_fidelidade/

## Autor(es)

| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 26/09/2026 | 1.0 | Criação do protótipo de baixa fidelidade da API com fluxos, endpoints e erros | Lucas Santos |
