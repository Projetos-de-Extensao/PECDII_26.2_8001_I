---
id: casos_de_uso
title: Casos de Uso
---
# Casos de Uso do GAAP

Este documento usa exclusivamente os perfis do cenário GAAP e rastreia os requisitos definidos em [LevReq](levreq.md). “Aula experimental”, “responsável legal”, “coordenação” e os fluxos de cancelamento/remarcação encontrados em artefatos anteriores não estão incluídos no MVP por não constarem no cenário atual; ver [Glossário](glossario.md).

## Atores

| Ator | Responsabilidade no cenário |
|---|---|
| Administrador | Mantém cadastros, serviços, horários e bloqueios, consulta pendências e solicita confirmação de sessões. |
| Treinador | Consulta agenda própria, registra presença/falta e cria/finaliza relatórios de treino. |
| Profissional de Saúde | Consulta atendimentos dos serviços e da agenda atribuídos; registra presença/falta dos alunos desses atendimentos. |

## Casos de uso e rastreabilidade

| ID | Caso de uso | Ator primário | Requisitos |
|---|---|---|---|
| UC-01 | Autenticar e autorizar acesso | Todos | RF-01 |
| UC-02 | Manter alunos, profissionais e serviços | Administrador | RF-02 |
| UC-03 | Configurar disponibilidade e bloqueios | Administrador | RF-03 |
| UC-04 | Consultar agenda autorizada | Todos | RF-04 |
| UC-05 | Confirmar agendamento | Administrador | RF-03, RF-05; RN-07 |
| UC-06 | Registrar presença/falta | Treinador ou Profissional de Saúde responsável | RF-06 |
| UC-07 | Criar e finalizar relatório de treino | Treinador | RF-07 |
| UC-08 | Receber aviso de sessão pendente por e-mail | Treinador | RF-08 (fora do escopo) |
| UC-09 | Consultar pendências operacionais | Administrador | RF-09 |
| UC-10 | Registrar compromisso ministrado | Treinador ou Profissional de Saúde responsável | RF-10 |
| UC-11 | Consultar dashboard simples | Administrador | RF-11 |
| UC-12 | Receber lembrete de relatório de treino pendente | Treinador responsável | RF-12 |

## Diagrama de casos de uso

```plantuml
@startuml gaap_casos_de_uso
left to right direction
skinparam actorStyle awesome

actor Administrador as Admin
actor Treinador as Trainer
actor "Profissional de Saúde" as Health

rectangle "API GAAP" {
  usecase "UC-01\nAutenticar e autorizar" as UC01
  usecase "UC-02\nManter cadastros e serviços" as UC02
  usecase "UC-03\nConfigurar disponibilidade e bloqueios" as UC03
  usecase "UC-04\nConsultar agenda autorizada" as UC04
  usecase "UC-05\nConfirmar agendamento" as UC05
  usecase "Validar conflitos do profissional e do aluno,\nbloqueio, capacidade e compatibilidade" as VALID
  usecase "UC-06\nRegistrar presença/falta" as UC06
  usecase "UC-07\nCriar/finalizar relatório de treino" as UC07
  usecase "UC-08\nEnviar aviso de sessão pendente\n(exceção fora do escopo)" as UC08
  usecase "UC-09\nConsultar pendências" as UC09
  usecase "UC-10\nRegistrar compromisso ministrado" as UC10
  usecase "UC-11\nConsultar dashboard simples" as UC11
  usecase "UC-12\nReceber lembrete de relatório pendente" as UC12
}

Admin --> UC01
Admin --> UC02
Admin --> UC03
Admin --> UC04
Admin --> UC05
Admin --> UC09
Admin --> UC11
Trainer --> UC01
Trainer --> UC04
Trainer --> UC06
Trainer --> UC07
Trainer --> UC10
Trainer --> UC12
Trainer --> UC08
Health --> UC01
Health --> UC04
Health --> UC06
Health --> UC10
UC05 ..> VALID : <<include>>
@enduml
```

## UC-01 — Autenticar e autorizar acesso

- **Atores:** Administrador, Treinador e Profissional de Saúde.
- **Pré-condição:** perfil e credenciais cadastrados.
- **Fluxo principal:** usuário envia credenciais; API valida; API associa o perfil e permite somente as operações e os dados autorizados.
- **Alternativas:** credencial inválida resulta em 401; usuário autenticado sem autorização resulta em 403.
- **Pós-condição:** requisição autorizada ou negada sem exposição de dados indevidos.
- **Requisitos:** RF-01; RNF-02, RNF-04, RNF-06 (auditoria da criação, sem credenciais).

