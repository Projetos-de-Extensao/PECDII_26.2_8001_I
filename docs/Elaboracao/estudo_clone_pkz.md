---
id: estudo_clone_pkz
title: Estudo do Clone PKZ & One to One
---
# Estudo do Clone PKZ & One to One

Este documento registra o percurso pelo clone do sistema da PKZ & One to One, disponibilizado pelo professor na issue #38, e compara o que o sistema real faz com o que o [levantamento de requisitos](levreq.md) descreve. Ele atende ao critério de pronto acordado na própria issue em 21/10/2026.

O objetivo não é copiar o clone. O cenário recorta um MVP bem menor, e boa parte do que aparece aqui fica deliberadamente fora. O valor do estudo está em **separar o que o grupo observou do que o grupo supôs**: vários requisitos já escritos descrevem comportamento que o sistema real não tem, e algumas regras que o sistema real aplica não têm requisito correspondente.

## Como o estudo foi feito

| Item | Registro |
|---|---|
| Data | 04/11/2026 |
| Ambiente | `https://pkzanalise.vercel.app`, clone de estudo informado na issue #38 |
| Contas | As nove publicadas pelo professor na issue, com a senha comum |
| Método | Login com cada conta, percurso pelas telas do menu e leitura dos textos de ajuda e das legendas da própria interface |

**Limites deste estudo, declarados de propósito:**

- A conta `nutri.demo` **continua recusando o login**, com a mensagem "Nome de usuário ou senha inválidos". É o mesmo defeito que Pedro Lucas relatou em 09/10/2026 na issue #38 e que segue sem correção. O perfil Nutricionista não pôde ser percorrido; o que se sabe dele vem de como ele aparece nas telas dos outros perfis.
- Nenhum agendamento foi criado ou cancelado. A base é compartilhada com a turma, e gravar dados nela atrapalharia quem for estudar depois. Em consequência, **as mensagens de erro de conflito, lotação e capacidade não foram observadas diretamente** — apenas os estados que a interface declara na legenda.
- A base de demonstração não tem agendamentos futuros, então a agenda do dia apareceu vazia em todos os perfis.

## Perfis e telas

O clone tem **sete perfis de usuário**, não três. Abaixo, o que cada conta mostra no menu.

| Conta | Perfil exibido | Itens de menu | Observação |
|---|---|---|---|
| `admin.demo` | Administração | Dashboard, Agendamento, Agenda Geral, Buscar, Relatórios, Relatórios de Treino, Relatórios Pendentes, Avaliações, Avaliação Fisio, Teste Físico, Sobre | Painel com as abas Alunos, Horários, Bloqueios, Usuários, Renovação e Logs |
| `recepcao.demo` | Recepção | Dashboard, Agendamento, Agenda Geral, Minha Agenda, Buscar | Só a aba Alunos no painel; sem acesso a horários, bloqueios, usuários, renovação e logs |
| `professor.demo` | Professor | Dashboard, Agendamento, Agenda Geral, Buscar, Relatórios de Treino | Dashboard abre em "Treinos de hoje" |
| `profpkz.demo` | Professor PKZ | Os mesmos itens de `professor.demo` | Acompanha o reteste físico dos alunos PKZ |
| `profoto.demo` | Professor One to One | Dashboard, Agenda Geral, Buscar, Relatórios de Treino | **Sem** o item Agendamento |
| `psico.demo` | Psicólogo | Dashboard, Minha Agenda, Agenda Geral, Buscar | Gerencia a própria disponibilidade e os próprios bloqueios |
| `fisio.demo` | Fisioterapeuta | Dashboard, Minha Agenda, Agenda Geral, Avaliação Fisio, Buscar | Igual ao Psicólogo, mais a avaliação de fisioterapia |
| `nutri.demo` | Nutricionista | — | Login recusado |
| `responsavel.demo` | Responsável | Dashboard, Agendamento, Meus Agendamentos, Minha Pasta, Relatórios de Treino | Agenda em nome dos alunos vinculados, gastando créditos |

