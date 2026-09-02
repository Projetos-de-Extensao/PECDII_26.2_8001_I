---
id: pesquisa
title: Pesquisa
---

# Pesquisa
### **1. Capa**

- Tema: Sistema Back-End Gestão de treinamento e acompanhamento de performance
- Data: 2026.2
- Stakeholder: PKZ Lab, Desenvolvedores, Professor Jonh

---

### **2. Pesquisa**

- **Contexto do Projeto**: O PKZ Lab é um centro de treinamento de performance integrada sediado na Av. Armando Lombardi, 949, loja G, Barra da Tijuca, Rio de Janeiro. Sua comunicação institucional declara quatro frentes de atuação: metodologia, treino, acompanhamento e avaliação, o que implica organizar continuamente sessões, atividades, espaços e profissionais. Toda a captação e o agendamento, porém, são conduzidos por WhatsApp, sem calendário, sem controle de salas ou horários e sem nenhum sistema de registro, o que gera risco de conflito de horário e de sala conforme a operação cresce.

- **Objetivo**: Especificar e desenvolver um back-end que permita cadastrar salas ou espaços do centro, professores e instrutores, atividades e modalidades, e alocar cada sessão de treino ou aula experimental a um espaço, a um horário e a um profissional sem conflito, expondo essas funcionalidades por meio de uma API

- **Público-Alvo**: O aluno é a pessoa atendida pelo centro de treinamento, em regime regular ou em aula experimental, e consulta sua agenda de sessões alocadas. O responsável legal, no caso de atleta menor de 18 anos, acompanha essa agenda e autoriza o tratamento de dados. O professor ou instrutor é o profissional alocado a cada sessão, e consulta e registra o que ocorre nela. A coordenação do centro cadastra atividades e espaços e realiza a alocação, resolvendo conflitos de horário quando necessário.

- **Escopo**: A API deve cobrir o cadastro de espaços do centro, de professores e instrutores, de atividades e modalidades, e de alunos e responsáveis; a alocação de cada sessão a um espaço, um horário e um profissional; a verificação automática de conflito de agenda e de capacidade; e a consulta da agenda por espaço, por profissional e por aluno, com persistência em banco de dados relacional.

- **Analise de aplicações e mercado**: O perfil do PKZ Lab usa apenas o WhatsApp como canal de contato e de agendamento, sem nenhuma ferramenta de alocação de sala, horário ou profissional. No mercado, softwares de gestão de academias, como Tecnofit e Sistema Pacto, já resolvem parte desse problema ao permitir agendamento de aulas e controle de turma, mas são voltados à operação comercial ampla, com módulos financeiros que não interessam a um centro pequeno. Ferramentas genéricas de alocação de eventos e salas, como SuperSaaS e Calenda, tratam bem a reserva de espaço e de horário, mas não relacionam essa reserva a um profissional específico nem a uma modalidade de treino.

- Levantamento de **Legislação**: O sistema deve observar a Lei nº 13.709/2018 (LGPD), especialmente quanto ao consentimento do responsável legal para o tratamento de dados de menores; o Estatuto da Criança e do Adolescente (Lei nº 8.069/1990), quanto à proteção do atleta menor de idade; e a Lei nº 9.696/1998, que exige que toda avaliação seja vinculada a um profissional de Educação Física habilitado.

---