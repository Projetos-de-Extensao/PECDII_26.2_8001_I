---
id: mapa_mental
title: Mapa Mental do Domínio
---
# Mapa Mental — GAAP

Mapa revisado conforme o cenário GAAP. Os IDs remetem ao [levantamento de requisitos](../Elaboracao/levreq.md); termos estão definidos no [glossário](../Elaboracao/glossario.md).

```plantuml
@startmindmap gaap_mapa_mental
skinparam monochrome true
skinparam ArrowColor #000000
skinparam NodeFontSize 14

* GAAP — API de agenda e treino
** Perfis
*** Administrador
**** RF-02 cadastros de base e serviços
**** RF-03 disponibilidade e bloqueios
**** RF-04 consulta operacional da agenda
**** RF-05 confirmação de agendamento
*** Treinador
**** RF-04 agenda sob responsabilidade
**** RF-06 presença/falta
**** RF-07 relatório de treino
*** Profissional de Saúde
**** RF-04 consulta de atendimentos do serviço e agenda atribuídos
** Domínio
*** Aluno
*** Profissional
*** Serviço: Treino, Fisioterapia, Psicologia, Nutrição
*** Sessão/Atendimento
*** Agenda: disponibilidade, bloqueios, conflitos e capacidade
*** Presença/falta e relatório de treino
** Regras
*** RN-01 conflito de horário
*** RN-02 capacidade máxima
*** RN-03 bloqueio e disponibilidade
*** RN-04 profissional compatível com serviço
*** RN-05 autorização para presença e relatório
*** RN-06 confirmação atômica
** Qualidade
*** RNF-01 banco relacional normalizado
*** RNF-02 hash de senha
*** RNF-03 atomicidade sob concorrência
*** RNF-04 validação e autorização
*** RNF-05 testes e documentação
** Exceção fora do escopo
*** RF-08 notificação por e-mail já implementada
** Fora do MVP
*** pagamentos, prontuário detalhado, assinatura digital
*** mobile, QR Code, WhatsApp, offline
*** dashboards analíticos, BI, multi-tenancy, integrações públicas
*** PDF e upload de fotos
@endmindmap
```

## Referências

- [Cenário GAAP](cenario.md)
- [Documento de Visão](documento_de_visao.md)
- [Glossário](../Elaboracao/glossario.md)
- [Levantamento de Requisitos](../Elaboracao/levreq.md)
