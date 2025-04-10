import streamlit as st
import os
import tempfile
import time
import logging
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image

# Importar módulos personalizados
from utils.article_extractor import extraer_contenido_articulo
from utils.image_processor import descargar_imagenes, descargar_fuente, procesar_imagen_subida
from utils.video_creator import crear_video
from utils.database import init_database, guardar_proyecto

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la página
st.set_page_config(
    page_title="Creador de Videos SEO",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Función para mostrar imágenes con un tamaño específico
def mostrar_imagen(imagen_path, width=200):
    try:
        img = Image.open(imagen_path)
        # Redimensionar para mostrar como thumbnail
        img.thumbnail((width, width * img.height // img.width))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        st.image(buf, width=width)
    except Exception as e:
        st.error(f"Error al mostrar la imagen: {str(e)}")

# Función para generar enlace de descarga
def get_binary_file_downloader_html(bin_file, file_label='Archivo'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:video/mp4;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

# Inicializar la base de datos
try:
    init_database()
    logging.info("Base de datos inicializada correctamente")
except Exception as e:
    logging.error(f"Error al inicializar la base de datos: {str(e)}")

# Inicializar el estado de la sesión si no existe
if 'paso_actual' not in st.session_state:
    st.session_state.paso_actual = 1
if 'textos' not in st.session_state:
    st.session_state.textos = []
if 'imagenes' not in st.session_state:
    st.session_state.imagenes = []
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'fuente_path' not in st.session_state:
    st.session_state.fuente_path = None
if 'imagenes_con_texto' not in st.session_state:
    st.session_state.imagenes_con_texto = []
if 'url_articulo' not in st.session_state:
    st.session_state.url_articulo = None
if 'proyecto_guardado' not in st.session_state:
    st.session_state.proyecto_guardado = False

# Sidebar con instrucciones
with st.sidebar:
    st.title("🎬 Creador de Videos SEO")
    st.write("Crea videos SEO optimizados a partir de artículos web.")
    
    st.subheader("Instrucciones:")
    st.write("1. Ingresa la URL del artículo")
    st.write("2. Edita los textos extraídos")
    st.write("3. Selecciona las imágenes a usar")
    st.write("4. Genera y descarga tu video")
    
    # Información sobre los pasos
    st.subheader("Proceso:")
    paso1_status = "✅" if st.session_state.paso_actual > 1 else "🔵" if st.session_state.paso_actual == 1 else "⚪️"
    paso2_status = "✅" if st.session_state.paso_actual > 2 else "🔵" if st.session_state.paso_actual == 2 else "⚪️"
    paso3_status = "✅" if st.session_state.paso_actual > 3 else "🔵" if st.session_state.paso_actual == 3 else "⚪️"
    paso4_status = "✅" if st.session_state.paso_actual > 4 else "🔵" if st.session_state.paso_actual == 4 else "⚪️"
    
    st.write(f"{paso1_status} Paso 1: Extraer contenido")
    st.write(f"{paso2_status} Paso 2: Editar textos")
    st.write(f"{paso3_status} Paso 3: Seleccionar imágenes")
    st.write(f"{paso4_status} Paso 4: Crear video")
    
    # Agregar enlace al historial de proyectos
    st.markdown("---")
    st.subheader("Proyectos:")
    if st.sidebar.button("📂 Ver historial de proyectos"):
        st.switch_page("pages/historial.py")

# Título principal
st.title("🎬 Creador de Videos SEO")

# PASO 1: Extraer contenido del artículo
if st.session_state.paso_actual == 1:
    st.header("Paso 1: Extraer contenido del artículo")
    
    # Descargar la fuente en segundo plano
    if not st.session_state.fuente_path:
        with st.spinner("Preparando recursos..."):
            st.session_state.fuente_path = descargar_fuente()
    
    url = st.text_input("Ingresa la URL del artículo:", 
                         placeholder="https://www.ejemplo.com/articulo")
    
    if st.button("Extraer contenido"):
        if url:
            try:
                with st.spinner("Extrayendo contenido del artículo..."):
                    textos, imagenes_urls = extraer_contenido_articulo(url)
                    
                    if not textos:
                        st.error("No se pudo extraer texto del artículo.")
                    else:
                        st.session_state.textos = textos
                        st.session_state.url_articulo = url
                        
                        progress_bar = st.progress(0)
                        st.info(f"Descargando {len(imagenes_urls)} imágenes...")
                        
                        imagenes_paths = descargar_imagenes(imagenes_urls, progress_bar)
                        
                        if not imagenes_paths:
                            st.warning("No se pudieron descargar imágenes del artículo.")
                        
                        st.session_state.imagenes = imagenes_paths
                        st.session_state.paso_actual = 2
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error al extraer contenido: {str(e)}")
        else:
            st.warning("Por favor, ingresa una URL válida.")

# PASO 2: Editar textos
elif st.session_state.paso_actual == 2:
    st.header("Paso 2: Editar textos para el video")
    
    if not st.session_state.textos:
        st.error("No hay textos para editar. Vuelve al paso anterior.")
        if st.button("Volver al paso 1"):
            st.session_state.paso_actual = 1
            st.rerun()
    else:
        st.write("Edita los textos que aparecerán en el video y selecciona cuáles incluir:")
        
        textos_editados = []
        textos_seleccionados = []
        
        for i, texto in enumerate(st.session_state.textos):
            col1, col2 = st.columns([10, 1])
            with col1:
                texto_editado = st.text_area(f"Texto {i+1}", 
                                           value=texto,
                                           height=100, 
                                           key=f"texto_{i}")
                textos_editados.append(texto_editado)
            
            with col2:
                incluir = st.checkbox("Incluir", value=True, key=f"incluir_{i}")
                textos_seleccionados.append(incluir)
        
        # Botones para navegar
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Volver"):
                st.session_state.paso_actual = 1
                st.session_state.textos = []
                st.session_state.imagenes = []
                st.rerun()
                
        with col2:
            if st.button("Continuar ➡️"):
                textos_finales = [texto for texto, seleccionado in zip(textos_editados, textos_seleccionados) if seleccionado]
                
                if not textos_finales:
                    st.error("Debes seleccionar al menos un texto para el video.")
                else:
                    st.session_state.textos = textos_finales
                    st.session_state.paso_actual = 3
                    st.rerun()

# PASO 3: Seleccionar imágenes
elif st.session_state.paso_actual == 3:
    st.header("Paso 3: Seleccionar imágenes")
    
    # Mostrar imágenes descargadas
    imagenes_seleccionadas = []
    
    if not st.session_state.imagenes:
        st.warning("No hay imágenes disponibles del artículo.")
    else:
        st.subheader("Imágenes del artículo")
        st.write("Selecciona las imágenes que deseas incluir en el video:")
        
        # Mostrar imágenes en una cuadrícula con checkboxes
        cols = 4
        
        for i in range(0, len(st.session_state.imagenes), cols):
            row = st.columns(cols)
            for j in range(cols):
                idx = i + j
                if idx < len(st.session_state.imagenes):
                    with row[j]:
                        mostrar_imagen(st.session_state.imagenes[idx])
                        seleccionada = st.checkbox("Seleccionar", value=True, key=f"img_{idx}")
                        imagenes_seleccionadas.append(seleccionada)
    
    # Opción para subir imágenes adicionales
    st.subheader("Subir imágenes adicionales")
    archivos_subidos = st.file_uploader("Selecciona imágenes para subir", 
                                        type=["jpg", "jpeg", "png"], 
                                        accept_multiple_files=True)
    
    imagenes_subidas = []
    if archivos_subidos:
        for archivo in archivos_subidos:
            st.write(f"Procesando imagen: {archivo.name}")
            imagen_path = procesar_imagen_subida(archivo)
            if imagen_path:
                imagenes_subidas.append(imagen_path)
                st.session_state.imagenes.append(imagen_path)
                # Actualizar imagenes_seleccionadas con True para las nuevas imágenes
                imagenes_seleccionadas.append(True)
    
    # Botones para navegar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅️ Volver"):
            st.session_state.paso_actual = 2
            st.rerun()
            
    with col2:
        if st.button("Continuar ➡️"):
            # Filtrar imágenes seleccionadas
            imagenes_finales = [img for img, sel in zip(st.session_state.imagenes, imagenes_seleccionadas) if sel]
            
            if not imagenes_finales:
                st.error("Debes seleccionar al menos una imagen para el video.")
            else:
                st.session_state.imagenes = imagenes_finales
                st.session_state.paso_actual = 4
                st.rerun()

# PASO 4: Crear video
elif st.session_state.paso_actual == 4:
    st.header("Paso 4: Crear video")
    
    if not st.session_state.textos or not st.session_state.imagenes:
        st.error("Faltan textos o imágenes para crear el video.")
        if st.button("Volver al inicio"):
            st.session_state.paso_actual = 1
            st.rerun()
    else:
        st.write(f"✅ {len(st.session_state.textos)} textos seleccionados")
        st.write(f"✅ {len(st.session_state.imagenes)} imágenes seleccionadas")
        
        if not st.session_state.video_path:
            if st.button("Generar Video"):
                try:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    def update_progress(progress):
                        progress_bar.progress(progress)
                        if progress < 0.25:
                            status_text.text("Preparando imágenes...")
                        elif progress < 0.5:
                            status_text.text("Añadiendo textos a las imágenes...")
                        elif progress < 0.75:
                            status_text.text("Creando secuencias de video...")
                        else:
                            status_text.text("Finalizando el video...")
                    
                    with st.spinner("Creando video..."):
                        titulo = st.session_state.textos[0]
                        imagenes_con_texto, video_path = crear_video(
                            st.session_state.textos,
                            st.session_state.imagenes,
                            titulo,
                            fuente_path=st.session_state.fuente_path,
                            progress_callback=update_progress
                        )
                        
                        st.session_state.imagenes_con_texto = imagenes_con_texto
                        
                        if video_path:
                            st.session_state.video_path = video_path
                            progress_bar.progress(1.0)
                            status_text.text("¡Video creado con éxito!")
                        else:
                            progress_bar.progress(1.0)
                            status_text.text("No se pudo crear el video, pero se generaron las imágenes con texto.")
                            st.warning("No se pudo crear el video, pero se han generado las imágenes con texto que puedes descargar. Si ves este mensaje después de instalar moviepy, es posible que falte FFmpeg u otras dependencias.")
                        
                        st.rerun()
                        
                except Exception as e:
                    error_message = str(e)
                    logging.error(f"Error al crear el video: {error_message}")
                    
                    # Mensajes más informativos según el tipo de error
                    if "ffmpeg" in error_message.lower():
                        st.error(f"Error con FFmpeg: {error_message}. Intenta ejecutar la aplicación en un entorno donde FFmpeg esté instalado correctamente.")
                    elif "imageio" in error_message.lower():
                        st.error(f"Error con imageio: {error_message}. Asegúrate de que imageio y imageio-ffmpeg estén instalados correctamente.")
                    elif "moviepy" in error_message.lower():
                        st.error(f"Error con moviepy: {error_message}. Asegúrate de que moviepy esté instalado correctamente.")
                    else:
                        st.error(f"Error al crear el video: {error_message}")
        else:
            if st.session_state.video_path:
                st.success("¡Video creado con éxito!")
                
                # Guardar el proyecto en la base de datos si aún no se ha guardado
                if not st.session_state.proyecto_guardado:
                    try:
                        # El título es el primer texto seleccionado
                        titulo = st.session_state.textos[0]
                        proyecto_id = guardar_proyecto(
                            titulo, 
                            url_articulo=st.session_state.url_articulo,
                            video_path=st.session_state.video_path,
                            textos=st.session_state.textos,
                            imagenes_originales=st.session_state.imagenes,
                            imagenes_con_texto=st.session_state.imagenes_con_texto
                        )
                        st.session_state.proyecto_guardado = True
                        st.success(f"Proyecto guardado en la base de datos (ID: {proyecto_id})")
                    except Exception as e:
                        st.error(f"Error al guardar el proyecto en la base de datos: {str(e)}")
                
                # Mostrar opciones de descarga
                st.subheader("Descargar video")
                video_name = os.path.basename(st.session_state.video_path)
                st.markdown(get_binary_file_downloader_html(st.session_state.video_path, f"Descargar {video_name}"), unsafe_allow_html=True)
                
                # Visualización del video
                st.subheader("Previsualización")
                st.video(st.session_state.video_path)
                
                # Enlace al historial de proyectos
                st.markdown("---")
                st.info("Puedes ver todos tus proyectos en el historial.")
                if st.button("Ver historial de proyectos"):
                    st.switch_page("pages/historial.py")
            else:
                st.warning("No se pudo crear el video, pero se generaron imágenes con texto que puedes descargar individualmente. Las imágenes con texto son útiles para redes sociales y otras publicaciones.")
                st.info("💡 Consejo: Aunque no se pudo crear el video, las imágenes con texto generadas son perfectas para compartir en redes sociales, blogs o presentaciones.")
                
                # Mostrar las imágenes generadas
                if 'imagenes_con_texto' in st.session_state and st.session_state.imagenes_con_texto:
                    st.subheader("Imágenes generadas con texto")
                    
                    # Mostrar imágenes en una cuadrícula
                    cols = 3
                    for i in range(0, len(st.session_state.imagenes_con_texto), cols):
                        row = st.columns(cols)
                        for j in range(cols):
                            idx = i + j
                            if idx < len(st.session_state.imagenes_con_texto):
                                with row[j]:
                                    mostrar_imagen(st.session_state.imagenes_con_texto[idx], width=300)
                                    img_name = os.path.basename(st.session_state.imagenes_con_texto[idx])
                                    st.markdown(get_binary_file_downloader_html(
                                        st.session_state.imagenes_con_texto[idx], 
                                        f"Descargar imagen {idx+1}"
                                    ), unsafe_allow_html=True)
            
            # Opciones para volver a empezar
            if st.button("Crear otro video"):
                # Reiniciar el estado
                st.session_state.paso_actual = 1
                st.session_state.textos = []
                st.session_state.imagenes = []
                st.session_state.video_path = None
                st.session_state.url_articulo = None
                st.session_state.proyecto_guardado = False
                if 'imagenes_con_texto' in st.session_state:
                    del st.session_state.imagenes_con_texto
                st.rerun()

# Agregar un pie de página
st.markdown("---")
st.markdown("📊 **Creador de Videos SEO** · Creado con Streamlit")
