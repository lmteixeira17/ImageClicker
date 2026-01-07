# ImageClicker - Instruções para Agentes Claude

## Visão Geral

ImageClicker é uma ferramenta de automação de cliques baseada em reconhecimento de imagem para Windows. Suporta execução paralela de múltiplas tasks em diferentes janelas simultaneamente.

**Versão**: 2.0 (Multi-Task & Multi-Window)
**Última Atualização**: 2026-01-06

## Estrutura do Projeto

```text
ImageClicker/
├── iclick.py              # CLI - Interface de linha de comando
├── gui.py                 # GUI - Interface gráfica multi-task
├── images/                # Templates capturados (PNG)
├── scripts/               # Scripts de automação sequencial (JSON)
├── tasks.json             # Configuração de tasks paralelas
├── docs/                  # Documentação estruturada
│   ├── README.md          # Índice da documentação
│   ├── installation.md    # Guia de instalação
│   ├── quickstart.md      # Início rápido
│   ├── concepts.md        # Conceitos fundamentais
│   ├── cli-guide.md       # Guia CLI completo
│   ├── gui-guide.md       # Guia GUI completo
│   ├── templates-guide.md # Gerenciamento de templates
│   ├── tasks-guide.md     # Sistema de tasks
│   ├── scripts-guide.md   # Scripts sequenciais
│   ├── api-reference.md   # Referência técnica
│   ├── architecture.md    # Arquitetura do sistema
│   ├── configuration.md   # Configurações
│   ├── faq.md             # Perguntas frequentes
│   ├── troubleshooting.md # Solução de problemas
│   └── best-practices.md  # Boas práticas
├── claude.md              # Este arquivo (instruções para agentes)
├── CHANGELOG.md           # Histórico de mudanças
├── CONTRIBUTING.md        # Guia de contribuição
├── requirements.txt       # Dependências Python
├── .markdownlint.json     # Config linting markdown
├── iclick.bat             # Launcher Windows (CLI)
├── ImageClicker.bat       # Launcher Windows (GUI)
└── final_icon.ico         # Ícone da aplicação
```

## Tecnologias e Dependências

### Python

- **Versão**: 3.8+
- **Dependências**:
  - `pyautogui` - Automação de mouse/teclado
  - `pillow` - Manipulação de imagens
  - `opencv-python` - Reconhecimento de imagem (template matching)
  - `customtkinter` - Interface gráfica moderna
  - `pywin32` - Controle de janelas Windows
  - `numpy` - Operações com arrays

### Arquitetura

- **CLI (iclick.py)**: Comandos para captura, clique, scripts e tasks
- **GUI (gui.py)**: Interface gráfica com tabs (Tasks, Imagens), galeria, log
- **TaskManager**: Gerenciador de execução paralela com ThreadPoolExecutor
- **Templates**: Imagens PNG para template matching (pyautogui + OpenCV)

## Funcionalidades Principais

### 1. Template Matching

- **pyautogui**: Busca em tela toda (confidence 90%)
- **OpenCV**: Busca em janela específica (threshold 85%, TM_CCOEFF_NORMED)
- Suporte multi-monitor via virtual screen

### 2. Sistema de Tasks (Paralelo)

- Execução simultânea de múltiplas automações
- Cada task monitora uma janela específica (wildcards suportados)
- Controle individual (play/stop por task)
- Persistência em `tasks.json`
- Status em tempo real

### 3. Sistema de Scripts (Sequencial)

- Workflows complexos definidos em JSON
- 8 tipos de ações: click, double_click, right_click, type, press, hotkey, wait, wait_for
- Execução passo-a-passo com validação

### 4. Captura Visual

- Overlay fullscreen multi-monitor
- Preview em tempo real
- Coordenadas e dimensões visíveis
- ESC para cancelar, botão direito para reiniciar

### 5. Galeria de Templates

- Grid de thumbnails 3 colunas
- Preview ampliável
- Teste, renomeação e exclusão de templates
- Integração com Explorer

## Comandos CLI Principais

```bash
# Captura
python iclick.py capture <nome>

# Clique
python iclick.py click <nome>                # Tela toda
python iclick.py click <nome> --window "App" # Janela específica

# Outros
python iclick.py wait <nome>                 # Espera e clica
python iclick.py run <script>                # Executa script JSON
python iclick.py tasks                       # Executa tasks.json
python iclick.py list                        # Lista recursos
```

