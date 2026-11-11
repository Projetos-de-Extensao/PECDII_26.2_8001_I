---
id: levantamento_requisitos
title: Levantamento de Requisitos
---
# Levantamento de Requisitos do GAAP

## Base e decisões

Este levantamento parte do [Cenário de Aula: Backend GAAP](../Iniciacao/cenario.md), sobretudo dos três perfis de usuário e dos critérios de aceite da seção 10. O próprio cenário deixa em branco parte das funcionalidades, entidades, regras de negócio e requisitos não funcionais. Por isso, requisitos marcados **(proposta a confirmar)** são hipóteses explícitas da equipe, ainda dependentes de validação com o responsável pelo cenário.

Os IDs RF, RN e RNF são estáveis e devem ser usados nos demais artefatos. O requisito RF-08 registra uma funcionalidade já existente que o cenário lista fora do escopo; não integra o MVP proposto.

Na revisão de 28/10/2026, a comparação com as seções 3 e 7 do cenário encontrou itens citados sem requisito correspondente: consulta de pendências pelo Administrador, aula ministrada, dashboard simples e auditoria. Eles entraram como RF-09 a RF-11 e RNF-06. Também entrou a RN-07, para o conflito de horário do aluno, que a RN-01 não cobria.

Em 30/10/2026, Pedro Lucas informou que o professor definiu a capacidade máxima de **6 alunos por sessão**. Pedro Lucas esclareceu que o limite vale para qualquer serviço e aceitou mantê-lo como constante de validação no backend, sem configuração administrativa no MVP.

Em 11/11/2026, o plano do grupo foi ampliado para incluir um cliente web responsivo em desktop e mobile, consumindo a API do MVP e tomando o protótipo de alta fidelidade como referência. Essa é uma extensão do cenário acadêmico, que descreve uma entrega de backend/API; não inclui aplicativo nativo. A extensão está registrada em RNF-07 e deve ser confirmada com o responsável pelo cenário.

## Stakeholders e perfis

| Stakeholder/perfil | Interesse e responsabilidade no recorte inicial |
|---|---|
| Administrador | Mantém cadastros, serviços, horários e bloqueios; consulta pendências operacionais. |
| Treinador | Consulta a própria agenda, registra presença/falta e cria e finaliza relatórios de treino. |
| Profissional de Saúde | Consulta somente atendimentos vinculados ao seu serviço e à sua agenda; registra presença/falta dos alunos atendidos sob sua responsabilidade. |
| Equipe desenvolvedora | Modela, implementa, testa e documenta a API e o cliente web responsivo do MVP. |
| Responsável pelo cenário/professor | Esclarece as lacunas do enunciado e valida o recorte proposto. |

Aluno é pessoa atendida e dado gerenciado pela API; o cenário não o define como perfil de acesso inicial.

## Requisitos funcionais

Prioridades: **Alta** = necessária para o aceite do MVP; **Média** = apoio ao uso operacional, sujeita à confirmação das lacunas do cenário; **A confirmar** = citada no cenário sem detalhe suficiente para definir critério ou prioridade; **Fora do escopo** = mantida apenas para registrar uma exceção já implementada.