Dois detalhes que mudam o desenho de autorização:

- O perfil **não decide sozinho** o que a pessoa pode fazer. Na aba Usuários, cada conta tem marcações próprias — "Pode ministrar treinos" nas contas de Administrador e "Pode agendar" nas de Professor. A permissão é o perfil **mais** essas marcações.
- A diferença entre `profpkz.demo` e `profoto.demo` mostra que PKZ e One to One não são só uma etiqueta: são duas operações, com durações, planos e permissões diferentes.

## Funcionalidades do clone que o MVP não cobre

Nenhum item desta lista está no [levantamento de requisitos](levreq.md). Estão aqui para ficar registrado que foram vistos e deixados de fora conscientemente.

| Área | O que o clone tem |
|---|---|
| Créditos | Plano mensal de créditos por aluno, renovação automática mensal e semanal, créditos não cumulativos, planos nomeados no One to One (Express, One Move, One Power, One Power Legado, Be The One) |
| Cancelamento | Prazo mínimo em horas para cancelar com devolução do crédito |
| Agenda automática | Liberação de um novo horário após o intervalo configurado, disparada ao marcar presença no último treino do dia |
| Fila de espera | Os textos de bloqueio dizem que ninguém consegue agendar "nem entrar na fila", o que indica uma fila para horários lotados |
| Avaliação física | Teste físico PKZ com controle de reteste atrasado por aluno |
| Fisioterapia | Avaliação com reavaliação esperada em 30 dias |
| Perfis extras | Recepção e Responsável, com o Responsável agendando por conta própria |
| Exportação | Excel e PDF dos relatórios do período, e PDF de cada relatório de treino |
| Documentos | "Minha Pasta", área de arquivos do aluno vista pelo Responsável |
| Outros | Aula experimental, busca global de alunos, instalação como aplicativo no celular, serviços liberados por aluno, responsável secundário, conta ativa/inativa e renomeação de usuário |

## Regras que aparecem na prática

Estas foram lidas na própria interface, nos textos de ajuda e nas legendas.

| Regra observada | Onde apareceu |
|---|---|
| Capacidade de 6 por horário, exibida como "6/6 VAGAS" | Grade de agendamento de Treino |
| A capacidade é **configurável por horário**, no campo "Vagas (Limite)" | Aba Horários do painel do Administrador |
| Antecedência mínima de 1 hora para agendar; a legenda marca o horário como "Fechado (≤ 1h)" | Grade de agendamento e painel do Responsável |
| Janela de agendamento de 14 dias e 1 crédito por treino | Painel do Responsável |
| Fisioterapia com acesso diferente por plano: "Express sem acesso; demais planos 15 minutos" | Painel do Responsável |
| Bloqueio por serviço **e** por agenda, com recorrência ("Toda Terça-Feira", "Todos Os Dias") e opção permanente | Abas Bloqueios do Administrador e dos profissionais de saúde |
| O bloqueio impede agendar e também entrar na fila | Texto da tela de bloqueio |
| A sessão nasce aguardando confirmação; a legenda da grade tem o estado "Aguardando confirmação" | Grade de agendamento |
| O Profissional de Saúde confirma as **próprias** solicitações, em "Solicitações Pendentes" | Painéis do Psicólogo e do Fisioterapeuta |
| Quem agenda define o professor responsável, e a recepção ou o administrador não entram nessa lista | Diálogo de confirmação do agendamento |
| A pendência de relatório nasce de **presença marcada sem relatório finalizado**, não do horário ter passado | Tela Relatórios Pendentes |
| Operações registradas no log: `book_service`, `confirm_booking`, `cancel_booking`, `mark_attendance`, `admin_create_user`, `admin_delete_user`, `daily_renewal`, `monthly_renewal` | Aba Logs |

## Divergências que afetam requisitos já escritos

