---
id: glossario
title: Glossário do Domínio
---
# Glossário do domínio GAAP

Este glossário padroniza os termos dos requisitos, casos de uso, modelos e protótipos. O cenário GAAP é a referência para o vocabulário atual.

| Termo | Definição no projeto |
|---|---|
| GAAP | Gestão de Atletas de Alta Performance; nome do produto acadêmico. |
| Administrador | Perfil que mantém alunos, profissionais, serviços, horários e bloqueios e consulta pendências operacionais. |
| Treinador | Perfil que consulta a agenda sob sua responsabilidade, registra presença/falta e cria e finaliza relatórios de treino. |
| Profissional de Saúde | Perfil que consulta atendimentos atribuídos ao seu serviço e à sua agenda. |
| Aluno | Pessoa atendida pelo GAAP. É um registro administrado no recorte inicial, não um dos três perfis de acesso listados no cenário. |
| Profissional | Pessoa que presta um serviço no GAAP. Pode atuar como Treinador ou Profissional de Saúde conforme seu perfil e vínculo de serviço. |
| Serviço | Categoria de atendimento oferecida: Treino, Fisioterapia, Psicologia ou Nutrição. |
| Sessão | Ocorrência agendada, com serviço, início, fim, profissional responsável e participantes quando aplicável. É o termo genérico do domínio. |
| Atendimento | Sessão associada a um serviço de saúde (Fisioterapia, Psicologia ou Nutrição). Não implica prontuário clínico. |
| Agenda | Visão de sessões, disponibilidades e bloqueios autorizada ao perfil que a consulta. |
| Disponibilidade | Faixa geral de data/horário em que um profissional pode receber sessões de qualquer serviço para o qual esteja habilitado. |
| Bloqueio de agenda | Intervalo geral em que um profissional não pode receber sessões de nenhum serviço. |
| Conflito de horário | Sobreposição entre a sessão solicitada e outro compromisso ou bloqueio aplicável. |
| Capacidade | Limite de participantes permitido para uma sessão/serviço; o cenário não especifica onde esse limite é cadastrado, decisão pendente de confirmação. |
| Presença/falta | Situação de participação de cada aluno em sessão de Treino ou atendimento de saúde, registrada pelo profissional responsável e autorizado. |
| Volume de treino | Quantidade executada expressa como valor e unidade compatíveis com a modalidade; no treino resistido, volume-carga pode usar séries × repetições × carga (kg). Não há uma unidade única válida para modalidades diferentes. |
| Intensidade da sessão | Percepção de esforço do treino registrada pelo Treinador na escala Borg CR10, de 0 a 10. |
| Relatório de treino | Um registro operacional por sessão de Treino, criado pelo Treinador, salvável como rascunho e finalizável após validação. Inclui os participantes, objetivo, exercícios executados, volume com unidade e intensidade Borg CR10. Após finalizado, não pode ser alterado. Não é prontuário clínico. |
| PKZ & One to One | Ambiente analisado que inspirou o cenário; não é o nome do produto acadêmico nem uma especificação para reproduzir todos os seus módulos. |

## Referências para métricas de treino

- A escala [Borg CR10](https://borgperception.se/cr10stinstr/) vai de 0 (“nada”) a 10 (“extremamente forte”); a avaliação da sessão por RPE é usada em diferentes modalidades de exercício ([revisão do método sRPE](https://pubmed.ncbi.nlm.nih.gov/33508782/)).
- Volume-carga no treino resistido pode ser calculado por carga × repetições × séries ([posicionamento da ACSM](https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/)).

## Termos herdados e decisões de nomenclatura

| Termo encontrado em artefatos anteriores | Decisão atual |
|---|---|
| Coordenação/coordenador | Substituir por **Administrador** quando indicar perfil de acesso do produto. Manter apenas em registros históricos de pesquisa ou brainstorm, identificados como anteriores ao cenário. |
| Professor/instrutor | Usar **Treinador** para o perfil do cenário. O código atual ainda contém o modelo `Professor`; esse nome técnico é legado e deve ser migrado em trabalho de implementação próprio, sem alterar o significado do ator nos artefatos atuais. |
| Atividade/modalidade | Usar **Serviço** para uma das quatro categorias do cenário. Preservar “atividade” somente em citação histórica ou quando se referir a outro conceito validado. |
| Espaço/sala | Não tratar como entidade ou regra do MVP sem validação: o cenário atual não lista espaço entre perfis, funcionalidades iniciais ou critérios de aceite. |
| Responsável legal/consentimento | Não tratar como perfil ou fluxo do MVP: não aparece entre os três perfis do cenário. Menções nos artefatos históricos ficam identificadas como legado. |
| Aula experimental/plano regular | Retirar do escopo atual: é regra herdada de documentos anteriores e não aparece no cenário GAAP. |
| Torneio/inscrição em torneio | Conteúdo estranho ao GAAP, presente no antigo protótipo de alta fidelidade; removido do artefato atual. |
| Playmakerz Lab | Referência histórica do levantamento anterior; não usar como nome do produto nem como descrição factual do cenário GAAP. |

## Orientação de uso

Nos documentos atuais, prefira os termos da primeira tabela. Quando uma decisão de domínio não estiver coberta pelo cenário, registre a hipótese e a pendência de validação em vez de apresentá-la como requisito aprovado.
