# MVP_EngDados_PUC

# Objetivo

Como cidadão da Zona Norte do RJ, após passar algumas dificuldades com serviços de banda larga fixa (fibra óptica) sendo vandalizados pelo tráfico de entorpecentes, me coloco em uma necessidade de utilizar exclusivamente os serviços de dados oriundos das redes móveis (ERBs) e nesse tempo, vem o seguinte questionamento: “***Como avaliar a performance de uma prestadora de telefonia móvel em um município Brasileiro***?”

Diante deste fato, vamos utilizar dados oficiais divulgados publicamente pela Anatel (órgão regulamentador das redes de telecomunicações no Brasil), visando comparar a evolução no crescimento de infraestrutura e cobertura, bem como também seus indicadores de performance RQUAL, ajudando a sanar nossa dúvida inicial.

https://www.gov.br/anatel/pt-br/dados/qualidade/qualidade-dos-servicos/sobre-o-rqual

## Indicadores de QoS (Qualidade de Serviço)

| Grupo | Aspecto | Acrônimo | Indicador | Serviços |
| --- | --- | --- | --- | --- |
| Redes | Acessibilidade | IND1 | Conexão de Chamadas na Rede de Acesso | Telefonia Móvel |
| Redes | Retenção | IND2 | Queda de Chamadas | Telefonia Móvel |
| Redes | Acessibilidade | IND3 | Conexão de Dados Medida na Rede de Acesso | Telefonia Móvel |
| Redes | Integridade | IND4 | Cumprimento da Velocidade de download e upload | Telefonia móvel e banda larga fixa |
| Redes | Integridade | IND5 | Latência bidirecional da Conexão de Dados | Telefonia móvel e banda larga fixa |
| Redes | Integridade | IND6 | Variação de Latência da Conexão de Dados | Telefonia móvel e banda larga fixa |
| Redes | Integridade | IND7 | Perda de Pacotes da Conexão de Dados | Telefonia móvel e banda larga fixa |
| Redes | Disponibilidade | IND8 | Disponibilidade | Telefonia móvel, banda larga fixa, telefonia fixa, TV por assinatura |

# Coleta

Os dados foram coletados no portal DadosAbertos disponibilizados pela Anatel:

