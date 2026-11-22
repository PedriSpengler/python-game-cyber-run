import pygame
import os

class Sounds():
    def __init__(self):        
        # Pre-initialize mixer with a 512 or 1024 buffer to minimize CPU timing interruptions
        #pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        try:
            pygame.mixer.init()
        except Exception:
            pass

    def load_assets(self): 
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                print("Aviso: Dispositivo de audio nao disponivel.")
                return

        self.nr_channels = pygame.mixer.get_num_channels() 
        self.g_channel = 1  # reserving channel 0 for prioritized sounds

        self.sound_wow = pygame.mixer.Sound(os.path.abspath('assets/sounds/Wow.wav'))
        self.sound_wow.set_volume(0.1)

        self.sound_jump = pygame.mixer.Sound(os.path.abspath('assets/sounds/estalo.mp3'))
        self.sound_jump.set_volume(0.3)

        self.sound_j1 = pygame.mixer.Sound(os.path.abspath('assets/sounds/j1.wav'))
        self.sound_j1.set_volume(0.3)

        self.sound_j2 = pygame.mixer.Sound(os.path.abspath('assets/sounds/j2.wav'))
        self.sound_j2.set_volume(0.3)

        self.sound_j3 = pygame.mixer.Sound(os.path.abspath('assets/sounds/j3.wav'))
        self.sound_j3.set_volume(0.3)

        self.sound_jump_list = [self.sound_j1, self.sound_j2, self.sound_j3]

        self.sound_click = pygame.mixer.Sound(os.path.abspath('assets/sounds/click.mp3'))
        self.sound_click.set_volume(0.3)

        #pygame.mixer.music.load(os.path.abspath('assets/sounds/Smooth Criminal.wav'))
        pygame.mixer.music.load(os.path.abspath('assets/sounds/_LAmourToujours.mp3'))

    def play_music(self):        
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.play(-1, 0.0)
                pygame.mixer.music.set_volume(0.2)
            except Exception:
                pass

    def pause_music(self):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def unpause_music(self):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass

    def stop_music(self):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def set_music_volume(self, volume: float):
        if pygame.mixer.get_init():
            try:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            except Exception:
                pass

    def set_sfx_volume(self, volume: float):
        vol = max(0.0, min(1.0, volume))
        for s in [getattr(self, 'sound_wow', None), getattr(self, 'sound_jump', None),
                  getattr(self, 'sound_j1', None), getattr(self, 'sound_j2', None),
                  getattr(self, 'sound_j3', None), getattr(self, 'sound_click', None)]:
            if s is not None:
                try:
                    s.set_volume(vol)
                except Exception:
                    pass

    def play_click(self):
        if hasattr(self, 'sound_click') and self.sound_click is not None:
            self.play_sound(self.sound_click)

    def play_sound(self,
                    sound:pygame.mixer.Sound,
                    channel:int=-1):
        if not pygame.mixer.get_init() or sound is None:
            return
        g_channel = self.g_channel
        if channel == -1:
            ch = pygame.mixer.Channel(g_channel)
            g_channel += 1  # move to next channel
            if g_channel == self.nr_channels:
                g_channel = 1
        else:
            ch = pygame.mixer.Channel(channel)        
        ch.play(sound)
        self.g_channel = g_channel

sounds = Sounds()