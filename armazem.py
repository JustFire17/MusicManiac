#!/usr/bin/python3
import math
import numpy as np
import pygame
import OpenGL.GL as GL
import random
import os
import wave
import struct
import numpy as np
from copy import deepcopy
import sys

from core.base import Base
from core_ext.camera import Camera
from core_ext.mesh import Mesh
from core_ext.renderer import Renderer
from core_ext.scene import Scene
from core_ext.texture import Texture
from extras.movement_rig import MovementRig
from geometry.box import TexturedBoxGeometry, BoxGeometry
from geometry.plane import TexturedPlaneGeometry
from geometry.rectangle import RectangleGeometry
from material.basic import BasicMaterial
from material.lambert import LambertMaterial
from light.ambient import AmbientLight
from light.directional import DirectionalLight
from material.texture import TextureMaterial
from geometry.tuba2 import TubaGeometry2
from core.obj_reader2 import my_obj_reader2
from core.matrix import Matrix
from light.point import PointLight
from material.phong import PhongMaterial
from geometry.colosseum import ColosseumGeometry
from core.obj_reader import my_obj_reader
from geometry.tuba2 import TubaGeometry2
from core.obj_reader2 import my_obj_reader2
from core.matrix import Matrix
from light.point import PointLight
from material.phong import PhongMaterial
from geometry.colosseum import ColosseumGeometry
from core.obj_reader import my_obj_reader
from geometry.rectangle import RectangleGeometry
from geometry.box import BoxGeometry

