# Cliente web do GAAP

Aplicação responsiva em React 19, TypeScript e Vite 8. O cliente consome a API Django existente, usando sessão no servidor e proteção CSRF. As regras de autorização e validação permanecem no backend.

## Requisitos e execução local

- Node.js 22.12 ou superior.
- Inicie o Django a partir de `backend/src/` em `http://127.0.0.1:8000`.
- No terminal do cliente: `cd frontend`, `npm install` e `npm run dev`.
- Abra `http://127.0.0.1:5173`.
- O Vite encaminha `/api/*` para o backend local; configure `server.proxy.target` em `vite.config.ts` se a API usar outro endereço.

Use `npm test` para a suíte do cliente e `npm run build` para conferir tipos e gerar os arquivos de produção em `dist/`.

## Fluxos iniciais

- Login por login/e-mail e senha, com sessão Django e CSRF.
- Agenda por período e serviço, limitada pelo perfil autenticado na API.
- Cadastros iniciais de aluno, profissional e serviço, exclusivos do Administrador.
- Estados de carregamento, lista vazia, erro de conexão, validação e acesso negado.

O layout usa o azul-marinho e o amarelo do protótipo, com navegação lateral em desktop e navegação adaptada para telas estreitas. Os formulários e cartões são renderizados com componentes React; dados recebidos da API são exibidos como texto.

