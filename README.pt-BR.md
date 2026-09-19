# jev-search

**Encontre pelo significado o que palavras-chave deixam passar.** Busca semântica complementar para agentes explorarem documentos e bases de conhecimento junto com suas ferramentas existentes.

A busca exata encontra nomes, símbolos e referências literais. O `jev-search` acrescenta outra perspectiva: identificar se uma linha expressa a intenção procurada, mesmo usando outras palavras. O objetivo é enriquecer a recuperação de conhecimento, não substituir grep, navegação no repositório ou seu second brain.

### Um primeiro sinal promissor

Em um pequeno experimento sintético PT/EN, o Jev recuperou **três pares distintos de linha/intenção relevantes que uma busca simples por palavras-chave perdeu**, de forma consistente nas duas repetições por intenção. Nesse conjunto, atingiu **100% de precisão e recall**, contra **40% de precisão e 66,7% de recall** do baseline lexical. As seis requisições custaram **US$ 0,000655704**, com **latência HTTP mediana de 0,556 segundo**.

O sinal útil é o conhecimento relevante adicional, não a ideia de substituir um método pelo outro. São resultados reportados pelo autor em 20 linhas inventadas, não um benchmark de repositórios ou bases de notas. Veja [detalhes e limitações do experimento](#experimento-sintético-pequeno).

### Onde a busca complementar pode ajudar

- **Documentação de repositórios:** procurar intenções de projeto e decisões descritas sem as palavras esperadas, depois inspecionar código e pontos de chamada com as ferramentas habituais.
- **LLM Wiki e second brains:** explorar notas Markdown selecionadas em busca de ideias relacionadas expressas de outras formas, depois seguir links e consultar as fontes originais.
- **Fluxos com Obsidian:** acrescentar uma consulta semântica em notas Markdown selecionadas e não privadas, junto da busca por CLI, tags e links existentes. Não inclui plugin nem integração com o CLI do Obsidian.

Exemplo ilustrativo, não um resultado medido: a consulta *decisões que reduzem dependência de fornecedores* poderia encontrar uma nota dizendo *adotamos formatos abertos para facilitar a migração*.

Use nomes de arquivos, índices, tags, links e busca exata para se orientar e selecionar material; explore significado com a busca semântica; leia o contexto para verificar os achados. Não selecione apenas resultados com coincidência literal, pois a busca semântica não recupera aquilo que esse filtro já excluiu.

### O que está disponível hoje

A v0.1.0 experimental pesquisa por linha em pequenos arquivos de texto e logs explicitamente selecionados. **Não percorre pastas ou vaults, interpreta estruturas de código, segue links entre páginas nem compreende um repositório inteiro.** Os limites atuais são **8 arquivos, 64 linhas físicas e 16 KiB no total**, detalhados abaixo. Extensões de código-fonte não são suportadas. Os cenários acima descrevem um fluxo complementar e oportunidades de validação futura, não integrações prontas.

**Simulação local por padrão.** A avaliação semântica real exige `--send`, que envia o conteúdo selecionado à OpenRouter e à TypeSafe. Leia a seção de privacidade antes de usar; vaults privados e repositórios confidenciais não são entradas apropriadas para esta versão.

Implementação Python original, inspirada em [uehaj/jev-semgrep](https://github.com/uehaj/jev-semgrep), sem importar ou executar esse projeto.

Usa `typesafe/jev-1.13` na API Decisions do OpenRouter, não chat ou embeddings. Sem indexação, recursão, serviço, MCP ou dependências de execução.

**Somente Linux, Python 3.11+.** Usa flags POSIX para abertura segura. Windows e macOS não são suportados/testados. [English](README.md).

## Instalação pela tag Git

Requer Git e uv ou pipx. Não é uma publicação no PyPI.

```sh
uv tool install 'git+https://github.com/larguesa/jev-search.git@v0.1.0'
# Alternativa:
pipx install 'git+https://github.com/larguesa/jev-search.git@v0.1.0'
jev-search --help
```

A instalação pode baixar ferramentas de build. O CLI instalado usa apenas a biblioteca padrão. Exemplos e benchmark ficam no checkout do código.

## Uso e privacidade

```sh
# Arquivo pequeno, UTF-8, revisado e sem dados privados.
jev-search --query 'Um cliente pede devolução por cobrança duplicada.' exemplo.log
```

O padrão é **dry-run**: sem rede nem leitura de credenciais. Mostra linhas e payload exato em JSON. Após revisar, configure `JEV_SEARCH_API_KEY` de forma segura com uma chave de inferência de orçamento limitado:

```sh
jev-search --send --max-requests 1 --query 'Um cliente pede devolução por cobrança duplicada.' exemplo.log
```

Nunca use chave de gerenciamento. O CLI não lê `.env`, cria ou revoga chaves. O limite monetário deve ser imposto na chave. Uma chamada pode ser cobrada mesmo com falha de conexão ou resposta rejeitada.

`--send` envia **todas as linhas não vazias selecionadas e a consulta** para `https://openrouter.ai/api/alpha/decisions` e seu provedor, não apenas os resultados positivos. Caminhos não entram no payload, mas podem aparecer no próprio conteúdo. A detecção de segredos é incompleta: revisão humana obrigatória; não use arquivos privados.

A saída contém caminhos absolutos locais e texto original; após envio, também contém a resposta e metadados do provedor, incluindo ID de geração. **Não publique essa saída.** Resultados incluem `line` (base 1), `probability` e `match` (`probability >= 0.5`). Não correspondências permanecem em ordem. Não há validação de que o score seja uma probabilidade calibrada. JSON escapa caracteres não ASCII e controles. Redirecionamento pelo shell pode sobrescrever arquivos.

## Limites

- 1 a 8 arquivos explícitos `.txt`, `.md`, `.csv`, `.jsonl` ou `.log`; UTF-8 estrito. CSV/JSON são lidos por linha, sem interpretar registros.
- Total de 16.384 bytes e 64 linhas físicas; 2.048 bytes por linha; consulta até 512 bytes; requisição serializada até 60.000 bytes. Linhas vazias contam no limite, mas não são avaliadas. Exceder limites falha, sem truncar.
- Rejeita componentes ocultos/suspeitos nos caminhos, symlinks inclusive ancestrais, inodes duplicados, arquivos não regulares, controles binários e padrões comuns de segredo. Não isola contra alteração concorrente de diretórios por adversário local.
- Uma requisição por execução do CLI; sem retries ou redirects. Timeout de socket de 30 segundos, não prazo total. Resposta até 256 KiB. Erros retornam código diferente de zero.
- Valida modelo, IDs, conjunto de respostas, tipo `noul`, scores finitos, custo e tokens. Somente provedor `typesafe`, sem fallback, `data_collection: deny`, preço máximo de entrada USD 0,042/milhão de tokens e saída zero. Isso não garante privacidade nem limita o custo total.
- A API é alpha: disponibilidade, formato e preços podem mudar. Respostas incompatíveis falham sem relaxar restrições.

## Experimento sintético pequeno

20 linhas inventadas PT/EN, 3 intenções, 2 repetições: 6 requisições, 60 pares únicos, 120 decisões. Rótulos, termos do baseline e limiar 0,5 foram definidos antes do piloto. Inclui paráfrases, negação, casos históricos/resolvidos e uma instrução adversarial.

| Método | Precisão micro | Recall micro | TP / FP / FN |
|---|---:|---:|---:|
| Jev | 1,00 | 1,00 | 18 / 0 / 0 |
| Baseline lexical OR por substring | 0,40 | 0,667 | 12 / 18 / 6 |

Custo reportado no piloto: **USD 0,000655704**. Mediana de latência HTTP: **0,556 s**. [Métricas agregadas](benchmark-summary.json), sem IDs de geração, dados de conta, caminhos ou respostas brutas. Evidência bruta não publicada; agregados reportados pelo autor, sem reprodução independente sem nova execução paga. A CI não faz inferência.

Isso **não** valida acurácia de produção, calibração, resistência a injection, qualidade multilíngue ou superioridade a BM25, embeddings ou regras mais fortes. Repetições não são amostras independentes. Linhas compartilham o estado da requisição e podem influenciar outras respostas.

```sh
git clone --branch v0.1.0 https://github.com/larguesa/jev-search.git
cd jev-search
python3 -m unittest -v
python3 jev_search.py --query 'pedido de reembolso' synthetic.txt
python3 benchmark.py  # resumo offline do desenho; sem API
# Opcional e pago: revisar exemplos e configurar chave limitada antes.
python3 benchmark.py --send --output benchmark-run-01
```

O benchmark opcional faz até seis requisições e salva apenas agregados em diretório novo. Não sobrescreve diretórios existentes; falhas deixam o diretório reservado. Interrompe após custo acumulado reportado superar USD 0,09, verificação posterior à cobrança, não garantia de orçamento. Não reutilize a chave do piloto. Execuções parciais não geram resumo completo.

## Desenvolvimento e licença

Testes offline: `python3 -m unittest -v`. Build: `python3 -m build` (requer o pacote `build`). CI prepara ferramentas e depois testa/builda e instala o CLI em venv novo sem inferência. Somente `jev_search` é módulo de execução; o arquivo-fonte distribuído usa lista explícita de inclusão.

MIT, copyright Ricardo Pupo Larguesa. Consulte [LICENSE](LICENSE).