| ID | Requisito | Critério observável de aceite | Prioridade |
|---|---|---|---|
| RF-01 | A API deve autenticar usuários e aplicar autorização conforme os perfis Administrador, Treinador e Profissional de Saúde. | Com credenciais válidas, o usuário acessa apenas operações permitidas ao seu perfil; uma chamada sem autenticação ou sem autorização recebe resposta de acesso negado. | Alta |
| RF-02 | O Administrador deve cadastrar e manter alunos, profissionais e serviços oferecidos. | O Administrador cria, consulta e atualiza cada tipo de cadastro; dados inválidos são rejeitados com indicação do campo. | Alta |
| RF-03 | O Administrador deve configurar horários de disponibilidade e bloqueios gerais na agenda de cada profissional. | A disponibilidade e os bloqueios valem para a agenda inteira do profissional, independentemente do serviço; a consulta apresenta esses períodos e horários inválidos são recusados. A compatibilidade com cada serviço é verificada separadamente. | Alta |
| RF-04 | Cada perfil deve consultar somente a agenda permitida para si. | Administrador consulta a visão operacional; Treinador vê sessões sob sua responsabilidade e pode filtrar os serviços vinculados ao seu perfil; Profissional de Saúde vê atendimentos dos serviços e agenda a que está vinculado. | Alta |
| RF-05 | O Administrador deve confirmar sessões/atendimentos após validar serviço, disponibilidade, bloqueios, conflitos e capacidade. | A API confirma uma solicitação válida; para cada regra violada, rejeita sem gravar uma sessão parcialmente válida e informa o motivo. | Alta |
| RF-06 | O profissional responsável deve registrar presença ou falta do aluno em sessões de Treino e atendimentos de saúde. | Treinador registra presença/falta nas sessões de Treino sob sua responsabilidade; Profissional de Saúde registra nos atendimentos vinculados à sua agenda e serviço. O registro só é aceito a partir do fim previsto, inclusive no instante exato; o sistema rejeita usuário sem vínculo/permissão, operação antecipada e valores inválidos. | Alta |
| RF-07 | O Treinador responsável deve criar, salvar como rascunho e finalizar um relatório por sessão de Treino. | O relatório pertence à sessão, identifica os alunos participantes e contém data, horário, local, objetivo, exercícios executados, volume (valor e unidade) e intensidade da sessão na escala Borg CR10 (0–10). Rascunhos podem estar incompletos; a finalização valida os campos obrigatórios e torna o relatório imutável. O responsável atual pela sessão pode editar o rascunho. | Alta |
| RF-08 | O sistema envia ao Treinador uma notificação por e-mail quando uma sessão permanece agendada por 30 minutos após o fim previsto. | Uma sessão elegível gera uma notificação ao profissional com e-mail cadastrado e é marcada para evitar envio duplicado. | Fora do escopo do cenário; exceção já implementada e mantida por recomendação do professor em 14/10/2026. Não integra o aceite funcional do MVP. |
| RF-09 | O Administrador deve consultar e acompanhar as pendências operacionais da agenda. | A lista mostra compromissos cujo horário já terminou, exceto cancelados, quando algum participante não tem presença/falta registrada; também inclui sessões de Treino sem relatório ou com relatório em rascunho. Cada item indica o motivo e o responsável. Há filtros por tipo de pendência, contador total no menu e atalhos para abrir os detalhes do compromisso/relatório. Esses atalhos não permitem ao Administrador alterar presença nem relatório; a alteração continua restrita aos profissionais autorizados. | Alta; decisão do grupo (04/11/2026) |
| RF-10 | O profissional responsável deve registrar se a sessão ou o atendimento foi ministrado. | A partir do fim previsto, inclusive no instante exato, o responsável registra realizado/não realizado. Esse estado descreve o compromisso e é independente da presença/falta de cada aluno; usuário sem vínculo ou tentativa antecipada recebe acesso negado/conflito. | Média; decisão de modelagem do grupo (03/11/2026) e D-17 |
| RF-11 | O Administrador deve consultar um dashboard simples da operação. | Para o período selecionado, a consulta mostra a quantidade de compromissos por serviço e situação (agendado, realizado, não realizado ou cancelado). O mês atual é o período padrão e o seletor de datas fica visível. As linhas são ordenadas pelo total geral decrescente e situações sem ocorrências exibem zero ou traço. Tons claros para destacar situações são opcionais. Restrito ao Administrador; não inclui BI nem análises adicionais. | Decisão do grupo (04/11/2026) |
| RF-12 | O sistema deve lembrar o responsável por uma sessão de Treino quando o relatório continuar pendente. | Uma única notificação por e-mail é enviada ao Treinador responsável 24 horas após o fim previsto da sessão quando não houver relatório ou ele estiver em rascunho. O envio é registrado para evitar duplicidade. Não se aplica a atendimentos de saúde. | Decisão do grupo (04/11/2026) |

## Regras de negócio

As regras abaixo detalham as lacunas identificadas na issue #59. O limite de capacidade foi informado pelo professor, vale para qualquer serviço e será uma constante de validação no backend do MVP.

