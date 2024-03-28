import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import re
from itertools import chain

#Configurações do Streamlit

st.set_page_config(page_title='Viabilidade ALF Itajaí', 
                   layout="centered", 
                   initial_sidebar_state='collapsed',
                   page_icon=('favicon.png'), 
                   menu_items=None
                   )

logo_image = ('logo.png')

#Tabelas CSV

df_permissao=pd.read_csv("permissao.csv", nrows=2000)
df_risco_uso=pd.read_csv("risco_uso.csv", nrows=2000)
df_zona_col=pd.read_csv("zona_col.csv", nrows=100)

#Página principal do Streamlit

st.image(logo_image, width=150)
st.subheader('Consulta de Viabilidade - Alvará de Funcionamento - Itajaí')
st.markdown('1. Tenha em em mãos o CNPJ da empresa. Selecione todas as informações clicando CTRL + A e cole da no devido campo usando CTRL + V.')
st.markdown('2. Levante a área ocupada pela empresa, englobando as áreas construídas e não construídas destinadas à operação.')
st.markdown('3. Busque a inscrição imobiliária através do seguinte link: https://arcgis.itajai.sc.gov.br/geoitajai/plantacadastral/plantacadastral.html')
st.divider()

col1, col2 = st.columns(2)

with col1:
    #ib_iscricao = st.text_input(
    #"Inscrição Imobiliária (Padrão 000.000.00.0000.0000.000)",
    #key="ib_iscricao"
    #)
  ib_zon = st.selectbox('Insira o zoneamento',
    ('', 'ZMC 1', 'ZMC 2', 'ZMC 3', 'ZMR', 'ZBR', 'ZBN 1', 'ZBN 2',
    'ZCA 1', 'ZCA 2', 'ZCA 3', 'ZBS 1', 'ZBS 2', 'ZBS 3', 'ZBS 4',
    'ZBS 5', 'ZBS 6', 'ZTU 1', 'ZTU 2', 'ZTU 3', 'ZTU 4', 'ZBP',
    'ZRP1', 'ZRP2', 'ZVP', 'ZTP', 'ZDR', 'ZI', 'ZPA', 'ZP', 'ZPL')
    )

with col2:
    ib_area = st.number_input(
    "Área ocupada (m²)",
    key="ib_area"
    )

ib_cnpj = st.text_input(
    "Cole todo o texto do CNPJ - O programa irá selecionar as atividades de forma automática ",
    key="ib_cnpj"
    )

def clear_text():
    st.session_state["ib_cnpj"] = ""
    st.session_state["ib_area"] = 0
    st.session_state["ib_iscricao"] = ""
st.button("Limpar", on_click=clear_text)

st.divider()    


try:
    if ib_cnpj and ib_area and ib_zon != "":
        
        #Lista os cnaes do CNPJ
        cnaes_cnpj = re.findall(r'\d\d.\d\d-\d-\d\d', ib_cnpj)
        cnae_principal_cnpj=cnaes_cnpj[0]
        numero_cnpj = re.findall(r'\d\d.\d\d\d.\d\d\d/\d\d\d\d-\d\d', ib_cnpj)
        texto_cnpj_split = re.sub(' +', ' ',ib_cnpj).split(' ')


        #Filtra a coluna de risco em função da área
        if ib_area <= 150:
            id_risco='ate150''
        if ib_area > 150 and ib_area <= 500:
            id_risco='150a500''
        if ib_area > 500 and ib_area <= 750:
            id_risco='500a750''
        if ib_area > 750:
            id_risco='acima750''
        
        #Filta a coluna de uso em função da área
        if ib_area <= 150:
            id_uso='ate150'
        if ib_area > 150 and ib_area <= 200:
            id_uso='150a200'
        if ib_area > 200 and ib_area <= 500:
            id_uso='200a500'
        if ib_area > 500 and ib_area <= 1000:
            id_uso='500a1000'
        if ib_area > 1000:
            id_uso='acima1000'

        df3=pd.DataFrame(cnaes_cnpj)
        df3.rename(columns={0: 'codigo'}, inplace=True)
        df_merge=pd.merge(df3,df_permissao,left_on='codigo',right_on='codigo', how='inner')
        df_selecionado = df_merge[['codigo', 'denominacao', id_risco, id_uso]]
        
        #Filtra em uma lista única os usos conforme CNPJ e área inserida
        df_uso=df_selecionado[id_uso].unique()
        df_uso=pd.DataFrame(df_uso)
        
        #Printa o resultado da consulta de viabilidade
        st.subheader('Consulta do grau de RISCO e USO da atividade')
        st.markdown('Classificação de grau de risco conforme Decreto 11.985/2020:')
        st.dataframe(df_selecionado, hide_index=True)
        riscos=df_selecionado[id_risco].unique().tolist()    

        if 'Alto' in riscos:
            st.markdown(''':red[Classificado como ALTO RISCO]''')
        if 'Alto' not in riscos:
            if 'Médio' in riscos:
                st.markdown(''':blue[Classificado como MÉDIO RISCO]''')
            if 'Médio' not in riscos:
                st.markdown(''':green[Classificado como BAIXO RISCO]''')

        usos=df_selecionado[id_uso].unique().tolist()
        st.markdown('Os usos desenvolvidos são: '+str(usos))

        #Printa a permissão de uso
        st.subheader('Consulta da PERMISSÃO de uso') 
        df_usoselect = pd.merge(df_zona_col, df_uso, left_on='ZONA',right_on=0, how='inner')
        filtro_colunas = df_usoselect['COL'].tolist()
        filtro_colunas.insert(0,0)
        df_usoselect_filtrado = df_risco_uso.iloc[:, filtro_colunas]
        #st.dataframe(df_usoselect_filtrado, hide_index=True)

        df_usoselect_filtrado = df_usoselect_filtrado.loc[df_usoselect_filtrado['ZONA'] == ib_zon]
        st.dataframe(df_usoselect_filtrado, hide_index=True)

        numero_colunas=df_usoselect_filtrado.shape[1]

        numero_colunas=list(range(numero_colunas))
        del numero_colunas[0]

        
        lista_uso=[]
        i=1
        while i <= len(numero_colunas):
            classificacao_uso=df_usoselect_filtrado.iloc[:,i].unique().tolist()
            lista_uso.append(classificacao_uso)
            i += 1

        lista_uso = list(chain(*lista_uso))
        lista_uso = set(lista_uso)

        if 'Proibido' in lista_uso:
            st.markdown(''':red[Classificado como PROIBIDO]''')
        if 'Proibido' not in lista_uso:
            if 'Permissível' in lista_uso:
                st.markdown(''':blue[Classificado como PERMISSÍVEL]''')
            if 'Permissível' not in lista_uso:
                st.markdown(''':green[Classificado como PERMITIDO]''')

except:
    st.markdown(''':red[Verifique o correto preenchimento de todos os campos.]''')


