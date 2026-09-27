---
id: documento_de_visao
title: Documento de Visão
---
## Introdução

<p align = "justify">
O propósito deste documento é apresentar uma visão geral do projeto desenvolvido na disciplina Projeto de Extensão em Computação II (IBM8936), no Ibmec, referente ao sistema back-end de gestão de treinamento e acompanhamento de performance da PKZ Lab. Neste documento são descritos de forma resumida o problema abordado, os objetivos do projeto, os stakeholders envolvidos, o escopo e as principais funcionalidades previstas para a API.
</p>

## Descrição do Problema

### Problema

<p align = "justify">
Hoje o agendamento de sessões na PKZ Lab é feito exclusivamente por WhatsApp, sem calendário, sem controle de salas ou horários e sem nenhum sistema de registro. Conforme a operação cresce, isso gera risco real de conflito de horário e de sala entre atividades diferentes.
</p>

### Impactados

<p align = "justify">
São impactados os alunos e seus responsáveis legais (quando menores de idade), que dependem de mensagens avulsas para saber horário e sala de suas sessões; os professores e instrutores, que não têm uma agenda confiável e só ficam sabendo de uma sessão quando alguém os avisa; e a coordenação do centro, que hoje resolve manualmente qualquer sobreposição de sala, horário ou profissional.
</p>

### Consequência

<p align = "justify">
Sem um sistema de controle, a tendência é o aumento de conflitos de agenda (dois grupos usando a mesma sala ou o mesmo profissional no mesmo horário), retrabalho da coordenação para reorganizar sessões na hora e risco de não conformidade com a LGPD e o ECA no tratamento dos dados de alunos menores de idade, já que hoje não existe um fluxo formal de consentimento do responsável legal.
</p>

### Solução

<p align = "justify">
Especificar e desenvolver uma API back-end que permita cadastrar espaços, professores/instrutores, atividades e alunos, e alocar cada sessão de treino ou aula experimental a um espaço, um horário e um profissional sem conflito, verificando automaticamente disponibilidade e capacidade antes de confirmar o agendamento.
</p>

## Objetivos

<p align = "justify">
O objetivo da equipe de desenvolvimento é entregar, até o fim do 2º semestre de 2026, uma API funcional que centralize o cadastro de espaços, profissionais, atividades e alunos/responsáveis, automatize a alocação de sessões com verificação de conflito de agenda e de capacidade, e disponibilize consultas de agenda por espaço, por profissional e por aluno, seguindo a metodologia RUP/UP e utilizando Python/Django com banco de dados relacional.
</p>

## Descrição do Usuário

<p align = "justify">
Os usuários da API são a Coordenação do centro, que administra os cadastros de espaços, profissionais e atividades e realiza a alocação das sessões; o Professor/Instrutor, que consulta a própria agenda e registra o que ocorreu em cada sessão; o Aluno, pessoa atendida pelo centro em regime regular ou em aula experimental, que consulta sua agenda e solicita cancelamento ou remarcação; e o Responsável Legal, obrigatório quando o aluno é menor de 18 anos, que autoriza o tratamento de dados e acompanha a agenda do aluno, podendo estar vinculado a mais de um aluno.
</p>

## Recursos do produto

### Cadastro de Espaços, Profissionais e Atividades

<p align = "justify">
A coordenação poderá cadastrar e atualizar os espaços do centro (nome e capacidade), os professores e instrutores (especialidades e disponibilidades) e as atividades oferecidas (nome, duração, modalidade), vinculando cada atividade aos profissionais habilitados e aos espaços adequados.
</p>

### Cadastro de Alunos e Responsáveis

<p align = "justify">
A coordenação poderá cadastrar alunos com nome, data de nascimento e dados de contato. Quando o aluno for menor de 18 anos, o sistema exigirá o cadastro de um responsável legal e o registro da sua autorização antes de liberar o aluno para agendamentos, em conformidade com a LGPD e o ECA.
</p>

### Agendamento de Sessões

<p align = "justify">
A coordenação poderá agendar sessões regulares e aulas experimentais, informando data, horário, atividade, espaço, profissional e alunos. Antes de confirmar, o sistema verificará automaticamente conflito de horário do espaço e do profissional e a capacidade máxima do espaço, recusando o agendamento quando alguma regra não for atendida.
</p>

### Cancelamento e Remarcação

<p align = "justify">
Alunos, responsáveis e a coordenação poderão cancelar ou remarcar sessões já agendadas, respeitando uma antecedência mínima. O sistema libera os recursos reservados e mantém o histórico de todas as alterações.
</p>

### Consulta de Agenda

<p align = "justify">
Cada perfil poderá consultar sua agenda com filtros por data, atividade e espaço: o aluno vê suas próprias sessões, o responsável vê as sessões dos alunos vinculados, o professor vê as sessões em que está alocado e a coordenação vê a agenda completa.
</p>

## Restrições

<p align = "justify">
O sistema não terá interface gráfica própria: toda a funcionalidade é exposta como uma API back-end, consumida por outra aplicação ou por ferramentas de teste como Postman/Insomnia. O escopo não inclui controle financeiro, cobrança ou pagamento de mensalidades, nem a gestão pedagógica do conteúdo das atividades. A implementação está limitada ao tempo disponível no 2º semestre de 2026 e ao trio responsável pelo projeto.
</p>

## Referências Bibliográficas

> Levantamento completo em [Pesquisa](pesquisa.md).

> BRASIL. Lei nº 13.709, de 14 de agosto de 2018 (Lei Geral de Proteção de Dados Pessoais - LGPD).

> BRASIL. Lei nº 8.069, de 13 de julho de 1990 (Estatuto da Criança e do Adolescente - ECA).

> BRASIL. Lei nº 9.696, de 1º de setembro de 1998 (regulamenta a profissão de Educação Física).

> BEZERRA, E. Princípios de Análise e Projeto de Sistemas com UML. 3. ed. Rio de Janeiro: Elsevier, 2015.

## Versionamento
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 27/09/2026 | 1.0 | Criação do documento de visão da API da PKZ Lab | Rodrigo |
