---
id: dt
title: Design Thinking
---
# Design Thinking

### **1. Capa**

- Título do Projeto: GAAP — Gestão de Atletas de Alta Performance
- Equipe: Rodrigo, Pedro Lucas e Lucas Santos
- Data: 2026.2

---

### **2. Introdução**

- **Contexto do Projeto**: O cenário GAAP descreve uma escola de treinamento esportivo que precisa organizar alunos, profissionais e sessões de Treino, Fisioterapia, Psicologia e Nutrição. PKZ & One to One é o ambiente analisado que inspirou o cenário; não é o nome do produto acadêmico.

- **Objetivo**: Entregar uma API funcional, testada e documentada para apoiar a operação de agenda e treino do recorte inicial do GAAP.

- **Público-Alvo**: Administrador, Treinador e Profissional de Saúde, conforme os perfis definidos no cenário GAAP.

- **Escopo**: Recorte inicial descrito no [Documento de Visão](documento_de_visao.md) e no [Cenário GAAP](cenario.md). Os detalhes deste documento que não estiverem alinhados a essas referências precisam ser revalidados.

---

### **3. Empatia**

- **Pesquisa**: O levantamento documental e o brainstorming registrados neste documento são materiais anteriores à adoção do cenário GAAP e devem ser tratados como contexto histórico até serem revalidados.

- **Insights**: Hoje um professor só fica sabendo que tem aula quando alguém manda mensagem, não existe nada fixo, é tudo combinado na hora pelo WhatsApp. Se dois grupos marcarem a mesma sala sem querer, ninguém percebe até um chegar lá e encontrar o outro. Pra aluno menor de idade tem que ter o responsável autorizando antes de qualquer agendamento, isso já traz a LGPD pro fluxo de cadastro.

- **Persona Administrador (Coordenação)**: é quem hoje resolve tudo no improviso, cadastra atividade nova, decide qual sala usar, e quando dois grupos batem no mesmo horário, é quem apaga o incêndio. Quer conseguir cadastrar espaço, profissional e atividade uma vez só e confiar que o sistema não deixa alocar errado depois.

- **Persona Treinador (Professor/Instrutor)**: quer saber a própria agenda sem depender de mensagem avulsa, e quer registrar rápido o que aconteceu na sessão.

- **Persona Profissional de Saúde**: o cenário GAAP define esse perfil como usuário que consulta somente os atendimentos atribuídos ao seu serviço e à sua agenda. Detalhes adicionais de responsabilidades devem ser confirmados antes de serem tratados como requisitos.

---

### **4. Definição**

- **Problema Central**: Como o GAAP pode oferecer uma fonte confiável para acompanhar vagas, presenças e relatórios de treino e apoiar a operação de agenda?

- **Pontos de Vista**: o Administrador vive apagando incêndio de agenda, precisa de um jeito de cadastrar e alocar que já avise quando há conflito, em vez de descobrir depois. Treinador e Profissional de Saúde precisam que o sistema saiba exatamente quem fez o quê, com quem, em qual sessão, um pra organizar o próprio dia, o outro porque a lei exige.

---

### **5. Ideação**

- **Brainstorming**: ideias levantadas na sessão da equipe, cobrindo objetivo do sistema, cadastro de aluno/responsável, cadastro de espaços/profissionais/atividades, alocação de sessão com verificação de conflito, cancelamento/remarcação e informações relevantes de agenda.

- **Critérios de Seleção**: aderência ao escopo já levantado, conformidade com a legislação aplicável (LGPD, ECA, Lei 9.696/1998) e viabilidade de implementação dentro do semestre.

- **Ideias Selecionadas**: cadastro de espaços, profissionais, atividades e alunos/responsáveis; alocação de sessão (espaço, horário e profissional); verificação automática de conflito de agenda e capacidade; consulta de agenda por espaço, profissional e aluno.

---

### **6. Prototipagem**

- **Descrição do Protótipo**: pendente.
- **Materiais Utilizados**: pendente.
- **Testes Realizados**: pendente.

---

### **7. Teste**

- **Feedback dos Usuários**: pendente.
- **Ajustes Realizados**: pendente.
- **Resultados Finais**: pendente.

---

### **8. Conclusão**

- **Resultados Obtidos**: as personas e pontos de vista foram definidos com base no levantamento já feito, e as ideias de ideação já batem com o escopo técnico levantado.

- **Próximos Passos**: aprovação do professor nas documentações, após isso, seguimos para o protótipo de baixa fidelidade.

- **Aprendizados**: aplicar Design Thinking ajudou a conectar as dores de cada ator ao escopo técnico já definido pra API.

---

### **9. Anexos**

- Mapa mental do projeto: [mapa_mental.md](mapa_mental.md)
- Sessão de brainstorming: [Brainstorm.md](Brainstorm.md)

---

## Referências Bibliográficas

> Design Thinking. Disponível em: https://jonh-carvalho.github.io/PECDII_26.2_8001/Iniciacao/design_thinking/

## Autor(es)
| Data | Versão | Descrição | Autor(es) |
| -- | -- | -- | -- |
| 08/09/2026 | 1.0 | Criação do documento | Pedro Lucas |
