---
id: levantamento_requisitos
title: Levantamento de Requisitos
---
# Levantamento de Requisitos do GAAP

## Base e decisões

Este levantamento parte do [Cenário de Aula: Backend GAAP](../Iniciacao/cenario.md), sobretudo dos três perfis de usuário e dos critérios de aceite da seção 10. O próprio cenário deixa em branco parte das funcionalidades, entidades, regras de negócio e requisitos não funcionais. Por isso, requisitos marcados **(proposta a confirmar)** são hipóteses explícitas da equipe, ainda dependentes de validação com o responsável pelo cenário.

Os IDs RF, RN e RNF são estáveis e devem ser usados nos demais artefatos. O requisito RF-08 registra uma funcionalidade já existente que o cenário lista fora do escopo; não integra o MVP proposto.

## Stakeholders e perfis

| Stakeholder/perfil | Interesse e responsabilidade no recorte inicial |
|---|---|
| Administrador | Mantém cadastros, serviços, horários e bloqueios; consulta pendências operacionais. |
| Treinador | Consulta a própria agenda, registra presença/falta e cria e finaliza relatórios de treino. |
| Profissional de Saúde | Consulta somente atendimentos vinculados ao seu serviço e à sua agenda; registra presença/falta dos alunos atendidos sob sua responsabilidade. |
| Equipe desenvolvedora | Modela, implementa, testa e documenta a API. |
| Responsável pelo cenário/professor | Esclarece as lacunas do enunciado e valida o recorte proposto. |

Aluno é pessoa atendida e dado gerenciado pela API; o cenário não o define como perfil de acesso inicial.

## Requisitos funcionais

Prioridades: **Alta** = necessária para o aceite do MVP; **Média** = apoio ao uso operacional, sujeita à confirmação das lacunas do cenário; **Fora do escopo** = mantida apenas para registrar uma exceção já implementada.

| ID | Requisito | Critério observável de aceite | Prioridade |
|---|---|---|---|
| RF-01 | A API deve autenticar usuários e aplicar autorização conforme os perfis Administrador, Treinador e Profissional de Saúde. | Com credenciais válidas, o usuário acessa apenas operações permitidas ao seu perfil; uma chamada sem autenticação ou sem autorização recebe resposta de acesso negado. | Alta |
| RF-02 | O Administrador deve cadastrar e manter alunos, profissionais e serviços oferecidos. | O Administrador cria, consulta e atualiza cada tipo de cadastro; dados inválidos são rejeitados com indicação do campo. | Alta |
| RF-03 | O Administrador deve configurar horários de disponibilidade e bloqueios gerais na agenda de cada profissional. | A disponibilidade e os bloqueios valem para a agenda inteira do profissional, independentemente do serviço; a consulta apresenta esses períodos e horários inválidos são recusados. A compatibilidade com cada serviço é verificada separadamente. | Alta |
| RF-04 | Cada perfil deve consultar somente a agenda permitida para si. | Administrador consulta a visão operacional; Treinador vê sessões sob sua responsabilidade; Profissional de Saúde vê atendimentos do serviço e agenda a que está vinculado. | Alta |
| RF-05 | O Administrador deve confirmar sessões/atendimentos após validar serviço, disponibilidade, bloqueios, conflitos e capacidade. | A API confirma uma solicitação válida; para cada regra violada, rejeita sem gravar uma sessão parcialmente válida e informa o motivo. | Alta |
| RF-06 | O profissional responsável deve registrar presença ou falta do aluno em sessões de Treino e atendimentos de saúde. | Treinador registra presença/falta nas sessões de Treino sob sua responsabilidade; Profissional de Saúde registra nos atendimentos vinculados à sua agenda e serviço. O sistema rejeita usuário sem vínculo/permissão e valores inválidos. | Alta |
| RF-07 | O Treinador autorizado deve criar, salvar como rascunho e finalizar um relatório por sessão de Treino. | O relatório fica associado à sessão e ao Treinador responsável, identifica os alunos participantes e contém data, horário, local, objetivo, exercícios executados, volume (valor e unidade) e intensidade da sessão na escala Borg CR10 (0–10). Rascunhos podem estar incompletos; a finalização valida os campos obrigatórios e torna o relatório imutável. | Alta |
| RF-08 | O sistema envia ao Treinador uma notificação por e-mail quando uma sessão permanece agendada por 30 minutos após o fim previsto. | Uma sessão elegível gera uma notificação ao profissional com e-mail cadastrado e é marcada para evitar envio duplicado. | Fora do escopo do cenário; exceção implementada por recomendação do professor em 14/10/2026. |

