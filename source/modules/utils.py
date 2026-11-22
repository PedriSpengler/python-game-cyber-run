import pygame
import os
import sys
from OpenGL.GL import *
from OpenGL.GLU import *

class Utils():
    def __init__(self):                   
        if getattr(sys, 'frozen', False):
            # Executável compilado com cx_Freeze
            self.path = os.path.dirname(sys.executable)
            # ou no main.py
            #os.path.split(os.path.abspath(__file__))[0]
        else:
            # Modo desenvolvimento (.py) - localiza a raiz do projeto de forma confiavel
            proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            self.path = proj_root if os.path.exists(os.path.join(proj_root, "assets")) else os.path.abspath(".")       
  
    def get_full_path(self, resource):
        return os.path.join(self.path, resource)

    def load_font(self, file, size):
        return pygame.font.Font(os.path.join(self.path, file), size)
    
    def load_image(self, file):
        return pygame.image.load(os.path.join(self.path, file)).convert_alpha()


    def cut_sprite(self, map:pygame.Surface, x,y,w,h, to_size:tuple[int,int],
                   frame_list:list[pygame.Surface], texture_list:list[any]):
        img = map.subsurface((x,y,w,h))
        img = pygame.transform.smoothscale(img, to_size)            
        frame_list.append(img)
        texture_list.append(self.surface_to_texture(img))


    def delete_texture(self, texture_id):
        """
        Libera com seguranca um ID de textura alocado no OpenGL.
        """
        if texture_id is not None and texture_id > 0:
            if pygame.display.get_init() and pygame.display.get_surface() is not None:
                try:
                    glDeleteTextures([texture_id])
                except Exception:
                    pass

    def surface_to_texture(self, pygame_surface:pygame.Surface):
        """
        Converte um Pygame Surface em uma textura OpenGL e retorna o ID da textura.
        """
        if not pygame.display.get_init() or pygame.display.get_surface() is None:
            return 0

        # 1. Inverte a imagem verticalmente para alinhar o sistema de coordenadas (Pygame vs OpenGL)
        flipped_surface = pygame.transform.flip(pygame_surface, False, True)
        
        # 2. Converte a superfície para uma string/bytes de pixels no formato RGBA
        texture_data = pygame.image.tobytes(flipped_surface, "RGBA", True)
        width, height = flipped_surface.get_size()
        
        # 3. Gera um ID único para a textura no OpenGL
        texture_id = glGenTextures(1)
        
        # Vincula (ativa) a textura criada para configurá-la
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # Define os filtros de renderização (GL_NEAREST preserva o estilo Pixel Art sem borrar)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        
        # Carrega os bytes da imagem diretamente para a memória da GPU
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data
        )
        
        glBindTexture(GL_TEXTURE_2D, 0)
        return texture_id

    def update_texture(self, texture_id, pygame_surface:pygame.Surface, prev_size:tuple[int,int]=None):
        """
        Atualiza uma textura OpenGL existente com novos dados do Pygame Surface.
        Reutiliza o texture_id existente sem alocar novos IDs na GPU.
        """
        if texture_id is None:
            return self.surface_to_texture(pygame_surface)

        flipped_surface = pygame.transform.flip(pygame_surface, False, True)
        texture_data = pygame.image.tobytes(flipped_surface, "RGBA", True)
        width, height = flipped_surface.get_size()

        glBindTexture(GL_TEXTURE_2D, texture_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        if prev_size and prev_size == (width, height):
            glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        else:
            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RGBA,
                width,
                height,
                0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                texture_data
            )

        glBindTexture(GL_TEXTURE_2D, 0)
        return texture_id


    def draw_textured_quad(self, texture_id, x, y, w, h):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        glColor4f(1, 1, 1, 1) # Reseta a cor global para não aplicar filtros cromáticos na imagem
        
        glBegin(GL_QUADS)
        # Mapeamento: (Coordenada_Textura, Coordenada_Tela)
        glTexCoord2f(0, 0); glVertex2f(x, y)         # Superior Esquerdo
        glTexCoord2f(1, 0); glVertex2f(x + w, y)     # Superior Direito
        glTexCoord2f(1, 1); glVertex2f(x + w, y + h) # Inferior Direito
        glTexCoord2f(0, 1); glVertex2f(x, y + h)     # Inferior Esquerdo
        glEnd()
        
        glDisable(GL_TEXTURE_2D)

    def draw_colored_quad(self, x, y, w, h, color: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.7)):
        """
        Desenha um quadrilátero com cor sólida ou translúcida diretamente via OpenGL.
        Útil para overlays de menus, botões, bordas e fundos de pausa.
        """
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(*color)

        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

        glColor4f(1, 1, 1, 1)
              

utils = Utils()