| ID | Regra | Critério observável | Situação |
|---|---|---|---|
| RN-01 | Um profissional não pode ter compromissos não cancelados com horários sobrepostos, independentemente do serviço; intervalos são tratados como `[início, fim)`. | A API consulta conflitos antes de confirmar, recusa a solicitação com mensagem clara e não persiste a sessão; horários contíguos podem ser aceitos. A consulta usa índice composto por profissional, início e fim. | Decisão do grupo (04/11/2026) |
| RN-02 | A capacidade máxima é de 6 alunos por sessão, para qualquer serviço. A quantidade de participantes ativos não pode ultrapassar esse limite. No MVP, a validação usa uma constante no backend, sem campo de configuração administrativa. | Em qualquer serviço, a API recusa integralmente uma solicitação com 7 alunos, sem gravar sessão ou participantes parcialmente; uma solicitação com até 6 passa pela validação das demais regras. | Valor comunicado por Pedro Lucas em 30/10/2026, atribuído ao professor; abrangência e forma de implementação definidas com Pedro Lucas |
| RN-03 | A disponibilidade e os bloqueios são gerais por profissional e compartilhados por todos os serviços que ele pode atender. | Sessão de qualquer serviço é recusada se estiver fora da disponibilidade geral ou dentro de bloqueio; compatibilidade profissional-serviço continua sendo validada pela RN-04. Depois da confirmação, remover ou alterar disponibilidade que deixe a sessão descoberta, ou criar ou alterar bloqueio sobre ela, é recusado; sessões canceladas ou encerradas não contam (D-18). | Decisão registrada |
| RN-04 | O profissional designado deve estar habilitado para o serviço solicitado. | Serviço incompatível com os vínculos cadastrados para o profissional é recusado. Um profissional pode ter vínculos com vários serviços. | Decisão de modelagem do grupo (D-09, 03/11/2026) |
| RN-05 | Somente o profissional responsável e autorizado pode registrar presença/falta no compromisso sob sua responsabilidade; somente o Treinador autorizado pode finalizar relatório de treino. | Treinador atua nas sessões de Treino atribuídas; Profissional de Saúde atua nos atendimentos vinculados ao seu serviço e agenda; usuário sem vínculo recebe acesso negado. | Regra definida para presença; autorização segue os vínculos do cenário |
| RN-06 | Confirmar a sessão e reservar capacidade são uma operação atômica. | Se qualquer validação ou gravação falhar, nenhuma sessão parcial nem reserva é persistida; solicitações concorrentes não excedem a capacidade. | Derivada do requisito de consistência/atomicidade da issue #59; validar implementação |
| RN-07 | Um aluno não pode participar de duas sessões ou atendimentos ativos com horários sobrepostos; intervalos são tratados como `[início, fim)`. | A API consulta conflitos antes de confirmar, recusa a solicitação com mensagem clara e não persiste a sessão; horários contíguos podem ser aceitos. A busca usa índices no vínculo aluno–sessão e nos horários da sessão, com desempenho confirmado pelo plano de execução e medição. | Decisão do grupo (04/11/2026) |

## Requisitos não funcionais

| ID | Requisito | Critério observável de aceite | Prioridade |
|---|---|---|---|
| RNF-01 | A persistência deve usar banco relacional normalizado com chaves, restrições e índices adequados às consultas de agenda. | Migrações aplicam em banco relacional limpo; integridade referencial e restrições são verificáveis no modelo/DER. | Alta |
| RNF-02 | Senhas nunca devem ser armazenadas em texto puro. | Verificação no banco confirma que a senha está representada por hash produzido pelo mecanismo seguro do framework. | Alta |
| RNF-03 | A confirmação de agendamento deve preservar atomicidade e consistência sob concorrência. | Teste concorrente demonstra que bloqueios, conflitos e capacidade não são violados por duas solicitações simultâneas. | Alta |
| RNF-04 | A API deve validar entrada e restringir dados/operações por perfil e vínculo. | Testes cobrem payload inválido, perfil sem permissão e acesso fora da própria agenda; erros retornam códigos HTTP apropriados. | Alta |
| RNF-05 | Regras prioritárias devem ter testes automatizados e a documentação deve refletir o comportamento implementado. | Pipeline executa testes de conflito, capacidade, bloqueio, autorização, presença e relatório; documentação e modelos correspondem às migrações. | Alta |
| RNF-06 | Operações críticas devem gerar registros de auditoria com mensagem legível por pessoas. | O log registra criação de usuário, confirmação de agendamento, alteração de presença/falta e finalização de relatório. Cada evento guarda o autor, a operação, a entidade, a data/hora e uma mensagem em linguagem humana. O registro não pode ser alterado pela API; senhas e credenciais não são incluídas. | Média; decisão do grupo (04/11/2026) |
| RNF-07 | O MVP deve oferecer um cliente web responsivo para os fluxos definidos, em desktop e mobile. | Os três perfis acessam pela interface os fluxos correspondentes aos RFs implementados, nas larguras de referência de 1920 × 1080 e 390 × 844. A interface consome a API; autorização e validações permanecem no backend. Sucessos, erros de validação e acesso negado são apresentados de forma clara. | Alta para a extensão do MVP do grupo; confirmar com o responsável pelo cenário |

## Pendências de validação

Nenhuma pendência de validação de escopo permanece nos requisitos RF/RN/RNF deste documento.

## Pendências de artefatos

- O [DER](der.md) descreve o modelo-alvo, mas sua compatibilidade com as migrações atuais ainda precisa ser verificada após a implementação da Construção 1 (RNF-01).
- Os IDs RF-09 a RF-11, RN-07 e RNF-06 estão relacionados na [rastreabilidade](rastreabilidade.md), nos casos de uso e, quando aplicável, no diagrama de sequência "Confirmar agendamento". As representações visuais de alta fidelidade continuam parciais (#62).

## Referências

- [Cenário de Aula: Backend GAAP](../Iniciacao/cenario.md)
- [Glossário do domínio](glossario.md)
- [Documento de Visão](../Iniciacao/documento_de_visao.md)
- [Tabela de rastreabilidade](rastreabilidade.md)