## Regras de negócio

As regras abaixo detalham as lacunas identificadas na issue #59. A regra de capacidade não diz onde o limite é configurado porque o cenário não define essa entidade; essa decisão está pendente de validação.

| ID | Regra | Critério observável | Situação |
|---|---|---|---|
| RN-01 | Uma sessão não pode sobrepor outro compromisso do mesmo profissional; intervalos são tratados como `[início, fim)`. | Uma solicitação que sobrepõe sessão existente é recusada; horários contíguos podem ser aceitos. | Proposta a confirmar |
| RN-02 | A quantidade de participantes ativos não pode ultrapassar a capacidade aplicável ao serviço/sessão. | A API aceita até o limite configurado e recusa o participante excedente. | Proposta a confirmar: definir onde o limite reside |
| RN-03 | A disponibilidade e os bloqueios são gerais por profissional e compartilhados por todos os serviços que ele pode atender. | Sessão de qualquer serviço é recusada se estiver fora da disponibilidade geral ou dentro de bloqueio; compatibilidade profissional-serviço continua sendo validada pela RN-04. | Decisão registrada |
| RN-04 | O profissional designado deve estar habilitado para o serviço solicitado. | Serviço incompatível com o cadastro/vínculo do profissional é recusado. | Proposta a confirmar |
| RN-05 | Somente o profissional responsável e autorizado pode registrar presença/falta no compromisso sob sua responsabilidade; somente o Treinador autorizado pode finalizar relatório de treino. | Treinador atua nas sessões de Treino atribuídas; Profissional de Saúde atua nos atendimentos vinculados ao seu serviço e agenda; usuário sem vínculo recebe acesso negado. | Regra definida para presença; autorização segue os vínculos do cenário |
| RN-06 | Confirmar a sessão e reservar capacidade são uma operação atômica. | Se qualquer validação ou gravação falhar, nenhuma sessão parcial nem reserva é persistida; solicitações concorrentes não excedem a capacidade. | Derivada do requisito de consistência/atomicidade da issue #59; validar implementação |

## Requisitos não funcionais

| ID | Requisito | Critério observável de aceite | Prioridade |
|---|---|---|---|
| RNF-01 | A persistência deve usar banco relacional normalizado com chaves, restrições e índices adequados às consultas de agenda. | Migrações aplicam em banco relacional limpo; integridade referencial e restrições são verificáveis no modelo/DER. | Alta |
| RNF-02 | Senhas nunca devem ser armazenadas em texto puro. | Verificação no banco confirma que a senha está representada por hash produzido pelo mecanismo seguro do framework. | Alta |
| RNF-03 | A confirmação de agendamento deve preservar atomicidade e consistência sob concorrência. | Teste concorrente demonstra que bloqueios, conflitos e capacidade não são violados por duas solicitações simultâneas. | Alta |
| RNF-04 | A API deve validar entrada e restringir dados/operações por perfil e vínculo. | Testes cobrem payload inválido, perfil sem permissão e acesso fora da própria agenda; erros retornam códigos HTTP apropriados. | Alta |
| RNF-05 | Regras prioritárias devem ter testes automatizados e a documentação deve refletir o comportamento implementado. | Pipeline executa testes de conflito, capacidade, bloqueio, autorização, presença e relatório; documentação e modelos correspondem às migrações. | Alta |

## Pendências de validação

1. Perguntar ao cliente/responsável pelo cenário qual é o limite de participantes, a que nível ele se aplica (serviço, sessão ou outro) e se sessões podem ser em grupo; a equipe não deve inventar esses valores.
2. Confirmar formalmente com o professor a manutenção da notificação por e-mail como exceção já implementada, pois ela permanece fora do escopo descrito no cenário.

## Referências

- [Cenário de Aula: Backend GAAP](../Iniciacao/cenario.md)
- [Glossário do domínio](glossario.md)
- [Documento de Visão](../Iniciacao/documento_de_visao.md)
- [Tabela de rastreabilidade](rastreabilidade.md)
