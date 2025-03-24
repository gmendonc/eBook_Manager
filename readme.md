# Gerenciador de Biblioteca de Ebooks

Uma aplicação Streamlit para gerenciar sua biblioteca de ebooks de várias fontes, enriquecer metadados, visualizar estatísticas e integrar com outras ferramentas como o Notion.

## 📋 Funcionalidades

- **Gerenciamento de Fontes**: Configure e gerencie múltiplas fontes de ebooks (iCloud, Sistema de Arquivos, Dropbox, Kindle)
- **Escaneamento**: Escaneie suas fontes para criar um inventário dos seus ebooks
- **Enriquecimento de Metadados**: Extração automática de autor, título e temas a partir dos nomes de arquivos e conteúdo
- **Visualização e Exploração**: Visualize sua biblioteca com filtros e estatísticas
- **Dashboard Analítico**: Análise gráfica da sua coleção por formato, autor, tamanho e temas
- **Integração com Notion**: Exportação da biblioteca para o Notion para gestão de leitura

## 🚀 Instalação

### Requisitos

- Python 3.7+
- pip

### Dependências

```bash
pip install streamlit pandas matplotlib seaborn altair wordcloud nltk requests
```

Dependências opcionais (para cada tipo de fonte):
```bash
# Para iCloud
pip install pyicloud keyring

# Para Dropbox
pip install dropbox

# Para enriquecimento de arquivos EPUB
pip install ebooklib

# Para enriquecimento de arquivos PDF
pip install PyPDF2
```

### Passos de instalação

1. Clone este repositório ou baixe os arquivos
2. Instale as dependências
3. Execute o aplicativo

```bash
streamlit run app.py
```

## 💡 Como usar

### Configuração de Fontes

1. Na página inicial, clique em "Configurar Fontes"
2. Selecione a aba "Adicionar Fonte"
3. Preencha as informações necessárias para sua fonte:
   - **Nome**: Um nome para identificar sua fonte
   - **Tipo de Fonte**: iCloud, Sistema de Arquivos, Dropbox ou Kindle
   - **Caminho**: Localização dos ebooks na fonte
   - **Credenciais**: Informe as credenciais necessárias (quando aplicável)

### Escaneamento de Ebooks

1. Acesse a página "Escanear Fontes"
2. Selecione uma fonte específica ou escaneie todas de uma vez
3. Aguarde a conclusão do processo
4. Os resultados serão salvos em arquivos CSV

### Visualização da Biblioteca

1. Acesse a página "Visualizar Biblioteca"
2. Selecione o arquivo CSV que deseja visualizar
3. Utilize os filtros disponíveis para explorar sua coleção
4. Você pode fazer download dos dados filtrados em formato CSV

### Dashboard Analítico

1. Acesse a página "Dashboard e Análise"
2. Selecione o arquivo CSV para análise
3. Explore os gráficos e estatísticas nas diferentes abas:
   - **Estatísticas**: Visão geral da biblioteca
   - **Autores**: Análise de autores e suas obras
   - **Formatos e Temas**: Análise de formatos de arquivo e temas
   - **Explorar**: Exploração interativa dos dados

### Integração com o Notion

1. Configure sua integração com o Notion em "Configurar Fontes" > "Integração com Notion"
2. Você precisará:
   - Criar uma integração no site do Notion
   - Obter um token de integração
   - Configurar uma página e uma base de dados
3. Com a integração configurada, você pode exportar seus ebooks para o Notion diretamente da página "Visualizar Biblioteca"

### Fluxo de Trabalho Completo

1. Acesse a página "Fluxo Completo"
2. Esta opção executará automaticamente:
   - Escaneamento de todas as fontes
   - Mesclagem dos resultados
   - Enriquecimento de metadados
   - Exportação para o Notion (opcional)

## 📁 Estrutura do Projeto

- **app.py**: Aplicação principal Streamlit
- **ebook_sources.py**: Módulo para escaneamento de fontes
- **ebook_enricher.py**: Módulo para enriquecimento de metadados
- **notion_integration.py**: Módulo para integração com Notion
- **dashboard_utils.py**: Utilitários para dashboard

## ⚙️ Configuração da Taxonomia de Temas

Para melhorar a categorização automática de temas, você pode fornecer um arquivo JSON com sua taxonomia personalizada:

1. Crie um arquivo JSON no formato:
```json
{
  "Ficção": ["Romance", "Fantasia", "Ficção Científica", "Terror"],
  "Não-ficção": ["Biografia", "História", "Ciência", "Filosofia"],
  "Técnico": ["Programação", "Engenharia", "Matemática"]
}
```

2. Configure o caminho para este arquivo em "Configurar Fontes" > "Configurar Taxonomia"

## 🔍 Solução de Problemas

- **Erro de conexão com iCloud**: Verifique suas credenciais e se autenticação de dois fatores está corretamente configurada
- **Erro ao exportar para Notion**: Verifique se a integração tem permissões corretas na página/base de dados
- **Enriquecimento limitado**: Instale as bibliotecas opcionais (ebooklib, PyPDF2) para melhor extração de metadados

## 📝 Limitações

- A extração de metadados funciona melhor com arquivos EPUB e PDF
- A autenticação de dois fatores no iCloud pode exigir interação manual
- O processamento de grandes bibliotecas pode ser lento

## 🤝 Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## 📄 Licença

Este projeto está licenciado sob a licença MIT.