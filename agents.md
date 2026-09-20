# Orientações para agentes

## Fluxo de desenvolvimento

Este projeto utiliza trunk-based development. O trunk é a branch `main`.

- Trabalhe com alterações pequenas e integre-as frequentemente à `main`.
- O fluxo padrão é validar, fazer commit e push diretamente no trunk, dentro do escopo autorizado pelo responsável. Não crie branches ou pull requests por padrão.
- Use branches curtas ou PRs apenas quando explicitamente solicitados ou exigidos pelas proteções do repositório. Não contorne essas proteções.
- Antes de alterar ou publicar, consulte o estado local e faça fetch do remoto. Preserve trabalho de terceiros; não use force-push nem reescreva o histórico compartilhado.
- Antes do push, valide a alteração, revise o diff e verifique que apenas arquivos intencionais serão publicados. Se o trunk tiver avançado, integre as mudanças e valide novamente.
- Após o push, confirme o commit no remoto e os checks do CI. Não considere a entrega concluída com testes falhando.

## Qualidade e fonte de verdade

- Use o código, os testes e os documentos versionados como fonte de verdade. Prefira o menor diff que resolva o problema, reutilizando código e biblioteca padrão.
- Execute `python3 -m tests` e `git diff --check`. Para alterações no CLI, valide também um dry-run; para empacotamento, valide wheel e sdist.
- Preserve compatibilidade com Linux e Windows. Mantenha o comportamento padrão e a proveniência dos resultados; recursos opcionais não devem descartar os resultados originais.
- Não publique credenciais, corpora privados, consultas privadas, respostas brutas ou detalhes de fontes confidenciais. Evidências públicas devem ser sanitizadas.
- Testes de desenvolvimento devem ser offline. Inferências pagas exigem escopo e autorização adequados. Preserve tentativas falhas e limitações; não altere evidências congeladas para obter aprovação.