## Padrões de Código

### Nomenclatura

- **Templates**: `nome_descritivo.png` (snake_case)
- **Scripts**: `nome_script.json` (snake_case)
- **Variáveis**: snake_case
- **Classes**: PascalCase
- **Constantes**: UPPER_CASE
- **Métodos privados**: `_prefixed`

### Paths

- Usar `BASE_DIR` como raiz
- Todos os paths são absolutos
- Hard-coded nos arquivos (editar se necessário)

### Error Handling

- Try-except em operações críticas
- Mensagens descritivas com emojis
- Logs detalhados

### Threading

- ThreadPoolExecutor para tasks paralelas
- threading.Event para stop events (parada graceful)
- threading.Lock para dicionários compartilhados
- GUI: usar `self.after()` para thread-safety

### Encoding

- UTF-8 para todos os arquivos JSON
- Logs com timestamp `[HH:MM:SS]`

---

## 📚 MANUTENÇÃO DA DOCUMENTAÇÃO

### Princípios de Documentação

1. **Documentação é Código**: Trate docs com o mesmo rigor que código
2. **Consistência Absoluta**: Siga padrões estabelecidos
3. **Clareza e Simplicidade**: Escreva para iniciantes e avançados
4. **Atualização Obrigatória**: Mudanças no código = mudanças nos docs
5. **Versionamento**: Documente versão e data de atualização

### Estrutura de Documentação

