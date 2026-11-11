# GAAP — Gestão de Atletas de Alta Performance

**Código da Disciplina**: IBM8936 (PECDII_26.2_8001)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white" alt="Python 3.14">
  <img src="https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white" alt="Django 6.1">
</p>

Projeto acadêmico baseado no cenário Backend GAAP. O produto é uma API Django REST Framework para apoiar a agenda e o treino de uma escola de treinamento esportivo. O ambiente PKZ & One to One é a referência analisada no cenário.

## Estado atual

A API oferece operações REST para:

- **Alunos**: cadastro, consulta, edição e remoção; telefones internacionais são validados pelo DDI e formatados conforme o país. Números sem DDI assumem o Brasil.
- **Profissionais**: cadastro dos Treinadores e Profissionais de Saúde do GAAP, junto com a conta usada para acessar a API. A senha é guardada somente como hash.
- **Serviços**: catálogo com as categorias Treino, Fisioterapia, Psicologia e Nutrição. O nome do serviço é único.
- **Disponibilidade e bloqueios**: períodos gerais por profissional, compartilhados entre os serviços; intervalos inválidos são recusados.
- **Sessões**: agendamento de treinamento ou avaliação, vínculo a um profissional, descrição, observações, horários e estado de realização.

Se uma sessão continuar com status `AGENDADA` 30 minutos após o horário de término, um timer do `systemd` verifica isso a cada minuto e notifica o profissional responsável. O profissional registra o desfecho atualizando o status para `REALIZADA` ou `NAO_REALIZADA` e pode editar as observações. Cada sessão é notificada uma única vez. O backend padrão é o console do Django; para enviar e-mails na VPS, configure o SMTP no arquivo `src/.env`.

## Documentação

