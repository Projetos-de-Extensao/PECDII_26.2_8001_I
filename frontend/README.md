# Cliente web do GAAP

Aplicação responsiva em React 19, TypeScript e Vite 8. O cliente consome a API Django existente, usando sessão no servidor e proteção CSRF. As regras de autorização e validação permanecem no backend.

## Requisitos e execução local

- Node.js 22.12 ou superior.
- Inicie o Django a partir de `backend/src/` em `http://127.0.0.1:8000`.
- No terminal do cliente: `cd frontend`, `npm install` e `npm run dev`.
- Abra `http://127.0.0.1:5173`.
- O Vite encaminha `/api/*` para o backend local; configure `server.proxy.target` em `vite.config.ts` se a API usar outro endereço.

Use `npm test` para a suíte do cliente e `npm run build` para conferir tipos e gerar os arquivos de produção em `dist/`.

### Publicação na VPS

O deploy de `main` compila o cliente com Node.js 26 e publica `frontend/dist/` em `/var/www/PECDII_26.2_8001_I/frontend/`. Antes do primeiro deploy do frontend, instale Node.js 26 pelo NVM no usuário `ubuntu` da VPS:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.41.0/install.sh | bash
source ~/.bashrc
cd /home/ubuntu/PECDII_26.2_8001_I/frontend
nvm install
```

O Nginx serve o cliente em `/` e encaminha `/api/`, `/admin/` e `/static/` ao Django. A API deve continuar vinculada a `127.0.0.1:8000`.

## Configuração

| Item | Onde fica | Padrão |
|---|---|---|
| Endereço da API em desenvolvimento | `server.proxy['/api'].target` em `vite.config.ts` | `http://127.0.0.1:8000` |
| Porta do cliente | script `dev` em `package.json` | `5173` |
| Produção | O cliente usa caminhos relativos (`/api/...`); o Nginx serve `dist/` e encaminha `/api/` ao Django (ver “Publicação na VPS”) | — |

A autenticação usa a sessão do Django com CSRF; não há token guardado no navegador.

## Comandos

| Comando | O que faz |
|---|---|
| `npm install` | Instala as dependências |
| `npm run dev` | Sobe o cliente com proxy para a API |
| `npm test` | Roda os testes (Vitest + Testing Library) |
| `npm run build` | Confere os tipos e gera `dist/` |

## Fluxos por perfil

| Perfil | Telas | Endpoints usados |
|---|---|---|
| Administrador | Agenda (Detalhes: presenças, relatório e cancelamento), Pendências (contador no menu e atalho “Ver sessão”), Dashboard, Novo agendamento, Equipe e treinos, Disponibilidade (filtro e edição), Habilitações, Cadastros (criar, listar, editar e remover) | `/api/sessoes/`, `/api/pendencias/`, `/api/dashboard/`, `/api/servicos/`, `/api/profissionais/`, `/api/alunos/`, `/api/disponibilidades/`, `/api/bloqueios-agenda/`, `/api/profissionais-servicos/`, `/api/sessoes/{id}/relatorio/` |
| Treinador | Agenda → Detalhes: presença/falta, “A sessão foi realizada?”, cancelamento e relatório de treino (rascunho e finalização, liberado depois da sessão realizada) | `/api/sessoes/`, `/api/sessoes/{id}/presencas/`, `PATCH /api/sessoes/{id}/`, `/api/sessoes/{id}/relatorio/`, `/api/sessoes/{id}/relatorio/finalizar/` |
| Profissional de Saúde | Agenda própria → Detalhes: presença/falta, “A sessão foi realizada?” e cancelamento | `/api/sessoes/`, `/api/sessoes/{id}/presencas/`, `PATCH /api/sessoes/{id}/` |

O Administrador consulta presenças e relatórios, mas não os altera (D-15). Cancelar uma sessão é permitido ao Administrador e ao profissional responsável (D-17).

O menu mostra só as telas que se aplicam ao perfil, mas quem decide é a API: horário, responsável, capacidade e permissões continuam no backend, e o cliente apenas exibe a resposta.

## Estados de tela

`src/errors.ts` traduz as respostas da API em mensagens:

| Resposta | O que a tela mostra |
|---|---|
| carregando | indicador “Carregando…” |
| sucesso | mensagem verde (ex.: “Presença registrada.”) |
| 400 | “Revise os dados: …” com os campos apontados pela API |
| 401 | volta ao login com “Sua sessão expirou. Entre novamente.” |
| 403 | “Acesso negado: …” |
| 404 | “Não encontrado: …” (no relatório, 404 significa “ainda não tem relatório” e abre o formulário vazio) |
| 409 | “Operação recusada: …” (ex.: presença antes do fim da sessão, conflito de agenda) |
| falha de rede | “Falha de conexão. Verifique a rede e tente novamente.” |

## Testes e validação de layout

- `src/App.test.tsx`: login, cadastro e erro de credenciais.
- `src/flows.test.tsx`: fluxos principais dos três perfis, incluindo 401, 403, 404, 409 e falha de rede.
- `src/review.test.tsx`: itens da revisão da interface (contador e atalho de pendências, detalhes e cancelamento pelo Administrador, CRUD de cadastros, contador de alunos do novo agendamento e edição de disponibilidade).

Os layouts foram conferidos em 1920×1080 e 390×844 com a API real e dados de exemplo, em todas as telas dos três perfis: nenhuma tela tem rolagem horizontal. Em telas estreitas o menu quebra em mais de uma linha e a tabela do dashboard rola dentro do próprio quadro.