class ArenaShooterCollision(Base):
    """
    Versão simplificada do Arena Shooter com detecção de colisão
    Controles:ad
    - WASD: Mover
    - Mouse: Controlar câmera
    - Mouse Click: Atirar
    """
    def __init__(self):
        # Inicializar o pygame primeiro
        pygame.init()
        pygame.mixer.init()

        # Agora podemos obter a resolução do monitor
        info = pygame.display.Info()
        screen_size = [info.current_w, info.current_h]
        
        super().__init__(screen_size=screen_size)

        # No macOS, usar uma janela borderless que ocupa toda a tela
        if sys.platform == 'darwin':  # macOS
            self._screen = pygame.display.set_mode(screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.NOFRAME)
            # Centralizar a janela
            os.environ['SDL_VIDEO_CENTERED'] = '1'
        else:
            self._screen = pygame.display.set_mode(screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN)
        
        print('Tamanho real da janela:', self._screen.get_size())
        
        # Adicionar contador de kills
        self.kill_count = 0
        
        # Adicionar contador de ocarinas
        self.ocarina_count = 0
        
        # Adicionar sistema de vida
        self.stack_max_health = 100
        self.stack_current_health = 100
        self.last_damage_time = 0
        self.damage_cooldown = 1.0  # Tempo em segundos entre danos
        
        # Adicionar variável para razão do fim do jogo
        self.game_over_reason = None  # "time" ou "death"
        
        # Variáveis para animação dos instrumentos
        self.animation_time = 0
        self.tuba_initial_position = [12.09, 1.00, -5.69]  # Nova posição inicial da tuba
        self.guitar_initial_position = [-13.21, 0.3, -5.56]  # Nova posição inicial da guitarra
        self.rotation_speed = 0.5  # Velocidade de rotação
        self.float_amplitude = 0.2  # Amplitude do movimento de flutuação
        self.float_speed = 2.0  # Velocidade do movimento de flutuação
        
        # Adicionar variável de estado para apanhar a guitarra
        self.has_guitar = True  # Começar com a guitarra
        self.guitar_pickup_time = None
        self.guitar_drop_time = None
        
        # Lista para armazenar personagens que estão esperando respawn
        self.respawning_characters = []  # Lista de tuplas (character, initial_position, respawn_time)
        self.respawn_delay = 3.0  # Tempo em segundos para respawn
        
        # Carregar o som base do trombone
        self.base_sound = pygame.mixer.Sound('sounds/trombone-C-note.wav')
        
        # Carregar os sons da ocarina
        self.ocarina_sound = pygame.mixer.Sound('sounds/ocarina_sound.mp3')
        self.ocarina_break = pygame.mixer.Sound('sounds/ocarina_break.mp3')
        # Ajustar volume dos sons da ocarina
        self.ocarina_sound.set_volume(0.3)
        self.ocarina_break.set_volume(0.3)
        
        # Carregar os sons da guitarra
        self.guitar_sounds = {}
        guitar_sound_files = [
            '97217__mikey_eff__mfmetal_short_pwrchrd_astr_a.wav',
            '97218__mikey_eff__mfmetal_short_pwrchrd_astr_b.wav',
            '97220__mikey_eff__mfmetal_short_pwrchrd_astr_c.wav',
            '97222__mikey_eff__mfmetal_short_pwrchrd_astr_d.wav',
            '97223__mikey_eff__mfmetal_short_pwrchrd_astr_e.wav',
            '97225__mikey_eff__mfmetal_short_pwrchrd_astr_f.wav',
            '97227__mikey_eff__mfmetal_short_pwrchrd_astr_g.wav'
        ]
        
        for sound_file in guitar_sound_files:
            sound_name = sound_file.split('_')[-1].split('.')[0]  # Extrair a nota (a, b, c, etc)
            self.guitar_sounds[sound_name] = pygame.mixer.Sound(f'sounds/{sound_file}')
            self.guitar_sounds[sound_name].set_volume(0.3)  # Ajustar volume se necessário
        
        # Criar diferentes notas a partir do som base
        self.notes = {}
        note_frequencies = {
            'do': 0.5,      # Frequência original dividida por 2
            're': 0.56125,  # 9/8 dividido por 2
            'mi': 0.625,    # 5/4 dividido por 2
            'fa': 0.66665,  # 4/3 dividido por 2
            'sol': 0.75,    # 3/2 dividido por 2
            'la': 0.83335,  # 5/3 dividido por 2
            'si': 0.9375    # 15/8 dividido por 2
        }
        
        # Carregar o arquivo WAV original
        with wave.open('sounds/trombone-C-note.wav', 'rb') as wav_file:
            # Obter parâmetros do arquivo
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Ler os dados do áudio
            frames = wav_file.readframes(n_frames)
            samples = struct.unpack(f'<{n_frames * n_channels}h', frames)
            
            # Converter para array numpy
            samples = np.array(samples, dtype=np.int16)
            
            # Criar cada nota
            for note_name, freq_ratio in note_frequencies.items():
                # Calcular novo número de frames
                new_n_frames = int(n_frames / freq_ratio)
                
                # Criar array para os novos samples
                new_samples = np.zeros(new_n_frames * n_channels, dtype=np.int16)
                
                # Interpolar os samples para a nova frequência
                for i in range(new_n_frames):
                    old_pos = i * freq_ratio
                    old_index = int(old_pos)
                    if old_index + 1 < len(samples):
                        # Interpolação linear
                        frac = old_pos - old_index
                        new_samples[i] = int(samples[old_index] * (1 - frac) + samples[old_index + 1] * frac)
                
                # Converter de volta para bytes
                new_frames = struct.pack(f'<{len(new_samples)}h', *new_samples)
                
                # Criar novo arquivo WAV temporário
                temp_filename = f'sounds/temp_{note_name}.wav'
                with wave.open(temp_filename, 'wb') as new_wav:
                    new_wav.setnchannels(n_channels)
                    new_wav.setsampwidth(sample_width)
                    new_wav.setframerate(frame_rate)
                    new_wav.writeframes(new_frames)
                
                # Carregar o som modificado
                self.notes[note_name] = pygame.mixer.Sound(temp_filename)
                self.notes[note_name].set_volume(0.3)
                
                # Remover arquivo temporário
                os.remove(temp_filename)
        
        # Forçar modo não redimensionável
        info = pygame.display.Info()
        screen_size = [info.current_w, info.current_h]
        self._screen = pygame.display.set_mode(screen_size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN)
        print('Tamanho real da janela:', self._screen.get_size())
        
        # Timer
        self.total_time = 200  # 2 minutos em segundos
        self.remaining_time = self.total_time
        self.game_over = False
        
        # Configuração do pulo
        self.is_jumping = False
        self.jump_velocity = 0
        self.jump_height = 2.0  # Altura máxima do pulo
        self.initial_jump_velocity = 8.0  # Velocidade inicial do pulo
        self.gravity = 18.0  # Força da gravidade
        self.initial_height = 1.0  # Altura inicial do jogador
        self.jump_buffered = False  # Para jump buffer
        
        # Configuração do mouse
        pygame.mouse.set_visible(False)  # Esconder o cursor
        pygame.event.set_grab(True)      # Travar o mouse na janela
        self.mouse_sensitivity = 0.2     # Sensibilidade do mouse
        self.vertical_angle = 0          # Ângulo vertical atual da câmera
        self.max_vertical_angle = 85     # Limite máximo de rotação vertical (em graus)
        
        # Lista para armazenar as balas ativas
        self.bullets = []
        self.bullet_speed = 10  # Velocidade das balas
        self.last_shot_time = 0
        self.shot_cooldown = 0.1  # Tempo mínimo entre tiros (em segundos)
        self.guitar_shot_cooldown = 1.0  # Tempo mínimo entre tiros da guitarra (em segundos)
        self.tuba_shot_cooldown = 2.0  # Tempo mínimo entre tiros da tuba (2 segundos)
        self.last_guitar_shot_time = 0  # Último tempo que a guitarra disparou
        self.last_tuba_shot_time = 0  # Último tempo que a tuba disparou
        
        # Carregar o modelo da bala uma vez
        self.bullet_positions, self.bullet_uvs = my_obj_reader2("geometry/bulletdouble2.obj")
        self.bullet_geometry = TubaGeometry2(1, 1, 1, self.bullet_positions, self.bullet_uvs)
        self.bullet_texture = Texture(file_name="images/tuba6.png")
        
        # Carregar modelo da nota musical para os tiros da tuba
        positions, uvs = my_obj_reader2("geometry/bulletdouble2.obj")
        self.note_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        self.note_texture = Texture(file_name="images/note_texture.png")
        
        # Configuração básica
        self.scene = Scene()
        self.renderer = Renderer()
        # Ajustar a proporção da câmera para o tamanho da tela
        aspect_ratio = screen_size[0] / screen_size[1]
        self.camera = Camera(aspect_ratio=aspect_ratio)
        # Aumentar a velocidade de movimento e rotação
        self.rig = MovementRig(units_per_second=3.5, degrees_per_second=90)
        self.rig.add(self.camera)
        self.rig.set_position([0.54, self.initial_height, -18.90])  # Nova posição inicial do jogador (Y igual ao chão)
        
        # Configurar controles
        self.rig.KEY_MOVE_FORWARDS = "w"
        self.rig.KEY_MOVE_BACKWARDS = "s"
        self.rig.KEY_MOVE_LEFT = "a"      
        self.rig.KEY_MOVE_RIGHT = "d"
        self.rig.KEY_TURN_LEFT = ""
        self.rig.KEY_TURN_RIGHT = ""
        self.rig.KEY_LOOK_UP = ""
        self.rig.KEY_LOOK_DOWN = ""
        # self.rig.KEY_MOVE_UP = "space"    # REMOVIDO: impedir que o espaço faça o jogador subir livremente
        self.rig.KEY_MOVE_DOWN = ""
        
        self.scene.add(self.rig)

        # Configuração do HUD
        self.setup_hud()
        
        # Configuração das luzes
        ambient_light = AmbientLight(color=[0.7, 0.7, 0.7])  # Luz ambiente mais clara
        self.scene.add(ambient_light)
        
        directional_light = DirectionalLight(color=[1.0, 1.0, 1.0], direction=[-1, -1, -2])  # Luz direcional branca
        self.scene.add(directional_light)

        # Luz neon azul para a tuba - na nova altura
        self.tuba_light = PointLight(
            color=[0.0, 2.0, 8.0],
            position=[0, 3, 0],  # Aumentei a altura de 1 para 3
            attenuation=[1.0, 0.05, 0.005]
        )
        self.scene.add(self.tuba_light)

        # Carregar textura do chão
        self.floor_texture = Texture(file_name="images/floorstone.jpg")
        self.floor_texture.set_properties({
            "magFilter": "GL_LINEAR",
            "minFilter": "GL_LINEAR_MIPMAP_LINEAR",
            "wrap": "GL_REPEAT"
        })

        # Material do chão
        floor_material = LambertMaterial(
            texture=self.floor_texture,
            property_dict={"baseColor": [1, 1, 1]},
            number_of_light_sources=3  # Ambient + Directional + Tuba light
        )

        # Material da parede
        wall_material = LambertMaterial(
            property_dict={"baseColor": [0.8, 0.3, 0.3]},
            number_of_light_sources=3  # Ambient + Directional + Tuba light
        )

        # Criar o ambiente
        self.create_environment(floor_material, wall_material)
        
        # Configuração da parede para colisão
        # self.wall_position = np.array([0, 0, -10])  # Centro da parede
        # self.wall_dimensions = np.array([10, 3.5, 0.7])  # Largura, altura, espessura

        # Adicionar variável de estado para pausa
        self.paused = False

        # Adicionar variável de estado para apanhar a tuba
        self.has_tuba = False

        # Adicionar variável de estado para o tempo de apanhar a tuba
        self.tuba_pickup_time = None
        # Adicionar variável de cooldown para apanhar a tuba após largar
        self.tuba_drop_time = None

        self.test_quadrants = False  # Novo modo de teste
        self.last_t_state = False    # Para evitar múltiplos triggers
        self.clicked_quadrant = None

        # Lista para armazenar as ocarinas dropadas
        self.dropped_ocarinas = []
        
        # Carregar geometria e textura da ocarina
        positions, uvs = my_obj_reader2("geometry/ocarina.obj")
        self.ocarina_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        self.ocarina_texture = Texture(file_name="images/ocarina_textura.png")
        
        # Material da ocarina
        self.ocarina_material = PhongMaterial(
            texture=self.ocarina_texture,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],
                "specularStrength": 2.0,
                "shininess": 32.0
            },
            number_of_light_sources=3
        )

        # Variável para controlar se o jogador tem uma ocarina
        self.has_ocarina = False
        
        # Variável para controlar o cooldown da granada
        self.last_grenade_time = 0
        self.grenade_cooldown = 3.0  # 3 segundos entre granadas
        
        # Lista para armazenar granadas ativas
        self.active_grenades = []
        
        # Lista para armazenar notas musicais da explosão
        self.explosion_notes = []

        # Adicionar variável para tempo de aparecimento da tuba
        self.tuba_appear_time = 60.0  # Tempo em segundos (1 minuto)
        self.tuba_has_appeared = False
        self.tuba_message_time = None
        self.tuba_message_duration = 5.0  # Duração da mensagem em segundos

        # Adicionar o modelo do French Horn ao centro do mapa
        positions, uvs = my_obj_reader2("french-horn/source/frenchhorn obj/frenchhorn OBJ 2/french horn 2.obj")
        french_horn_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        french_horn_diffuse = Texture(file_name="french-horn/source/frenchhorn obj/frenchhorn OBJ 2/dif map.jpg")
        french_horn_material = PhongMaterial(
            texture=french_horn_diffuse,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],
                "specularStrength": 1.0,
                "shininess": 16.0
            },
            number_of_light_sources=3
        )
        self.french_horn_mesh = Mesh(french_horn_geometry, french_horn_material)
        self.french_horn_mesh.set_position([0, self.initial_height, 0])  # Centro do mapa
        self.french_horn_mesh.scale(0.2)
        self.french_horn_mesh.rotate_x(-math.pi/2)  # Orientação correta
        self.scene.add(self.french_horn_mesh)

        # Organizar instrumentos no centro: guitarra deitada no centro, outros ao redor
        # Remover instrumentos antigos da pilha se existirem
        if hasattr(self, 'instrument_stack'):
            for mesh in self.instrument_stack:
                self.scene.remove(mesh)
        self.instrument_stack = []
        
        # Guitarra deitada no centro, apontando para cima
        positions, uvs = my_obj_reader2("geometry/ElectricGuitar.obj")
        guitar_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        guitar_texture = Texture(file_name="images/ElectricGuitar.jpg")
        guitar_material = PhongMaterial(
            texture=guitar_texture,
            property_dict={"baseColor": [1.0, 1.0, 1.0], "specularStrength": 2.0, "shininess": 32.0},
            number_of_light_sources=3
        )
        guitar_mesh = Mesh(guitar_geometry, guitar_material)
        guitar_mesh.scale(0.45)
        guitar_mesh.set_position([0, 0.15, 0])
        guitar_mesh.rotate_x(math.radians(-90))  # Deitada
        guitar_mesh.rotate_z(math.radians(0))    # Apontando para cima
        self.scene.add(guitar_mesh)
        self.instrument_stack.append(guitar_mesh)
        
        # Posições ao redor da guitarra (círculo de raio 0.7)
        radius = 0.7
        angle_offset = math.radians(30)
        center_y = 0.25
        
        # Tuba
        positions, uvs = my_obj_reader2("geometry/tubabuedafixecomUVsemface.obj")
        tuba_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        tuba_texture = Texture(file_name="images/tuba6.png")
        tuba_material = PhongMaterial(
            texture=tuba_texture,
            property_dict={"baseColor": [1.0, 1.0, 1.0], "specularStrength": 2.0, "shininess": 32.0},
            number_of_light_sources=3
        )
        tuba_mesh = Mesh(tuba_geometry, tuba_material)
        tuba_mesh.scale(0.22)
        tuba_mesh.set_position([
            radius * math.cos(angle_offset),
            center_y,
            radius * math.sin(angle_offset)
        ])
        tuba_mesh.rotate_y(math.radians(60))
        self.scene.add(tuba_mesh)
        self.instrument_stack.append(tuba_mesh)
        
        # Ocarina
        positions, uvs = my_obj_reader2("geometry/ocarina.obj")
        ocarina_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        ocarina_texture = Texture(file_name="images/ocarina_textura.png")
        ocarina_material = PhongMaterial(
            texture=ocarina_texture,
            property_dict={"baseColor": [1.0, 1.0, 1.0], "specularStrength": 2.0, "shininess": 32.0},
            number_of_light_sources=3
        )
        ocarina_mesh = Mesh(ocarina_geometry, ocarina_material)
        ocarina_mesh.scale(0.16)
        ocarina_mesh.set_position([
            radius * math.cos(angle_offset + math.radians(120)),
            center_y,
            radius * math.sin(angle_offset + math.radians(120))
        ])
        ocarina_mesh.rotate_y(math.radians(120))
        self.scene.add(ocarina_mesh)
        self.instrument_stack.append(ocarina_mesh)
        
        # French horn (já existe, mas vamos garantir que está na pilha e bem posicionado)
        # Reposicionar o french horn se necessário
        if hasattr(self, 'french_horn_mesh'):
            self.french_horn_mesh.set_position([
                radius * math.cos(angle_offset + math.radians(240)),
                center_y,
                radius * math.sin(angle_offset + math.radians(240))
            ])
            self.french_horn_mesh.scale(0.22)
            self.french_horn_mesh.rotate_y(math.radians(180))
            self.instrument_stack.append(self.french_horn_mesh)

    def setup_hud(self):
        # Carregar a textura do crosshair
        crosshair_texture = Texture(file_name="images/crosshair2.png")
        crosshair_texture.set_properties({
            "magFilter": "GL_LINEAR",
            "minFilter": "GL_LINEAR",
            "wrap": "GL_CLAMP_TO_EDGE"  # Evita que a textura se repita
        })
        
        # Criar material com a textura do crosshair
        hud_material = TextureMaterial(
            texture=crosshair_texture,
            property_dict={
                "baseColor": [1, 0, 0],  # Cor vermelha
                "doubleSide": True  # Renderizar ambos os lados do plano
            }
        )
        
        # Criar um plano pequeno para o HUD
        hud_geometry = TexturedPlaneGeometry(width=0.02, height=0.02)  # Tamanho bem menor para o crosshair
        self.hud_mesh = Mesh(hud_geometry, hud_material)
        
        # Posicionar o HUD na frente da câmera
        self.hud_mesh.set_position([0, 0, -0.5])
        self.camera.add(self.hud_mesh)

        # Configurar fonte para o timer
        pygame.font.init()
        self.font = pygame.font.Font(None, 36)  # None usa a fonte padrão
        self.timer_surface = pygame.Surface((100, 50))
        self.timer_surface.set_colorkey((0,0,0))  # Faz o preto ficar transparente
        
        # Criar textura para o timer
        self.timer_texture = Texture()
        self.timer_material = TextureMaterial(
            texture=self.timer_texture,
            property_dict={"doubleSide": True}
        )
        
        # Criar plano para o timer
        timer_geometry = TexturedPlaneGeometry(width=0.2, height=0.1)
        self.timer_mesh = Mesh(timer_geometry, self.timer_material)
        self.timer_mesh.set_position([0.18, 0.13, -0.4])  # Melhor posição no canto superior direito
        self.timer_mesh.visible = True  # Garantir que está visível
        self.camera.add(self.timer_mesh)

        # Criar surface para o contador de kills
        self.kills_surface = pygame.Surface((100, 50))
        self.kills_surface.set_colorkey((0,0,0))
        
        # Criar textura para o contador de kills
        self.kills_texture = Texture()
        self.kills_material = TextureMaterial(
            texture=self.kills_texture,
            property_dict={"doubleSide": True}
        )
        
        # Criar plano para o contador de kills
        kills_geometry = TexturedPlaneGeometry(width=0.2, height=0.1)
        self.kills_mesh = Mesh(kills_geometry, self.kills_material)
        self.kills_mesh.set_position([-0.18, 0.13, -0.4])  # Posição no canto superior esquerdo
        self.kills_mesh.visible = True
        self.camera.add(self.kills_mesh)

        # Adicionar texto de pausa
        self.pause_font = pygame.font.Font(None, 36)
        self.pause_surface = pygame.Surface((200, 50))
        self.pause_surface.set_colorkey((0,0,0))
        
        # Criar textura para o texto de pausa
        self.pause_texture = Texture()
        self.pause_material = TextureMaterial(
            texture=self.pause_texture,
            property_dict={"doubleSide": True}
        )
        
        # Criar plano para o texto de pausa
        pause_geometry = TexturedPlaneGeometry(width=0.4, height=0.1)
        self.pause_mesh = Mesh(pause_geometry, self.pause_material)
        self.pause_mesh.set_position([0, 0, -0.3])  # Mais próximo da câmara
        self.pause_mesh.visible = False  # Começa invisível
        self.camera.add(self.pause_mesh)

        # Criar plano para a mensagem de fim de ronda
        self.end_font = pygame.font.Font(None, 40)
        self.end_surface = pygame.Surface((300, 60))
        self.end_surface.set_colorkey((0,0,0))
        self.end_texture = Texture()
        self.end_material = TextureMaterial(
            texture=self.end_texture,
            property_dict={"doubleSide": True}
        )
        end_geometry = TexturedPlaneGeometry(width=0.4, height=0.10)
        self.end_mesh = Mesh(end_geometry, self.end_material)
        self.end_mesh.set_position([0, 0.08, -0.29])  # ligeiramente acima do centro
        self.end_mesh.visible = False
        self.camera.add(self.end_mesh)

        # Botão Reiniciar
        self.restart_font = pygame.font.Font(None, 32)
        self.restart_surface = pygame.Surface((140, 40))
        self.restart_surface.set_colorkey((0,0,0))
        self.restart_texture = Texture()
        self.restart_material = TextureMaterial(
            texture=self.restart_texture,
            property_dict={"doubleSide": True}
        )
        restart_geometry = TexturedPlaneGeometry(width=0.18, height=0.06)
        self.restart_mesh = Mesh(restart_geometry, self.restart_material)
        self.restart_mesh.set_position([-0.11, -0.05, -0.29])
        self.restart_mesh.visible = False
        self.camera.add(self.restart_mesh)

        # Botão Sair
        self.exit_font = pygame.font.Font(None, 32)
        self.exit_surface = pygame.Surface((140, 40))
        self.exit_surface.set_colorkey((0,0,0))
        self.exit_texture = Texture()
        self.exit_material = TextureMaterial(
            texture=self.exit_texture,
            property_dict={"doubleSide": True}
        )
        exit_geometry = TexturedPlaneGeometry(width=0.18, height=0.06)
        self.exit_mesh = Mesh(exit_geometry, self.exit_material)
        self.exit_mesh.set_position([0.11, -0.05, -0.29])
        self.exit_mesh.visible = False
        self.camera.add(self.exit_mesh)

        # No setup_hud, adicionar criação de um texto/ícone para a tuba:
        self.tuba_icon_surface = pygame.Surface((180, 30))
        self.tuba_icon_surface.set_colorkey((0,0,0))
        self.tuba_icon_font = pygame.font.Font(None, 24)
        self.tuba_icon_texture = Texture()
        self.tuba_icon_material = TextureMaterial(texture=self.tuba_icon_texture, property_dict={"doubleSide": True})
        tuba_icon_geometry = TexturedPlaneGeometry(width=0.25, height=0.04)
        self.tuba_icon_mesh = Mesh(tuba_icon_geometry, self.tuba_icon_material)
        self.tuba_icon_mesh.set_position([-0.7, -0.45, -0.5])  # canto inferior esquerdo
        self.camera.add(self.tuba_icon_mesh)

        # No setup_hud, criar mesh da tuba para a "arma":
        positions, uvs = my_obj_reader2("geometry/tubabuedafixecomUVsemface.obj")
        tuba_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        tuba_texture = Texture(file_name="images/tuba6.png")
        tuba_material = PhongMaterial(
            texture=tuba_texture,
            property_dict={"baseColor": [1.0, 1.0, 1.0], "specularStrength": 2.0, "shininess": 32.0},
            number_of_light_sources=3
        )
        self.tuba_weapon_mesh = Mesh(tuba_geometry, tuba_material)
        self.tuba_weapon_mesh.scale(0.03)
        self.tuba_weapon_mesh.set_position([0.13, -0.18, -0.5])
        self.tuba_weapon_mesh.rotate_y(math.radians(-90))  # Rodar 90 graus no eixo Y
        self.tuba_weapon_mesh.visible = False
        self.camera.add(self.tuba_weapon_mesh)

        # No setup_hud, adicionar criação de um texto/ícone para a guitarra:
        self.guitar_icon_surface = pygame.Surface((180, 30))
        self.guitar_icon_surface.set_colorkey((0,0,0))
        self.guitar_icon_font = pygame.font.Font(None, 24)
        self.guitar_icon_texture = Texture()
        self.guitar_icon_material = TextureMaterial(texture=self.guitar_icon_texture, property_dict={"doubleSide": True})
        guitar_icon_geometry = TexturedPlaneGeometry(width=0.25, height=0.04)
        self.guitar_icon_mesh = Mesh(guitar_icon_geometry, self.guitar_icon_material)
        self.guitar_icon_mesh.set_position([-0.7, -0.4, -0.5])  # canto inferior esquerdo, ligeiramente acima do ícone da tuba
        self.camera.add(self.guitar_icon_mesh)

        # No setup_hud, criar mesh da guitarra para a "arma":
        positions, uvs = my_obj_reader2("geometry/ElectricGuitar.obj")
        guitar_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        guitar_texture = Texture(file_name="images/ElectricGuitar.jpg")
        guitar_material = PhongMaterial(
            texture=guitar_texture,
            property_dict={"baseColor": [1.0, 1.0, 1.0], "specularStrength": 2.0, "shininess": 32.0},
            number_of_light_sources=3
        )
        self.guitar_weapon_mesh = Mesh(guitar_geometry, guitar_material)
        self.guitar_weapon_mesh.scale(0.5)
        self.guitar_weapon_mesh.set_position([0.9, -1.4, -0.2])  # Mais afastada e mais baixa
        self.guitar_weapon_mesh.rotate_x(math.radians(20))  # Inclinar para baixo
        self.guitar_weapon_mesh.rotate_z(math.radians(330))  # Inclinar para baixo
        self.guitar_weapon_mesh.rotate_y(math.radians(200))   # Virar para a frente
        self.guitar_weapon_mesh.visible = True  # Começar visível pois o jogador já tem a guitarra
        self.camera.add(self.guitar_weapon_mesh)

        # HUD dos quadrantes (inicialmente invisível)
        self.quadrant_surface = pygame.Surface((1024, 768), pygame.SRCALPHA)
        self.quadrant_texture = Texture()
        self.quadrant_material = TextureMaterial(
            texture=self.quadrant_texture,
            property_dict={"doubleSide": True}
        )
        quadrant_geometry = TexturedPlaneGeometry(width=4, height=3)
        self.quadrant_mesh = Mesh(quadrant_geometry, self.quadrant_material)
        self.quadrant_mesh.set_position([0, 0, -0.3])
        self.quadrant_mesh.visible = False
        self.camera.add(self.quadrant_mesh)

        # HUD de fim de ronda (surface 2D)
        self.end_hud_surface = pygame.Surface((1024, 768), pygame.SRCALPHA)
        self.end_hud_texture = Texture()
        self.end_hud_material = TextureMaterial(
            texture=self.end_hud_texture,
            property_dict={"doubleSide": True}
        )
        end_hud_geometry = TexturedPlaneGeometry(width=0.6, height=0.6)
        self.end_hud_mesh = Mesh(end_hud_geometry, self.end_hud_material)
        self.end_hud_mesh.set_position([0, 0, -0.3])
        self.end_hud_mesh.visible = False
        self.camera.add(self.end_hud_mesh)

        # Criar surface para a barra de vida
        self.health_surface = pygame.Surface((200, 30))
        self.health_surface.set_colorkey((0,0,0))
        
        # Criar textura para a barra de vida
        self.health_texture = Texture()
        self.health_material = TextureMaterial(
            texture=self.health_texture,
            property_dict={"doubleSide": True}
        )
        
        # Criar plano para a barra de vida
        health_geometry = TexturedPlaneGeometry(width=0.4, height=0.06)
        self.health_mesh = Mesh(health_geometry, self.health_material)
        self.health_mesh.set_position([0, 0.2, -0.4])  # Posição no topo da tela
        self.health_mesh.visible = True
        self.camera.add(self.health_mesh)

        # Adicionar texto para mensagem de instrumento disponível
        self.instrument_message_surface = pygame.Surface((400, 60))
        self.instrument_message_surface.set_colorkey((0,0,0))
        self.instrument_message_font = pygame.font.Font(None, 36)
        self.instrument_message_texture = Texture()
        self.instrument_message_material = TextureMaterial(
            texture=self.instrument_message_texture, 
            property_dict={"doubleSide": True}
        )
        instrument_message_geometry = TexturedPlaneGeometry(width=0.6, height=0.1)
        self.instrument_message_mesh = Mesh(instrument_message_geometry, self.instrument_message_material)
        self.instrument_message_mesh.set_position([0, 0.2, -0.4])  # Posição central na tela
        self.instrument_message_mesh.visible = False
        self.camera.add(self.instrument_message_mesh)

    def create_environment(self, floor_material, wall_material):
        # Criar skybox
        sky_texture = Texture(file_name="images/sky.jpg")
        sky_texture.set_properties({
            "magFilter": "GL_LINEAR",
            "minFilter": "GL_LINEAR",
            "wrap": "GL_CLAMP_TO_EDGE"
        })
        
        sky_material = TextureMaterial(
            texture=sky_texture,
            property_dict={
                "baseColor": [0.3, 0.3, 0.3],  # Céu mais escuro
                "doubleSide": True
            }
        )
        
        # Criar uma esfera grande para o céu
        from geometry.sphere import SphereGeometry
        sky_geometry = SphereGeometry(radius=100)
        sky = Mesh(sky_geometry, sky_material)
        # Inverter a esfera para que a textura apareça do lado de dentro
        sky.scale(-1)
        self.scene.add(sky)

        # Carregar geometria e textura do personagem uma vez
        positions, uvs = my_obj_reader2("geometry/3DCharacter.obj")
        character_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        character_texture = Texture(file_name="images/Material_0.png")
        
        # Material do personagem
        character_material = PhongMaterial(
            texture=character_texture,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],
                "specularStrength": 0.5,
                "shininess": 8.0
            },
            number_of_light_sources=3
        )

        # Lista de coordenadas para os personagens - posições em frente às portas
        self.character_positions = [
            [0, 0.5, -24.0],    # Porta traseira
            [0, 0.5, 24.0],     # Porta frontal
            [-24.0, 0.5, 0],    # Porta esquerda
            [24.0, 0.5, 0]      # Porta direita
        ]

        # Criar e posicionar os personagens
        self.character_meshes = []  # Lista para armazenar todos os personagens
        for pos in self.character_positions:
            character_mesh = Mesh(character_geometry, character_material)
            character_mesh.set_position(pos)
            character_mesh.scale(1.8)  # Ajustar o tamanho conforme necessário
            
            # Rotacionar o personagem para olhar para o centro do armazém
            if pos[0] == 0 and pos[2] < 0:  # Porta traseira
                character_mesh.rotate_y(math.radians(0))  # Olhar para frente
            elif pos[0] == 0 and pos[2] > 0:  # Porta frontal
                character_mesh.rotate_y(math.radians(180))  # Olhar para trás
            elif pos[0] < 0:  # Porta esquerda
                character_mesh.rotate_y(math.radians(90))  # Olhar para direita
            else:  # Porta direita
                character_mesh.rotate_y(math.radians(-90))  # Olhar para esquerda
                
            self.scene.add(character_mesh)
            self.character_meshes.append(character_mesh)

        # Configuração do armazém
        warehouse_texture = Texture(file_name="images/DoorsMetalBig0306_4_350.jpg")
        warehouse_material = TextureMaterial(texture=warehouse_texture)
        wall_width = 50
        wall_height = 15
        wall_distance = 25

        # Parede de trás
        parede_tras = Mesh(RectangleGeometry(width=wall_width, height=wall_height), warehouse_material)
        parede_tras.set_position([0, wall_height/2, -wall_distance])
        self.scene.add(parede_tras)

        # Parede da frente
        parede_frente = Mesh(RectangleGeometry(width=wall_width, height=wall_height), warehouse_material)
        parede_frente.set_position([0, wall_height/2, wall_distance])
        parede_frente.rotate_y(math.pi)
        self.scene.add(parede_frente)

        # Parede esquerda
        parede_esq = Mesh(RectangleGeometry(width=wall_width, height=wall_height), warehouse_material)
        parede_esq.set_position([-wall_distance, wall_height/2, 0])
        parede_esq.rotate_y(math.pi/2)
        self.scene.add(parede_esq)

        # Parede direita
        parede_dir = Mesh(RectangleGeometry(width=wall_width, height=wall_height), warehouse_material)
        parede_dir.set_position([wall_distance, wall_height/2, 0])
        parede_dir.rotate_y(-math.pi/2)
        self.scene.add(parede_dir)

        # Teto do armazém
        ceiling_texture = Texture(file_name="images/preview16.jpg")
        ceiling_material = TextureMaterial(texture=ceiling_texture, property_dict={"repeatUV": [5, 5]})
        ceiling_geometry = RectangleGeometry(width=50, height=50)
        self.ceiling = Mesh(ceiling_geometry, ceiling_material)
        self.ceiling.rotate_x(math.pi / 2)
        self.ceiling.set_position([0, wall_height, 0])
        self.scene.add(self.ceiling)

        # Chão com textura de cimento
        cement_path = "images/360_F_348213401_4qDDlTEphzmi778eCDKRoMWJEQvKp8vj.jpg"
        if os.path.exists(cement_path):
            cement_texture = Texture(file_name=cement_path)
            chao_geometry = RectangleGeometry(width=50, height=50)
            chao_material = TextureMaterial(texture=cement_texture, property_dict={"repeatUV": [10, 10]})
            self.chao = Mesh(chao_geometry, chao_material)
            self.chao.rotate_x(-math.pi / 2)
            self.chao.set_position([0, -0.01, 0])
            self.scene.add(self.chao)

        # Caixas empilhadas e espalhadas
        box_texture = Texture(file_name="images/crate.jpg")
        box_material = TextureMaterial(texture=box_texture)
        # Menos caixas espalhadas para liberar caminho
        num_caixas = 10
        self.caixas = []
        
        # Lista para guardar posições já ocupadas
        occupied_positions = []
        
        for _ in range(num_caixas):
            # Tentar encontrar uma posição válida
            max_attempts = 10
            valid_position = False
            
            for _ in range(max_attempts):
                x = random.uniform(-20, 20)
                z = random.uniform(-20, 20)
                y = 0.5  # Altura base da caixa
                # Verificar se a posição está muito próxima de outras caixas
                too_close = False
                for pos in occupied_positions:
                    if abs(x - pos[0]) < 1.0 and abs(z - pos[1]) < 1.0:
                        too_close = True
                        break
                if not too_close:
                    valid_position = True
                    break
            if valid_position:
                # Criar a caixa base
                caixa = Mesh(BoxGeometry(), box_material)
                caixa.set_position([x, y, z])
                caixa.rotate_y(random.uniform(0, 2*math.pi))
                self.scene.add(caixa)
                self.caixas.append(caixa)
                occupied_positions.append((x, z))
                # 30% de chance de adicionar uma caixa em cima
                if random.random() < 0.3:
                    caixa_cima = Mesh(BoxGeometry(), box_material)
                    caixa_cima.set_position([x, y + 1.0, z])  # Uma unidade acima
                    caixa_cima.rotate_y(random.uniform(0, 2*math.pi))
                    self.scene.add(caixa_cima)
                    self.caixas.append(caixa_cima)

        # Adicionar o modelo da tuba - inicialmente invisível
        positions, uvs = my_obj_reader2("geometry/tubabuedafixecomUVsemface.obj")
        tuba_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        tuba_texture = Texture(file_name="images/tuba6.png")
        
        # Material da tuba com efeito neon mais intenso mas mantendo a textura original
        tuba_material = PhongMaterial(
            texture=tuba_texture,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],  # Cor base branca para não afetar a textura
                "specularStrength": 2.0,       # Aumentei o brilho especular
                "shininess": 32.0              # Reduzindo um pouco para espalhar mais o brilho
            },
            number_of_light_sources=3
        )
        
        # Criar e posicionar a tuba no centro do mapa (inicialmente invisível)
        self.tuba_mesh = Mesh(tuba_geometry, tuba_material)
        self.tuba_mesh.set_position([0, 1.0, -20.0])  # Centro do mapa
        self.tuba_mesh.scale(0.2)
        self.tuba_mesh.visible = False  # Inicialmente invisível
        self.scene.add(self.tuba_mesh)

        # Adicionar o modelo da guitarra elétrica - já colocada ao lado do jogador
        positions, uvs = my_obj_reader2("geometry/ElectricGuitar.obj")
        guitar_geometry = TubaGeometry2(1, 1, 1, positions, uvs)
        guitar_texture = Texture(file_name="images/ElectricGuitar.jpg")  # Usando a textura da guitarra
        
        # Material da guitarra
        guitar_material = PhongMaterial(
            texture=guitar_texture,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],
                "specularStrength": 2.0,
                "shininess": 32.0
            },
            number_of_light_sources=3
        )
        
        # Criar e posicionar a guitarra ao lado do jogador
        self.guitar_mesh = Mesh(guitar_geometry, guitar_material)
        self.guitar_mesh.set_position([2.0, 1.0, -18.0])  # Ao lado da posição inicial do jogador
        self.guitar_mesh.scale(0.5)  # Aumentado o tamanho para 0.5
        self.guitar_mesh.rotate_x(math.radians(-90))  # Rotacionar para ficar na vertical
        self.guitar_mesh.rotate_z(math.radians(90))  # Rotacionar para ficar de frente
        self.guitar_mesh.visible = False  # Inicialmente invisível pois o jogador já tem a guitarra
        self.scene.add(self.guitar_mesh)

        # Ajustar a distância de renderização da câmera
        self.camera.set_perspective(60, 1024/768, 0.1, 6000.0)  # Aumentado para 3x a distância original

    def check_wall_collision(self, position):
        """
        Verifica se há colisão entre o jogador e as paredes/caixas/pilha de instrumentos
        Returns: (colidiu, posição_ajustada)
        """
        # Margem de colisão (raio do "cilindro" do jogador)
        player_radius = 0.5
        
        # Verificar colisão com a pilha de instrumentos
        stack_pos = np.array([0, 0, 0])  # Posição do centro da pilha
        stack_radius = 1.0  # Raio de colisão da pilha
        
        # Verificar apenas colisão no plano XZ (2D)
        player_pos_xz = np.array([position[0], position[2]])
        stack_pos_xz = np.array([stack_pos[0], stack_pos[2]])
        
        # Calcular a distância do jogador até o centro da pilha
        dx = player_pos_xz[0] - stack_pos_xz[0]
        dz = player_pos_xz[1] - stack_pos_xz[1]
        
        # Se estiver dentro da área de colisão
        if (abs(dx) < stack_radius + player_radius and 
            abs(dz) < stack_radius + player_radius):
            
            # Calcular a posição ajustada (deslizar ao longo da pilha)
            adjusted_position = position.copy()
            
            # Determinar qual face da pilha foi atingida
            if abs(dx) / (stack_radius + player_radius) > abs(dz) / (stack_radius + player_radius):
                # Colisão lateral (esquerda/direita)
                if dx > 0:
                    adjusted_position[0] = stack_pos_xz[0] + stack_radius + player_radius
                else:
                    adjusted_position[0] = stack_pos_xz[0] - stack_radius - player_radius
            else:
                # Colisão frontal/traseira
                if dz > 0:
                    adjusted_position[2] = stack_pos_xz[1] + stack_radius + player_radius
                else:
                    adjusted_position[2] = stack_pos_xz[1] - stack_radius - player_radius
            
            return True, adjusted_position
        
        # Verificar colisão com as caixas
        for caixa in self.caixas:
            caixa_pos = np.array(caixa.global_position)
            caixa_size = 1.0  # Tamanho da caixa (assumindo caixas de 1x1x1)
            
            # Verificar apenas colisão no plano XZ (2D)
            player_pos_xz = np.array([position[0], position[2]])
            caixa_pos_xz = np.array([caixa_pos[0], caixa_pos[2]])
            
            # Calcular a distância do jogador até o centro da caixa
            dx = player_pos_xz[0] - caixa_pos_xz[0]
            dz = player_pos_xz[1] - caixa_pos_xz[1]
            
            # Se estiver dentro da área de colisão
            if (abs(dx) < caixa_size/2 + player_radius and 
                abs(dz) < caixa_size/2 + player_radius):
                
                # Calcular a posição ajustada (deslizar ao longo da caixa)
                adjusted_position = position.copy()
                
                # Determinar qual face da caixa foi atingida
                if abs(dx) / (caixa_size/2 + player_radius) > abs(dz) / (caixa_size/2 + player_radius):
                    # Colisão lateral (esquerda/direita)
                    if dx > 0:
                        adjusted_position[0] = caixa_pos_xz[0] + caixa_size/2 + player_radius
                    else:
                        adjusted_position[0] = caixa_pos_xz[0] - caixa_size/2 - player_radius
                else:
                    # Colisão frontal/traseira
                    if dz > 0:
                        adjusted_position[2] = caixa_pos_xz[1] + caixa_size/2 + player_radius
                    else:
                        adjusted_position[2] = caixa_pos_xz[1] - caixa_size/2 - player_radius
                
                return True, adjusted_position
        
        # Verificar colisão com as paredes do armazém
        wall_distance = 25  # Distância das paredes do centro
        wall_width = 50    # Largura das paredes
        
        # Verificar colisão com cada parede
        if abs(position[0]) > wall_distance - player_radius:  # Paredes laterais
            adjusted_position = position.copy()
            if position[0] > 0:
                adjusted_position[0] = wall_distance - player_radius
            else:
                adjusted_position[0] = -wall_distance + player_radius
            return True, adjusted_position
            
        if abs(position[2]) > wall_distance - player_radius:  # Paredes frontal/traseira
            adjusted_position = position.copy()
            if position[2] > 0:
                adjusted_position[2] = wall_distance - player_radius
            else:
                adjusted_position[2] = -wall_distance + player_radius
            return True, adjusted_position
        
        return False, position

    def create_bullet(self):
        # Gerar cor aleatória
        random_color = [random.random(), random.random(), random.random()]
        
        # Escolher uma nota aleatória baseada na cor
        # Usamos a soma dos componentes RGB para determinar a nota
        color_sum = sum(random_color)
        
        # Tocar o som apropriado baseado no instrumento equipado
        if self.has_guitar:
            # Usar sons da guitarra
            note_names = list(self.guitar_sounds.keys())
            note_index = int((color_sum / 3.0) * len(note_names))
            selected_note = note_names[note_index % len(note_names)]
            
            # Verificar cooldown da guitarra
            current_time = pygame.time.get_ticks() / 1000
            if current_time - self.last_guitar_shot_time < self.guitar_shot_cooldown:
                return  # Não disparar se ainda estiver em cooldown
                
            self.last_guitar_shot_time = current_time
            self.guitar_sounds[selected_note].play()
            
            # Criar material com cor aleatória
            bullet_material = TextureMaterial(
                texture=self.bullet_texture,
                property_dict={
                    "baseColor": random_color,
                    "doubleSide": True
                }
            )
            
            # Criar mesh da bala com tamanho reduzido
            bullet_mesh = Mesh(self.bullet_geometry, bullet_material)
            bullet_mesh.scale(0.125)  # Reduzir para 1/8 do tamanho original
            
            # Obter a posição da câmara
            camera_position = self.camera.global_position
            # Obter a direção da câmara usando a matriz de rotação global
            camera_matrix = self.camera.global_matrix
            camera_direction = [-camera_matrix[0][2],
                              -camera_matrix[1][2],
                              -camera_matrix[2][2]]
            # Fazer a bala sair da guitarra (ajustar offsets conforme necessário)
            offset = 0.8  # distância à frente
            offset_x = 0.10  # desvio lateral (direita)
            offset_y = -0.08  # desvio vertical (baixo)
            right = [self.camera.global_matrix[0][0], self.camera.global_matrix[1][0], self.camera.global_matrix[2][0]]
            up = [self.camera.global_matrix[0][1], self.camera.global_matrix[1][1], self.camera.global_matrix[2][1]]
            bullet_start = [
                camera_position[0] + camera_direction[0] * offset + right[0] * offset_x + up[0] * offset_y,
                camera_position[1] + camera_direction[1] * offset + right[1] * offset_x + up[1] * offset_y,
                camera_position[2] + camera_direction[2] * offset + right[2] * offset_x + up[2] * offset_y
            ]
            bullet_mesh.set_position(bullet_start)
            
            # Obter a direção da câmera usando a matriz de rotação global
            camera_matrix = self.camera.global_matrix
            # O vetor de direção é o negativo do eixo Z da câmera (terceira coluna da matriz)
            camera_direction = [-camera_matrix[0][2],
                              -camera_matrix[1][2],
                              -camera_matrix[2][2]]
            
            # Normalizar o vetor de direção
            length = math.sqrt(sum(d*d for d in camera_direction))
            camera_direction = [d/length for d in camera_direction]
            
            # Adicionar a bala à cena e à lista de balas
            self.scene.add(bullet_mesh)
            # Alinhar o mesh da bala com a direção do disparo
            bullet_mesh.set_direction(camera_direction)
            bullet_mesh.scale(0.125)
            self.bullets.append({
                "mesh": bullet_mesh,
                "direction": camera_direction,
                "lifetime": 5.0,  # Tempo de vida da bala em segundos
                "is_rocket": False,  # Não é um foguete
                "exploded": False   # Não explodiu ainda
            })
        else:
            # TUBA = ROCKET LAUNCHER - FOGUETE MUSICAL
            # Verificar cooldown da tuba
            current_time = pygame.time.get_ticks() / 1000
            if current_time - self.last_tuba_shot_time < self.tuba_shot_cooldown:
                return  # Não disparar se ainda estiver em cooldown
                
            self.last_tuba_shot_time = current_time
            
            # Usar sons da tuba
            note_names = list(self.notes.keys())
            note_index = int((color_sum / 3.0) * len(note_names))
            selected_note = note_names[note_index % len(note_names)]
            self.notes[selected_note].play()
            
            # Calcular o número de fontes de luz na cena
            # (Ambient + Directional + Tuba light = 3)
            num_lights = 3
            
            # Usar a geometria da nota musical
            geometry = self.note_geometry
            texture = self.note_texture
            
            # Criar material com cor aleatória e brilho
            note_material = PhongMaterial(
                texture=texture,
                property_dict={
                    "baseColor": [random_color[0]*1.5, random_color[1]*1.5, random_color[2]*1.5],  # Cor brilhante
                    "specularStrength": 3.0,
                    "shininess": 16.0
                },
                number_of_light_sources=num_lights
            )
            
            # Criar mesh do projétil (nota musical)
            bullet_mesh = Mesh(geometry, note_material)
            bullet_mesh.scale(0.2)  # Tamanho similar ao da ocarina
            
            # Obter a posição da câmara
            camera_position = self.camera.global_position
            # Obter a direção da câmara usando a matriz de rotação global
            camera_matrix = self.camera.global_matrix
            camera_direction = [-camera_matrix[0][2],
                              -camera_matrix[1][2],
                              -camera_matrix[2][2]]
            # Fazer o projétil sair da campânula da tuba (ajustar offsets conforme necessário)
            offset = 0.8  # distância à frente
            offset_x = 0.10  # desvio lateral (direita)
            offset_y = -0.08  # desvio vertical (baixo)
            right = [self.camera.global_matrix[0][0], self.camera.global_matrix[1][0], self.camera.global_matrix[2][0]]
            up = [self.camera.global_matrix[0][1], self.camera.global_matrix[1][1], self.camera.global_matrix[2][1]]
            bullet_start = [
                camera_position[0] + camera_direction[0] * offset + right[0] * offset_x + up[0] * offset_y,
                camera_position[1] + camera_direction[1] * offset + right[1] * offset_x + up[1] * offset_y,
                camera_position[2] + camera_direction[2] * offset + right[2] * offset_x + up[2] * offset_y
            ]
            bullet_mesh.set_position(bullet_start)
            
            # Rotação aleatória para dar um efeito de giro
            bullet_mesh.rotate_x(random.uniform(0, 2*math.pi))
            bullet_mesh.rotate_y(random.uniform(0, 2*math.pi))
            bullet_mesh.rotate_z(random.uniform(0, 2*math.pi))
            
            # Obter a direção da câmera usando a matriz de rotação global
            camera_matrix = self.camera.global_matrix
            # O vetor de direção é o negativo do eixo Z da câmera (terceira coluna da matriz)
            camera_direction = [-camera_matrix[0][2],
                              -camera_matrix[1][2],
                              -camera_matrix[2][2]]
            
            # Normalizar o vetor de direção
            length = math.sqrt(sum(d*d for d in camera_direction))
            camera_direction = [d/length for d in camera_direction]
            
            # Adicionar o projétil à cena e à lista de balas
            self.scene.add(bullet_mesh)
            
            # Adicionar à lista de balas com propriedades especiais
            self.bullets.append({
                "mesh": bullet_mesh,
                "direction": camera_direction,
                "lifetime": 5.0,  # Tempo de vida do projétil em segundos
                "is_rocket": True,  # É um foguete
                "exploded": False,  # Não explodiu ainda
                "color": random_color,  # Cor para a explosão
                "rotation_speed": [  # Velocidades de rotação em cada eixo
                    random.uniform(-5.0, 5.0),
                    random.uniform(-5.0, 5.0),
                    random.uniform(-5.0, 5.0)
                ],
                "is_note": True  # Marcar como nota musical
            })

    def update_bullets(self, delta_time):
        # Atualizar posição das balas e remover as que expiraram
        bullets_to_remove = []
        characters_to_remove = []
        
        for bullet in self.bullets:
            # Atualizar posição
            current_pos = bullet["mesh"].local_position
            
            # Verificar se é uma partícula de explosão
            if bullet.get("is_particle", False):
                # Verificar se é a explosão central
                if bullet.get("is_central_explosion", False):
                    # Apenas aumentar o tamanho rapidamente
                    if not "expansion_factor" in bullet:
                        bullet["expansion_factor"] = 1.0
                    
                    bullet["expansion_factor"] *= 1.2  # Aumentar 20% a cada frame
                    bullet["mesh"].scale(bullet["current_scale"] * bullet["expansion_factor"])
                    
                    # Reduzir a opacidade (não suportado diretamente, então apenas reduzir o brilho)
                    if "opacity" not in bullet:
                        bullet["opacity"] = 1.0
                    
                    bullet["opacity"] *= 0.9  # Reduzir opacidade
                    if bullet["opacity"] < 0.1:
                        bullets_to_remove.append(bullet)
                        continue
                else:
                    # Usar velocidade específica da partícula
                    particle_speed = bullet.get("velocity", 10.0)
                    new_pos = [
                        current_pos[0] + bullet["direction"][0] * particle_speed * delta_time,
                        current_pos[1] + bullet["direction"][1] * particle_speed * delta_time,
                        current_pos[2] + bullet["direction"][2] * particle_speed * delta_time
                    ]
                    bullet["mesh"].set_position(new_pos)
                    
                    # Reduzir tamanho gradualmente, mas não tão rápido
                    if not "current_scale" in bullet:
                        bullet["current_scale"] = 0.25  # Tamanho inicial da partícula
                    
                    if bullet["current_scale"] > 0.05:  # Permitir ficar um pouco maior antes de encolher
                        bullet["current_scale"] *= 0.98  # Redução mais lenta de apenas 2% a cada frame
                        bullet["mesh"].scale(bullet["current_scale"])
                
                # Atualizar tempo de vida
                bullet["lifetime"] -= delta_time
                if bullet["lifetime"] <= 0:
                    bullets_to_remove.append(bullet)
                
                # Pular o resto da lógica para partículas
                continue
            
            # Velocidade baseada no tipo de projétil (foguetes são mais lentos)
            speed_multiplier = 0.7 if bullet.get("is_rocket", False) else 1.0
            
            new_pos = [
                current_pos[0] + bullet["direction"][0] * self.bullet_speed * speed_multiplier * delta_time,
                current_pos[1] + bullet["direction"][1] * self.bullet_speed * speed_multiplier * delta_time,
                current_pos[2] + bullet["direction"][2] * self.bullet_speed * speed_multiplier * delta_time
            ]
            bullet["mesh"].set_position(new_pos)
            
            # Remover bala se colidir com o chão (com tolerância)
            if new_pos[1] < self.initial_height - 0.9:
                bullets_to_remove.append(bullet)
                continue
            
            # Remover bala se colidir com paredes/obstáculos
            collided, _ = self.check_wall_collision(new_pos)
            if collided:
                # Se for foguete e ainda não explodiu, criar explosão
                if bullet.get("is_rocket", False) and not bullet.get("exploded", True):
                    bullet["exploded"] = True
                    if bullet.get("is_note", False):
                        self.create_grenade_explosion(new_pos)
                    else:
                        self.create_rocket_explosion(new_pos, bullet.get("color", [1,1,1]))
                bullets_to_remove.append(bullet)
                continue
            
            # Adicionar rotação contínua para as ocarinas lançadas
            if bullet.get("is_rocket", False) and "rotation_speed" in bullet:
                rot_speed = bullet["rotation_speed"]
                bullet["mesh"].rotate_x(rot_speed[0] * delta_time)
                bullet["mesh"].rotate_y(rot_speed[1] * delta_time)
                bullet["mesh"].rotate_z(rot_speed[2] * delta_time)
            
            # Verificar colisão com personagens
            bullet_pos = np.array(new_pos)
            hit_something = False
            
            for character in self.character_meshes:
                if character in characters_to_remove:
                    continue
                character_pos = np.array(character.global_position)
                dist = np.linalg.norm(bullet_pos - character_pos)
                
                # Raio de colisão maior para foguetes
                collision_radius = 1.5 if bullet.get("is_rocket", False) else 1.0
                
                if dist < collision_radius:  # Distância de colisão
                    # Se for um foguete e ainda não explodiu, criar explosão
                    if bullet.get("is_rocket", False) and not bullet.get("exploded", True):
                        bullet["exploded"] = True
                        
                        # Se for uma nota musical, usar comportamento da ocarina
                        if bullet.get("is_note", False):
                            self.create_grenade_explosion(new_pos)
                        else:
                            self.create_rocket_explosion(new_pos, bullet.get("color", [1,1,1]))
                        
                        # Procurar por personagens próximos para dano em área
                        for other_character in self.character_meshes:
                            if other_character in characters_to_remove:
                                continue
                            
                            other_pos = np.array(other_character.global_position)
                            explosion_dist = np.linalg.norm(bullet_pos - other_pos)
                            
                            if explosion_dist < 3.5:  # Raio de explosão maior
                                characters_to_remove.append(other_character)
                                # Incrementar contador de kills
                                self.kill_count += 1
                                self.update_kills_display()
                                # Dropar uma ocarina na posição do personagem com 30% de chance
                                if random.random() < 0.3:  # Aumentar chance
                                    self.create_ocarina_drop(other_pos)
                                # Escolher uma posição inicial aleatória
                                random_position = random.choice(self.character_positions)
                                # Adicionar à lista de respawn
                                self.respawning_characters.append((other_character, random_position, self.respawn_delay))
                        
                        # Marcar para remover o foguete
                        bullets_to_remove.append(bullet)
                        hit_something = True
                        break
                    else:
                        # Bala normal
                        bullets_to_remove.append(bullet)
                        characters_to_remove.append(character)
                        # Incrementar contador de kills
                        self.kill_count += 1
                        self.update_kills_display()
                        # Dropar uma ocarina na posição do personagem com 25% de chance
                        if random.random() < 0.25:  # 25% de chance
                            self.create_ocarina_drop(character_pos)
                        # Escolher uma posição inicial aleatória
                        random_position = random.choice(self.character_positions)
                        # Adicionar à lista de respawn
                        self.respawning_characters.append((character, random_position, self.respawn_delay))
                        print(f"Personagem atingido! Kills: {self.kill_count}")
                        hit_something = True
                        break
            
            # Verificar colisão com paredes/chão para foguetes
            if not hit_something and bullet.get("is_rocket", False) and not bullet.get("exploded", True):
                # Colisão com o chão
                if new_pos[1] <= 0.2:  # Altura do chão
                    bullet["exploded"] = True
                    
                    # Se for uma nota musical, usar comportamento da ocarina
                    if bullet.get("is_note", False):
                        self.create_grenade_explosion(new_pos)
                    else:
                        self.create_rocket_explosion(new_pos, bullet.get("color", [1,1,1]))
                    
                    bullets_to_remove.append(bullet)
                    hit_something = True
                
                # Simplificando: colisão com a parede vermelha
                wall_pos = self.wall_position
                wall_dim = self.wall_dimensions
                if (abs(new_pos[0] - wall_pos[0]) < wall_dim[0]/2 + 0.5 and 
                    abs(new_pos[2] - wall_pos[2]) < wall_dim[2]/2 + 0.5 and
                    new_pos[1] < wall_dim[1]):
                    bullet["exploded"] = True
                    
                    # Se for uma nota musical, usar comportamento da ocarina
                    if bullet.get("is_note", False):
                        self.create_grenade_explosion(new_pos)
                    else:
                        self.create_rocket_explosion(new_pos, bullet.get("color", [1,1,1]))
                    
                    bullets_to_remove.append(bullet)
                    hit_something = True
            
            # Atualizar tempo de vida
            bullet["lifetime"] -= delta_time
            if bullet["lifetime"] <= 0:
                # Se for um foguete que expirou sem colidir, ainda criar uma explosão
                if bullet.get("is_rocket", False) and not bullet.get("exploded", True):
                    
                    # Se for uma nota musical, usar comportamento da ocarina
                    if bullet.get("is_note", False):
                        self.create_grenade_explosion(new_pos)
                    else:
                        self.create_rocket_explosion(new_pos, bullet.get("color", [1,1,1]))
                
                bullets_to_remove.append(bullet)
        
        # Remover balas expiradas ou que colidiram
        for bullet in bullets_to_remove:
            if bullet in self.bullets:  # Verificar se a bala ainda existe
                self.scene.remove(bullet["mesh"])
                self.bullets.remove(bullet)
        
        # Remover personagens atingidos
        for character in characters_to_remove:
            if character in self.character_meshes:  # Verificar se o personagem ainda existe
                self.scene.remove(character)
                self.character_meshes.remove(character)

    def update_timer_display(self):
        try:
            # Converter o tempo restante em minutos e segundos
            minutes = int(self.remaining_time // 60)
            seconds = int(self.remaining_time % 60)
            
            # Criar texto do timer
            self.timer_surface.fill((0,0,0))  # Limpar superfície
            timer_text = f"{minutes:02d}:{seconds:02d}"
            
            # Verificar se a fonte está inicializada
            if not hasattr(self, 'font') or self.font is None:
                pygame.font.init()
                self.font = pygame.font.Font(None, 36)
            
            # Renderizar o texto com tratamento de erro
            try:
                text_surface = self.font.render(timer_text, True, (255,255,255))
            except Exception as e:
                print(f"Erro ao renderizar texto: {e}")
                return
            
            # Centralizar texto na superfície
            x = (self.timer_surface.get_width() - text_surface.get_width()) // 2
            y = (self.timer_surface.get_height() - text_surface.get_height()) // 2
            self.timer_surface.blit(text_surface, (x,y))
            
            # Atualizar textura
            self.timer_texture.surface = self.timer_surface
            self.timer_texture.upload_data()
            
        except Exception as e:
            print(f"Erro ao atualizar timer: {e}")
            # Tentar reinicializar o timer se necessário
            if not hasattr(self, 'timer_surface') or self.timer_surface is None:
                self.timer_surface = pygame.Surface((100, 50))
                self.timer_surface.set_colorkey((0,0,0))

    def update_pause_display(self):
        self.pause_surface.fill((0,0,0))
        pause_text = "PAUSE" if self.paused else ""
        text_surface = self.pause_font.render(pause_text, True, (255,255,255))
        
        # Centralizar texto na superfície
        x = (self.pause_surface.get_width() - text_surface.get_width()) // 2
        y = (self.pause_surface.get_height() - text_surface.get_height()) // 2
        self.pause_surface.blit(text_surface, (x,y))
        
        # Atualizar textura
        self.pause_texture.surface = self.pause_surface
        self.pause_texture.upload_data()
        self.pause_mesh.visible = self.paused  # Só visível se estiver pausado

    def update_tuba_icon(self):
        self.tuba_icon_surface.fill((0,0,0))
        show = False
        alpha = 255
        if self.tuba_pickup_time is not None:
            elapsed = pygame.time.get_ticks() / 1000 - self.tuba_pickup_time
            if elapsed < 2.0:
                show = True
                alpha = int(255 * (1 - elapsed / 2.0))
            else:
                self.tuba_pickup_time = None
        if show:
            text = "Tuba equipada!"
            text_surface = self.tuba_icon_font.render(text, True, (255, 255, 0))
            text_surface.set_alpha(alpha)
            self.tuba_icon_surface.blit(text_surface, (0, 0))
            self.tuba_icon_mesh.visible = True
        else:
            self.tuba_icon_mesh.visible = False
        self.tuba_icon_texture.surface = self.tuba_icon_surface
        self.tuba_icon_texture.upload_data()

    def update_guitar_icon(self):
        self.guitar_icon_surface.fill((0,0,0))
        show = False
        alpha = 255
        if self.guitar_pickup_time is not None:
            elapsed = pygame.time.get_ticks() / 1000 - self.guitar_pickup_time
            if elapsed < 2.0:
                show = True
                alpha = int(255 * (1 - elapsed / 2.0))
            else:
                self.guitar_pickup_time = None
        if show:
            text = "Guitarra equipada!"
            text_surface = self.guitar_icon_font.render(text, True, (255, 255, 0))
            text_surface.set_alpha(alpha)
            self.guitar_icon_surface.blit(text_surface, (0, 0))
            self.guitar_icon_mesh.visible = True
        else:
            self.guitar_icon_mesh.visible = False
        self.guitar_icon_texture.surface = self.guitar_icon_surface
        self.guitar_icon_texture.upload_data()

    def percent_to_surface(self, px, py):
        w, h = self.end_hud_surface.get_size()
        return int(px * w), int(py * h)

    def screen_to_hud_surface(self, mx, my):
        screen_w, screen_h = self._screen.get_size()
        hud_surface_w, hud_surface_h = self.end_hud_surface.get_size()
        # Tamanho do mesh do HUD (deve ser igual ao usado em TexturedPlaneGeometry)
        hud_mesh_width = 0.6
        hud_mesh_height = 0.6
        # Centro do ecrã
        cx, cy = screen_w // 2, screen_h // 2
        # Tamanho do mesh em pixeis
        mesh_px_w = int(screen_w * hud_mesh_width)
        mesh_px_h = int(screen_h * hud_mesh_height)
        # Canto superior esquerdo do mesh
        mesh_left = cx - mesh_px_w // 2
        mesh_top = cy - mesh_px_h // 2
        # Só converte se o cursor estiver dentro do mesh
        if not (mesh_left <= mx < mesh_left + mesh_px_w and mesh_top <= my < mesh_top + mesh_px_h):
            return -1, -1  # Fora do mesh
        # Coordenadas relativas ao mesh
        rel_x = mx - mesh_left
        rel_y = my - mesh_top
        # Converter para coordenadas da surface
        hud_x = int(rel_x * hud_surface_w / mesh_px_w)
        hud_y = int(rel_y * hud_surface_h / mesh_px_h)
        return hud_x, hud_y

    def draw_end_hud(self, hover_restart=False, hover_exit=False):
        w, h = self.end_hud_surface.get_size()
        self.end_hud_surface.fill((0,0,0,0))
        
        # Texto de fim de ronda
        font_title = pygame.font.Font(None, 70)
        end_text = "MORRESTE!" if self.game_over_reason == "death" else "RONDA ACABOU"
        text = font_title.render(end_text, True, (255,255,255))
        rect = text.get_rect(center=self.percent_to_surface(0.5, 0.3))
        self.end_hud_surface.blit(text, rect)
        
        # Texto do kill count
        font_kills = pygame.font.Font(None, 50)
        kills_text = f"Total de Kills: {self.kill_count}"
        kills_surface = font_kills.render(kills_text, True, (255,255,255))
        kills_rect = kills_surface.get_rect(center=self.percent_to_surface(0.5, 0.4))
        self.end_hud_surface.blit(kills_surface, kills_rect)
        
        # Botões com novo estilo
        font_btn = pygame.font.Font(None, 36)
        btn_w, btn_h = 200, 50
        btn1_center = self.percent_to_surface(0.35, 0.55)
        btn2_center = self.percent_to_surface(0.65, 0.55)
        
        # Cores dos botões
        btn_color = (200, 0, 0)
        btn_hover_color = (255, 50, 50)
        
        # Botão Reiniciar
        btn1_rect = pygame.Rect(0, 0, btn_w, btn_h)
        btn1_rect.center = btn1_center
        color1 = btn_hover_color if hover_restart else btn_color
        pygame.draw.rect(self.end_hud_surface, color1, btn1_rect, border_radius=20)
        txt1 = font_btn.render("Reiniciar", True, (255,255,255))
        txt1_rect = txt1.get_rect(center=btn1_center)
        self.end_hud_surface.blit(txt1, txt1_rect)
        
        # Botão Sair
        btn2_rect = pygame.Rect(0, 0, btn_w, btn_h)
        btn2_rect.center = btn2_center
        color2 = btn_hover_color if hover_exit else btn_color
        pygame.draw.rect(self.end_hud_surface, color2, btn2_rect, border_radius=20)
        txt2 = font_btn.render("Sair", True, (255,255,255))
        txt2_rect = txt2.get_rect(center=btn2_center)
        self.end_hud_surface.blit(txt2, txt2_rect)
        
        # Atualizar textura
        self.end_hud_texture.surface = self.end_hud_surface
        self.end_hud_texture.upload_data()
        self.end_hud_mesh.visible = True
        
        # Guardar para detecção de clique
        self._end_btn1_rect = btn1_rect
        self._end_btn2_rect = btn2_rect

    def draw_quadrant_hud(self):
        w, h = self.quadrant_surface.get_size()
        self.quadrant_surface.fill((0,0,0,0))  # Limpar com transparência
        # Linhas pretas finas
        pygame.draw.line(self.quadrant_surface, (0,0,0,255), (w//2, 0), (w//2, h), 1)
        pygame.draw.line(self.quadrant_surface, (0,0,0,255), (0, h//2), (w, h//2), 1)
        # Números dos quadrantes (branco com contorno preto, fonte pequena)
        font = pygame.font.Font(None, 36)
        def draw_text(txt, px, py):
            x, y = self.percent_to_surface(px, py)
            for dx in [-2,0,2]:
                for dy in [-2,0,2]:
                    if dx != 0 or dy != 0:
                        text = font.render(str(txt), True, (0,0,0))
                        rect = text.get_rect(center=(x+dx, y+dy))
                        self.quadrant_surface.blit(text, rect)
            text = font.render(str(txt), True, (255,255,255))
            rect = text.get_rect(center=(x, y))
            self.quadrant_surface.blit(text, rect)
        # Quadrante 1 (top-left)
        draw_text('1', 0.47, 0.47)
        # Quadrante 2 (top-right)
        draw_text('2', 0.53, 0.47)
        # Quadrante 3 (bottom-left)
        draw_text('3', 0.47, 0.53)
        # Quadrante 4 (bottom-right)
        draw_text('4', 0.53, 0.53)
        # Atualizar textura
        self.quadrant_texture.surface = self.quadrant_surface
        self.quadrant_texture.upload_data()

    def update_kills_display(self):
        try:
            # Criar texto do contador de kills
            self.kills_surface.fill((0,0,0))  # Limpar superfície
            kills_text = f"Kills: {self.kill_count}"
            
            # Renderizar o texto
            text_surface = self.font.render(kills_text, True, (255,255,255))
            
            # Centralizar texto na superfície
            x = (self.kills_surface.get_width() - text_surface.get_width()) // 2
            y = (self.kills_surface.get_height() - text_surface.get_height()) // 2
            self.kills_surface.blit(text_surface, (x,y))
            
            # Atualizar textura
            self.kills_texture.surface = self.kills_surface
            self.kills_texture.upload_data()
            
        except Exception as e:
            print(f"Erro ao atualizar contador de kills: {e}")

    def update_health_display(self):
        try:
            # Limpar superfície
            self.health_surface.fill((0,0,0))
            
            # Desenhar fundo da barra (vermelho escuro)
            pygame.draw.rect(self.health_surface, (100, 0, 0), (0, 0, 200, 30))
            
            # Calcular largura da barra de vida
            health_width = int((self.stack_current_health / self.stack_max_health) * 200)
            
            # Desenhar barra de vida (verde)
            pygame.draw.rect(self.health_surface, (0, 255, 0), (0, 0, health_width, 30))
            
            # Adicionar texto com a porcentagem
            health_text = f"{int(self.stack_current_health)}%"
            text_surface = self.font.render(health_text, True, (255, 255, 255))
            
            # Centralizar texto na barra
            x = (self.health_surface.get_width() - text_surface.get_width()) // 2
            y = (self.health_surface.get_height() - text_surface.get_height()) // 2
            self.health_surface.blit(text_surface, (x, y))
            
            # Atualizar textura
            self.health_texture.surface = self.health_surface
            self.health_texture.upload_data()
            
        except Exception as e:
            print(f"Erro ao atualizar barra de vida: {e}")

    def check_character_collision(self):
        """Verifica se os inimigos estão próximos da pilha de instrumentos e aplica dano"""
        # Posição da pilha de instrumentos (centro do mapa)
        stack_pos = np.array([0, 0, 0])  # Ignorar Y
        current_time = pygame.time.get_ticks() / 1000  # Tempo atual em segundos
        
        # Verificar se passou tempo suficiente desde o último dano
        if current_time - self.last_damage_time < self.damage_cooldown:
            return
            
        # Verificar distância de cada personagem até a pilha (apenas XZ)
        for character in self.character_meshes:
            character_pos = np.array(character.global_position)
            character_pos_xz = np.array([character_pos[0], character_pos[2]])
            stack_pos_xz = np.array([stack_pos[0], stack_pos[2]])
            dist = np.linalg.norm(character_pos_xz - stack_pos_xz)
            
            # Se um personagem está muito próximo da pilha
            if dist < 2.5:  # Raio de colisão aumentado
                # Aplicar dano à pilha
                self.stack_current_health = max(0, self.stack_current_health - 10)  # 10 de dano por hit
                self.last_damage_time = current_time
                
                # Atualizar a barra de vida
                self.update_health_display()
                
                # Verificar se a pilha foi destruída
                if self.stack_current_health <= 0:
                    print("A pilha de instrumentos foi destruída!")
                    self.game_over = True
                    self.game_over_reason = "stack_destroyed"
                break  # Sair do loop após aplicar dano

    def update_instrument_message(self):
        """Atualiza a mensagem de novo instrumento disponível"""
        self.instrument_message_surface.fill((0,0,0))
        show = False
        alpha = 255
        
        if self.tuba_message_time is not None:
            elapsed = pygame.time.get_ticks() / 1000 - self.tuba_message_time
            if elapsed < self.tuba_message_duration:
                show = True
                alpha = int(255 * (1 - elapsed / self.tuba_message_duration))
            else:
                self.tuba_message_time = None
                
        if show:
            text = "Novo instrumento disponível!"
            text_surface = self.instrument_message_font.render(text, True, (255, 255, 0))
            text_surface.set_alpha(alpha)
            x = (self.instrument_message_surface.get_width() - text_surface.get_width()) // 2
            y = (self.instrument_message_surface.get_height() - text_surface.get_height()) // 2
            self.instrument_message_surface.blit(text_surface, (x, y))
            self.instrument_message_mesh.visible = True
        else:
            self.instrument_message_mesh.visible = False
            
        self.instrument_message_texture.surface = self.instrument_message_surface
        self.instrument_message_texture.upload_data()

    def update(self):
        # --- TESTE DE QUADRANTES (agora logo no início) ---
        t_pressed = self.input.is_key_down("t")
        if t_pressed and not self.last_t_state:
            self.test_quadrants = not self.test_quadrants
            self.clicked_quadrant = None
            if self.test_quadrants:
                pygame.mouse.set_visible(True)
                pygame.event.set_grab(False)
            else:
                # Voltar ao estado normal
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(True)
        self.last_t_state = t_pressed

        if self.test_quadrants:
            # Congelar tudo, esconder mira e tempo
            self.end_mesh.visible = False
            self.pause_mesh.visible = False
            self.hud_mesh.visible = False
            self.tuba_weapon_mesh.visible = False
            self.timer_mesh.visible = False
            self.tuba_icon_mesh.visible = False
            self.restart_mesh.visible = False
            self.exit_mesh.visible = False
            self.quadrant_mesh.visible = True
            self.draw_quadrant_hud()
            # Processar clique do rato
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mx, my = event.pos
                    w, h = self._screen.get_size()
                    if mx < w//2 and my < h//2:
                        print("Você clicou no quadrante 1")
                    elif mx >= w//2 and my < h//2:
                        print("Você clicou no quadrante 2")
                    elif mx < w//2 and my >= h//2:
                        print("Você clicou no quadrante 3")
                    elif mx >= w//2 and my >= h//2:
                        print("Você clicou no quadrante 4")
            # Renderizar cena normalmente (fundo)
            self.renderer.render(self.scene, self.camera)
            return

        if self.game_over:
            # Mostrar HUD de fim de ronda
            self.end_hud_mesh.visible = True
            self.pause_mesh.visible = False
            self.hud_mesh.visible = False
            self.tuba_weapon_mesh.visible = False
            self.timer_mesh.visible = False
            self.tuba_icon_mesh.visible = False
            self.restart_mesh.visible = False
            self.exit_mesh.visible = False
            self.kills_mesh.visible = False  # Esconder o contador de kills durante o jogo
            
            # Garantir rato visível e libertado
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            
            # Processar eventos do menu de fim de jogo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    screen_w, screen_h = self._screen.get_size()
                    
                    # Calcular posições dos botões
                    btn_w, btn_h = 200, 50
                    btn1_center = (screen_w * 0.35, screen_h * 0.55)
                    btn2_center = (screen_w * 0.65, screen_h * 0.55)
                    
                    # Criar retângulos dos botões
                    btn1_rect = pygame.Rect(0, 0, btn_w, btn_h)
                    btn1_rect.center = btn1_center
                    btn2_rect = pygame.Rect(0, 0, btn_w, btn_h)
                    btn2_rect.center = btn2_center
                    
                    # Verificar clique nos botões
                    if btn1_rect.collidepoint(mx, my):
                        print("Reiniciar clicado!")
                        self.restart_game()
                        return
                    if btn2_rect.collidepoint(mx, my):
                        print("Sair clicado!")
                        pygame.quit()
                        sys.exit()
            
            # Verificar hover
            mx, my = pygame.mouse.get_pos()
            screen_w, screen_h = self._screen.get_size()
            btn1_center = (screen_w * 0.35, screen_h * 0.55)
            btn2_center = (screen_w * 0.65, screen_h * 0.55)
            
            btn1_rect = pygame.Rect(0, 0, 200, 50)
            btn1_rect.center = btn1_center
            btn2_rect = pygame.Rect(0, 0, 200, 50)
            btn2_rect.center = btn2_center
            
            hover_restart = btn1_rect.collidepoint(mx, my)
            hover_exit = btn2_rect.collidepoint(mx, my)
            
            # Desenhar o menu de fim de jogo
            self.draw_end_hud(hover_restart, hover_exit)
            
            # Renderizar a cena
            self.renderer.render(self.scene, self.camera)
            return
        else:
            self.end_hud_mesh.visible = False
            self.quadrant_mesh.visible = False
            self.timer_mesh.visible = True
            self.hud_mesh.visible = True
            self.kills_mesh.visible = True  # Mostrar o contador de kills durante o jogo
            
            # O resto do update normal
            if not self.game_over:
                # Alternar pausa
                if self.input.is_key_down("escape"):
                    self.paused = not self.paused
                    print("Jogo pausado" if self.paused else "Jogo retomado")
                    pygame.mouse.get_rel()  # Limpa o movimento acumulado do rato
                    if self.paused:
                        pygame.mouse.set_visible(True)
                        pygame.event.set_grab(False)
                        self.hud_mesh.visible = False  # Esconde a mira
                        # Colocar o rato no centro da janela
                        screen_center = (self._screen.get_width() // 2, self._screen.get_height() // 2)
                        pygame.mouse.set_pos(screen_center)
                    else:
                        pygame.mouse.set_visible(False)
                        pygame.event.set_grab(True)
                        self.hud_mesh.visible = True   # Mostra a mira

                if not self.paused:
                    # Atualizar timer
                    self.remaining_time -= self.delta_time
                    self.update_timer_display()
                    self.update_kills_display()
                    self.update_health_display()
                    
                    # Verificar colisão com personagens
                    self.check_character_collision()
                    
                    if self.remaining_time <= 0:
                        self.remaining_time = 0
                        self.game_over = True
                        self.game_over_reason = "time"
                        print("Tempo Esgotado!")

                    # Atualizar movimento
                    self.rig.update(self.input, self.delta_time)
                    
                    # Atualizar rotação da câmera com o mouse
                    mouse_movement = pygame.mouse.get_rel()  # Get relative mouse movement
                    self.rig.rotate_y(-mouse_movement[0] * self.mouse_sensitivity * self.delta_time)
                    self.vertical_angle -= mouse_movement[1] * self.mouse_sensitivity * self.delta_time * 60
                    self.vertical_angle = max(-self.max_vertical_angle, min(self.max_vertical_angle, self.vertical_angle))
                    self.camera.local_matrix = Matrix.make_identity()
                    self.camera.rotate_x(math.radians(self.vertical_angle))
                    
                    # Verificar nova posição após movimento
                    new_position = np.array(self.rig.global_position)
                    collided, adjusted_position = self.check_wall_collision(new_position)
                    if collided:
                        self.rig.set_position(adjusted_position.tolist())
                    
                    # Mover personagens automaticamente em direção ao centro da pilha de instrumentos
                    target_pos = np.array([0, 0.25, 0])
                    for character in self.character_meshes:
                        old_pos = np.array(character.global_position)
                        # Calcular direção para a pilha, ignorando o eixo Y
                        target_pos_flat = target_pos.copy()
                        target_pos_flat[1] = old_pos[1]
                        direction = target_pos_flat - old_pos
                        distance = np.linalg.norm(direction)
                        if distance > 0:
                            direction = direction / distance * 0.05  # Mover apenas 0.05 unidades por frame
                            new_pos = old_pos + direction
                            # Verificar colisão com paredes (tal como o jogador)
                            collided, adjusted_position = self.check_wall_collision(new_pos)
                            if collided:
                                new_pos = adjusted_position
                            character.set_position(new_pos.tolist())
                            angle = math.atan2(direction[0], direction[2])
                            angle_degrees = math.degrees(angle)
                            angle_degrees += -90
                            current_pos = character.local_position.copy()
                            character.local_matrix = Matrix.make_identity()
                            character.rotate_y(math.radians(angle_degrees))
                            character.set_position(current_pos)
                    
                    # Dano à pilha de instrumentos se inimigo colidir com ela
                    pilha_centro = np.array([0, 0.25, 0])
                    for character in self.character_meshes:
                        char_pos = np.array(character.global_position)
                        dist = np.linalg.norm(char_pos - pilha_centro)
                        if dist < 1.0:
                            self.stack_current_health = max(0, self.stack_current_health - 10 * self.delta_time)
                            self.update_health_display()
                            # Empurrar inimigo levemente para fora para evitar stuck
                            away = (char_pos - pilha_centro)
                            if np.linalg.norm(away) > 0:
                                away = away / np.linalg.norm(away)
                                character.set_position((pilha_centro + away * 1.2).tolist())
                            if self.stack_current_health <= 0:
                                print("A pilha de instrumentos foi destruída!")
                                self.game_over = True
                                self.game_over_reason = "stack_destroyed"
                            # Não break, para que múltiplos inimigos possam causar dano simultaneamente
                    
                    # Imprimir coordenadas ao pressionar P
                    if self.input.is_key_down("p"):
                        player_pos = self.rig.global_position
                        print(f"Coordenadas do jogador: X={player_pos[0]:.2f}, Y={player_pos[1]:.2f}, Z={player_pos[2]:.2f}")
                    
                    # Processar pulo
                    GROUND_TOLERANCE = 0.05  # tolerância para considerar que está no chão
                    current_position = list(self.rig.global_position)
                    on_ground = abs(current_position[1] - self.initial_height) < GROUND_TOLERANCE

                    # Jump buffer: regista pedido de salto se espaço pressionado
                    if self.input.is_key_down("space") or self.input.is_key_pressed("space"):
                        self.jump_buffered = True

                    # Se está no chão e há pedido de salto, executa salto
                    if on_ground and self.jump_buffered and not self.is_jumping:
                        self.is_jumping = True
                        self.jump_velocity = self.initial_jump_velocity
                        self.jump_buffered = False  # Consome o salto

                    # Se o espaço foi largado, limpa o buffer
                    if not self.input.is_key_pressed("space"):
                        self.jump_buffered = False

                    if self.is_jumping:
                        self.jump_velocity -= self.gravity * self.delta_time
                        current_position[1] += self.jump_velocity * self.delta_time
                        # Se aterrou ou passou do chão
                        if current_position[1] <= self.initial_height:
                            current_position[1] = self.initial_height
                            self.is_jumping = False
                            self.jump_velocity = 0
                        self.rig.set_position(current_position)
                    
                    # Animar os instrumentos quando estiverem visíveis
                    if self.tuba_mesh.visible:
                        # Atualizar tempo de animação
                        self.animation_time += self.delta_time
                        
                        # Calcular nova posição Y usando função seno
                        float_offset = math.sin(self.animation_time * self.float_speed) * self.float_amplitude
                        
                        # Atualizar posição da tuba
                        new_y = self.tuba_initial_position[1] + float_offset
                        self.tuba_mesh.set_position([
                            self.tuba_initial_position[0],
                            new_y,
                            self.tuba_initial_position[2]
                        ])
                        
                        # Rotacionar a tuba em torno do eixo Y
                        self.tuba_mesh.rotate_y(self.rotation_speed * self.delta_time)
                        
                        # Atualizar posição da guitarra (mesmo movimento)
                        new_y = self.guitar_initial_position[1] + float_offset
                        self.guitar_mesh.set_position([
                            self.guitar_initial_position[0],
                            new_y,
                            self.guitar_initial_position[2]
                        ])
                        
                        # Rotacionar a guitarra em torno do eixo Y
                        self.guitar_mesh.rotate_z(self.rotation_speed * self.delta_time)
                    
                    # Verificar colisão com a tuba
                    if not self.has_tuba and not self.has_guitar:  # Só pode pegar a tuba se não tiver nenhum instrumento
                        tuba_pos = np.array(self.tuba_mesh.global_position)
                        player_pos = np.array(self.rig.global_position)
                        dist = np.linalg.norm(tuba_pos - player_pos)
                        now = pygame.time.get_ticks() / 1000
                        can_pickup = (
                            self.tuba_drop_time is None or
                            (now - self.tuba_drop_time) >= 2.0
                        )
                        # Só pode apanhar se a tuba estiver visível
                        if self.tuba_mesh.visible and dist < 1.0 and can_pickup:
                            self.has_tuba = True
                            self.tuba_mesh.visible = False
                            self.tuba_pickup_time = now
                            print('Tuba apanhada!')
                    
                    # Verificar colisão com a guitarra
                    if not self.has_guitar and not self.has_tuba:  # Só pode pegar a guitarra se não tiver nenhum instrumento
                        guitar_pos = np.array(self.guitar_mesh.global_position)
                        player_pos = np.array(self.rig.global_position)
                        dist = np.linalg.norm(guitar_pos - player_pos)
                        now = pygame.time.get_ticks() / 1000
                        can_pickup = (
                            self.guitar_drop_time is None or
                            (now - self.guitar_drop_time) >= 2.0
                        )
                        if dist < 1.0 and can_pickup:
                            self.has_guitar = True
                            self.guitar_mesh.visible = False
                            self.guitar_pickup_time = now
                            print('Guitarra apanhada!')
                    
                    # Largar a tuba ao pressionar G
                    keys = pygame.key.get_pressed()
                    if self.has_tuba and keys[pygame.K_g]:
                        self.has_tuba = False
                        self.tuba_weapon_mesh.visible = False
                        
                        # Obter posição e direção da câmera
                        player_pos = np.array(self.rig.global_position)
                        camera_matrix = self.camera.global_matrix
                        camera_direction = np.array([-camera_matrix[0][2], -camera_matrix[1][2], -camera_matrix[2][2]])
                        
                        # Posicionar a tuba 1 unidade à frente do jogador
                        drop_pos = player_pos + camera_direction * 1.0
                        drop_pos[1] = 1.0  # Altura fixa
                        
                        # Atualizar a posição inicial da tuba para a nova posição
                        self.tuba_initial_position = drop_pos.tolist()
                        
                        # Resetar a tuba
                        self.tuba_mesh.local_matrix = Matrix.make_identity()
                        self.tuba_mesh.set_position(drop_pos.tolist())
                        self.tuba_mesh.scale(0.2)
                        
                        # Calcular ângulo em Y baseado na direção da câmera
                        y_angle = math.atan2(camera_direction[0], camera_direction[2])
                        self.tuba_mesh.rotate_y(y_angle)
                        
                        # Resetar o tempo de animação para começar do zero
                        self.animation_time = 0
                        
                        self.tuba_mesh.visible = True
                        self.tuba_drop_time = pygame.time.get_ticks() / 1000
                        print("Tuba largada!")
                    
                    # Largar a guitarra ao pressionar Gdddddw
                    if self.has_guitar and keys[pygame.K_g]:
                        self.has_guitar = False
                        self.guitar_weapon_mesh.visible = False
                        
                        # Obter posição e direção da câmera
                        player_pos = np.array(self.rig.global_position)
                        camera_matrix = self.camera.global_matrix
                        camera_direction = np.array([-camera_matrix[0][2], -camera_matrix[1][2], -camera_matrix[2][2]])
                        
                        # Posicionar a guitarra 1 unidade à frente do jogador
                        drop_pos = player_pos + camera_direction * 1.0
                        drop_pos[1] = 0.3  # Altura fixa
                        
                        # Atualizar a posição inicial da guitarra para a nova posição
                        self.guitar_initial_position = drop_pos.tolist()
                        
                        # Resetar a guitarra
                        self.guitar_mesh.local_matrix = Matrix.make_identity()
                        self.guitar_mesh.set_position(drop_pos.tolist())
                        self.guitar_mesh.scale(0.5)
                        self.guitar_mesh.rotate_x(math.radians(-90))
                        self.guitar_mesh.rotate_z(math.radians(90))
                        
                        # Resetar o tempo de animação para começar do zero
                        self.animation_time = 0
                        
                        self.guitar_mesh.visible = True
                        self.guitar_drop_time = pygame.time.get_ticks() / 1000
                        print("Guitarra largada!")
                    
                    # Só permitir disparar se tiver a tuba ou a guitarra
                    if self.has_tuba or self.has_guitar:
                        mouse_buttons = pygame.mouse.get_pressed()
                        current_time = pygame.time.get_ticks() / 1000  # Converter para segundos
                        
                        if mouse_buttons[0]:  # Se o botão do mouse está pressionado
                            if self.has_tuba and (current_time - self.last_shot_time) >= self.shot_cooldown:
                                self.create_bullet()
                                self.last_shot_time = current_time
                            elif self.has_guitar and (current_time - self.last_guitar_shot_time) >= self.guitar_shot_cooldown:
                                self.create_bullet()
                                self.last_guitar_shot_time = current_time
                    
                    # Atualizar as balas
                    self.update_bullets(self.delta_time)

                    # Calcular a intensidade da luz usando seno
                    time_now = pygame.time.get_ticks() / 1000.0
                    intensity = abs(math.sin(time_now * 2.0))
                    base_color = [0.0, 2.0, 8.0]
                    self.tuba_light._color = [
                        base_color[0] * intensity,
                        base_color[1] * intensity,
                        base_color[2] * intensity
                    ]

                    self.update_tuba_icon()
                    self.update_guitar_icon()
                    # Mostrar a tuba como arma (em frente à câmara)
                    self.tuba_weapon_mesh.visible = self.has_tuba
                    # Mostrar a guitarra como arma (em frente à câmara)
                    self.guitar_weapon_mesh.visible = self.has_guitar
                
                # Atualizar respawn dos personagens
                current_time = pygame.time.get_ticks() / 1000.0
                characters_to_respawn = []
                
                for respawn_data in self.respawning_characters:
                    character, initial_position, respawn_time = respawn_data
                    respawn_time -= self.delta_time
                    
                    if respawn_time <= 0:
                        # Recriar o personagem na posição inicial
                        character.set_position(initial_position)
                        self.scene.add(character)
                        self.character_meshes.append(character)
                        characters_to_respawn.append(respawn_data)
                        print("Personagem respawnado!")
                    else:
                        # Atualizar o tempo restante
                        self.respawning_characters[self.respawning_characters.index(respawn_data)] = (character, initial_position, respawn_time)
                
                # Remover personagens que já respawnaram da lista
                for respawn_data in characters_to_respawn:
                    self.respawning_characters.remove(respawn_data)

                # Renderizar a cena
                self.renderer.render(self.scene, self.camera)

                # Atualizar as ocarinas dropadas
                self.update_ocarinas(self.delta_time)

                # Verificar coleta de ocarinas
                self.check_ocarina_pickup()
                
                # Verificar lançamento de granada
                if self.input.is_key_down("q"):
                    self.create_grenade()
                
                # Atualizar granadas
                self.update_grenades(self.delta_time)

                # Atualizar notas musicais da explosão
                self.update_explosion_notes(self.delta_time)

            # Atualizar o texto de pausa SEMPRE no final do update
            self.update_pause_display()

    def restart_game(self):
        # Resetar todas as variáveis do jogo ao estado inicial
        self.remaining_time = self.total_time
        self.game_over = False
        self.game_over_reason = None
        self.paused = False
        self.has_tuba = False
        self.tuba_pickup_time = None
        self.tuba_drop_time = None
        self.tuba_mesh.visible = True
        self.tuba_weapon_mesh.visible = False
        self.rig.set_position([0.54, 1.00, -18.90])  # Nova posição inicial do jogador
        self.vertical_angle = 0
        self.camera.local_matrix = Matrix.make_identity()
        self.camera.rotate_x(math.radians(self.vertical_angle))
        self.bullets.clear()
        self.kill_count = 0
        self.stack_current_health = self.stack_max_health  # Resetar vida
        self.update_timer_display()
        self.update_pause_display()
        self.update_tuba_icon()
        self.update_guitar_icon()
        self.update_kills_display()
        self.update_health_display()  # Atualizar barra de vida

    def __del__(self):
        # Restaurar configurações do mouse ao fechar
        try:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        except:
            pass

    def create_ocarina_drop(self, position):
        """Cria uma ocarina dropada na posição especificada"""
        ocarina_mesh = Mesh(self.ocarina_geometry, self.ocarina_material)
        ocarina_mesh.set_position(position)
        ocarina_mesh.scale(0.2)  # Ajustar tamanho conforme necessário
        self.scene.add(ocarina_mesh)
        self.dropped_ocarinas.append({
            "mesh": ocarina_mesh,
            "initial_position": position.copy(),
            "animation_time": 0
        })

    def update_ocarinas(self, delta_time):
        """Atualiza a animação das ocarinas dropadas"""
        for ocarina in self.dropped_ocarinas:
            # Atualizar tempo de animação
            ocarina["animation_time"] += delta_time
            
            # Calcular nova posição Y usando função seno
            float_offset = math.sin(ocarina["animation_time"] * self.float_speed) * self.float_amplitude
            
            # Atualizar posição da ocarina
            new_y = ocarina["initial_position"][1] + float_offset
            ocarina["mesh"].set_position([
                ocarina["initial_position"][0],
                new_y,
                ocarina["initial_position"][2]
            ])
            
            # Rotacionar a ocarina em torno do eixo Y
            ocarina["mesh"].rotate_y(self.rotation_speed * delta_time)

    def create_grenade(self):
        """Cria uma granada (ocarina) que explode após um tempo"""
        if self.ocarina_count <= 0:
            return
            
        current_time = pygame.time.get_ticks() / 1000
        if current_time - self.last_grenade_time < self.grenade_cooldown:
            return
            
        self.last_grenade_time = current_time
        self.ocarina_count -= 1
        
        # Tocar o som da ocarina ao lançar
        self.ocarina_sound.play()
        
        # Obter posição e direção da câmera
        player_pos = np.array(self.rig.global_position)
        camera_matrix = self.camera.global_matrix
        camera_direction = np.array([-camera_matrix[0][2], -camera_matrix[1][2], -camera_matrix[2][2]])
        
        # Criar a granada
        grenade_mesh = Mesh(self.ocarina_geometry, self.ocarina_material)
        grenade_mesh.scale(0.2)
        
        # Posicionar a granada um pouco à frente do jogador
        throw_pos = player_pos + camera_direction * 1.0
        throw_pos[1] += 1.0  # Um pouco acima do jogador
        grenade_mesh.set_position(throw_pos.tolist())
        
        # Adicionar à cena
        self.scene.add(grenade_mesh)
        
        # Adicionar à lista de granadas ativas
        self.active_grenades.append({
            "mesh": grenade_mesh,
            "position": throw_pos,
            "velocity": camera_direction * 10.0,  # Velocidade inicial
            "lifetime": 2.0,  # Tempo até explodir
            "explosion_radius": 5.0,  # Raio da explosão
            "has_hit": False  # Flag para controlar se já atingiu algo
        })
        
        print(f"Granada lançada! Ocarinas restantes: {self.ocarina_count}")

    def create_explosion_notes(self, position):
        """Cria notas musicais na explosão"""
        # Tocar o som de quebra da ocarina
        self.ocarina_break.play()
        
        num_notes = 8  # Número de notas na explosão
        for i in range(num_notes):
            # Criar uma nota musical
            note_mesh = Mesh(self.ocarina_geometry, self.ocarina_material)
            note_mesh.scale(0.1)  # Menor que a ocarina original
            
            # Posicionar no centro da explosão
            note_mesh.set_position(position.tolist())
            
            # Calcular direção aleatória
            angle = (i / num_notes) * 2 * math.pi
            direction = np.array([
                math.cos(angle),
                random.uniform(0.5, 1.0),  # Componente Y sempre para cima
                math.sin(angle)
            ])
            
            # Normalizar e escalar a velocidade
            direction = direction / np.linalg.norm(direction) * random.uniform(5.0, 8.0)
            
            # Adicionar à cena
            self.scene.add(note_mesh)
            
            # Adicionar à lista de notas
            self.explosion_notes.append({
                "mesh": note_mesh,
                "position": position.copy(),
                "velocity": direction,
                "lifetime": 1.0,  # Tempo de vida da nota
                "rotation_speed": random.uniform(2.0, 5.0)  # Velocidade de rotação aleatória
            })

    def update_explosion_notes(self, delta_time):
        """Atualiza a posição e rotação das notas musicais"""
        notes_to_remove = []
        
        for note in self.explosion_notes:
            # Atualizar posição com gravidade
            note["velocity"][1] -= 9.8 * delta_time  # Gravidade
            note["position"] += note["velocity"] * delta_time
            note["mesh"].set_position(note["position"].tolist())
            
            # Rotacionar a nota
            note["mesh"].rotate_y(note["rotation_speed"] * delta_time)
            
            # Atualizar tempo de vida
            note["lifetime"] -= delta_time
            
            # Remover nota se o tempo acabou
            if note["lifetime"] <= 0:
                notes_to_remove.append(note)
        
        # Remover notas expiradas
        for note in notes_to_remove:
            self.scene.remove(note["mesh"])
            self.explosion_notes.remove(note)

    def update_grenades(self, delta_time):
        """Atualiza a posição das granadas e verifica explosões"""
        grenades_to_remove = []
        
        for grenade in self.active_grenades:
            # Atualizar posição com gravidade
            grenade["velocity"][1] -= 9.8 * delta_time  # Gravidade
            grenade["position"] += grenade["velocity"] * delta_time
            grenade["mesh"].set_position(grenade["position"].tolist())
            
            # Rotacionar a granada
            grenade["mesh"].rotate_y(self.rotation_speed * delta_time)
            
            # Verificar colisão com o chão
            if grenade["position"][1] <= 0.2 and not grenade["has_hit"]:  # Altura do chão
                grenade["has_hit"] = True
                self.create_explosion_notes(grenade["position"])
                # Verificar inimigos no raio da explosão
                explosion_pos = grenade["position"]
                characters_to_remove = []
                for character in self.character_meshes:
                    character_pos = np.array(character.global_position)
                    dist = np.linalg.norm(explosion_pos - character_pos)
                    if dist < grenade["explosion_radius"]:
                        characters_to_remove.append(character)
                        # Incrementar kills
                        self.kill_count += 1
                        self.update_kills_display()
                        # Adicionar à lista de respawn
                        random_position = random.choice(self.character_positions)
                        self.respawning_characters.append((character, random_position, self.respawn_delay))
                
                # Remover personagens atingidos
                for character in characters_to_remove:
                    self.scene.remove(character)
                    self.character_meshes.remove(character)
                
                grenades_to_remove.append(grenade)
                continue
            
            # Verificar colisão com inimigos
            if not grenade["has_hit"]:
                for character in self.character_meshes:
                    character_pos = np.array(character.global_position)
                    dist = np.linalg.norm(grenade["position"] - character_pos)
                    if dist < 1.0:  # Distância de colisão
                        grenade["has_hit"] = True
                        self.create_explosion_notes(grenade["position"])
                        # Verificar inimigos no raio da explosão
                        explosion_pos = grenade["position"]
                        characters_to_remove = []
                        for other_character in self.character_meshes:
                            other_pos = np.array(other_character.global_position)
                            other_dist = np.linalg.norm(explosion_pos - other_pos)
                            if other_dist < grenade["explosion_radius"]:
                                characters_to_remove.append(other_character)
                                # Incrementar kills
                                self.kill_count += 1
                                self.update_kills_display()
                                # Adicionar à lista de respawn
                                random_position = random.choice(self.character_positions)
                                self.respawning_characters.append((other_character, random_position, self.respawn_delay))
                        
                        # Remover personagens atingidos
                        for other_character in characters_to_remove:
                            self.scene.remove(other_character)
                            self.character_meshes.remove(other_character)
                        
                        grenades_to_remove.append(grenade)
                        break
            
            # Atualizar tempo de vida
            grenade["lifetime"] -= delta_time
            
            # Verificar se explodiu por tempo
            if grenade["lifetime"] <= 0:
                self.create_explosion_notes(grenade["position"])
                # Verificar inimigos no raio da explosão
                explosion_pos = grenade["position"]
                characters_to_remove = []
                for character in self.character_meshes:
                    character_pos = np.array(character.global_position)
                    dist = np.linalg.norm(explosion_pos - character_pos)
                    if dist < grenade["explosion_radius"]:
                        characters_to_remove.append(character)
                        # Incrementar kills
                        self.kill_count += 1
                        self.update_kills_display()
                        # Adicionar à lista de respawn
                        random_position = random.choice(self.character_positions)
                        self.respawning_characters.append((character, random_position, self.respawn_delay))
                
                # Remover personagens atingidos
                for character in characters_to_remove:
                    self.scene.remove(character)
                    self.character_meshes.remove(character)
                
                grenades_to_remove.append(grenade)
        
        # Remover granadas que explodiram
        for grenade in grenades_to_remove:
            self.scene.remove(grenade["mesh"])
            self.active_grenades.remove(grenade)

    def check_ocarina_pickup(self):
        """Verifica se o jogador está próximo o suficiente para apanhar uma ocarina"""
        player_pos = np.array(self.rig.global_position)
        ocarinas_to_remove = []
        
        for ocarina in self.dropped_ocarinas:
            ocarina_pos = np.array(ocarina["mesh"].global_position)
            dist = np.linalg.norm(player_pos - ocarina_pos)
            
            if dist < 1.0:  # Distância de coleta
                self.ocarina_count += 1
                self.scene.remove(ocarina["mesh"])
                ocarinas_to_remove.append(ocarina)
                print(f"Ocarina apanhada! Total: {self.ocarina_count}. Pressione Q para lançar como granada.")
                break
        
        # Remover ocarinas apanhadas
        for ocarina in ocarinas_to_remove:
            self.dropped_ocarinas.remove(ocarina)

    # Adicionar nova função para criar explosões de foguetes
    def create_rocket_explosion(self, position, color):
        """Cria uma explosão de notas pequenas quando um foguete colide"""
        # Tocar um som mais potente
        note_names = list(self.notes.keys())
        selected_note = random.choice(note_names)
        sound = self.notes[selected_note]
        sound.set_volume(0.8)  # Volume alto
        sound.play()
        
        # Número de notas na explosão
        num_notes = 16
        
        # Número de fontes de luz na cena (Ambient + Directional + Tuba light = 3)
        num_lights = 3
        
        # Escolher a geometria para as notas da explosão
        if hasattr(self, 'note_geometry') and self.note_geometry is not None:
            geometry = self.note_geometry
            texture = self.note_texture
        else:
            geometry = self.bullet_geometry
            texture = self.bullet_texture
        
        for i in range(num_notes):
            # Criar cor baseada na cor do foguete, mas com variação
            note_color = [
                min(1.0, color[0]*2.0 + random.uniform(-0.2, 0.2)),
                min(1.0, color[1]*2.0 + random.uniform(-0.2, 0.2)),
                min(1.0, color[2]*2.0 + random.uniform(-0.2, 0.2))
            ]
            
            # Criar material para a nota com brilho
            note_material = PhongMaterial(
                texture=texture,
                property_dict={
                    "baseColor": note_color,
                    "specularStrength": 2.0,
                    "shininess": 12.0,
                    "doubleSide": True
                },
                number_of_light_sources=num_lights
            )
            
            # Criar mesh da nota pequena
            note_mesh = Mesh(geometry, note_material)
            note_mesh.scale(0.15)  # Tamanho adequado
            
            # Posicionar no ponto da explosão
            note_mesh.set_position(position)
            
            # Calcular direção aleatória em 3D
            # Usar distribuição uniforme na esfera
            theta = random.uniform(0, 2 * math.pi)  # Ângulo horizontal
            phi = random.uniform(0, math.pi)        # Ângulo vertical
            
            # Conversão de coordenadas esféricas para cartesianas
            direction = [
                math.sin(phi) * math.cos(theta),
                math.sin(phi) * math.sin(theta),
                math.cos(phi)
            ]
            
            # Velocidade aleatória para cada nota
            speed = random.uniform(4.0, 10.0)
            
            # Rotação aleatória
            note_mesh.rotate_x(random.uniform(0, 2*math.pi))
            note_mesh.rotate_y(random.uniform(0, 2*math.pi))
            note_mesh.rotate_z(random.uniform(0, 2*math.pi))
            
            # Adicionar à cena
            self.scene.add(note_mesh)
            
            # Adicionar à lista de balas com tempo de vida adequado
            self.bullets.append({
                "mesh": note_mesh,
                "direction": direction,
                "lifetime": random.uniform(1.0, 2.0),  # Tempo de vida adequado
                "is_rocket": False,
                "is_particle": True,  # Marcar como partícula de explosão
                "velocity": speed,  # Velocidade específica para esta partícula
                "current_scale": 0.15,  # Tamanho inicial para efeito de encolhimento
                "rotation_speed": [  # Velocidades de rotação em cada eixo
                    random.uniform(-8.0, 8.0),
                    random.uniform(-8.0, 8.0),
                    random.uniform(-8.0, 8.0)
                ]
            })
        
        # Adicionar um flash de luz no ponto da explosão
        explosion_mesh = Mesh(geometry, PhongMaterial(
            texture=texture,
            property_dict={
                "baseColor": [1.0, 1.0, 1.0],  # Branco brilhante
                "specularStrength": 5.0,
                "shininess": 5.0,
                "doubleSide": True
            },
            number_of_light_sources=num_lights
        ))
        explosion_mesh.scale(0.3)  # Tamanho maior para o flash
        explosion_mesh.set_position(position)
        self.scene.add(explosion_mesh)
        
        # Adicionar à lista com tempo de vida curto
        self.bullets.append({
            "mesh": explosion_mesh,
            "direction": [0, 0, 0],  # Não se move
            "lifetime": 0.3,  # Tempo curto
            "is_rocket": False,
            "is_particle": True,
            "velocity": 0,  # Sem velocidade
            "current_scale": 0.3,  # Tamanho inicial
            "is_central_explosion": True  # Marcar como explosão central
        })

    # Adicionar nova função para replicar a explosão da ocarina
    def create_grenade_explosion(self, position):
        """Cria uma explosão de notas musicais quando uma nota colide, igual à explosão da ocarina"""
        # Tocar o som de quebra da ocarina
        self.ocarina_break.play()
        
        # Usar a geometria da nota musical para a explosão
        geometry = self.note_geometry
        texture = self.note_texture
        
        # Garantir que position seja um array numpy
        if not isinstance(position, np.ndarray):
            position = np.array(position)
        
        num_notes = 8  # Número de notas na explosão (igual à ocarina)
        for i in range(num_notes):
            # Criar uma nota musical
            note_mesh = Mesh(geometry, PhongMaterial(
                texture=texture,
                property_dict={
                    "baseColor": [1.0, 1.0, 1.0],  # Cor base branca
                    "specularStrength": 2.0,
                    "shininess": 16.0
                },
                number_of_light_sources=3
            ))
            note_mesh.scale(0.15)  # Menor que a nota original
            
            # Posicionar no centro da explosão
            if hasattr(position, 'tolist'):
                note_mesh.set_position(position.tolist())
            else:
                note_mesh.set_position(position)
            
            # Calcular direção aleatória
            angle = (i / num_notes) * 2 * math.pi
            direction = np.array([
                math.cos(angle),
                random.uniform(0.5, 1.0),  # Componente Y sempre para cima
                math.sin(angle)
            ])
            
            # Normalizar e escalar a velocidade
            direction = direction / np.linalg.norm(direction) * random.uniform(5.0, 8.0)
            
            # Adicionar à cena
            self.scene.add(note_mesh)
            
            # Adicionar à lista de notas
            self.explosion_notes.append({
                "mesh": note_mesh,
                "position": position.copy() if hasattr(position, 'copy') else np.array(position),
                "velocity": direction,
                "lifetime": 1.0,  # Tempo de vida da nota
                "rotation_speed": random.uniform(2.0, 5.0)  # Velocidade de rotação aleatória
            })

# Executar o jogo
ArenaShooterCollision().run() 