- [Documentação do projeto publicada](https://projetos-de-extensao.github.io/PECDII_26.2_8001_I/)
- [Documentos e diagramas](docs/)
- [Requisitos](docs/Elaboracao/levreq.md)
- [Casos de uso](docs/Elaboracao/casos_de_uso.md)
- [Diagrama de classes](docs/Elaboracao/diagrama_de_classes.md)
- [Modelo para documentos](docs/Iniciacao/doc_template.md)

## API

Os endpoints ficam sob `/api/`:

| Recurso | Endpoint |
| --- | --- |
| Alunos | `/api/alunos/` |
| Profissionais | `/api/profissionais/` |
| Serviços | `/api/servicos/` |
| Sessões | `/api/sessoes/` |
| Sessões ainda agendadas 30 minutos após o fim | `/api/sessoes/pendentes-status/` |
| Disponibilidades | `/api/disponibilidades/` |
| Bloqueios da agenda | `/api/bloqueios-agenda/` |

Disponibilidade e bloqueio aceitam `GET`, `POST`, `PUT`, `PATCH` e `DELETE` no recurso e em `/api/disponibilidades/{id}/` ou `/api/bloqueios-agenda/{id}/`. O payload da disponibilidade contém `profissional`, `inicio` e `fim`; o bloqueio também aceita `motivo` (opcional, até 200 caracteres). Os horários usam data/hora ISO 8601, por exemplo:

```json
{
  "profissional": 12,
  "inicio": "2026-11-10T09:00:00-03:00",
  "fim": "2026-11-10T12:00:00-03:00"
}
```

O fim precisa ser posterior ao início. A API responde `400` ao intervalo inválido ou profissional que não seja Treinador/Profissional de Saúde, `401` sem autenticação e `403` se um perfil não administrador tentar alterar dados. Qualquer perfil autenticado pode consultar esses períodos, conforme a regra de leitura usada nos demais cadastros.

### Confirmar agendamento

O `POST /api/sessoes/` confirma uma sessão (UC-05) e é exclusivo do Administrador; os demais perfis recebem `403`. O payload informa o serviço, o profissional, o intervalo e os alunos participantes:

```json
{
  "titulo": "Treino de força",
  "tipo": "TREINAMENTO",
  "servico": 3,
  "profissional": 12,
  "inicio": "2026-11-16T09:00:00-03:00",
  "fim": "2026-11-16T10:00:00-03:00",
  "participantes": [5, 8]
}
```

A sessão e os participantes são gravados numa única transação: se qualquer validação ou gravação falhar, nada é gravado (RN-06). A resposta `201` traz a sessão com `participantes` listando os IDs dos alunos, e a presença de cada um começa vazia.

| Resposta | Quando |
| --- | --- |
| `400` | Falta `servico`, `profissional` ou `participantes`; lista de participantes vazia; aluno inexistente ou repetido; fim igual ou anterior ao início. |
| `409` | Regra de negócio violada. O corpo traz a regra e o motivo, por exemplo `{"regra": "RN-02", "detail": "Uma sessão pode ter no máximo 6 alunos; foram informados 7."}`. |

O limite é de 6 alunos por sessão, para qualquer serviço (RN-02). Os participantes são definidos na confirmação: enviar `participantes` num `PUT` ou `PATCH` responde `400`. As validações de habilitação do profissional, disponibilidade, bloqueios e conflitos de horário (RN-01, RN-03, RN-04 e RN-07) rodam no mesmo ponto da confirmação, dentro da transação, e também respondem `409`.

Duas confirmações simultâneas não validam a mesma agenda: o SQLite está configurado com `transaction_mode` `IMMEDIATE`, que reserva a escrita no início da transação, e a segunda confirmação espera a primeira terminar (até 20 segundos) antes de validar (RNF-03).

### Registrar presença ou falta

O `PATCH /api/sessoes/{id}/presencas/` registra a presença de cada aluno participante (RF-06). Só o profissional responsável pela sessão registra; outro profissional e o Administrador recebem `403` (RN-05). O registro pode ser parcial e corrigido depois:

```json
{
  "presencas": [
    {"aluno": 5, "situacao": "PRESENTE"},
    {"aluno": 8, "situacao": "FALTA"}
  ]
}
```

Os registros são gravados juntos: se algum falhar, nenhum é gravado. A resposta `200` traz a sessão, e a consulta de qualquer sessão mostra `presencas`, com `situacao_presenca` nula enquanto não houver registro. Aluno que não participa da sessão, aluno repetido, lista vazia ou situação diferente de `PRESENTE`/`FALTA` recebem `400`; sessão cancelada recebe `409`.

### Perfis e acesso

Toda a API exige autenticação: sem credenciais, a resposta é `401`. Cada conta tem um dos três perfis do GAAP — Administrador, Treinador ou Profissional de Saúde.

Nos cadastros de alunos, profissionais, serviços, disponibilidades e bloqueios, qualquer perfil autenticado consulta, mas só o Administrador cria, edita e remove; os demais recebem `403`. O superusuário do Django é tratado como Administrador, o que permite administrar o sistema antes de existir qualquer cadastro. Nas sessões, qualquer perfil autenticado consulta. Só o Administrador confirma (`POST /api/sessoes/`) e remove sessões. Alterar uma sessão (`PUT`/`PATCH`) é permitido ao Administrador e ao profissional responsável por ela; o responsável muda apenas `status` e `observacoes` (RF-10). Outro profissional recebe `403`. A responsabilidade da sessão é enviada no campo `profissional` com o ID do cadastro em `/api/profissionais/`; o antigo campo `professor` e o endpoint `/api/professores/` foram removidos.

O perfil fica no modelo `Usuario`, ligado por `conta` ao usuário do Django, que guarda o login e o hash da senha. Cadastre o primeiro Administrador pelo painel `/admin/`, ou use um superusuário.

Na migração da Construção 1, os professores já cadastrados são convertidos em usuários com perfil Treinador, preservando nome, e-mail, telefone e vínculos com sessões. Essas contas recebem um login interno no formato `gaap-migrado-professor-{id}` e senha inutilizável; um Administrador deve definir a senha antes que o profissional possa autenticar-se. A migração interrompe-se se o e-mail já pertencer a outro perfil GAAP ou se o login interno já estiver ocupado, para evitar associar dados à conta errada.

Para registrar o desfecho, atualize `status` e, opcionalmente, `observacoes` com `PATCH` no endpoint da sessão. O comando para processar notificações pode ser executado manualmente:

```bash
cd src
python manage.py notificar_sessoes_pendentes
```

## Executar localmente

Requer Python 3.14. Na raiz do repositório, crie e ative um ambiente virtual, instale as dependências e configure o ambiente da API:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux/macOS

.venv\Scripts\activate          # Windows PowerShell
pip install -r requirements.txt

cp src/.env.example src/.env    # Linux/macOS
```

Edite `src/.env` e substitua `SECRET_KEY` por uma chave local. Depois, inicie a API:

```bash
cd src
python manage.py migrate
python manage.py runserver
```

A API ficará disponível em `http://127.0.0.1:8000/api/` e o painel administrativo em `http://127.0.0.1:8000/admin/`. Crie um usuário administrativo com `python manage.py createsuperuser`.

## Configurar envio de e-mails por SMTP

O backend padrão imprime os e-mails no terminal e serve para desenvolvimento. Para o timer enviar notificações reais na VPS, configure estas variáveis em `src/.env`, usando os dados fornecidos pelo seu provedor:

```dotenv
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.seu-provedor.com
EMAIL_PORT=587
EMAIL_HOST_USER=conta@seu-dominio.com
EMAIL_HOST_PASSWORD=senha-de-aplicativo
DEFAULT_FROM_EMAIL=conta@seu-dominio.com
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
```

Use a porta e a criptografia exigidas pelo provedor. Normalmente, a porta 587 usa TLS e a porta 465 usa SSL; não habilite `EMAIL_USE_TLS` e `EMAIL_USE_SSL` ao mesmo tempo. Prefira uma senha de aplicativo ou credencial SMTP própria e nunca envie `src/.env` ao Git. O projeto lê essas variáveis e configura o `MAILERS` do Django; esse é o formato atual de configuração de e-mail no Django 6.1 ([documentação oficial](https://docs.djangoproject.com/en/6.1/howto/mailers-migration/)). Como o comando do timer carrega esse mesmo arquivo ao iniciar, as configurações são aplicadas na próxima execução. Para testar manualmente, rode `python manage.py notificar_sessoes_pendentes` dentro de `src/`; sem SMTP, o e-mail aparece no terminal.

## Testes e workflows

O workflow [Verificação de Pull Request](.github/workflows/verificacao-pr.yml) roda em PRs direcionados à `main`. Ele verifica a configuração do Django, detecta migrations ausentes e executa os testes da API. Para rodar as mesmas verificações localmente, dentro de `src/`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test app
```

Após merge em `main`, os workflows [Deploy da API](.github/workflows/deploy-api.yml) e [Deploy da documentação MkDocs](.github/workflows/deploy.yml) cuidam de publicar a API e a documentação, respectivamente.

O GitHub disponibiliza modelos para [pull requests](.github/PULL_REQUEST_TEMPLATE.md) e para abrir issues de [documentação](.github/ISSUE_TEMPLATE/documentacao.md), [bugs](.github/ISSUE_TEMPLATE/reportar_bug.md) e [funcionalidades](.github/ISSUE_TEMPLATE/sugerir_feature.md).