## UC-02 — Manter alunos, profissionais e serviços

- **Ator:** Administrador.
- **Pré-condição:** Administrador autenticado e autorizado.
- **Fluxo principal:** Administrador cria, consulta ou atualiza um cadastro; API valida os campos e persiste os dados.
- **Alternativas:** perfil sem permissão recebe 403; payload inválido recebe 400 e identificação dos campos.
- **Pós-condição:** cadastro válido disponível para operações de agenda.
- **Requisitos:** RF-02; RNF-01, RNF-04.

## UC-03 — Configurar disponibilidade e bloqueios

- **Ator:** Administrador.
- **Pré-condição:** Administrador autenticado; profissional existente.
- **Fluxo principal:** Administrador informa profissional e faixa de disponibilidade ou bloqueio; API valida intervalo; registra a configuração e a exibe na agenda.
- **Alternativas:** intervalo inválido recebe 400; usuário sem permissão recebe 403.
- **Pós-condição:** regra de disponibilidade/bloqueio passa a ser considerada em novos agendamentos.
- **Requisitos:** RF-03; RN-03; RNF-04.

## UC-04 — Consultar agenda autorizada

- **Atores:** Administrador, Treinador e Profissional de Saúde.
- **Pré-condição:** usuário autenticado.
- **Fluxo principal:** usuário consulta um período; API restringe a resposta ao escopo do perfil: administrador consulta a operação, treinador consulta sessões sob sua responsabilidade e serviços a ele vinculados, e profissional de saúde consulta atendimentos dos serviços e agenda a ele vinculados. Treinadores e Profissionais de Saúde podem filtrar por um serviço vinculado ao próprio perfil.
- **Alternativas:** período inválido recebe 400; usuário não pode ampliar o escopo de acesso alterando filtros.
- **Pós-condição:** API retorna apenas registros autorizados.
- **Requisitos:** RF-04; RNF-04.

## UC-05 — Confirmar agendamento

