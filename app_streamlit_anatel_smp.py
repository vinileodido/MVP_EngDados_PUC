%%writefile app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import matplotlib.pyplot as plt

# Configuração da página
st.set_page_config(page_title="Análise de ERBs", layout="wide")
st.markdown("<style>div[data-testid='metric-container'] {background-color: #f0f2f6; border-radius: 5px; padding: 10px;}</style>", unsafe_allow_html=True)

# Função para carregar dados
@st.cache_data
def load_data():
    df_br = pd.read_csv('https://github.com/vinileodido/MVP_EngDados_PUC/raw/refs/heads/main/Datasets/vw_erbs_br.csv', 
                       header=0, names=['PRESTADORA', '2G', '3G', '4G', '5G'])
    df_uf = pd.read_csv('https://github.com/vinileodido/MVP_EngDados_PUC/raw/refs/heads/main/Datasets/vw_erbs_uf.csv', 
                      header=0, names=['UF', 'COD_UF', 'COD_AREA', 'PRESTADORA', '2G', '3G', '4G', '5G'])
    df_cidade = pd.read_csv('https://github.com/vinileodido/MVP_EngDados_PUC/raw/refs/heads/main/Datasets/vw_erbs_cid.csv', 
                          header=0, names=['UF', 'COD_UF', 'COD_AREA', 'COD_IBGE', 'CIDADE', 'CAPITAL', 'PRESTADORA', '2G', '3G', '4G', '5G'])
    
    # Converter valores numéricos para inteiros
    for df in [df_br, df_uf, df_cidade]:
        for col in ['2G', '3G', '4G', '5G']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    
    # Renomear colunas
    df_br = df_br.rename(columns={'PRESTADORA': 'Operadora'})
    df_uf = df_uf.rename(columns={'PRESTADORA': 'Operadora'})
    df_cidade = df_cidade.rename(columns={'PRESTADORA': 'Operadora', 'CIDADE': 'Cidade'})
    
    return df_br, df_uf, df_cidade

# Função para formatação de tabelas
def format_table_with_highlights(df, cols_to_highlight, group_by=None):
    if group_by:
        # Máximos por grupo
        max_values_by_group = {}
        for group_val in df[group_by].unique():
            max_values_by_group[group_val] = {}
            group_df = df[df[group_by] == group_val]
            for col in cols_to_highlight:
                if col in df.columns:
                    max_values_by_group[group_val][col] = group_df[col].dropna().max()
                    
        def highlight_max_by_group(x):
            styles = pd.DataFrame('', index=x.index, columns=x.columns)
            for i, row in x.iterrows():
                for col in cols_to_highlight:
                    if col in x.columns and group_by in x.columns:
                        group_val = row[group_by]
                        if group_val in max_values_by_group and pd.notna(row[col]):
                            if row[col] == max_values_by_group[group_val].get(col):
                                styles.loc[i, col] = 'background-color: #E0FFFF; color: darkblue; font-weight: bold'
            return styles
        
        return df.style.apply(highlight_max_by_group, axis=None).format({col: '{:,.0f}'.format for col in cols_to_highlight}, na_rep="")
    
    else:
        # Máximos sem agrupamento
        max_values = {col: df[col].dropna().max() for col in cols_to_highlight if col in df.columns}
        
        def highlight_max(x):
            return ['background-color: #E0FFFF; color: darkblue; font-weight: bold' 
                    if pd.notna(x[col]) and x[col] == max_values.get(col) else '' 
                    for col in x.index]
        
        return df.style.apply(highlight_max, axis=1, subset=cols_to_highlight).format({col: '{:,.0f}'.format for col in cols_to_highlight}, na_rep="")

