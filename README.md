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
- **Professores**: cadastro, consulta, edição e remoção, com e-mail de contato.
- **Sessões**: agendamento de treinamento ou avaliação, vínculo obrigatório a um professor, descrição, observações, horários e estado de realização.

Se uma sessão continuar com status `AGENDADA` 30 minutos após o horário de término, um timer do `systemd` verifica isso a cada minuto e notifica o professor. O professor registra o desfecho atualizando o status para `REALIZADA` ou `NAO_REALIZADA` e pode editar as observações. Cada sessão é notificada uma única vez. O backend padrão é o console do Django; para enviar e-mails na VPS, configure o SMTP no arquivo `src/.env`.

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
| Professores | `/api/professores/` |
| Sessões | `/api/sessoes/` |
| Sessões ainda agendadas 30 minutos após o fim | `/api/sessoes/pendentes-status/` |

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
