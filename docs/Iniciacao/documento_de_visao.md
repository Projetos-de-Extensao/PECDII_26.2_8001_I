---
id: documento_de_visao
title: Documento de Visão
---
## Introdução

Este documento apresenta a visão do recorte inicial do **GAAP (Gestão de Atletas de Alta Performance)** desenvolvido na disciplina Projeto de Extensão em Computação II (IBM8936), no Ibmec. O produto acadêmico é uma API back-end para apoiar a operação de agenda e treino de uma escola de treinamento esportivo. PKZ & One to One é o ambiente analisado que inspirou o cenário, não o nome do produto desenvolvido.

## Descrição do Problema

### Problema

Uma escola de treinamento esportivo precisa organizar alunos, profissionais e sessões de Treino, Fisioterapia, Psicologia e Nutrição. A operação depende de controles dispersos e não possui uma fonte confiável para acompanhar vagas, presenças e relatórios de treino.

### Impactados

O cenário identifica três perfis de usuário: Administrador, Treinador e Profissional de Saúde. Alunos também são atendidos pelo sistema, mas não são descritos como um perfil de acesso inicial no cenário.

### Consequências

Sem uma fonte confiável para a agenda e os registros de treino, a equipe tem dificuldade para acompanhar vagas, presenças e relatórios, além de prevenir conflitos e respeitar bloqueios de agenda e limites de capacidade.

### Solução

Entregar uma API funcional, testada e documentada para sustentar a operação de agenda e treino do recorte inicial do GAAP, com autenticação e autorização por perfil.

## Objetivos

- Organizar os dados de alunos, profissionais e serviços necessários à operação (RF-02).
- Apoiar a consulta e a gestão da agenda, incluindo horários e bloqueios (RF-03, RF-04).
- Evitar a confirmação de agendamentos conflitantes, bloqueados ou acima da capacidade (RF-05; RN-01 a RN-04).
- Permitir o registro de presença/falta e a criação e finalização de relatórios de treino por profissionais autorizados (RF-06, RF-07; RN-05).
- Entregar uma API com autenticação, autorização e persistência relacional, testada e documentada (RF-01; RNF-01 a RNF-05).

## Perfis de Usuário

| Perfil | Responsabilidades iniciais |
|---|---|
| Administrador | Mantém alunos, profissionais, serviços, horários e bloqueios; consulta pendências (RF-02 a RF-05). |
| Treinador | Consulta a agenda sob sua responsabilidade, registra presença/falta e cria/finaliza relatórios de treino (RF-04, RF-06, RF-07). |
| Profissional de Saúde | Consulta somente os atendimentos atribuídos ao seu serviço e à sua agenda e registra presença/falta dos alunos atendidos sob sua responsabilidade (RF-04, RF-06). |

## Escopo do MVP

O MVP contempla uma API back-end com autenticação e autorização por perfil; cadastro dos dados de base e configuração de ao menos um serviço; gestão de horários e bloqueios; consulta de agenda; validação de conflitos e capacidade nos agendamentos; registro de presença/falta; e criação e finalização de relatórios de treino por profissionais autorizados (RF-01 a RF-07; RN-01 a RN-06).

O cenário recebido deixa em branco quatro itens da lista de funcionalidades iniciais, não enumera as entidades mínimas e não detalha as regras RN01–RN03 nem os requisitos não funcionais. Os itens acima se limitam ao que está descrito no contexto, nos perfis e nos critérios de aceite do cenário. Regras e detalhes adicionais devem ser confirmados antes de serem assumidos como requisitos.

## Fora do Escopo

Esta entrega não inclui os itens abaixo, salvo a exceção identificada com RF-08:

- Pagamentos, gateway, cobrança recorrente ou ledger financeiro completo — não implementados.
- Prontuário clínico detalhado, assinatura digital ou cálculos de força por sexo e idade — não implementados.
- Aplicativo mobile — não implementado.
- QR Code — não implementado.
- Notificações por WhatsApp — não implementadas.
- Notificações por e-mail — **RF-08 implementada fora do escopo**, por recomendação do professor durante uma revisão com a equipe em 14/10/2026.
- Operação offline — não implementada.
- Dashboards analíticos, data warehouse, multi-tenancy e integrações públicas — não implementados.
- Geração de PDF e upload de fotos — não implementados; devem ser documentados pontos de extensão para essas evoluções.

O cenário lista notificações por e-mail entre os itens fora do escopo. A equipe manteve a implementação após recomendação do professor durante uma revisão em 14/10/2026; RF-08 registra essa exceção. Requisitos, regras e dúvidas estão detalhados em [LevReq](../Elaboracao/levreq.md); a [tabela de rastreabilidade](../Elaboracao/rastreabilidade.md) relaciona este documento aos demais artefatos.

## Restrições e Requisitos de Qualidade

- A solução é uma API back-end, sem aplicativo mobile ou operação offline nesta entrega.
- A persistência deve usar banco de dados relacional normalizado, com chaves, restrições e índices adequados às consultas de agenda.
- Senhas não podem ser armazenadas em texto puro; devem ser protegidas por hash.
- As operações devem validar dados e permissões, e os testes automatizados devem cobrir as regras prioritárias.
- A implementação deve seguir as fases e iterações RUP/UP descritas no [Cenário de Aula: Backend GAAP](cenario.md).

## Referências

- [Cenário de Aula: Backend GAAP](cenario.md), referência principal para o problema, perfis, escopo e critérios de aceite.
- [Glossário do domínio](../Elaboracao/glossario.md), vocabulário comum do projeto.
- [Levantamento de Requisitos](../Elaboracao/levreq.md), requisitos RF, RN e RNF.
- [Tabela de rastreabilidade](../Elaboracao/rastreabilidade.md), relação entre requisitos e artefatos.
- [Pesquisa](pesquisa.md), levantamento complementar do projeto.

## Versionamento
| Data | Versão | Descrição | Autor(es) |
|---|---|---|---|
| 27/09/2026 | 1.0 | Criação do documento de visão da API da Playmakerz Lab | Rodrigo |
| 29/09/2026 | 1.1 | Delimitação do escopo de agenda e registro de ocorrências, distinção entre remarcação de sessão e de participação | Pedro Lucas |
| 21/10/2026 | 2.0 | Revalidação do problema, dos perfis e do recorte do MVP com base no cenário GAAP | Equipe |
| 21/10/2026 | 2.1 | Registro da manutenção das notificações automáticas por e-mail como funcionalidade implementada fora do escopo | Equipe |
| 28/10/2026 | 2.2 | Rastreabilidade dos objetivos, perfis e escopo aos requisitos; registro explícito da RF-08 como exceção implementada fora do escopo | Pedro Lucas |
| 28/10/2026 | 2.3 | Alinhamento das responsabilidades do Profissional de Saúde à RF-06 para presença/falta nos atendimentos | Pedro Lucas |
