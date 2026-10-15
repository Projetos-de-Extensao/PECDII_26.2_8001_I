# Sistema de Gestão de Treinamento e Acompanhamento de Performance

**Código da Disciplina**: IBM8936 (PECDII_26.2_8001)

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white" alt="Python 3.14">
  <img src="https://img.shields.io/badge/Django-6.1-092E20?logo=django&logoColor=white" alt="Django 6.1">
</p>

Projeto desenvolvido para a PKZ Lab, centro de treinamento de performance integrada na Barra da Tijuca. O sistema está sendo construído como uma API Django REST Framework para organizar alunos, professores e sessões de treinamento e avaliação.

## Estado atual

A API oferece operações REST para:

- **Alunos**: cadastro, consulta, edição e remoção; telefones brasileiros são validados e normalizados.
- **Professores**: cadastro, consulta, edição e remoção, com e-mail de contato.
- **Sessões**: agendamento de treinamento ou avaliação, vínculo obrigatório a um professor, descrição, observações, horários e estado de realização.

Uma sessão agendada que permaneça sem confirmação por pelo menos 30 minutos após o horário de término pode ser listada para confirmação. O professor pode confirmar se ocorreu e registrar observações. O comando `notificar_sessoes_pendentes` envia e-mail aos professores uma única vez por sessão pendente. O backend de e-mail padrão do projeto é o console do Django, que exibe as mensagens no terminal. O envio real exige configurar um backend SMTP nas configurações da aplicação.

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
| Sessões aguardando confirmação após 30 minutos | `/api/sessoes/pendentes-confirmacao/` |
| Confirmar realização de uma sessão | `/api/sessoes/{id}/confirmar-realizacao/` |

Para confirmar uma sessão, envie `POST` para o endpoint da sessão com `ocorreu` (`true` ou `false`) e, opcionalmente, `observacoes`. O comando para processar notificações pode ser executado manualmente:

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

## Testes e workflows

O workflow [Verificação de Pull Request](.github/workflows/verificacao-pr.yml) roda em PRs direcionados à `main`. Ele verifica a configuração do Django, detecta migrations ausentes e executa os testes da API. Para rodar as mesmas verificações localmente, dentro de `src/`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test app
```

Após merge em `main`, os workflows [Deploy da API](.github/workflows/deploy-api.yml) e [Deploy da documentação MkDocs](.github/workflows/deploy.yml) cuidam de publicar a API e a documentação, respectivamente.

O GitHub disponibiliza modelos para [pull requests](.github/PULL_REQUEST_TEMPLATE.md) e para abrir issues de [documentação](.github/ISSUE_TEMPLATE/documentacao.md), [bugs](.github/ISSUE_TEMPLATE/reportar_bug.md) e [funcionalidades](.github/ISSUE_TEMPLATE/sugerir_feature.md).