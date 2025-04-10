import os
import sys
import logging
from pathlib import Path
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def crear_imagen_test(texto, idx, size=(800, 600), color='white'):
    """Crea una imagen de prueba con texto"""
    img = Image.new('RGB', size, color=color)
    draw = ImageDraw.Draw(img)
    
    # Dibujar texto
    font_size = 40
    try:
        font = ImageFont.truetype("Arial", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Posición del texto (centrado)
    text_width = draw.textlength(texto, font=font)
    position = ((size[0] - text_width) // 2, (size[1] // 2) - font_size)
    
    # Dibujar el texto
    draw.text(position, texto, fill='black', font=font)
    
    # Guardar la imagen
    temp_dir = Path(tempfile.mkdtemp())
    img_path = temp_dir / f"test_image_{idx}.png"
    img.save(img_path)
    
    logging.info(f"Imagen creada: {img_path}")
    return str(img_path)

def test_moviepy():
    """Prueba la funcionalidad básica de moviepy"""
    try:
        logging.info("Importando moviepy...")
        
        # Intentar diferentes formas de importar moviepy
        try:
            # Forma moderna
            from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
            logging.info("Importación exitosa de ImageSequenceClip")
            
            # Crear algunas imágenes de prueba
            imagenes = [
                crear_imagen_test("Test Imagen 1", 1),
                crear_imagen_test("Test Imagen 2", 2),
                crear_imagen_test("Test Imagen 3", 3)
            ]
            
            # Crear un video
            logging.info("Creando video con ImageSequenceClip...")
            clip = ImageSequenceClip(imagenes, durations=[3, 3, 3])
            
            # Guardar el video
            output_path = Path(tempfile.mkdtemp()) / "test_video.mp4"
            logging.info(f"Guardando video en {output_path}...")
            clip.write_videofile(str(output_path), fps=24)
            
            return f"Video creado exitosamente en {output_path}"
            
        except ImportError as e:
            logging.error(f"Error al importar ImageSequenceClip: {str(e)}")
            
            # Intentar con el método clásico
            logging.info("Intentando importación clásica...")
            from moviepy.editor import ImageClip, concatenate_videoclips
            
            # Crear algunas imágenes de prueba
            imagenes = [
                crear_imagen_test("Test Imagen 1", 1),
                crear_imagen_test("Test Imagen 2", 2),
                crear_imagen_test("Test Imagen 3", 3)
            ]
            
            # Crear clips
            clips = [ImageClip(img).set_duration(3) for img in imagenes]
            
            # Concatenar clips
            final_clip = concatenate_videoclips(clips, method="compose")
            
            # Guardar el video
            output_path = Path(tempfile.mkdtemp()) / "test_video.mp4"
            logging.info(f"Guardando video en {output_path}...")
            final_clip.write_videofile(str(output_path), fps=24)
            
            return f"Video creado exitosamente (método clásico) en {output_path}"
    
    except Exception as e:
        logging.error(f"Error general: {str(e)}")
        return f"Error al crear video: {str(e)}"

if __name__ == "__main__":
    resultado = test_moviepy()
    print(resultado)