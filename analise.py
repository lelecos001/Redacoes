import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
import json
import os

SERVICE_ACCOUNT_INFO = json.loads(os.environ['GOOGLE_CREDENTIALS'])
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
gc = gspread.authorize(credentials)

# Abrindo a planilha e aba
spreadsheet = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/19nGpslFKRyKsMeQy_j9Waw6FvpG2roXTq4OZ0BaumFw/edit?gid=156629943#gid=156629943'
)
worksheet = spreadsheet.worksheet('REDAÇÃO - ENEM')
data = worksheet.get('A:I')

# Configuração da página
st.set_page_config(
    page_title='Redações ENEM',
    page_icon=':page_facing_up:',
    layout='wide'
)

st.write('# Análise das Redações do ENEM')

# Cria o DataFrame e ajusta as colunas
df = pd.DataFrame(data[1:], columns=data[0])

# Converte colunas de nota para numérico
df['NOTA'] = pd.to_numeric(df['NOTA'], errors='coerce')
competencias = ['C1', 'C2', 'C3', 'C4', 'C5']
for c in competencias:
    df[c] = pd.to_numeric(df[c], errors='coerce').round(2)

# Agrupa por aluno e encontra a maior nota de cada um
notas_max = df.groupby('ALUNO')['NOTA'].max()

# Filtra alunos que nunca tiraram 900 ou mais
alunos_abaixo_900 = notas_max[notas_max < 900].index.tolist()

# Filtra apenas os dados desses alunos
df_filtrado = df[df['ALUNO'].isin(alunos_abaixo_900)]

# ========================================
# AGRUPAMENTO POR ALUNO (para tabela final)
# ========================================

# Média por competência por aluno
media_por_competencia = df_filtrado.groupby('ALUNO')[competencias].mean().reset_index()
media_por_competencia[competencias] = media_por_competencia[competencias].round(2)  # ⬅️ Arredonda C1-C5

# Identifica a competência com menor média por aluno
media_por_competencia['COMPETÊNCIA_COM_MAIS_DIFICULDADE'] = media_por_competencia[competencias].idxmin(axis=1)

# Média geral da nota por aluno
media_nota = df_filtrado.groupby('ALUNO')['NOTA'].mean().reset_index().rename(columns={'NOTA': 'MÉDIA'})
media_nota['MÉDIA'] = media_nota['MÉDIA'].round(2)  # ⬅️ Arredonda média da nota

# Junta tudo
resultado_final = pd.merge(media_nota, media_por_competencia, on='ALUNO')

# ================================
# Visualização do resultado final
# ================================

st.write("## Desempenho Geral por Aluno")

st.data_editor(
    resultado_final[['ALUNO', 'MÉDIA']],
    column_config={
        "MÉDIA": st.column_config.ProgressColumn(
            "Média das Notas",
            help="Média das notas das redações do aluno",
            format="%f",
            min_value=0,
            max_value=1000,
        ),
    },
    hide_index=True,
)

# Mostrar também as médias por competência
st.write("### Médias por Competência por Aluno")
st.dataframe(resultado_final[['ALUNO'] + competencias + ['COMPETÊNCIA_COM_MAIS_DIFICULDADE']], hide_index=True)

# ========================================
# Análise Geral: Qual competência mais difícil no geral?
# ========================================
st.subheader("📉 Competência com mais dificuldade (geral)")

# Calcular média por competência (geral)
media_competencias_geral = df_filtrado[competencias].mean()
media_competencias_geral = media_competencias_geral.round(2)  # ⬅️ Arredonda geral

competencia_mais_dificil = media_competencias_geral.idxmin()
menor_media = media_competencias_geral.min()

st.write(f"A competência mais difícil no geral é **{competencia_mais_dificil}**, com média **{menor_media:.2f}**")

# Mostrar todas as médias gerais
st.write("### Médias gerais por competência (todos alunos com nota < 900)")
st.dataframe(
    media_competencias_geral.reset_index().rename(columns={'index': 'Competência', 0: 'Média'}),
    hide_index=True
)