# Função que calcula razão 5G/4G
def calculate_5g_growth_ratio(df, group_col=None, top_n_operators=5):
    """
    Calcula a razão entre ERBs 5G e 4G, considerando apenas operadoras principais.
    
    Args:
        df: DataFrame com os dados
        group_col: Coluna para agrupamento (ex: 'UF')
        top_n_operators: Número de operadoras principais a considerar
    
    Returns:
        DataFrame com a razão calculada
    """
    # Verificar se o DataFrame está vazio
    if df.empty:
        if group_col:
            return pd.DataFrame(columns=[group_col, 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
        else:
            return pd.DataFrame(columns=['Operadora', 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
    
    # Identificar as operadoras principais com base no total de ERBs
    operator_totals = df.groupby('Operadora').agg({
        '2G': lambda x: x.fillna(0).sum(),
        '3G': lambda x: x.fillna(0).sum(), 
        '4G': lambda x: x.fillna(0).sum(), 
        '5G': lambda x: x.fillna(0).sum()
    })
    
    operator_totals['Total_ERBs'] = operator_totals['2G'] + operator_totals['3G'] + operator_totals['4G'] + operator_totals['5G']
    
    # Verificar se há operadoras no DataFrame
    if operator_totals.empty:
        if group_col:
            return pd.DataFrame(columns=[group_col, 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
        else:
            return pd.DataFrame(columns=['Operadora', 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
    
    top_operators = operator_totals.nlargest(min(top_n_operators, len(operator_totals)), 'Total_ERBs').index.tolist()
    
    # Filtrar apenas as operadoras principais
    df_filtered = df[df['Operadora'].isin(top_operators)]
    
    if group_col:
        result = []
        for group in df_filtered[group_col].unique():
            group_df = df_filtered[df_filtered[group_col] == group]
            total_4g = group_df['4G'].fillna(0).sum()
            total_5g = group_df['5G'].fillna(0).sum()
            ratio = (total_5g / total_4g * 100) if total_4g > 0 else 0
            result.append({
                group_col: group, 
                'Total 4G': total_4g, 
                'Total 5G': total_5g, 
                'Razão 5G/4G (%)': ratio,
                'Total_ERBs': group_df['2G'].fillna(0).sum() + group_df['3G'].fillna(0).sum() + 
                             group_df['4G'].fillna(0).sum() + group_df['5G'].fillna(0).sum()
            })
        
        # Verificar se result não está vazio antes de tentar classificar
        if not result:
            return pd.DataFrame(columns=[group_col, 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
        
        return pd.DataFrame(result).sort_values('Razão 5G/4G (%)', ascending=False)
    else:
        result = []
        for op in df_filtered['Operadora'].unique():
            op_df = df_filtered[df_filtered['Operadora'] == op]
            total_4g = op_df['4G'].fillna(0).sum()
            total_5g = op_df['5G'].fillna(0).sum()
            ratio = (total_5g / total_4g * 100) if total_4g > 0 else 0
            total_erbs = op_df['2G'].fillna(0).sum() + op_df['3G'].fillna(0).sum() + op_df['4G'].fillna(0).sum() + op_df['5G'].fillna(0).sum()
            result.append({
                'Operadora': op, 
                'Total 4G': total_4g, 
                'Total 5G': total_5g, 
                'Razão 5G/4G (%)': ratio,
                'Total_ERBs': total_erbs
            })
        
        # Verificar se result não está vazio antes de tentar classificar
        if not result:
            return pd.DataFrame(columns=['Operadora', 'Total 4G', 'Total 5G', 'Razão 5G/4G (%)', 'Total_ERBs'])
        
        return pd.DataFrame(result).sort_values('Total_ERBs', ascending=False)

def plot_quadrant_chart(df, title):
    """
    Cria um gráfico de quadrantes que mostra a relação entre volume total de ERBs
    e a razão de modernização 5G/4G
    
    Args:
        df: DataFrame com os dados
        title: Título do gráfico
    """
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Calcular medianas para divisão dos quadrantes
    median_erbs = df['Total_ERBs'].median()
    median_ratio = df['Razão 5G/4G (%)'].median()
    
    # Criar o gráfico de dispersão
    scatter = ax.scatter(
        df['Total_ERBs'], 
        df['Razão 5G/4G (%)'], 
        s=df['Total_ERBs']/df['Total_ERBs'].max() * 500,  # Tamanho normalizado
        c=df['Razão 5G/4G (%)'],  # Cor baseada na razão
        cmap='viridis', 
        alpha=0.7
    )
    
    # Adicionar linhas de referência para os quadrantes
    ax.axhline(y=median_ratio, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=median_erbs, color='gray', linestyle='--', alpha=0.5)
    
    # Adicionar texto para os quadrantes
    ax.text(
        df['Total_ERBs'].max() * 0.75, 
        df['Razão 5G/4G (%)'].max() * 0.9,
        'Alta Modernização\nAlto Volume',
        ha='center', va='center',
        bbox=dict(facecolor='white', alpha=0.5)
    )
    ax.text(
        df['Total_ERBs'].min() * 1.5, 
        df['Razão 5G/4G (%)'].max() * 0.9,
        'Alta Modernização\nBaixo Volume',
        ha='center', va='center',
        bbox=dict(facecolor='white', alpha=0.5)
    )
    ax.text(
        df['Total_ERBs'].max() * 0.75, 
        df['Razão 5G/4G (%)'].min() * 1.5,
        'Baixa Modernização\nAlto Volume',
        ha='center', va='center',
        bbox=dict(facecolor='white', alpha=0.5)
    )
    ax.text(
        df['Total_ERBs'].min() * 1.5, 
        df['Razão 5G/4G (%)'].min() * 1.5,
        'Baixa Modernização\nBaixo Volume',
        ha='center', va='center',
        bbox=dict(facecolor='white', alpha=0.5)
    )
    
    # Adicionar rótulos para cada operadora
    for i, row in df.iterrows():
        ax.annotate(
            row['Operadora'], 
            (row['Total_ERBs'], row['Razão 5G/4G (%)']),
            xytext=(5, 5), 
            textcoords='offset points',
            fontweight='bold'
        )
    
    # Configurar eixos e título
    ax.set_xlabel('Volume Total de ERBs', fontsize=12)
    ax.set_ylabel('Razão 5G/4G (%)', fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # Adicionar barra de cores
    cbar = plt.colorbar(scatter)
    cbar.set_label('Razão 5G/4G (%)')
    
    # Adicionar anotação explicativa
    ax.text(
        0.02, 0.02, 
        "Tamanho do círculo = Volume total de ERBs",
        transform=ax.transAxes,
        bbox=dict(facecolor='white', alpha=0.7)
    )
    
    return fig

# Carregar dados
df_br, df_uf, df_cidade = load_data()

# Sidebar para navegação
st.sidebar.title("Navegação")
page = st.sidebar.radio("Selecione a página:", 
                         ["ERBs por Prestadora - BR", 
                          "ERBs por Prestadora - UF", 
                          "ERBs por Prestadora - Cidade"])

with st.sidebar.expander("📋 Sobre os Dados"):
    st.write("""
    Este dashboard apresenta a análise de ERBs (Estações Rádio Base) licenciadas pelas operadoras de telefonia móvel no Brasil.
    
    Dados da API da Anatel organizados em três níveis:
    - **Nacional (BR)**: Visão consolidada por operadora
    - **Estadual (UF)**: Detalhamento por estado
    - **Municipal (Cidade)**: Detalhamento por cidade
    
    Tecnologias: 2G (GSM), 3G (WCDMA), 4G (LTE), 5G (NR)
    """)

# Página Brasil
if page == "ERBs por Prestadora - BR":
    st.title("Dados de Cobertura por Operadora - Brasil")
    
    # Métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    total_erbs = df_br['2G'].fillna(0).sum() + df_br['3G'].fillna(0).sum() + df_br['4G'].fillna(0).sum() + df_br['5G'].fillna(0).sum()
    col1.metric("Total ERBs", f"{total_erbs:,.0f}".replace(",", "."))
    col2.metric("Total 2G", f"{df_br['2G'].fillna(0).sum():,.0f}".replace(",", "."))
    col3.metric("Total 3G", f"{df_br['3G'].fillna(0).sum():,.0f}".replace(",", "."))
    col4.metric("Total 4G", f"{df_br['4G'].fillna(0).sum():,.0f}".replace(",", "."))
    col5.metric("Total 5G", f"{df_br['5G'].fillna(0).sum():,.0f}".replace(",", "."))
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Tabela de Dados", "📈 Gráficos", "📉 Análises"])
    
    with tab1:
        st.dataframe(format_table_with_highlights(df_br, ['2G', '3G', '4G', '5G']), use_container_width=True, hide_index=True)
        st.markdown("**Legenda:** Os valores destacados representam o maior valor em cada categoria de tecnologia.")
    
    with tab2:
        # Gráfico de barras
        df_melted = df_br.melt(id_vars=['Operadora'], value_vars=['2G', '3G', '4G', '5G'], var_name='Tecnologia', value_name='Quantidade')
        chart = alt.Chart(df_melted).mark_bar().encode(
            x=alt.X('Operadora:N', title='Operadora'),
            y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
            color=alt.Color('Tecnologia:N', scale=alt.Scale(
                domain=['2G', '3G', '4G', '5G'],
                range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
            )),
            tooltip=['Operadora', 'Tecnologia', 'Quantidade']
        ).properties(width='container', height=400)
        st.subheader("Distribuição de ERBs por Operadora e Tecnologia")
        st.altair_chart(chart, use_container_width=True)
        
        # Gráfico de pizza
        st.subheader("Distribuição de ERBs por Tecnologia")
        tech_totals = [df_br['2G'].fillna(0).sum(), df_br['3G'].fillna(0).sum(), df_br['4G'].fillna(0).sum(), df_br['5G'].fillna(0).sum()]
        fig, ax = plt.subplots(figsize=(8, 6))
        labels = ['2G', '3G', '4G', '5G']
        colors = ['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
        total = sum(tech_totals)
        percentages = [val/total*100 for val in tech_totals]
        labels_with_values = [f'{label}: {val:,.0f} ({pct:.1f}%)' for label, val, pct in zip(labels, tech_totals, percentages)]
        ax.pie(tech_totals, labels=labels_with_values, colors=colors, autopct='', startangle=90, shadow=False)
        ax.axis('equal')
        st.pyplot(fig)
    
    with tab3:
      st.subheader("Análise de Modernização da Rede")
      
      # Adicionar seletor para número de operadoras principais
      n_operadoras = st.slider("Número de operadoras principais a considerar:", 
                              min_value=3, max_value=10, value=5)
      
      growth_df = calculate_5g_growth_ratio(df_br, top_n_operators=n_operadoras)
      
      st.markdown(f"##### Razão entre ERBs 5G e 4G para as {n_operadoras} principais operadoras")
      
      # Adicionar colunas de percentual
      growth_df['Percentual 4G'] = growth_df['Total 4G'] / growth_df['Total_ERBs'] * 100
      growth_df['Percentual 5G'] = growth_df['Total 5G'] / growth_df['Total_ERBs'] * 100
      
      # Exibir tabela com dados
      st.dataframe(
          growth_df.style.format({
              'Total 4G': '{:,.0f}'.format, 
              'Total 5G': '{:,.0f}'.format, 
              'Razão 5G/4G (%)': '{:.2f}%'.format,
              'Total_ERBs': '{:,.0f}'.format,
              'Percentual 4G': '{:.1f}%'.format,
              'Percentual 5G': '{:.1f}%'.format
          }),
          use_container_width=True, 
          hide_index=True
      )
      
      # Criar gráfico de quadrantes
      st.subheader("Análise de Quadrantes: Volume vs Modernização")
      quadrant_fig = plot_quadrant_chart(
          growth_df, 
          f"Relação entre Volume e Modernização para as {n_operadoras} Principais Operadoras"
      )
      st.pyplot(quadrant_fig)
      
      st.markdown("""
      **Interpretação dos Quadrantes:**
      
      - **Quadrante Superior Direito:** Operadoras com alto volume de ERBs e alta razão 5G/4G. 
        Estas são líderes em modernização e cobertura, investindo fortemente em tecnologias avançadas.
      
      - **Quadrante Superior Esquerdo:** Operadoras com menor volume total, mas alta taxa de modernização.
        Possivelmente focadas em mercados específicos com estratégia de diferenciação pela tecnologia avançada.
      
      - **Quadrante Inferior Direito:** Operadoras com grande volume de ERBs, mas baixa razão 5G/4G.
        Priorizam cobertura ampla sobre modernização, possivelmente com ênfase em áreas rurais ou de baixa densidade.
      
      - **Quadrante Inferior Esquerdo:** Operadoras com baixo volume e baixa modernização.
        Podem ser operadoras regionais ou com menor capacidade de investimento.
      """)
      
      # Adicionar visualização da proporção de tecnologias por operadora
      st.subheader("Proporção de Tecnologias por Operadora")
      
      # Preparar dados para o gráfico de composição
      tech_cols = ['2G', '3G', '4G', '5G']
      stack_data = []
      
      for i, row in growth_df.iterrows():
          operator = row['Operadora']
          total = row['Total_ERBs']
          # Filtrar dados da operadora do DataFrame original
          op_data = df_br[df_br['Operadora'] == operator].iloc[0]
          
          for tech in tech_cols:
              value = op_data[tech] if pd.notna(op_data[tech]) else 0
              percentage = (value / total * 100) if total > 0 else 0
              stack_data.append({
                  'Operadora': operator,
                  'Tecnologia': tech,
                  'Valor': value,
                  'Percentual': percentage,
                  'Total_ERBs': total
              })
      
      stack_df = pd.DataFrame(stack_data)
      
      # Criar gráfico de barras empilhadas com Altair
      base = alt.Chart(stack_df).encode(
          x=alt.X('Operadora:N', sort='-y'),
          tooltip=['Operadora', 'Tecnologia', 'Valor', 'Percentual']
      )
      
      # Gráfico de valores absolutos
      absolute_chart = base.mark_bar().encode(
          y=alt.Y('Valor:Q', title='Número de ERBs'),
          color=alt.Color('Tecnologia:N', scale=alt.Scale(
              domain=['2G', '3G', '4G', '5G'],
              range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
          ))
      ).properties(
          width='container',
          height=400,
          title='Distribuição Absoluta de Tecnologias'
      )
      
      # Gráfico de valores percentuais
      percentage_chart = base.mark_bar().encode(
          y=alt.Y('Percentual:Q', title='Percentual (%)'),
          color=alt.Color('Tecnologia:N', scale=alt.Scale(
              domain=['2G', '3G', '4G', '5G'],
              range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
          ))
      ).properties(
          width='container',
          height=400,
          title='Distribuição Percentual de Tecnologias'
      )
      
      # Exibir os gráficos lado a lado
      col1, col2 = st.columns(2)
      with col1:
          st.altair_chart(absolute_chart, use_container_width=True)
      with col2:
          st.altair_chart(percentage_chart, use_container_width=True)
      
      st.markdown("""
      **Análise da Distribuição de Tecnologias:**
      
      - Compare a composição tecnológica entre as operadoras principais
      - Observe como algumas operadoras mantêm maior presença de tecnologias legadas (2G/3G)
      - Identifique operadoras com foco em tecnologias mais recentes (4G/5G)
      - A visualização percentual ajuda a entender a estratégia tecnológica de cada operadora, independente do seu tamanho
      """)

# Página UF
elif page == "ERBs por Prestadora - UF":
    st.title("Dados de Cobertura por Operadora - Por Estado")
    
    # Filtro por UF
    ufs = sorted(df_uf['UF'].unique())
    selected_uf = st.selectbox("Selecione o Estado:", ["Todos"] + list(ufs))
    
    # Filtrar dados
    if selected_uf != "Todos":
        filtered_df = df_uf[df_uf['UF'] == selected_uf]
        group_by = None
    else:
        filtered_df = df_uf
        group_by = 'UF'
    
    # Métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    total_erbs = filtered_df['2G'].fillna(0).sum() + filtered_df['3G'].fillna(0).sum() + filtered_df['4G'].fillna(0).sum() + filtered_df['5G'].fillna(0).sum()
    col1.metric("Total ERBs", f"{total_erbs:,.0f}".replace(",", "."))
    col2.metric("Total 2G", f"{filtered_df['2G'].fillna(0).sum():,.0f}".replace(",", "."))
    col3.metric("Total 3G", f"{filtered_df['3G'].fillna(0).sum():,.0f}".replace(",", "."))
    col4.metric("Total 4G", f"{filtered_df['4G'].fillna(0).sum():,.0f}".replace(",", "."))
    col5.metric("Total 5G", f"{filtered_df['5G'].fillna(0).sum():,.0f}".replace(",", "."))
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Tabela de Dados", "📈 Gráficos", "📉 Análises"])
    
    with tab1:
        # Selecionar colunas relevantes
        display_cols = ['UF', 'Operadora', '2G', '3G', '4G', '5G']
        display_df = filtered_df[display_cols]
        st.dataframe(format_table_with_highlights(display_df, ['2G', '3G', '4G', '5G'], group_by), use_container_width=True, hide_index=True)
        if selected_uf != "Todos":
            st.markdown("**Legenda:** Os valores destacados representam o maior valor em cada categoria de tecnologia.")
        else:
            st.markdown("**Legenda:** Os valores destacados representam o maior valor em cada categoria de tecnologia para cada estado.")
    
    with tab2:
        if selected_uf != "Todos":
            # Gráfico para estado específico
            df_melted = filtered_df.melt(id_vars=['Operadora'], value_vars=['2G', '3G', '4G', '5G'], var_name='Tecnologia', value_name='Quantidade')
            chart = alt.Chart(df_melted).mark_bar().encode(
                x=alt.X('Operadora:N', title='Operadora'),
                y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
                color=alt.Color('Tecnologia:N', scale=alt.Scale(
                    domain=['2G', '3G', '4G', '5G'],
                    range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                )),
                tooltip=['Operadora', 'Tecnologia', 'Quantidade']
            ).properties(width='container', height=400)
            st.subheader(f"Distribuição de ERBs em {selected_uf} por Operadora e Tecnologia")
            st.altair_chart(chart, use_container_width=True)
        else:
            # Gráfico para todos os estados
            df_uf_total = filtered_df.groupby('UF').sum().reset_index()
            df_uf_total['Total'] = df_uf_total['2G'].fillna(0) + df_uf_total['3G'].fillna(0) + df_uf_total['4G'].fillna(0) + df_uf_total['5G'].fillna(0)
            df_uf_total = df_uf_total.sort_values('Total', ascending=False)
            
            # Gráfico de barras para total por estado
            st.subheader("Comparação de ERBs por Estado")
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(df_uf_total['UF'], df_uf_total['Total'], color='skyblue')
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:,.0f}'.replace(',', '.'), ha='center', va='bottom', fontweight='bold')
            ax.set_xlabel('Estado (UF)')
            ax.set_ylabel('Total de ERBs')
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            st.pyplot(fig)
            
            # Gráfico para top 10 estados
            top_10_ufs = df_uf_total.head(10)
            df_stacked = top_10_ufs[['UF', '2G', '3G', '4G', '5G']]
            df_stacked_melted = df_stacked.melt(id_vars=['UF'], value_vars=['2G', '3G', '4G', '5G'], var_name='Tecnologia', value_name='Quantidade')
            
            st.subheader("Distribuição de ERBs por Estado e Tecnologia (Top 10)")
            chart = alt.Chart(df_stacked_melted).mark_bar().encode(
                x=alt.X('UF:N', title='Estado', sort='-y'),
                y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
                color=alt.Color('Tecnologia:N', scale=alt.Scale(
                    domain=['2G', '3G', '4G', '5G'],
                    range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                )),
                tooltip=['UF', 'Tecnologia', 'Quantidade']
            ).properties(width='container', height=400)
            st.altair_chart(chart, use_container_width=True)
    
    with tab3:
      st.subheader("Análise de Modernização da Rede")
      
      # Adicionar seletor para número de operadoras principais
      n_operadoras = st.slider("Número de operadoras principais a considerar:", 
                            min_value=3, max_value=10, value=5)
      
      if selected_uf != "Todos":
          # Análise para o estado específico
          growth_df = calculate_5g_growth_ratio(filtered_df, top_n_operators=n_operadoras)
          st.markdown(f"##### Razão entre ERBs 5G e 4G para as {n_operadoras} principais operadoras em {selected_uf}")
          
          # Adicionar colunas de percentual
          growth_df['Percentual 4G'] = growth_df['Total 4G'] / growth_df['Total_ERBs'] * 100
          growth_df['Percentual 5G'] = growth_df['Total 5G'] / growth_df['Total_ERBs'] * 100
          
          # Exibir tabela com dados
          st.dataframe(
              growth_df.style.format({
                  'Total 4G': '{:,.0f}'.format, 
                  'Total 5G': '{:,.0f}'.format, 
                  'Razão 5G/4G (%)': '{:.2f}%'.format,
                  'Total_ERBs': '{:,.0f}'.format,
                  'Percentual 4G': '{:.1f}%'.format,
                  'Percentual 5G': '{:.1f}%'.format
              }),
              use_container_width=True, 
              hide_index=True
          )
          
          # Criar gráfico de quadrantes
          quadrant_fig = plot_quadrant_chart(
              growth_df, 
              f"Relação entre Volume e Modernização em {selected_uf}"
          )
          st.pyplot(quadrant_fig)
          
          # Interpretação e demais visualizações similares à página nacional
          st.markdown("""
          **Interpretação dos Quadrantes:**
          - Os quadrantes mostram a relação entre volume total de ERBs e modernização (5G/4G)
          - Operadoras no quadrante superior direito lideram tanto em volume quanto em modernização
          - Operadoras no quadrante inferior direito têm grande cobertura, mas menor foco em 5G
          """)
          
      else:
          # Análise comparativa entre estados
          growth_df = calculate_5g_growth_ratio(filtered_df, 'UF', top_n_operators=n_operadoras)
          st.markdown("##### Razão entre ERBs 5G e 4G por Estado")
          
          # Adicionar coluna de percentual
          growth_df['Percentual 5G'] = growth_df['Total 5G'] / growth_df['Total_ERBs'] * 100
          
          # Exibir tabela
          st.dataframe(
              growth_df.style.format({
                  'Total 4G': '{:,.0f}'.format, 
                  'Total 5G': '{:,.0f}'.format, 
                  'Razão 5G/4G (%)': '{:.2f}%'.format,
                  'Total_ERBs': '{:,.0f}'.format,
                  'Percentual 5G': '{:.1f}%'.format
              }),
              use_container_width=True, 
              hide_index=True
          )
          
          # Gráfico de dispersão para estados
          fig, ax = plt.subplots(figsize=(12, 8))
          scatter = ax.scatter(
              growth_df['Total_ERBs'], 
              growth_df['Razão 5G/4G (%)'], 
              s=growth_df['Total_ERBs']/growth_df['Total_ERBs'].max() * 500,
              c=growth_df['Razão 5G/4G (%)'],
              cmap='viridis', 
              alpha=0.7
          )
          
          # Adicionar rótulos para cada estado
          for i, row in growth_df.head(15).iterrows():  # Limitar a 15 para não sobrecarregar
              ax.annotate(
                  row['UF'], 
                  (row['Total_ERBs'], row['Razão 5G/4G (%)']),
                  xytext=(5, 5), 
                  textcoords='offset points',
                  fontweight='bold'
              )
          
          ax.set_xlabel('Volume Total de ERBs', fontsize=12)
          ax.set_ylabel('Razão 5G/4G (%)', fontsize=12)
          ax.set_title('Relação entre Volume e Modernização por Estado', fontsize=14)
          ax.grid(True, linestyle='--', alpha=0.3)
          
          cbar = plt.colorbar(scatter)
          cbar.set_label('Razão 5G/4G (%)')
          
          st.pyplot(fig)

# Página Cidade
elif page == "ERBs por Prestadora - Cidade":
    st.title("Dados de Cobertura por Operadora - Por Cidade")
    
    # Filtros UF e Cidade
    col1, col2 = st.columns(2)
    with col1:
        ufs = sorted(df_cidade['UF'].unique())
        selected_uf = st.selectbox("Selecione o Estado:", ["Todos"] + list(ufs))
    
    # Filtrar cidades pelo UF
    if selected_uf != "Todos":
        cidades_filtradas = sorted(df_cidade[df_cidade['UF'] == selected_uf]['Cidade'].unique())
    else:
        cidades_filtradas = sorted(df_cidade['Cidade'].unique())
    
    with col2:
        selected_cidade = st.selectbox("Selecione a Cidade:", ["Todas"] + list(cidades_filtradas))
    
    # Aplicar filtros
    filtered_df = df_cidade
    if selected_uf != "Todos":
        filtered_df = filtered_df[filtered_df['UF'] == selected_uf]
    if selected_cidade != "Todas":
        filtered_df = filtered_df[filtered_df['Cidade'] == selected_cidade]
    
    # Métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    total_erbs = filtered_df['2G'].fillna(0).sum() + filtered_df['3G'].fillna(0).sum() + filtered_df['4G'].fillna(0).sum() + filtered_df['5G'].fillna(0).sum()
    col1.metric("Total ERBs", f"{total_erbs:,.0f}".replace(",", "."))
    col2.metric("Total 2G", f"{filtered_df['2G'].fillna(0).sum():,.0f}".replace(",", "."))
    col3.metric("Total 3G", f"{filtered_df['3G'].fillna(0).sum():,.0f}".replace(",", "."))
    col4.metric("Total 4G", f"{filtered_df['4G'].fillna(0).sum():,.0f}".replace(",", "."))
    col5.metric("Total 5G", f"{filtered_df['5G'].fillna(0).sum():,.0f}".replace(",", "."))
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Tabela de Dados", "📈 Gráficos", "📉 Análises"])
    
    with tab1:
        # Determinar agrupamento e colunas
        display_cols = ['UF', 'Cidade', 'Operadora', '2G', '3G', '4G', '5G']
        if selected_cidade != "Todas":
            group_by = None
        else:
            group_by = 'Cidade'
            
        # Limitar quantidade de linhas se necessário
        if len(filtered_df) > 1000 and selected_cidade == "Todas" and selected_uf == "Todos":
            st.warning("Exibindo apenas as 1000 primeiras linhas devido ao grande volume de dados.")
            display_df = filtered_df[display_cols].head(1000)
        else:
            display_df = filtered_df[display_cols]
            
        st.dataframe(format_table_with_highlights(display_df, ['2G', '3G', '4G', '5G'], group_by), 
                     use_container_width=True, hide_index=True)
        
        # Legenda
        if selected_cidade != "Todas":
            st.markdown("**Legenda:** Os valores destacados representam o maior valor em cada categoria de tecnologia.")
        else:
            st.markdown("**Legenda:** Os valores destacados representam o maior valor em cada categoria de tecnologia para cada cidade.")
    
    with tab2:
        if selected_cidade != "Todas":
            # Gráfico para cidade específica
            df_melted = filtered_df.melt(id_vars=['Operadora'], value_vars=['2G', '3G', '4G', '5G'], 
                                      var_name='Tecnologia', value_name='Quantidade')
            chart = alt.Chart(df_melted).mark_bar().encode(
                x=alt.X('Operadora:N', title='Operadora'),
                y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
                color=alt.Color('Tecnologia:N', scale=alt.Scale(
                    domain=['2G', '3G', '4G', '5G'],
                    range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                )),
                tooltip=['Operadora', 'Tecnologia', 'Quantidade']
            ).properties(width='container', height=400)
            st.subheader(f"Distribuição de ERBs em {selected_cidade} por Operadora e Tecnologia")
            st.altair_chart(chart, use_container_width=True)
            
            # Info de capital
            capital_info = filtered_df['CAPITAL'].iloc[0] if not filtered_df.empty else None
            if capital_info == 1:
                st.info(f"{selected_cidade} é uma capital de estado, o que pode explicar uma melhor cobertura, especialmente em 5G.")
            
        else:
            if selected_uf != "Todos":
                # Mostrar cidades do estado selecionado
                filtered_by_uf = filtered_df[filtered_df['UF'] == selected_uf]
                city_totals = filtered_by_uf.groupby('Cidade').agg({'2G': 'sum', '3G': 'sum', '4G': 'sum', '5G': 'sum'}).reset_index()
                city_totals['Total'] = city_totals['2G'].fillna(0) + city_totals['3G'].fillna(0) + city_totals['4G'].fillna(0) + city_totals['5G'].fillna(0)
                top_cities = city_totals.sort_values('Total', ascending=False).head(10)
                
                # Gráfico de barras para top 10 cidades
                st.subheader(f"Top 10 Cidades em {selected_uf} por Total de ERBs")
                fig, ax = plt.subplots(figsize=(12, 6))
                bars = ax.bar(top_cities['Cidade'], top_cities['Total'], color='skyblue')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:,.0f}'.replace(',', '.'), 
                            ha='center', va='bottom', fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                ax.set_xlabel('Cidade')
                ax.set_ylabel('Total de ERBs')
                st.pyplot(fig)
                
                # Distribuição por tecnologia para top 5
                top5_cities = top_cities.head(5)
                top5_melted = pd.melt(top5_cities, id_vars=['Cidade'], value_vars=['2G', '3G', '4G', '5G'],
                                    var_name='Tecnologia', value_name='Quantidade')
                
                st.subheader(f"Distribuição de ERBs por Tecnologia nas Top 5 Cidades de {selected_uf}")
                chart = alt.Chart(top5_melted).mark_bar().encode(
                    x=alt.X('Cidade:N', title='Cidade'),
                    y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
                    color=alt.Color('Tecnologia:N', scale=alt.Scale(
                        domain=['2G', '3G', '4G', '5G'],
                        range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                    )),
                    tooltip=['Cidade', 'Tecnologia', 'Quantidade']
                ).properties(width='container', height=400)
                st.altair_chart(chart, use_container_width=True)
            
            else:
                # Mostrar capitais brasileiras
                capitais = df_cidade[df_cidade['CAPITAL'] == 1]
                capital_totals = capitais.groupby(['UF', 'Cidade']).agg({
                    '2G': 'sum', '3G': 'sum', '4G': 'sum', '5G': 'sum'
                }).reset_index()
                capital_totals['Total'] = capital_totals['2G'].fillna(0) + capital_totals['3G'].fillna(0) + capital_totals['4G'].fillna(0) + capital_totals['5G'].fillna(0)
                capital_totals = capital_totals.sort_values('Total', ascending=False)
                
                # Gráfico para capitais
                st.subheader("Capitais Brasileiras por Total de ERBs")
                top_capitals = capital_totals.head(15)
                fig, ax = plt.subplots(figsize=(14, 7))
                bars = ax.bar(top_capitals['Cidade'] + ' (' + top_capitals['UF'] + ')', top_capitals['Total'], color='skyblue')
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height, f'{height:,.0f}'.replace(',', '.'), 
                            ha='center', va='bottom', fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
                ax.set_xlabel('Capital')
                ax.set_ylabel('Total de ERBs')
                st.pyplot(fig)
                
                # Distribuição por tecnologia para top 5 capitais
                top5_capitals = capital_totals.head(5)
                top5_melted = pd.melt(top5_capitals, id_vars=['Cidade', 'UF'],
                                    value_vars=['2G', '3G', '4G', '5G'],
                                    var_name='Tecnologia', value_name='Quantidade')
                
                st.subheader("Distribuição de ERBs por Tecnologia nas 5 Principais Capitais")
                chart = alt.Chart(top5_melted).mark_bar().encode(
                    x=alt.X('Cidade:N', title='Cidade'),
                    y=alt.Y('Quantidade:Q', title='Quantidade de ERBs'),
                    color=alt.Color('Tecnologia:N', scale=alt.Scale(
                        domain=['2G', '3G', '4G', '5G'],
                        range=['#FF9800', '#2196F3', '#4CAF50', '#9C27B0']
                    )),
                    tooltip=['Cidade', 'UF', 'Tecnologia', 'Quantidade']
                ).properties(width='container', height=400)
                st.altair_chart(chart, use_container_width=True)
    
    with tab3:
        st.subheader("Análise de Modernização da Rede")
        
        # Adicionar seletor para número de operadoras principais
        n_operadoras = st.slider("Número de operadoras principais a considerar:", 
                              min_value=3, max_value=10, value=5)
        
        if selected_cidade != "Todas":
            # Análise para cidade específica
            if filtered_df.empty:
                st.warning("Não há dados disponíveis para a cidade selecionada.")
            else:
                growth_df = calculate_5g_growth_ratio(filtered_df, top_n_operators=n_operadoras)
                
                # Verificar se há dados após o filtro
                if growth_df.empty:
                    st.warning("Não há dados suficientes para análise com as operadoras principais.")
                else:
                    cidade_title = f"{selected_cidade}" + (f" - {selected_uf}" if selected_uf != "Todos" else "")
                    st.markdown(f"##### Razão entre ERBs 5G e 4G para as {n_operadoras} principais operadoras em {cidade_title}")
                    
                    # Adicionar colunas de percentual
                    growth_df['Percentual 4G'] = growth_df['Total 4G'] / growth_df['Total_ERBs'] * 100
                    growth_df['Percentual 5G'] = growth_df['Total 5G'] / growth_df['Total_ERBs'] * 100
                    
                    # Exibir tabela
                    st.dataframe(
                        growth_df.style.format({
                            'Total 4G': '{:,.0f}'.format, 
                            'Total 5G': '{:,.0f}'.format, 
                            'Razão 5G/4G (%)': '{:.2f}%'.format,
                            'Total_ERBs': '{:,.0f}'.format,
                            'Percentual 4G': '{:.1f}%'.format,
                            'Percentual 5G': '{:.1f}%'.format
                        }),
                        use_container_width=True, 
                        hide_index=True
                    )
                    
                    # Criar gráfico de quadrantes se houver dados suficientes
                    if len(growth_df) >= 4:
                        quadrant_fig = plot_quadrant_chart(
                            growth_df, 
                            f"Relação entre Volume e Modernização em {cidade_title}"
                        )
                        st.pyplot(quadrant_fig)
                    elif len(growth_df) > 0:
                        # Gráfico simplificado para poucos dados
                        fig, ax = plt.subplots(figsize=(10, 6))
                        bars = ax.bar(growth_df['Operadora'], growth_df['Razão 5G/4G (%)'], 
                                    color='skyblue')
                        
                        # Adicionar rótulos de dados
                        for bar in bars:
                            height = bar.get_height()
                            ax.text(bar.get_x() + bar.get_width()/2., height, 
                                    f'{height:.2f}%', ha='center', va='bottom', fontweight='bold')
                        
                        # Adicionar círculos proporcionais ao volume de ERBs
                        for i, row in growth_df.iterrows():
                            ax.scatter(i, row['Razão 5G/4G (%)'] / 2, 
                                      s=row['Total_ERBs'] / growth_df['Total_ERBs'].max() * 500 if growth_df['Total_ERBs'].max() > 0 else 100,
                                      alpha=0.5, color='navy')
                        
                        ax.set_xlabel('Operadora')
                        ax.set_ylabel('Razão 5G/4G (%)')
                        ax.set_title(f'Taxa de Modernização (5G/4G) por Operadora em {cidade_title}')
                        ax.grid(axis='y', linestyle='--', alpha=0.7)
                        st.pyplot(fig)
        
        elif selected_uf != "Todos":
            # Para todas as cidades de um estado
            if filtered_df.empty:
                st.warning(f"Não há dados disponíveis para o estado {selected_uf}.")
            else:
                # Análise similar à página UF, mas para cidades do estado selecionado
                if len(filtered_df['Cidade'].unique()) > 100:
                    st.warning("Muitas cidades para análise. Limitando às 50 principais cidades por volume de ERBs.")
                    # Agrupar por cidade para obter volume total
                    city_volumes = filtered_df.groupby('Cidade').agg({'2G': 'sum', '3G': 'sum', '4G': 'sum', '5G': 'sum'})
                    city_volumes['Total'] = city_volumes.sum(axis=1)
                    top_cities = city_volumes.nlargest(50, 'Total').index.tolist()
                    
                    # Filtrar para as 50 principais cidades
                    filtered_top_cities = filtered_df[filtered_df['Cidade'].isin(top_cities)]
                    growth_df = calculate_5g_growth_ratio(filtered_top_cities, 'Cidade', top_n_operators=n_operadoras)
                else:
                    growth_df = calculate_5g_growth_ratio(filtered_df, 'Cidade', top_n_operators=n_operadoras)
                
                # Verificar se há dados após o filtro
                if growth_df.empty:
                    st.warning("Não há dados suficientes para análise com as operadoras principais.")
                else:
                    st.markdown(f"##### Razão entre ERBs 5G e 4G para Cidades em {selected_uf}")
                    # Exibir tabela 
                    st.dataframe(
                        growth_df.head(15).style.format({
                            'Total 4G': '{:,.0f}'.format, 
                            'Total 5G': '{:,.0f}'.format, 
                            'Razão 5G/4G (%)': '{:.2f}%'.format,
                            'Total_ERBs': '{:,.0f}'.format
                        }),
                        use_container_width=True, 
                        hide_index=True
                    )
        
        else:
            # Para todas as cidades do Brasil
            st.info("Selecione um estado específico para analisar suas cidades. A análise nacional utiliza apenas capitais.")
            
            # Analisar apenas capitais para não sobrecarregar
            capitais = df_cidade[df_cidade['CAPITAL'] == 1]
            
            if capitais.empty:
                st.warning("Não há dados de capitais disponíveis para análise.")
            else:
                growth_df = calculate_5g_growth_ratio(capitais, 'Cidade', top_n_operators=n_operadoras)
                
                # Verificar se há dados após o filtro
                if growth_df.empty:
                    st.warning("Não há dados suficientes para análise com as operadoras principais nas capitais.")
                else:
                    st.markdown("##### Razão entre ERBs 5G e 4G para Capitais Brasileiras")

                    # Exibir tabela
                    st.dataframe(
                        growth_df.head(15).style.format({
                            'Total 4G': '{:,.0f}'.format, 
                            'Total 5G': '{:,.0f}'.format, 
                            'Razão 5G/4G (%)': '{:.2f}%'.format,
                            'Total_ERBs': '{:,.0f}'.format
                        }),
                        use_container_width=True, 
                        hide_index=True
                    )

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888;'>Desenvolvido para análise de ERBs licenciadas no Brasil • Dados: ANATEL</div>", unsafe_allow_html=True)