- **Ator:** Administrador.
- **Pré-condição:** Administrador autenticado; aluno, profissional e serviço cadastrados.
- **Fluxo principal:** Administrador informa serviço, profissional, intervalo e participantes; API valida payload, compatibilidade do profissional, disponibilidade, bloqueios, conflitos de horário do profissional e dos alunos participantes e capacidade; persiste e confirma a sessão integralmente.
- **Alternativas:** conflito do profissional retorna “O profissional já possui um compromisso neste horário”; conflito de participante retorna “O aluno já possui um compromisso neste horário”. Qualquer falha resulta em erro observável, sem persistir sessão parcial; concorrência não pode ultrapassar a capacidade.
- **Pós-condição:** sessão confirmada e visível aos perfis autorizados.
- **Requisitos:** RF-03, RF-05; RN-01 a RN-04, RN-06 e RN-07; RNF-01, RNF-03, RNF-04.
- **Diagrama:** [Confirmar agendamento](diagrama_de_sequencia.md#confirmar-agendamento).

## UC-06 — Registrar presença/falta

- **Atores:** Treinador responsável por sessão de Treino; Profissional de Saúde responsável por atendimento vinculado ao seu serviço e agenda.
- **Pré-condição:** sessão/atendimento existente; profissional autenticado e associado ao compromisso.
- **Fluxo principal:** profissional seleciona o compromisso e informa presença/falta por aluno participante; API valida os participantes e salva o resultado.
- **Alternativas:** profissional diferente do responsável recebe 403; participante inexistente ou situação inválida recebe 400/404.
- **Pós-condição:** presença/falta persistida por participante.
- **Requisitos:** RF-06; RN-05; RNF-04, RNF-05.

## UC-07 — Criar e finalizar relatório de treino

- **Ator:** Treinador responsável pela sessão.
- **Pré-condição:** sessão de Treino realizada e Treinador autorizado.
- **Fluxo principal:** Treinador responsável cria um relatório associado somente à sessão, registra objetivo, exercícios executados, volume total com unidade e intensidade Borg CR10 (0–10), e pode salvá-lo como rascunho. Ao finalizar, a API valida os campos obrigatórios e associa o relatório à lista de participantes da sessão. Se a sessão for reatribuída enquanto o relatório for rascunho, o responsável atual passa a poder editá-lo; o vínculo do relatório à sessão não muda.
- **Alternativas:** perfil sem permissão recebe 403; sessão inexistente recebe 404; payload incompleto/inválido impede a finalização e recebe 400; rascunhos podem permanecer incompletos; relatório finalizado não pode ser alterado.
- **Pós-condição:** há no máximo um relatório por sessão; fica como rascunho ou finalizado e consultável por perfis autorizados.
- **Requisitos:** RF-07; RN-05; RNF-01, RNF-04, RNF-06.
- **Diagrama:** [Finalizar relatório de treino](diagrama_de_sequencia.md#finalizar-relatorio-de-treino).

## UC-08 — Receber aviso por e-mail de sessão pendente

- **Ator:** Treinador com e-mail cadastrado; serviço de e-mail é ator externo.
- **Pré-condição:** sessão permanece agendada por 30 minutos após o fim previsto.
- **Fluxo principal:** tarefa agendada localiza sessões elegíveis; envia uma mensagem ao Treinador e registra o envio para evitar duplicidade.
- **Alternativa:** sem e-mail, o envio é ignorado e registrado no log.
- **Pós-condição:** aviso enviado uma única vez por sessão.
- **Requisito:** RF-08. **Fora do escopo do cenário, mantido por recomendação do professor em 14/10/2026.**

## UC-09 — Consultar pendências operacionais

- **Ator:** Administrador.
- **Pré-condição:** Administrador autenticado e autorizado.
- **Fluxo principal:** Administrador consulta compromissos cujo horário terminou, exceto cancelados, com ao menos um participante sem presença/falta registrada; também consulta sessões de Treino sem relatório ou com relatório em rascunho. Cada item identifica motivo e responsável; filtros permitem selecionar o tipo de pendência, o menu mostra o total, e atalhos abrem os detalhes sem conceder permissão para alterar presença ou relatório.
- **Alternativas:** período inválido recebe 400; perfil sem permissão recebe 403.
- **Pós-condição:** lista de pendências retornada sem alterar os compromissos.
- **Requisito:** RF-09. Treinador e Profissional de Saúde não acessam a visão completa.

## UC-10 — Registrar compromisso ministrado

- **Atores:** Treinador ou Profissional de Saúde responsável.
- **Pré-condição:** compromisso atribuído ao profissional autenticado.
- **Fluxo principal:** depois do horário previsto, o profissional responsável registra se a sessão ou o atendimento foi realizado ou não realizado. Essa informação é independente da presença/falta dos participantes.
- **Alternativas:** usuário sem vínculo recebe 403; estado inválido recebe 400.
- **Pós-condição:** situação do compromisso atualizada.
- **Requisitos:** RF-10; RNF-04, RNF-06.

## UC-11 — Consultar dashboard simples

- **Ator:** Administrador.
- **Pré-condição:** Administrador autenticado e autorizado.
- **Fluxo principal:** Administrador consulta, para um período selecionado por controles de data visíveis, a quantidade de compromissos por serviço e situação (agendado, realizado, não realizado ou cancelado). O mês atual é o período padrão; linhas aparecem por total geral decrescente e categorias sem ocorrências exibem zero ou traço. Como opção visual, realizados podem receber destaque verde claro e cancelados/não realizados, vermelho claro.
- **Alternativa:** perfil sem permissão recebe 403.
- **Pós-condição:** visão somente de leitura exibida.
- **Requisito:** RF-11. A consulta é somente de leitura e exclusiva do Administrador; não inclui análises adicionais.

## UC-12 — Receber lembrete de relatório de treino pendente

- **Ator:** Treinador responsável pela sessão de Treino.
- **Pré-condição:** sessão de Treino terminou há 24 horas e continua sem relatório ou com relatório em rascunho.
- **Fluxo principal:** tarefa agendada localiza sessões elegíveis, envia um lembrete por e-mail ao Treinador responsável e registra o envio para não duplicá-lo.
- **Alternativa:** relatório finalizado antes do envio torna a sessão inelegível; sem e-mail cadastrado, o envio é ignorado e registrado no log.
- **Pós-condição:** no máximo um lembrete é enviado por sessão.
- **Requisito:** RF-12.

## Referências

- [Cenário GAAP](../Iniciacao/cenario.md)
- [Glossário](glossario.md)
- [Levantamento de Requisitos](levreq.md)
- [Tabela de rastreabilidade](rastreabilidade.md)