A documentação está organizada em **docs/** com arquivos específicos:

- **README.md**: Índice e navegação
- **Guias de Uso**: installation, quickstart, conceitos básicos
- **Guias Técnicos**: CLI, GUI, templates, tasks, scripts
- **Referência**: API, arquitetura, configuração
- **Suporte**: FAQ, troubleshooting, best practices

### Regras de Manutenção

#### QUANDO Atualizar Documentação

Você DEVE atualizar a documentação quando:

1. **Adicionar Funcionalidade**:
   - Novo comando CLI
   - Nova feature na GUI
   - Novo tipo de ação em scripts
   - Nova configuração

2. **Modificar Comportamento**:
   - Mudança em algoritmos
   - Alteração de thresholds/defaults
   - Mudança em estrutura de dados

3. **Corrigir Bugs**:
   - Se o bug afeta comportamento documentado
   - Se a correção muda o uso esperado

4. **Refatoração Significativa**:
   - Mudança em arquitetura
   - Rename de funções/classes públicas
   - Alteração em APIs

5. **Deprecação/Remoção**:
   - Features removidas
   - APIs depreciadas

#### O QUE Atualizar

##### 1. Mudanças em Código → Docs Afetados

| Tipo de Mudança | Arquivos para Atualizar |
|-----------------|-------------------------|
| Nova funcionalidade CLI | cli-guide.md, quickstart.md, README.md |
| Nova funcionalidade GUI | gui-guide.md, quickstart.md, README.md |
| Novo tipo de ação (script) | scripts-guide.md, concepts.md, api-reference.md |
| Nova configuração | configuration.md, installation.md |
| Mudança em threshold/default | concepts.md, configuration.md, troubleshooting.md |
| Bug fix significativo | troubleshooting.md, faq.md, CHANGELOG.md |
| Refatoração de API | api-reference.md, architecture.md |
| Novo comando | cli-guide.md, quickstart.md, README.md (índice) |
| Nova dependência | installation.md, requirements.txt |
| Mudança em estrutura de arquivos | Todos os guias afetados + claude.md |

##### 2. Sempre Atualizar

- **claude.md**: Se mudanças afetam instruções para agentes
- **CHANGELOG.md**: Todas as mudanças user-facing
- **README.md** (raiz): Se mudanças afetam quick-start geral
- **docs/README.md**: Se novos docs foram adicionados

#### COMO Atualizar Documentação

##### Processo Passo-a-Passo

1. **Identifique Impacto**:
   - Quais features foram afetadas?
   - Quais docs mencionam essas features?
   - Use `grep` para buscar termos relevantes em docs/

2. **Atualize Docs Específicos**:
   - Edite seções relevantes
   - Mantenha estrutura existente
   - Siga padrões de formatação

3. **Atualize Referências Cruzadas**:
   - Links entre docs
   - Exemplos que usam a feature
   - Troubleshooting relacionado

4. **Atualize Changelog**:
   - Adicione entrada em CHANGELOG.md
   - Use formato: `## [Unreleased]` ou `## [X.Y.Z] - YYYY-MM-DD`
   - Categorias: Added, Changed, Deprecated, Removed, Fixed, Security

5. **Atualize Versão/Data**:
   - claude.md: `Última Atualização: YYYY-MM-DD`
   - docs afetados: Adicionar nota de atualização se significativo

##### Padrões de Formatação Markdown

**Headings**:

```markdown
# Título Principal (H1 - apenas um por arquivo)

## Seção Principal (H2)

### Subseção (H3)

#### Sub-subseção (H4)
```

**Listas**:

```markdown
- Item (usar hífen)
  - Sub-item (indent 2 espaços)
- Outro item

1. Item numerado
2. Outro item
```

**Code Blocks**:

````markdown
```python
# Código Python com linguagem especificada
```

```bash
# Comandos bash
```

```json
{
  "json": "example"
}
```
````

**Tabelas**:

```markdown
| Coluna 1 | Coluna 2 | Coluna 3 |
|----------|----------|----------|
| Valor 1  | Valor 2  | Valor 3  |
```

**Links**:

```markdown
[Texto do Link](arquivo.md)
[Link Externo](https://example.com)
[Seção](#titulo-da-secao)
```

**Ênfase**:

```markdown
**Negrito**
*Itálico*
`código inline`
```

**Avisos e Notas**:

```markdown
> **Nota**: Informação importante

> **Aviso**: Cuidado com isso

> **Dica**: Sugestão útil
```

##### Estrutura de Novos Docs

Se criar novo arquivo em docs/:

```markdown
# Título do Documento

Breve descrição (1-2 parágrafos).

## Conteúdo Principal

### Seção 1

Conteúdo...

### Seção 2

Conteúdo...

## Exemplos

### Exemplo 1

```code
exemplo
```

### Exemplo 2

```code
exemplo
```

## Próximos Passos

- [Documento Relacionado 1](link.md)
- [Documento Relacionado 2](link.md)

## Referências

- [API Reference](api-reference.md)
- [Outros links relevantes]
```

#### Regras de CRIAR Novos Docs

**Quando Criar**:

- Nova funcionalidade complexa (> 200 linhas doc)
- Novo conceito fundamental
- Guia tutorial específico
- Referência técnica extensa

**Onde Criar**:

- **docs/** para documentação user-facing
- **docs/dev/** (criar se necessário) para docs técnicos internos
- Atualizar **docs/README.md** com link

**Processo**:

1. Verifique se não existe doc similar
2. Planeje estrutura (outline)
3. Escreva conteúdo
4. Adicione exemplos práticos
5. Adicione links relacionados
6. Atualize docs/README.md (índice)
7. Adicione referências cruzadas em outros docs

#### Regras de REMOVER Docs

**Quando Remover**:

- Feature foi completamente removida
- Doc foi consolidado em outro
- Informação está obsoleta e não aplicável

**Processo**:

1. **Nunca Delete Imediatamente**: Marque como deprecated primeiro
2. Adicione aviso no topo:

```markdown
> **⚠️ DEPRECATED**: Este documento está obsoleto.
> Veja [Novo Documento](link.md) para informação atualizada.
```

3. Após 1-2 versões, delete arquivo
4. Remova links para o doc em outros arquivos
5. Atualize docs/README.md
6. Adicione nota em CHANGELOG.md: "Removed: docs/old-file.md"

#### Regras de ATUALIZAR Docs Existentes

**Edições Menores** (typos, clareza, exemplos):

- Edite diretamente
- Não precisa mencionar em changelog

**Edições Significativas** (mudança de comportamento, novos conceitos):

- Edite conteúdo
- Adicione nota de atualização (se relevante):

```markdown
> **Atualizado em YYYY-MM-DD**: [Descrição da mudança]
```

- Adicione entrada em CHANGELOG.md

**Reestruturação Completa**:

1. Crie novo arquivo com `_new` suffix
2. Reescreva conteúdo
3. Revise e valide
4. Renomeie old → old_deprecated
5. Renomeie new → nome correto
6. Atualize links
7. Delete old após confirmar

### Validação de Documentação

#### Checklist Antes de Commit

- [ ] Todos os links funcionam (internos e externos)
- [ ] Code blocks têm linguagem especificada
- [ ] Exemplos foram testados
- [ ] Sem typos (use spell checker)
- [ ] Formatação markdown correta (.markdownlint.json)
- [ ] Referências cruzadas atualizadas
- [ ] docs/README.md reflete estrutura atual
- [ ] CHANGELOG.md atualizado (se aplicável)
- [ ] claude.md atualizado (se afeta agentes)

#### Linting

Use markdownlint (configurado em .markdownlint.json):

```bash
# Instalar (se disponível)
npm install -g markdownlint-cli

# Validar
markdownlint docs/**/*.md claude.md

