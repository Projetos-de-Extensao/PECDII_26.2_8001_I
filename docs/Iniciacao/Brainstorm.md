---
id: brainstorm
title: Brainstorm
---
 
## Introdução
<p align = "justify">
O brainstorm é uma técnica de elicitação de requisitos que consiste em reunir a equipe e discutir sobre diversos tópicos gerais do projeto apresentados no documento problema de negócio. No brainstorm o diálogo é incentivado e críticas são evitadas para permitir que todos colaborem com suas próprias ideias.
</p>
 
## Metodologia
<p align = "justify">
A equipe se reuniu para debater ideias gerais sobre a API da PKZ Lab via Discord, começou 15:37 e terminou 17:52, onde o aluno Pedro Lucas foi o moderador, direcionando a equipe com questões pré-elaboradas, e transcrevendo as respostas para o documento.
</p>
 
## Brainstorm
 
## Versão 1.0
 
## Perguntas
 
### 1. Qual o objetivo principal do sistema?

<p align = "justify">
<b>Rodrigo</b>: Organizar em um único sistema os agendamentos de sessões da PKZ Lab

<b>Pedro Lucas</b>: Facilitar o agendamento das sessões e permitir que a coordenação tenha mais controle sobre os horários, as salas e os instrutores disponíveis

<b>Lucas Santos</b>: A API deve permitir que alunos, responsáveis, professores e a coordenação consultem e gerenciem as informações da agenda de forma confiável
</p>
 
---
 
### 2. Como será o processo de cadastro de um aluno e do responsável legal (quando menor de idade)?

<p align = "justify">
<b>Rodrigo</b>: O aluno deve ser cadastrado com nome, data de nascimento e dados de contato. Caso seja menor de idade, o sistema deve exigir também os dados e o vínculo de um responsável legal antes de permitir qualquer agendamento

<b>Pedro Lucas</b>: O cadastro deve solicitar os dados básicos do aluno. Se ele for menor de idade, também será necessário cadastrar um responsável legal e registrar sua autorização para que o aluno possa participar das atividades

<b>Lucas Santos</b>: Para menores de idade, o responsável legal deve confirmar a autorização para o uso dos dados conforme a LGPD (Lei Geral de Proteção de Dados). Um responsável também pode ficar associado a mais de um aluno
</p>

---
 
### 3. Como será o cadastro de espaços, professores/instrutores e atividades pela coordenação?

<p align = "justify">
<b>Rodrigo</b>: A coordenação deve ter acesso exclusivo ao cadastro e a atualização dos espaços, informando nome e capacidade, e dos professores, registrando especialidades e horários disponíveis

<b>Pedro Lucas</b>: A coordenação deverá cadastrar e atualizar os espaços, os professores e as atividades. Essas informações devem indicar onde cada atividade pode acontecer e quais profissionais podem realizá-la.

<b>Lucas Santos</b>: Cada atividade deve possuir informações como nome, duração e modalidade, além de estar vinculada aos profissionais habilitados a ministrá-la e aos espaços adequados para sua realização.
</p>

---
 
### 4. Como deve funcionar a alocação de uma sessão (sala + horário + profissional) e a verificação automática de conflitos?

<p align = "justify">
<b>Rodrigo</b>: A sessão deve reunir data, horário inicial e final, atividade, espaço e profissional. Antes de confirmar, a API deve verificar automaticamente se algum desses recursos já está reservado no período solicitado.

<b>Pedro Lucas</b>: Antes de confirmar uma sessão, o sistema deve verificar se a sala e o profissional estão livres naquele horário. Caso exista algum conflito ou a sala esteja lotada, o agendamento não pode ser concluído.

<b>Lucas Santos</b>: Além dos choques de horário, o sistema deve conferir a disponibilidade do professor e a capacidade máxima da sala. Se alguma regra não for atendida, a atribuição deve ser recusada com uma mensagem que explique o conflito.
</p>
 
---
 
