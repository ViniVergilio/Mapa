import streamlit as st
import pandas as pd
import folium
import googlemaps
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from io import BytesIO
import base64
import requests



# Sua chave da API do Google Maps
GOOGLE_MAPS_API_KEY = "AIzaSyBqV8owCcFNiRcg3vNZp_9Po7PnteL1VqM"

# Criando o cliente do Google Maps
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

# Função para obter o contorno de estados e municípios
def get_boundaries(region_name, region_type="state"):
    try:
        query_type = "state" if region_type == "state" else "city"
        url = f"https://nominatim.openstreetmap.org/search?{query_type}={region_name}&country=Brazil&format=json&polygon_geojson=1"
        headers = {"User-Agent": "Mozilla/5.0"}  # Evitar bloqueios da API
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data and "geojson" in data[0]:
            return data[0]["geojson"]
        else:
            st.warning(f"Não foi possível encontrar os limites para {region_name}")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao buscar limites de {region_name}: {e}")
    return None

# Configuração do título
st.title("📍 Aplicativo de Geolocalização com Google Maps")

# Escolha de Tema
tema = st.radio("Escolha o Tema:", ["Claro", "Escuro"])

# Upload do arquivo Excel
uploaded_file = st.file_uploader("Faça upload do arquivo Excel", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if "Logradouro: - Cidade:" in df.columns and "Logradouro: - Estado:" in df.columns:
        filtro_tipo = st.radio("Buscar por:", ["Logradouro: - Cidade:", "Logradouro: - Estado:"])
        
        if filtro_tipo == "Logradouro: - Cidade:":
            filtro_selecionado = st.multiselect("Selecione as cidades:", df["Logradouro: - Cidade:"].dropna().unique().tolist())
            df_filtrado = df[df["Logradouro: - Cidade:"].isin(filtro_selecionado)]
        else:
            filtro_selecionado = st.multiselect("Selecione os estados:", df["Logradouro: - Estado:"].dropna().unique().tolist())
            df_filtrado = df[df["Logradouro: - Estado:"].isin(filtro_selecionado)]
        
        enderecos = df_filtrado.iloc[:, 15].dropna().unique().tolist()
        
        mapa = folium.Map(location=[-14.2350, -51.9253], zoom_start=4, tiles="cartodbdark_matter" if tema == "Escuro" else "OpenStreetMap")
        marker_cluster = MarkerCluster().add_to(mapa)
        
        for item in filtro_selecionado:
            geojson_data = get_boundaries(item, region_type="state" if filtro_tipo == "Logradouro: - Estado:" else "city")
            if geojson_data:
                folium.GeoJson(
                    geojson_data,
                    name=item,
                    style_function=lambda x: {"fillColor": "blue", "color": "blue", "weight": 2, "fillOpacity": 0.3},
                ).add_to(mapa)
            
        if enderecos:
            for index, row in df_filtrado.iterrows():
                endereco = row.iloc[10]
                info_adicional = f"Cidade: {row['Logradouro: - Cidade:']}<br>Estado: {row['Logradouro: - Estado:']}"
                try:
                    geocode_result = gmaps.geocode(endereco)
                    if geocode_result:
                        location = geocode_result[0]['geometry']['location']
                        popup_text = f"<b>Endereço:</b> {endereco}<br>{info_adicional}"
                        folium.Marker(
                            [location['lat'], location['lng']],
                            popup=popup_text,
                            tooltip=endereco,
                        ).add_to(marker_cluster)
                except Exception as e:
                    st.error(f"Erro ao geocodificar o endereço {endereco}: {e}")
            
        folium.LayerControl().add_to(mapa)
        folium_static(mapa)

        # Opção para download do mapa
        img_data = BytesIO()
        mapa.save(img_data, close_file=False)
        b64 = base64.b64encode(img_data.getvalue()).decode()
        href = f'<a href="data:image/png;base64,{b64}" download="mapa.png">Baixar Mapa</a>'
        st.write("")  # Adiciona espaço antes do botão de download do mapa
        st.markdown(href, unsafe_allow_html=True)
        
        # Exibir tabela com os dados filtrados
        st.subheader("📊 Dados Selecionados")
        st.dataframe(df_filtrado, height=400)  # Permite rolagem caso tenha muitas linhas
        
        
        
        # Opção para exportar dados filtrados
        st.write("")  # Espaço extra antes da exportação de dados
        st.subheader("📂 Exportar Dados Filtrados")
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar dados filtrados",
            data=csv,
            file_name="dados_filtrados.csv",
            mime="text/csv"
        )

        # Cálculo de distância entre dois pontos
        st.subheader("📐 Calcular Distância entre Dois Pontos")
        pontos = st.multiselect("Selecione dois endereços:", enderecos, default=None)
        if len(pontos) == 2:
            try:
                loc1 = gmaps.geocode(pontos[0])[0]['geometry']['location']
                loc2 = gmaps.geocode(pontos[1])[0]['geometry']['location']
                distancia = gmaps.distance_matrix(origins=[(loc1['lat'], loc1['lng'])], destinations=[(loc2['lat'], loc2['lng'])], mode="driving")
                dist_km = distancia["rows"][0]["elements"][0]["distance"]["text"]
                st.success(f"Distância entre os pontos: {dist_km}")
            except Exception as e:
                st.error(f"Erro ao calcular distância: {e}")
    else:
        st.error("O arquivo Excel deve conter as colunas 'Logradouro: - Cidade:' e 'Logradouro: - Estado:' para a busca.")