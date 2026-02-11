#!/usr/bin/python3
import pygame
import sys
import os
import importlib

class MainMenu:
    def __init__(self):
        pygame.init()
        # Obter o tamanho da tela
        screen_info = pygame.display.Info()
        self.width = screen_info.current_w
        self.height = screen_info.current_h
        
        # Inicializar a tela com fullscreen
        if sys.platform == 'darwin':  # macOS
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
            # Centralizar a janela
            os.environ['SDL_VIDEO_CENTERED'] = '1'
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
            
        pygame.display.set_caption("Music Maniac")
        
        # Cores
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (128, 128, 128)
        self.RED = (200, 0, 0)
        self.RED_HOVER = (255, 50, 50)
        
        # Carregar imagem de fundo
        try:
            self.bg_image = pygame.image.load("images/hell.gif")
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")
            self.bg_image = None
        
        # Fontes
        self.title_font = pygame.font.Font(None, 74)
        self.button_font = pygame.font.Font(None, 36)
        self.manual_font = pygame.font.Font(None, 24)
        
        # Botões - Ajustados para o centro da tela
        button_width = 300
        button_height = 50
        center_x = self.width // 2 - button_width // 2
        
        self.buttons = {
            'ataque': pygame.Rect(center_x, self.height//2 - 150, button_width, button_height),
            'defesa': pygame.Rect(center_x, self.height//2 - 50, button_width, button_height),
            'manual': pygame.Rect(center_x, self.height//2 + 50, button_width, button_height),
            'exit': pygame.Rect(center_x, self.height//2 + 150, button_width, button_height)
        }
        
        self.running = True
        self.showing_manual = False
        
    def draw_button(self, text, rect, hover=False):
        # Desenhar o fundo do botão
        color = self.RED_HOVER if hover else self.RED
        pygame.draw.rect(self.screen, color, rect, border_radius=20)
        
        # Desenhar o texto do botão
        text_surface = self.button_font.render(text, True, self.WHITE)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
        
    def draw_manual(self):
        # Criar uma superfície semi-transparente para o fundo do manual
        overlay = pygame.Surface((self.width, self.height))
        overlay.fill(self.BLACK)
        overlay.set_alpha(200)
        self.screen.blit(overlay, (0, 0))
        
        # Título do manual
        title = self.title_font.render("MANUAL DE CONTROLOS", True, self.WHITE)
        title_rect = title.get_rect(center=(self.width/2, 100))
        self.screen.blit(title, title_rect)
        
        # Conteúdo do manual
        manual_text = [
            "MOVIMENTAÇÃO:",
            "W, A, S, D - Movimento do jogador",
            "ESPAÇO - Pular",
            "",
            "ARMAS E AÇÕES:",
            "BOTÃO ESQUERDO DO MOUSE - Atirar",
            "Q - Usar Ocarina (se tiver)",
            "G - Largar arma",
            "",
            "OUTROS CONTROLOS:",
            "ESC - Pausar jogo"
        ]
        
        y_offset = 200
        for line in manual_text:
            text = self.manual_font.render(line, True, self.WHITE)
            text_rect = text.get_rect(center=(self.width/2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 30
        
        # Botão para voltar
        back_button = pygame.Rect(self.width//2 - 100, self.height - 100, 200, 50)
        self.draw_button("Voltar", back_button)
        return back_button
        
    def run(self):
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.showing_manual:
                        back_button = pygame.Rect(self.width//2 - 100, self.height - 100, 200, 50)
                        if back_button.collidepoint(mouse_pos):
                            self.showing_manual = False
                    else:
                        if self.buttons['ataque'].collidepoint(mouse_pos):
                            # Importar e iniciar o jogo de ataque
                            arena_module = importlib.import_module('arena_shooter_collision')
                            game = arena_module.ArenaShooterCollision()
                            game.run()
                        elif self.buttons['defesa'].collidepoint(mouse_pos):
                            # Importar e iniciar o jogo de defesa
                            armazem_module = importlib.import_module('armazem')
                            game = armazem_module.ArenaShooterCollision()
                            game.run()
                        elif self.buttons['manual'].collidepoint(mouse_pos):
                            self.showing_manual = True
                        elif self.buttons['exit'].collidepoint(mouse_pos):
                            self.running = False
            
            # Desenhar fundo
            if self.bg_image:
                self.screen.blit(self.bg_image, (0, 0))
            else:
                self.screen.fill(self.BLACK)
            
            if self.showing_manual:
                back_button = self.draw_manual()
                # Verificar hover no botão voltar
                if back_button.collidepoint(mouse_pos):
                    self.draw_button("Voltar", back_button, True)
            else:
                # Desenhar título
                title = self.title_font.render("Music Maniac", True, self.BLACK)
                title_rect = title.get_rect(center=(self.width/2, self.height//4))
                self.screen.blit(title, title_rect)
                
                # Desenhar botões
                for button_name, rect in self.buttons.items():
                    hover = rect.collidepoint(mouse_pos)
                    if button_name == 'ataque':
                        text = "Ataque Musical"
                    elif button_name == 'defesa':
                        text = "Defesa da Música"
                    elif button_name == 'manual':
                        text = "Manual de Controlos"
                    else:
                        text = "Sair"
                    self.draw_button(text, rect, hover)
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    MainMenu().run() 