# Auto-fix (cuidado!)
markdownlint --fix docs/**/*.md
```

Regras desabilitadas (ver .markdownlint.json):

- MD013 - Line length (linhas podem ser longas)
- MD033 - HTML inline (permitido quando necessário)
- MD041 - First line heading (nem sempre aplicável)

### Workflow de Atualização Completo

#### Exemplo: Adicionando Nova Feature

**Cenário**: Adicionei suporte a `triple_click` em tasks.

**Steps**:

1. **Identifique Impacto**:
   ```bash
   cd docs/
   grep -r "double_click" .
   # Encontrou: concepts.md, tasks-guide.md, api-reference.md
   ```

2. **Atualize Docs Específicos**:

   **tasks-guide.md**:
   ```markdown
   ## Tipos de Ação

   - `click` - Clique simples
   - `double_click` - Duplo clique
   - `triple_click` - Triplo clique (novo!)
   - `right_click` - Clique direito
   ```

   **concepts.md**:
   ```markdown
   ### Estrutura de uma Task

   action: "click" | "double_click" | "triple_click" | "right_click"
   ```

   **api-reference.md**:
   ```markdown
   #### find_and_click()

   **Parameters**:
   - action (str): "click" | "double_click" | "triple_click" | "right_click"
   ```

3. **Atualize CHANGELOG.md**:
   ```markdown
   ## [Unreleased]

   ### Added
   - Suporte a triplo clique (`triple_click`) em tasks e scripts
   ```

4. **Atualize claude.md**:
   ```markdown
   ## Funcionalidades Principais

   ### 2. Sistema de Tasks
   - Suporte a múltiplos tipos de clique (simples, duplo, triplo, direito)
   ```

5. **Valide**:
   - Teste exemplos
   - Verifique links
   - Markdownlint
   - Review completo

#### Exemplo: Corrigindo Bug Documentado

**Cenário**: Bug em multi-monitor foi corrigido (coordenadas negativas).

**Steps**:

1. **Atualize troubleshooting.md**:
   ```markdown
   ## Multi-Monitor Issues

   ### ~~Coordenadas Negativas~~

   **Status**: Resolvido na v2.0.1

   ~~Problema: Templates em monitor secundário (esquerda) não funcionavam.~~

   Solução: Atualizado para usar virtual screen corretamente.
   ```

2. **Atualize concepts.md** (se aplicável):
   ```markdown
   ## Multi-Monitor

   - Suporte completo a coordenadas negativas (monitor à esquerda)
   ```

3. **CHANGELOG.md**:
   ```markdown
   ## [2.0.1] - 2026-01-06

   ### Fixed
   - Corrigido suporte a coordenadas negativas em multi-monitor
   ```

4. **faq.md** (adicione se comum):
   ```markdown
   **P: Funciona com monitor à esquerda?**

   R: Sim! A partir da v2.0.1, suporte completo a múltiplos monitores.
   ```

### Templates para Docs Comuns

#### Novo Guia Tutorial

```markdown
# [Nome do Guia]

[Breve descrição em 1-2 parágrafos]

## Pré-requisitos

- Item 1
- Item 2

## [Seção Principal 1]

### Conceito

Explicação...

### Exemplo Prático

```code
exemplo
```

## [Seção Principal 2]

...

## Troubleshooting

