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

<p align="justify">O objetivo principal do sistema é centralizar e facilitar o agendamento das sessões da Playmakerz Lab, permitindo que alunos, responsáveis, professores e a coordenação consultem e gerenciem de forma confiável informações sobre horários, salas, atividades e instrutores disponíveis.</p>
 
---
 
### 2. Como será o processo de cadastro de um aluno e do responsável legal (quando menor de idade)?

<p align="justify">O cadastro deve solicitar nome, data de nascimento e os dados de contato do aluno. Caso ele seja menor de idade, o sistema deve exigir o cadastro e a autorização de um responsável legal antes de permitir qualquer agendamento, garantindo a conformidade com a LGPD e possibilitando que um mesmo responsável seja associado a mais de um aluno.</p>

---
 
### 3. Como será o cadastro de espaços, professores/instrutores e atividades pela coordenação?

<p align="justify">A coordenação deve possuir acesso exclusivo ao cadastro e à atualização de espaços, professores, instrutores e atividades. Os espaços devem conter informações como nome e capacidade, aos profissionais, suas especialidades e disponibilidades, e as atividades, nome, duração e modalidade, além dos vínculos com os profissionais habilitados e os espaços adequados para sua realização.</p>

---
 
### 4. Como deve funcionar a alocação de uma sessão (sala + horário + profissional) e a verificação automática de conflitos?

<p align="justify">A alocação de uma sessão deve reunir informações sobre data, horários inicial e final, atividade, espaço e profissional. Antes da confirmação, o sistema deve verificar automaticamente a disponibilidade da sala e do profissional, possíveis conflitos de horário e a capacidade máxima do espaço, recusando o agendamento e apresentando uma mensagem explicativa quando alguma regra não for atendida.</p>
 
---
 
### 5. Outras perguntas pertinentes ao contexto (ex: cancelamento/remarcação de sessão, aula experimental)

<p align="justify">O aluno ou responsável deve poder solicitar o cancelamento ou a remarcação de uma sessão, respeitando uma possível antecedência mínima e sem permitir alterações em sessões já realizadas. A operação deve atualizar imediatamente a agenda, liberar o espaço e o profissional, registrar o motivo e manter o histórico das alterações. As aulas experimentais podem ser agendadas sem um plano regular, mas devem seguir as mesmas regras de disponibilidade e capacidade aplicadas às outras sessões.</p>

---
 
### 6. Quais informações seriam interessantes para o aluno/responsável e para o professor visualizarem na agenda?

<p align="justify">O aluno ou responsável deve visualizar as próximas sessões, o histórico de agendamentos incluindo data, horário, atividade, professor, espaço, situação e eventuais cancelamentos ou remarcações. O professor deve consultar sua agenda diária e semanal, com informações sobre horários, espaços, atividades e alunos de cada sessão. A agenda também deve oferecer filtros por data, atividade e espaço para facilitar a localização de informações.</p>
 
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
| 25/09/2026 | 1.1 | Revisão das respostas do brainstorm | Pedro Lucas |