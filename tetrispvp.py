import pygame
import random
import sys

# ===== CONFIGURAÇÃO INICIAL =====
pygame.init()  # Liga o Pygame

# Dimensões da tela e do grid do Tetris
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
GRID_WIDTH = 10   # 10 colunas
GRID_HEIGHT = 20  # 20 linhas
CELL_SIZE = 30    # Tamanho de cada bloco

# Cores (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
GARBAGE_COLOR = (60, 60, 80)  # Cor do "lixo" (ataque)

# Cores para cada tipo de peça
COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]

# Formato das 7 peças clássicas do Tetris
SHAPES = [
    [[1, 1, 1, 1]],  # I (linha)
    [[1, 1],         # O (quadrado)
     [1, 1]],
    [[0, 1, 0],      # T
     [1, 1, 1]],
    [[1, 0, 0],      # L
     [1, 1, 1]],
    [[0, 0, 1],      # J (L invertido)
     [1, 1, 1]],
    [[0, 1, 1],      # S
     [1, 1, 0]],
    [[1, 1, 0],      # Z
     [0, 1, 1]]
]

# ===== CLASSE DAS PEÇAS =====
class Piece:
    """Representa uma peça do Tetris (forma + cor + posição)"""
    def __init__(self, shape, color):
        self.shape = shape      # Matriz da peça
        self.color = color      # Cor correspondente
        self.x = GRID_WIDTH // 2 - len(shape[0]) // 2  # Posição X inicial
        self.y = 0              # Posição Y inicial (topo)
    
    def rotate(self):
        """Rotaciona a matriz 90 graus no sentido horário"""
        rotated = list(zip(*self.shape[::-1]))
        return [list(row) for row in rotated]

