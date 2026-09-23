---
id: mapa_mental
title: Mapas Mentais
---

## Introdução

<p align = "justify">
Mapa mental consiste em criar resumos cheios de símbolos, cores, setas e frases de efeito com o objetivo de organizar o conteúdo e facilitar associações entre as informações destacadas. Esse material é muito indicado para pessoas que têm facilidade de aprender de forma visual.
</p>

## Metodologia

<p align = "justify">
O documento foi elaborado por Pedro Lucas, com base no levantamento já registrado em <a href="pesquisa.md">pesquisa.md</a> e nos requisitos elicitados em <a href="Brainstorm.md">Brainstorm.md</a>, organizando o projeto PKZ Lab em dois mapas mentais feitos em PlantUML.
</p>

## Mapa mental - Geral

### Mapa mental 1

```plantuml
@startmindmap pkz_lab_mapa_mental
skinparam monochrome true
skinparam ArrowColor #000000
skinparam NodeFontSize 14

* PKZ Lab: Sistema de Gestão de Treinamento
** Problema
*** Agendamento feito só por WhatsApp
*** Sem calendário ou controle de salas/horários
*** Risco de conflito de sala/horário com o crescimento da operação
** Objetivo
*** API de agendamento
*** Cadastro de espaços, profissionais, atividades e alunos
*** Alocação de sessões sem conflito
** Atores
*** Aluno
*** Responsável legal
*** Professor/Instrutor
*** Coordenação do centro
** Escopo da API
*** Cadastro
    **** Espaços/salas
    **** Professores e instrutores
    **** Atividades e modalidades
    **** Alunos e responsáveis
*** Alocação de sessões
    **** Espaço + horário + profissional
*** Verificação automática de conflito
    **** Conflito de agenda
    **** Conflito de capacidade
*** Consulta de agenda
    **** Por espaço
    **** Por profissional
    **** Por aluno
*** Persistência em banco de dados relacional
** Legislação
*** Lei Geral de Proteção de Dados
    **** Consentimento do responsável legal
*** Estatuto da Criança e do Adolescente
    **** Proteção do atleta menor de idade
*** Lei 9.696/1998
    **** Avaliação vinculada a profissional de Educação Física habilitado
** Mercado
*** Tecnofit/Sistema Pacto
    **** ERPs não necessários para um centro pequeno
*** SuperSaaS/Calenda
    **** Não relacionam reserva a profissional/modalidade
@endmindmap
```

### Mapa mental 2

```plantuml
@startmindmap pkz_lab_mapa_mental_brainstorm
skinparam monochrome true
skinparam ArrowColor #000000
skinparam NodeFontSize 14

* Requisitos elicitados no Brainstorm
** Cadastro
*** Alunos (nome, data de nascimento, contato)
*** Responsável legal (obrigatório se menor, pode ter mais de um aluno vinculado)
*** Espaços (nome, capacidade)
*** Professores/instrutores (especialidade, disponibilidade)
*** Atividades (nome, duração, modalidade, vinculada a profissional e espaço)
** Agendamento de sessão
*** Data, horário inicial e final, atividade, espaço e profissional
*** Verificação de disponibilidade de espaço e profissional
*** Verificação de capacidade da sala
** Gestão da sessão
*** Cancelamento e remarcação
    **** Libera os recursos reservados
    **** Mantém histórico das alterações
*** Aula experimental
    **** Mesmas regras de disponibilidade e capacidade
** Consulta de agenda
*** Aluno/responsável
*** Professor
*** Filtros por data, atividade e espaço
@endmindmap
```

## Conclusão

<p align = "justify">
O mapa mental 1 organizou visualmente o problema do PKZ Lab (agendamento só via WhatsApp), o objetivo da API, os atores envolvidos, o escopo do sistema, a legislação aplicável e o comparativo ao mercado. O mapa mental 2 organizou os requisitos elicitados na sessão de Brainstorm, agrupados por cadastro, agendamento de sessão, gestão da sessão e consulta de agenda. Juntos, servem de base para o levantamento de requisitos.
</p>

## Referências
> PlantUML Mindmap Diagram. Disponível em: https://plantuml.com/mindmap-diagram

## Versionamento
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 08/09/26 | 1.0 | Criação do documento | Pedro Lucas |