### 5. Outras perguntas pertinentes ao contexto (ex: cancelamento/remarcação de sessão, aula experimental)

<p align = "justify">
<b>Rodrigo</b>: O cancelamento ou a remarcação deve atualizar a agenda e liberar imediatamente o espaço e o profissional. Também seria importante registrar o motivo e manter um histórico das alterações

<b>Pedro Lucas</b>: O aluno ou responsável deve poder solicitar o cancelamento ou a remarcação de uma sessão. As aulas experimentais também devem ser registradas na agenda para evitar conflitos com as demais atividades

<b>Lucas Santos</b>: A aula experimental pode ser agendada sem um plano regular, mas deve seguir as mesmas regras de disponibilidade e capacidade. O sistema também poderia definir antecedência mínima para cancelamentos e impedir alterações em sessões já realizadas
</p>

---
 
### 6. Quais informações seriam interessantes para o aluno/responsável e para o professor visualizarem na agenda?

<p align = "justify">
<b>Rodrigo</b>: O aluno/responsável deve visualizar as próximas sessões com data, horário, atividade, professor, espaço e situação do agendamento, além de poder consultar sessões anteriores e eventuais alterações

<b>Pedro Lucas</b>: O aluno/responsável deve visualizar as informações das suas sessões, enquanto o professor deve consultar os alunos e as atividades de cada horário. A agenda também deve indicar quando uma sessão for cancelada ou remarcada

<b>Lucas Santos</b>: O professor deve conseguir consultar sua agenda diária e semanal, com os horários, espaços, atividades e alunos de cada sessão. Filtros por data, atividade e espaço ajudariam a localizar as informações com maior rapidez
</p>
 
### Requisitos elicitados
 
|ID|Descrição|
|----|-------------|
|BS01|O sistema deve permitir o cadastro de alunos com nome, data de nascimento e dados de contato.|
|BS02|O sistema deve exigir o cadastro e a autorização de um responsável legal quando o aluno for menor de idade, permitindo que um responsável seja associado a mais de um aluno.|
|BS03|O sistema deve permitir que a coordenação cadastre e atualize os espaços, incluindo nome e capacidade.|
|BS04|O sistema deve permitir que a coordenação cadastre e atualize professores e instrutores, incluindo suas especialidades e disponibilidades.|
|BS05|O sistema deve permitir o cadastro de atividades com nome, duração e modalidade, vinculando-as aos profissionais habilitados e aos espaços adequados.|
|BS06|O sistema deve permitir o agendamento de sessões com data, horários inicial e final, atividade, espaço e profissional.|
|BS07|O sistema deve verificar a disponibilidade do espaço e do profissional, assim como a capacidade da sala, antes de confirmar uma sessão.|
|BS08|O sistema deve permitir o cancelamento e a remarcação de sessões, liberando os recursos reservados e mantendo o histórico das alterações.|
|BS09|O sistema deve permitir o agendamento de aulas experimentais, aplicando as mesmas regras de disponibilidade e capacidade das demais sessões.|
|BS10|O sistema deve disponibilizar agendas para alunos, responsáveis e professores, com informações das sessões e filtros por data, atividade e espaço.|
 
## Conclusão
<p align = "justify">
A aplicação da técnica de brainstorm permitiu reunir diferentes ideias sobre o funcionamento da API da PKZ Lab e identificar os principais requisitos do sistema. A discussão destacou a necessidade de centralizar os agendamentos, organizar os cadastros, verificar conflitos automaticamente e oferecer agendas adequadas para cada usuário. Esses requisitos servirão como base para as próximas etapas de análise e desenvolvimento do projeto.
</p>
## Referências Bibliográficas
 
> BARBOSA, S. D. J; DA SILVA, B. S. Interação humano-computador. Elsevier, 2010.
 
 
## Autor(es)
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 08/09/2026 | 1.0 | Criação do documento | Rodrigo, Pedro Lucas e Lucas Santos |