Esta é a parte do estudo que precisa de decisão. Cada linha compara o que o documento afirma hoje com o que o sistema real faz.

| Requisito | O que está escrito | O que o clone faz | O que decidir |
|---|---|---|---|
| RF-03, RN-03 | O **Administrador** configura disponibilidade e bloqueios, gerais por profissional | O próprio Profissional de Saúde gerencia a sua agenda, e o bloqueio é por serviço e por agenda, com recorrência | Manter a configuração centralizada no Administrador ou permitir que o profissional gerencie a própria agenda |
| RF-05 | O **Administrador** confirma as sessões e atendimentos | O Profissional de Saúde confirma as próprias solicitações; o Responsável agenda direto, gastando crédito | Confirmar quem é o dono da confirmação em cada serviço |
| RF-07 | O relatório tem volume (valor e unidade) e intensidade na escala Borg CR10, e fica **imutável** ao ser finalizado | O relatório real tem materiais utilizados, tecnologias e capacidades desenvolvidas, **não tem** volume nem Borg, e continua com "Editar" e "Excluir" depois de finalizado | Revisar os campos do relatório e decidir se a imutabilidade é regra nossa ou suposição |
| RF-09 | Os atalhos **não** permitem ao Administrador alterar presença nem relatório | Administrador e Recepção têm o botão "Preencher" nos relatórios pendentes | Decidir se o Administrador preenche relatório ou só acompanha |
| RN-02 | Capacidade de 6 como constante no backend, igual para qualquer serviço | Capacidade por horário, definida pelo Administrador ao criar o horário | Manter a constante no MVP ou tornar a capacidade um campo do horário |
| RF-01, RF-02 | Três perfis fechados | Sete perfis, mais marcações por usuário que concedem capacidades extras | Confirmar que os três perfis bastam para o aceite do MVP |
| RNF-06 | O log guarda uma mensagem legível por pessoas | A lista de logs mostra operação, entidade e data; não exibe mensagem | Confirmar se a mensagem humana é exigência nossa ou do cenário |

Além disso, o clone aplica regras que **não têm requisito nenhum** do nosso lado: antecedência mínima de uma hora, janela de 14 dias, fila de espera e todo o controle de créditos. Nenhuma delas precisa entrar no MVP, mas a ausência deveria ser uma decisão registrada, não um esquecimento.

## O que levar para a revisão de requisitos

Para a issue #59, na ordem de impacto:

1. **RF-07 é o caso mais grave.** Volume e intensidade Borg CR10 não existem no sistema real. Ou o grupo confirma com o professor que são exigência do cenário, ou o requisito descreve algo que ninguém pediu.
2. **Quem confirma o agendamento** (RF-05) e **quem configura a agenda** (RF-03, RN-03) precisam ser confirmados, porque o clone contradiz o documento nos dois pontos.
3. **Capacidade** (RN-02): decidir conscientemente entre a constante e o campo por horário.
4. **Imutabilidade do relatório finalizado** (RF-07) e **o que o Administrador pode fazer na pendência** (RF-09) são regras que o grupo escreveu e o sistema real não aplica.
5. Registrar, como decisão explícita, que créditos, fila de espera, avaliação física, exportação e os perfis Recepção e Responsável ficam fora do MVP.

## Pendências

- O login de `nutri.demo` continua falhando. Enquanto não for corrigido, o perfil Nutricionista não pode ser percorrido e as telas específicas dele ficam sem registro.
- As mensagens de recusa por conflito, lotação e capacidade não foram observadas, porque isso exigiria gravar dados na base compartilhada. Se o grupo quiser esse registro, vale combinar antes quem faz e quando limpa.

## Referências

- [Levantamento de requisitos](levreq.md)
- [Cenário de Aula: Backend GAAP](../Iniciacao/cenario.md)
- [Revisão do escopo GAAP](revisao_cruzada.md)
- [Rastreabilidade requisito × artefato](rastreabilidade.md)
- Issue #38 — Estudar o APP