[https://informacoes.anatel.gov.br/paineis/](https://informacoes.anatel.gov.br/paineis/)

As categorias disponibilizadas pela Anatel que utilizarei neste MVP são:

- Qualidade: https://informacoes.anatel.gov.br/paineis/qualidade
    - Arquivo de indicadores de Qualidade (Dados Brutos): [https://www.anatel.gov.br/dadosabertos/paineis_de_dados/qualidade/indicadores_rqual.zip](https://www.anatel.gov.br/dadosabertos/paineis_de_dados/qualidade/indicadores_rqual.zip)
    
    ![image.png](/Imagens/image.png)
    

- Outorga e Licenciamento:  https://informacoes.anatel.gov.br/paineis/outorga-e-licenciamento
    - Arquivos de estações do SMP (Dados Brutos): [https://www.anatel.gov.br/dadosabertos/paineis_de_dados/outorga_e_licenciamento/estacoes_smp.zip](https://www.anatel.gov.br/dadosabertos/paineis_de_dados/outorga_e_licenciamento/estacoes_smp.zip)
    
    ![image.png](/Imagens/image%201.png)
    

**Bases auxiliares**

Como dados utilizados para enriquecimento, utilizarei a base de códigos de municípios brasileiros divulgada pelo **IBGE:** [https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2023/DTB_2023.zip](https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2023/DTB_2023.zip)

Utilizaremos também a base de códigos de área local nacionais, disponibilizada também pela **Anatel:** [https://www.anatel.gov.br/dadosabertos/paineis_de_dados/areastarifarias/areaslocais.zip](https://www.anatel.gov.br/dadosabertos/paineis_de_dados/areastarifarias/areaslocais.zip)

Os arquivo serão obtidos via download para um repositório temporário no cluster Databricks e posteriormente, pré-processado utilizando scripts na linguagem de programação Python.

# Modelagem

![modelo_dados_MVP.png](/Imagens/modelo_dados_MVP.png)

# Carga de Dados

A carga dos dados está sendo realizada na plataforma Databricks Community, as anotações mais técnicas e passos realizados poderão ser vistos no notebook: https://github.com/vinileodido/MVP_EngDados_PUC/blob/def249e55cc013022dd589c1fd6791513664e67f/databricks_mvp_anatel_smp.ipynb

A abordagem que foi utilizada pode ser analisada na seguinte arquitetura:

![Architecture_MVP.png](/Imagens/Architecture_MVP.png)

os dados são coletados da origem e armazenados localmente no ambiente do cluster; ao invés de carregá-los para a camada ***Bronze***, os mantive “*as-is* ” dentro do repositorio de coleta e carreguei para um job via duckdb para realizar um pré-processamento.

Após os dados transformados e normalizados, foram carregados para a camada ***Silver.***

Na camada ***Gold*** são realizadas construções de visões analíticas visando responder as necessidades do negócio.

# Análise

Para atender aos questionamentos e facilitar tanto a visualização quanto ao manuseio das informações, foi construído um app python em Streamlit e publicado via google colab: https://github.com/vinileodido/MVP_EngDados_PUC/blob/def249e55cc013022dd589c1fd6791513664e67f/MVP_AnatelSMP_StreamlitApp.ipynb

Ao abrir o notebook no colab, basta executar as células individualmente;

**Atenção** ⚠️**:** na última célula será criado um tunnel para poder visualizar o funcionamento da aplicação, caso solicite para instalar o pacote “*localtunnel@2.0.2* ” digite “y” e confirme, será gerado uma url temporária para acesso conforme veremos na image seguinte:

![image.png](/Imagens/image%202.png)

Acesse o endereço que será fornecido pela aplicação, ao carregar solicitará um *password*, basta digitar o endereço ip da **External URL** que está informado na saída da execução da célula.
Aqui no exemplo trata-se do ip 34.169.0.80

![image.png](/Imagens/image%203.png)

## Navegando pela Aplicação

### Tela inicial

Contendo 4 páginas, sendo três delas para visualização das informações de cobertura por operadora em granularidades diferentes (Nacional, UF e Municípios).

A última apresenta índices de qualidade de serviço dos municípios brasileiros.

![image.png](/Imagens/image%204.png)

### ERBs por Prestadora - Visão Nacional

- Tabela de Dados: Apresenta a agregação dos dados por tecnologia e operadora

![image.png](/Imagens/image%205.png)

- Gráficos

![image.png](/Imagens/image%206.png)

![image.png](/Imagens/image%207.png)

- Análise: visa realizar um breve comparativo entre a modernização da infraestrutura entre as top players do mercado

![image.png](/Imagens/image%208.png)

![image.png](/Imagens/image%209.png)

![image.png](/Imagens/image%2010.png)

### ERBs por Prestadora - Visão Unidades Federativas (UF)

Apresenta as mesmas categorizações apresentadas anteriormente, porém em um outro nível de granularidade. Irei demonstrar como exemplo a relação de estados que possuem maior abrangência de concentração de equipamentos e consequentemente cobertura móvel.

![image.png](/Imagens/image%2011.png)

### ERBs por Prestadora - Visão Municípios

Possui o mesmo nível de categorização, porém, com a granularidade por municípios podendo realizar um melhor comparativo visual entre municípios vizinhos ou fronteiriços, qual operadora oferta melhor na região e etc.

![image.png](/Imagens/image%2012.png)

Municípios do Estado do Rio de Janeiro e quais densidades de cobertura móvel apresentam:

![image.png](/Imagens/image%2013.png)

### Indicadores RQUAL

Apresentação da tabela com os valores obtidos por cada prestadora nos municípios brasileiros. Podemos ver pelo exemplo, o comparativo entre as prestadoras Vivo, Claro e Tim para o município do Rio de Janeiro (Capital):

Vivo:

![image.png](/Imagens/image%2014.png)

Claro:

![image.png](/Imagens/image%2015.png)

Tim:

![image.png](/Imagens/image%2016.png)


## Autoavaliação

Podemos observar, principalmente através dos indicadores **IND4 “*Cumprimento da Velocidade de download e upload*”** e **IND8 “*Disponibilidade*”**, que a CLARO e TIM possuem similaridades no comportamento do indicador de velocidade (IND4), enquanto a VIVO possui um breve ganho de performance em relação as outras concorrentes. Já no indicador de Disponibilidade é notório que a TIM apresenta poucas variações entre os períodos dos meses apresentados, enquanto a CLARO e VIVO mantêm uma constância em obter o máximo resultado na disponibilização da rede móvel no município.

As diferenças são poucas e sutis, mas podem pesar em uma escolha quando for levado em consideração pelo cliente e consumidor final.

Os conjuntos de dados são massivos e nem sempre lidar com dados de órgãos públicos são de fáceis manuseio. Creio que o objetivo foi atingido ao responder aos questionamentos e a facilidade de pode visualizar as informações, todo o trabalho foi um ótimo desenvolvimento para contribuir aos meus skills como profissional na carreira de dados.