### Problema Comum 1

**Sintoma**: Descrição

**Solução**: Passos

## Próximos Passos

- [Doc Relacionado](link.md)

## Referências

- [API](api-reference.md)
```

#### Nova Entrada de FAQ

```markdown
**P: [Pergunta]?**

R: [Resposta clara e concisa]

[Exemplo de código ou comando, se aplicável]

```bash
comando exemplo
```

Veja também: [Doc Relacionado](link.md)
```

#### Nova Entrada de Troubleshooting

```markdown
### [Nome do Problema]

**Sintomas**:
- Sintoma 1
- Sintoma 2

**Causa Provável**:
Explicação técnica breve.

**Solução**:

1. Passo 1
   ```bash
   comando
   ```

2. Passo 2

3. Passo 3

**Verificação**:
Como confirmar que foi resolvido.

**Se Não Resolver**:
- Alternativa 1
- Alternativa 2
- Link para support/issue tracker
```

---

## 🤖 INSTRUÇÕES ESPECÍFICAS PARA AGENTES

### Ao Modificar Código

**SEMPRE**:

1. Identifique docs impactados
2. Atualize docs relevantes NA MESMA SESSÃO
3. Valide exemplos de código em docs
4. Atualize CHANGELOG.md se user-facing
5. Mencione mudanças em docs no commit/resposta

**NUNCA**:

- Deixe docs desatualizados "para depois"
- Assuma que mudança é "pequena demais" para docs
- Crie inconsistências entre código e docs

### Ao Responder Perguntas

**Use a Documentação**:

1. Busque primeiro em docs/ (Read tool)
2. Referencie docs em respostas: "Veja [Guia X](docs/X.md)"
3. Se doc não existe, sugira criar

**Atualize se Necessário**:

- Se resposta revela gap em docs → adicione em FAQ
- Se problema comum → adicione em troubleshooting
- Se conceito não documentado → adicione em concepts.md

### Ao Adicionar Features

**Processo Obrigatório**:

1. Implemente feature
2. Teste funcionamento
3. **Escreva/atualize docs**:
   - Guia relevante (cli/gui/tasks/scripts)
   - Exemplos práticos
   - API reference (se aplicável)
   - Troubleshooting (problemas conhecidos)
4. Atualize CHANGELOG.md
5. Atualize claude.md (se afeta agentes)
6. Valide exemplos
7. Commit tudo junto

### Ao Fazer Refatoração

**Se Refatoração Interna** (não afeta usuário):

- Atualize apenas architecture.md e api-reference.md (se necessário)
- Não precisa changelog

**Se Refatoração Afeta API/Uso**:

- Trate como "mudança de comportamento"
- Atualize todos os docs relevantes
- Deprecation notice se aplicável
- CHANGELOG.md: seção "Changed"

### Verificação Final

Antes de considerar tarefa completa:

```text
✅ Código funciona
✅ Testes passam (se houver)
✅ Docs atualizados
✅ Exemplos testados
✅ Links funcionam
✅ CHANGELOG.md atualizado (se aplicável)
✅ claude.md atualizado (se afeta agentes)
✅ Sem markdown warnings (.markdownlint.json)
```

---

## Referências Rápidas

### Comandos Úteis

```bash
# Buscar em docs
grep -r "termo" docs/

# Listar todos os docs
ls docs/*.md

# Validar markdown (se markdownlint instalado)
markdownlint docs/**/*.md

# Contar linhas de doc
wc -l docs/*.md
```

### Links Internos Importantes

- [Documentação Principal](../docs/README.md)
- [Instalação](../docs/installation.md)
- [Início Rápido](../docs/quickstart.md)
- [Conceitos](../docs/concepts.md)
- [FAQ](../docs/faq.md)
- [Changelog](../CHANGELOG.md)

### Contato e Suporte

- **GitHub Issues**: Para bugs e feature requests
- **Docs**: Sempre consulte primeiro
- **Claude.md**: Para instruções aos agentes (este arquivo)

---

**Manutenção deste documento**: Atualize sempre que:

- Estrutura do projeto mudar
- Novos padrões forem estabelecidos
- Regras de documentação forem modificadas
- Workflow de desenvolvimento mudar

**Última Revisão Completa**: 2026-01-06