# ===== CLASSE DO JOGADOR (Cada jogador tem um grid e peças) =====
class Player:
    """Gerencia o estado de um jogador: grid, peça atual, pontuação, etc."""
    def __init__(self, x, y, player_id):
        self.x = x                  # Posição X na tela
        self.y = y                  # Posição Y na tela
        self.player_id = player_id  # 1 ou 2
        
        # Grid do jogador (20x10), inicialmente vazio (preto)
        self.grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        self.current_piece = None   # Peça que está caindo
        self.next_piece = None      # Próxima peça (pré-visualização)
        self.last_piece_index = -1  # Evita repetir a mesma peça seguida
        self.score = 0              # Pontuação atual
        self.total_lines = 0        # Total de linhas eliminadas
        self.game_over = False      # Estado do jogo
        self.pending_attack = 0     # Quantidade de lixo a enviar
        self.last_fall_time = 0     # Último tempo de queda automática
        self.fall_speed = 500       # Velocidade de queda (ms)
        
        self.spawn_new_piece()      # Cria a primeira peça
    
    def get_random_piece_unique(self):
        """Garante que a peça não repete a última que saiu"""
        available_indices = [i for i in range(len(SHAPES)) if i != self.last_piece_index]
        idx = random.choice(available_indices)
        self.last_piece_index = idx
        shape = [row[:] for row in SHAPES[idx]]
        return Piece(shape, COLORS[idx])
    
    def spawn_new_piece(self):
        """Gera uma nova peça (usa a próxima armazenada)"""
        if self.next_piece is None:
            self.next_piece = self.get_random_piece_unique()
        
        self.current_piece = self.next_piece
        self.next_piece = self.get_random_piece_unique()
        self.current_piece.x = GRID_WIDTH // 2 - len(self.current_piece.shape[0]) // 2
        self.current_piece.y = 0
        
        if self.collision():  # Se já bate no topo, fim de jogo
            self.game_over = True
    
    def get_ghost_position(self):
        """Calcula onde a peça vai parar (posição fantasma)"""
        if not self.current_piece:
            return 0
        
        ghost_y = self.current_piece.y
        while True:
            if self.check_collision_at(self.current_piece.x, ghost_y + 1, self.current_piece.shape):
                break
            ghost_y += 1
        return ghost_y
    
    def check_collision_at(self, x, y, shape):
        """Verifica se a peça colide com o grid ou bordas numa posição específica"""
        for row_idx, row in enumerate(shape):
            for col_idx, cell in enumerate(row):
                if cell:
                    grid_x = x + col_idx
                    grid_y = y + row_idx
                    
                    # Fora da tela (laterais ou chão)
                    if grid_x < 0 or grid_x >= GRID_WIDTH or grid_y >= GRID_HEIGHT:
                        return True
                    
                    # Colisão com peças já fixadas
                    if grid_y >= 0 and self.grid[grid_y][grid_x] != BLACK:
                        return True
        return False
    
    def collision(self):
        """Verifica colisão da peça atual"""
        return self.check_collision_at(self.current_piece.x, self.current_piece.y, self.current_piece.shape)
    
    def move(self, dx, dy):
        """Move a peça (dx=horizontal, dy=vertical). Retorna True se moveu"""
        self.current_piece.x += dx
        self.current_piece.y += dy
        
        if self.collision():  # Desfaz movimento se colidir
            self.current_piece.x -= dx
            self.current_piece.y -= dy
            if dy == 1:  # Se moveu pra baixo e colidiu, fixa a peça
                self.lock_piece()
            return False
        return True
    
    def rotate_piece(self):
        """Tenta rotacionar a peça (desfaz se colidir)"""
        original_shape = self.current_piece.shape
        self.current_piece.shape = self.current_piece.rotate()
        
        if self.collision():
            self.current_piece.shape = original_shape
    
    def drop_piece(self):
        """Abaixa a peça até o fundo (queda instantânea)"""
        while self.move(0, 1):
            pass
    
    def count_garbage_lines(self):
        """Conta quantas linhas de lixo existem no grid"""
        count = 0
        for y in range(GRID_HEIGHT):
            if self.grid[y][0] == GARBAGE_COLOR:
                count += 1
        return count
    
    def remove_garbage_lines(self, amount):
        """Remove linhas de lixo (mecânica de defesa)"""
        removed = 0
        y = GRID_HEIGHT - 1
        
        while y >= 0 and removed < amount:
            if self.grid[y][0] == GARBAGE_COLOR:
                for row in range(y, 0, -1):
                    self.grid[row] = self.grid[row - 1][:]
                self.grid[0] = [BLACK for _ in range(GRID_WIDTH)]
                removed += 1
            else:
                y -= 1
        return removed
    
    def lock_piece(self):
        """Fixa a peça no grid e processa linhas completas + ataques"""
        # 1) Copia a peça pro grid
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    grid_y = self.current_piece.y + y
                    grid_x = self.current_piece.x + x
                    if grid_y >= 0:
                        self.grid[grid_y][grid_x] = self.current_piece.color
        
        # 2) Conta linhas completas (normais, sem lixo)
        lines_cleared = self.clear_normal_lines()
        
        if lines_cleared > 0:
            # Pontuação (exponencial por número de linhas)
            points = [0, 100, 300, 500, 800]
            self.score += points[lines_cleared] * (1 + self.total_lines // 10)
            self.total_lines += lines_cleared
            self.fall_speed = max(100, 500 - (self.total_lines // 10) * 30)  # Acelera o jogo
            
            # 🔥 LÓGICA DO PVP: DEFESA vs ATAQUE 🔥
            garbage_count = self.count_garbage_lines()
            
            if garbage_count > 0:
                # Se TEM LINHA DE LIXO → DEFENDE (limpa, NÃO ataca)
                removed = self.remove_garbage_lines(lines_cleared)
                print(f"🛡️ Jogador {self.player_id} se DEFENDEU! Removeu {removed} linha(s) de lixo!")
            else:
                # Se NÃO TEM LIXO → ATACA (envia lixo pro oponente)
                self.pending_attack = lines_cleared
                print(f"⚔️ Jogador {self.player_id} ATACOU! Enviou {lines_cleared} linha(s) de lixo!")
        
        # 3) Gera nova peça
        self.spawn_new_piece()
    
    def clear_normal_lines(self):
        """Remove linhas completas (que não são de lixo)"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        
        while y >= 0:
            # Verifica se a linha está completa (sem buracos e não é lixo)
            if (all(self.grid[y][x] != BLACK for x in range(GRID_WIDTH)) and 
                self.grid[y][0] != GARBAGE_COLOR):
                # Remove a linha (desce tudo acima)
                for row in range(y, 0, -1):
                    self.grid[row] = self.grid[row - 1][:]
                self.grid[0] = [BLACK for _ in range(GRID_WIDTH)]
                lines_cleared += 1
            else:
                y -= 1
        return lines_cleared
    
    def receive_garbage(self, lines):
        """Recebe lixo do adversário (linhas escuras no fundo)"""
        for _ in range(lines):
            garbage_line = [GARBAGE_COLOR] * GRID_WIDTH
            self.grid.pop(0)        # Remove linha do topo
            self.grid.append(garbage_line)  # Adiciona lixo no fundo
        print(f"💀 Jogador {self.player_id} RECEBEU {lines} linha(s) de lixo!")
    
    def update(self, current_time):
        """Atualiza queda automática da peça (baseado no tempo)"""
        if self.game_over:
            return
        
        if current_time - self.last_fall_time > self.fall_speed:
            self.move(0, 1)
            self.last_fall_time = current_time
    
    def draw_ghost(self, screen):
        """Desenha a sombra da peça (preview de onde vai cair)"""
        if self.current_piece and not self.game_over:
            ghost_y = self.get_ghost_position()
            
            if ghost_y > self.current_piece.y:
                for y, row in enumerate(self.current_piece.shape):
                    for x, cell in enumerate(row):
                        if cell:
                            rect = pygame.Rect(
                                self.x + (self.current_piece.x + x) * CELL_SIZE,
                                self.y + (ghost_y + y) * CELL_SIZE,
                                CELL_SIZE - 1, CELL_SIZE - 1
                            )
                            ghost_surface = pygame.Surface((CELL_SIZE - 1, CELL_SIZE - 1))
                            ghost_surface.set_alpha(100)  # Transparência
                            ghost_surface.fill(self.current_piece.color)
                            screen.blit(ghost_surface, rect)
                            pygame.draw.rect(screen, WHITE, rect, 1)
    
    def draw(self, screen):
        """Desenha tudo do jogador: grid, peça, fantasma, UI"""
        # Desenha o grid
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                rect = pygame.Rect(
                    self.x + x * CELL_SIZE,
                    self.y + y * CELL_SIZE,
                    CELL_SIZE - 1, CELL_SIZE - 1
                )
                
                if self.grid[y][x] == GARBAGE_COLOR:
                    # Lixo: fundo escuro com X vermelho
                    pygame.draw.rect(screen, GARBAGE_COLOR, rect)
                    pygame.draw.rect(screen, DARK_GRAY, rect, 1)
                    center_x = rect.centerx
                    center_y = rect.centery
                    pygame.draw.line(screen, RED, 
                                   (center_x - 5, center_y - 5),
                                   (center_x + 5, center_y + 5), 2)
                    pygame.draw.line(screen, RED,
                                   (center_x + 5, center_y - 5),
                                   (center_x - 5, center_y + 5), 2)
                else:
                    pygame.draw.rect(screen, self.grid[y][x], rect)
                    pygame.draw.rect(screen, GRAY, rect, 1)
        
        self.draw_ghost(screen)  # Sombra
        
        # Desenha a peça atual
        if self.current_piece and not self.game_over:
            for y, row in enumerate(self.current_piece.shape):
                for x, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(
                            self.x + (self.current_piece.x + x) * CELL_SIZE,
                            self.y + (self.current_piece.y + y) * CELL_SIZE,
                            CELL_SIZE - 1, CELL_SIZE - 1
                        )
                        pygame.draw.rect(screen, self.current_piece.color, rect)
                        pygame.draw.rect(screen, WHITE, rect, 2)
        
        # Pré-visualização da próxima peça
        preview_x = self.x + GRID_WIDTH * CELL_SIZE + 20
        preview_y = self.y + 50
        
        pygame.draw.rect(screen, DARK_GRAY, (preview_x - 10, preview_y - 10, 120, 120))
        pygame.draw.rect(screen, WHITE, (preview_x - 10, preview_y - 10, 120, 120), 2)
        
        if self.next_piece:
            shape = self.next_piece.shape
            color = self.next_piece.color
            for y, row in enumerate(shape):
                for x, cell in enumerate(row):
                    if cell:
                        rect = pygame.Rect(preview_x + x * 30, preview_y + y * 30, 28, 28)
                        pygame.draw.rect(screen, color, rect)
                        pygame.draw.rect(screen, WHITE, rect, 1)
        
        # UI: placar e status
        font = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        
        player_text = font.render(f"Jogador {self.player_id}", True, WHITE)
        screen.blit(player_text, (self.x, self.y - 40))
        
        score_text = font_small.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (self.x, self.y + GRID_HEIGHT * CELL_SIZE + 10))
        
        lines_text = font_small.render(f"Linhas: {self.total_lines}", True, WHITE)
        screen.blit(lines_text, (self.x, self.y + GRID_HEIGHT * CELL_SIZE + 35))
        
        garbage_count = self.count_garbage_lines()
        garbage_text = font_small.render(f"Lixo: {garbage_count}", True, RED)
        screen.blit(garbage_text, (self.x, self.y + GRID_HEIGHT * CELL_SIZE + 60))
        
        if self.game_over:
            go_text = font.render("GAME OVER", True, RED)
            go_rect = go_text.get_rect(center=(
                self.x + GRID_WIDTH * CELL_SIZE // 2,
                self.y + GRID_HEIGHT * CELL_SIZE // 2
            ))
            screen.blit(go_text, go_rect)

# ===== CLASSE PRINCIPAL DO JOGO =====
class Game:
    """Gerencia os dois jogadores, eventos e loop principal"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris PvP")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 48)
        
        # Posiciona os grids dos jogadores (esquerda e direita)
        player1_x = 50
        player2_x = SCREEN_WIDTH - GRID_WIDTH * CELL_SIZE - 150
        
        self.player1 = Player(player1_x, 100, 1)
        self.player2 = Player(player2_x, 100, 2)
        
        self.running = True
        self.winner = None
    
    def handle_events(self):
        """Processa entrada do teclado (movimentos de cada jogador)"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                # Controles do Jogador 1 (WASD + Espaço)
                if event.key == pygame.K_a:
                    self.player1.move(-1, 0)
                elif event.key == pygame.K_d:
                    self.player1.move(1, 0)
                elif event.key == pygame.K_s:
                    self.player1.move(0, 1)
                elif event.key == pygame.K_w:
                    self.player1.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    self.player1.drop_piece()
                
                # Controles do Jogador 2 (Setas + Enter)
                elif event.key == pygame.K_LEFT:
                    self.player2.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.player2.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    self.player2.move(0, 1)
                elif event.key == pygame.K_UP:
                    self.player2.rotate_piece()
                elif event.key == pygame.K_RETURN:
                    self.player2.drop_piece()
                
                # Reinicia o jogo
                elif event.key == pygame.K_r:
                    self.__init__()
    
    def update(self):
        """Atualiza lógica do jogo a cada frame"""
        current_time = pygame.time.get_ticks()
        
        self.player1.update(current_time)
        self.player2.update(current_time)
        
        # 🎯 Sistema de ataque: envia lixo ao oponente
        if self.player1.pending_attack > 0:
            self.player2.receive_garbage(self.player1.pending_attack)
            self.player1.pending_attack = 0
        
        if self.player2.pending_attack > 0:
            self.player1.receive_garbage(self.player2.pending_attack)
            self.player2.pending_attack = 0
        
        # Verifica quem ganhou/perdeu
        if self.player1.game_over and self.player2.game_over:
            self.winner = "EMPATE!"
        elif self.player1.game_over:
            self.winner = "JOGADOR 2 VENCEU!"
        elif self.player2.game_over:
            self.winner = "JOGADOR 1 VENCEU!"
    
    def draw_ui(self):
        """Desenha título e linha divisória"""
        title = self.font.render("TETRIS PVP", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Linha vertical no meio da tela
        pygame.draw.line(self.screen, WHITE, (SCREEN_WIDTH // 2, 80), 
                        (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50), 3)
    
    def draw_winner(self):
        """Tela de fim de jogo com opção de reiniciar"""
        if self.winner:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            winner_text = self.font.render(self.winner, True, GREEN)
            winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(winner_text, winner_rect)
            
            restart_text = pygame.font.Font(None, 32).render("Pressione R para reiniciar", True, WHITE)
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
            self.screen.blit(restart_text, restart_rect)
            
            pygame.display.flip()
            
            # Aguarda o jogador reiniciar ou sair
            waiting = True
            while waiting:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        waiting = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_r:
                            self.__init__()
                            waiting = False
    
    def run(self):
        """Loop principal do jogo"""
        while self.running:
            self.handle_events()
            self.update()
            
            self.screen.fill(BLACK)
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            self.draw_ui()
            
            if self.winner:
                self.draw_winner()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
        sys.exit()

# ===== PONTO DE ENTRADA =====
if __name__ == "__main__":
    game = Game()
    game.run()