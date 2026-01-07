# Início Rápido

Guia para começar a usar o ImageClicker em 5 minutos.

## CLI - Uso Básico

### 1. Capturar um Template

```bash
python iclick.py capture meu_botao
```

1. Aguarde 3 segundos
2. Posicione o mouse no canto superior esquerdo do elemento
3. Aguarde 3 segundos
4. Posicione o mouse no canto inferior direito
5. Pronto! Template salvo em `images/meu_botao.png`

### 2. Clicar no Template

```bash
python iclick.py click meu_botao
```

O programa buscará o template na tela e clicará no centro.

### 3. Clicar em Janela Específica

```bash
python iclick.py click meu_botao --window "Chrome*"
```

Busca apenas na janela do Chrome.

## GUI - Uso Básico

### 1. Iniciar GUI

```bash
python gui.py
```

Ou clique duas vezes em `ImageClicker.bat`

### 2. Capturar Template

**Método 1**: Atalho Global

1. Pressione `Ctrl+Shift+C`
2. Digite o nome do template
3. A GUI minimiza automaticamente
4. Overlay fullscreen aparece
5. Clique no canto superior-esquerdo do elemento
6. Clique no canto inferior-direito
7. Template capturado!

**Método 2**: Botão Capturar

1. Aba "📋 Tasks"
2. Clique em "📸 Capturar"
3. Siga os mesmos passos

### 3. Adicionar Task

Na aba "📋 Tasks":

1. **Janela**: Selecione a janela alvo (ex: "Chrome - Google")
2. **Imagem**: Selecione o template capturado
3. **Ação**: click / double_click / right_click
4. **Repetir**: ✓ para loop contínuo
5. **Intervalo**: Segundos entre repetições
6. Clique em "+ Adicionar Task"

### 4. Executar Task

**Execução Individual**:

- Clique no botão "▶" na task específica

**Execução em Lote**:

- Clique em "▶ Iniciar Todas" no topo

Para parar: Clique em "⏹ Parar"

## Exemplo Prático: Refresh Automático

### Cenário

Atualizar página do Chrome a cada 10 segundos.

### Passos

1. Abra o Chrome
2. Inicie a GUI do ImageClicker
3. Pressione `Ctrl+Shift+C`
4. Digite: `chrome_refresh`
5. Capture o botão de refresh do Chrome (ícone circular)
6. Na aba Tasks:
   - Janela: "Chrome*"
   - Imagem: chrome_refresh
   - Ação: click
   - Repetir: ✓
   - Intervalo: 10
7. Clique "+ Adicionar Task"
8. Clique "▶" na task
9. Pronto! Refresh automático ativo

Para parar: Clique "⏹" na task

## Exemplo Prático: Script Sequencial

### Cenário

Abrir menu → Clicar em "Salvar" → Aguardar confirmação

### Passos

1. Capture os templates necessários:
   - `menu_button`
   - `save_button`
   - `confirmation_ok`

2. Crie `scripts/salvar.json`:

```json
{
  "name": "Salvar Documento",
  "description": "Abre menu e salva",
  "actions": [
    {
      "type": "click",
      "image": "menu_button",
      "wait": true,
      "required": true
    },
    {
      "type": "wait",
      "seconds": 1
    },
    {
      "type": "click",
      "image": "save_button",
      "wait": true,
      "required": true
    },
    {
      "type": "wait_for",
      "image": "confirmation_ok",
      "timeout": 10
    },
    {
      "type": "click",
      "image": "confirmation_ok"
    }
  ]
}
```

3. Execute:

```bash
python iclick.py run salvar
```

## Exemplo Prático: Multi-Task Paralelo

### Cenário

- Refresh no Chrome a cada 10s
- Save no Excel a cada 5s
- Backup no Notepad a cada 60s

### Passos

1. Capture templates:
   - `chrome_refresh`
   - `excel_save`
   - `notepad_file_menu`

2. Na GUI, adicione 3 tasks:

**Task 1**:

- Janela: "Chrome*"
- Imagem: chrome_refresh
- Ação: click
- Repetir: ✓
- Intervalo: 10

**Task 2**:

- Janela: "*Excel*"
- Imagem: excel_save
- Ação: click
- Repetir: ✓
- Intervalo: 5

**Task 3**:

- Janela: "*Notepad*"
- Imagem: notepad_file_menu
- Ação: click
- Repetir: ✓
- Intervalo: 60

3. Clique "▶ Iniciar Todas"

Todas as tasks rodam em paralelo!

## Dicas Rápidas

### Captura de Templates

- Capture a menor região possível que seja única
- Evite áreas com animação
- Use elementos com cores/formas distintas
- Teste com o botão "🔍 Testar na Tela" (aba Imagens)

### Wildcards em Janelas

- `"Chrome*"` - Começa com "Chrome"
- `"*YouTube*"` - Contém "YouTube"
- `"*- Notepad"` - Termina com "- Notepad"

### Atalhos da GUI

- `Ctrl+Shift+C` - Captura rápida
- `ESC` - Cancelar captura (durante overlay)
- Botão Direito - Reiniciar captura (durante overlay)

### Galeria de Imagens

Aba "🖼️ Imagens":

- Clique em thumbnail para preview
- Clique no preview para ampliar
- "🔍 Testar" - Verifica se encontra na tela
- "✏️ Renomear" - Renomeia template
- "🗑️ Deletar" - Remove template
- "📂 Abrir Pasta" - Explora diretório images/

## Próximos Passos

- Leia os [Conceitos Básicos](concepts.md)
- Explore o [CLI Guide](cli-guide.md) completo
- Aprenda sobre [Tasks](tasks-guide.md) avançadas
- Veja [Best Practices](best-practices.md)

## Ajuda

Se algo não funcionar:

1. Consulte [Troubleshooting](troubleshooting.md)
2. Veja o [FAQ](faq.md)
3. Reporte issues no GitHub
