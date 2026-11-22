import pygame
#import time
from pygame.locals import *
from .constants import WIDTH, HEIGHT, TITLE, FPS
from OpenGL.GL import *
from OpenGL.GLU import *

class Display():
    def __init__(self):
        pygame.display.init()
        self.screen = None
        self.clock = None
        self.size = (WIDTH, HEIGHT)
        self.is_initialized = False

    def create_display(self):                
        if self.is_initialized and self.screen is not None:
            return self.screen

        self.clock = pygame.time.Clock()  
        #info = pygame.display.Info()    # vetorial dirty sprites        
        #self.size = (info.current_w, info.current_h)
        self.size = (WIDTH, HEIGHT)
               
        pygame.display.set_caption(TITLE)         
        #flags = 0  
        #flags = pygame.NOFRAME #| pygame.OPENGL | pygame.DOUBLEBUF    # vetorial
        #flags = pygame.SCALED | pygame.FULLSCREEN  # pixel art  
        #flags = FULLSCREEN | DOUBLEBUF | OPENGL      
        flags = DOUBLEBUF | OPENGL      # ligar vsync no final com fps limitado ex. 60
        self.screen = pygame.display.set_mode(self.size, flags, display=0, vsync=0)
       
        # Setup 2D orthogonal projection
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)  # (0,0) at top-left
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # Enable Blending for Alpha/Transparency
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.is_initialized = True
        return self.screen

        
    def reload(self):
        pass


    def game_tick(self):
        # Captura o tempo decorrido desde o último quadro em segundos (Delta Time)
        # Limita o FPS máximo para não estressar o processador desnecessariamente
        self.delta_time = min(self.clock.tick_busy_loop(FPS) / 1000.0, 0.033)
        #print(self.delta_time)
        return self.delta_time       

       


display = Display()