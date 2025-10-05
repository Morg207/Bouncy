
import pygame
import sys
import math
import random
import numpy as np
from OpenGL.GL import *
import ctypes

pygame.mixer.pre_init(frequency=48000)
pygame.init()
window_width = 800
window_height = 600
display_info = pygame.display.Info()
display_width = display_info.current_w
display_height = display_info.current_h
pygame.display.set_mode((display_width,display_height),flags=pygame.DOUBLEBUF | pygame.OPENGL | pygame.FULLSCREEN,vsync=True)
window = pygame.Surface((window_width,window_height),pygame.SRCALPHA)
resolution_scale = min(display_width / window_width, display_height / window_height)
ndc_w = (window_width * resolution_scale) / display_width
ndc_h = (window_height * resolution_scale) / display_height
pygame.display.set_caption("Bouncy!")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
player_image = pygame.transform.smoothscale_by(pygame.image.load("Images/character idle.png"), 0.05).convert_alpha()
player_right_leg = pygame.transform.smoothscale_by(pygame.image.load("Images/character right leg.png"), 0.05).convert_alpha()
player_left_leg = pygame.transform.smoothscale_by(pygame.image.load("Images/character left leg.png"), 0.05).convert_alpha()
fps =  60
running = True
grass_left = pygame.transform.smoothscale_by(pygame.image.load("Images/grass tile left.png"), 0.04).convert_alpha()
grass_right = pygame.transform.smoothscale_by(pygame.image.load("Images/grass tile right.png"), 0.04).convert_alpha()
grass_middle = pygame.transform.smoothscale_by(pygame.image.load("Images/grass tile middle.png"), 0.04).convert_alpha()
grass_small = pygame.transform.smoothscale_by(pygame.image.load("Images/grass tile small.png"), 0.04).convert_alpha()
tile_width = grass_small.get_width()
tile_height = grass_small.get_height()
gold_coin = pygame.transform.scale(pygame.image.load("Images/coin.png"),(41,41)).convert_alpha()
coin_group = pygame.sprite.Group()
bunny_group = pygame.sprite.Group()
snake_group = pygame.sprite.Group()
bunny_right = pygame.transform.smoothscale_by(pygame.image.load("Images/bunny right.png"),0.05).convert_alpha()
bunny_left = pygame.transform.smoothscale_by(pygame.image.load("Images/bunny left.png"),0.05).convert_alpha()
c_prompt = pygame.transform.smoothscale_by(pygame.image.load("Images/c prompt.png"),0.04).convert_alpha()
coin_sound = pygame.mixer.Sound("Sounds/coin_collect.wav")
jump_sound = pygame.mixer.Sound("Sounds/jump.wav")
prompt_sound = pygame.mixer.Sound("Sounds/prompt.wav")
capture_sound = pygame.mixer.Sound("Sounds/capture.wav")
snake_sound = pygame.mixer.Sound("Sounds/snake_kill.wav")
damage_sound = pygame.mixer.Sound("Sounds/damage.wav")
damage_sound.set_volume(0.7)
bunny_hud = pygame.transform.smoothscale_by(pygame.image.load("Images/bunny hud.png"),0.04).convert_alpha()
coin_hud = pygame.transform.smoothscale_by(pygame.image.load("Images/coin.png"),0.06).convert_alpha()
snake_left = pygame.transform.smoothscale_by(pygame.image.load("Images/snake left.png"),0.045).convert_alpha()
snake_right = pygame.transform.smoothscale_by(pygame.image.load("Images/snake right.png"),0.045).convert_alpha()
player_particle = pygame.USEREVENT + 1
pygame.time.set_timer(player_particle,50)

def prepare_screen():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    pygame.display.flip()

def load_shader(path):
    with open(path, 'r') as file:
        return file.read()

def compile_shader(source, shader_type):
    shader = glCreateShader(shader_type)
    glShaderSource(shader, source)
    glCompileShader(shader)

    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        error = glGetShaderInfoLog(shader).decode()
        raise RuntimeError(f'Shader compile error: {error}')
    return shader

def create_shader_program(vertex_path, fragment_path):
    vertex_src = load_shader(vertex_path)
    fragment_src = load_shader(fragment_path)
    vertex_shader = compile_shader(vertex_src, GL_VERTEX_SHADER)
    fragment_shader = compile_shader(fragment_src, GL_FRAGMENT_SHADER)
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        error_msg = glGetProgramInfoLog(program).decode()
        raise RuntimeError(f"Shader linking failed: {error_msg}")
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program

def surface_to_texture(surface):
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    data = pygame.image.tostring(surface, "RGBA", True)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, surface.get_width(), surface.get_height(), 0, GL_RGBA, GL_UNSIGNED_BYTE,
                 data)
    return texture_id

def update_texture(texture_id, surface):
    glBindTexture(GL_TEXTURE_2D, texture_id)
    data = pygame.image.tostring(surface, "RGBA", 1)
    glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, surface.get_width(), surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, data)

def draw_text(text, x, y, size, colour):
    font = pygame.font.Font("Fonts/pixel.ttf",size)
    text_image = font.render(text, True, colour)
    text_rect = text_image.get_rect()
    text_rect.x = x
    text_rect.y = y
    window.blit(text_image, text_rect)

def display_hud():
    draw_text(str(player.bunnies_caught), window_width-75, 102, 41, (255, 255, 255))
    draw_text(str(player.coins_collected),window_width-75,40,41, (255,255,255))
    window.blit(bunny_hud, (window_width-140, 100))
    window.blit(coin_hud,(window_width-134,35))

def display_health_bar():
    if player.death_count < 20:
        player.health_bar_outline.x = int(player.x+6-camera.x_offset)
        player.health_bar_outline.y = int(player.y-18-camera.y_offset)
        player.health_bar.x = int(player.x+6-camera.x_offset)
        player.health_bar.y = int(player.y-18-camera.y_offset)
        pygame.draw.rect(window, (224,99,92), player.health_bar_outline, border_radius=2)
        pygame.draw.rect(window, (0, 140, 20), player.health_bar, border_radius=2)

def draw_snakes():
    for snake in snake_group:
        snake.update()
        snake.draw()

def draw_coins():
    for coin in coin_group:
        coin.update()
        coin.draw()

def draw_bunnies():
    for bunny in bunny_group:
        bunny.update()
        bunny.draw()

def generate_particles():
    if not player.falling and player.running:
        if player.image == player.run_frames[0]:
            player.particle_spawner.add_particles(player.x - camera.x_offset + 25,
                                                  player.y - camera.y_offset + player.rect.height)
        elif player.image == player.run_frames[1]:
            player.particle_spawner.add_particles(player.x - camera.x_offset + 50,
                                                  player.y - camera.y_offset + player.rect.height)

class DayNightCycle():
    def __init__(self):
        self.day = 1100
        self.day_count = 0
        self.night = 900
        self.night_count = 0
        self.night_loaded = False
        self.is_day = True
        self.ambient = 1.0
        self.torch_colour = (1.0, 0.8, 0.6)
        self.shader_program = create_shader_program("vertex.glsl","fragment.glsl")
        self.texture_id = surface_to_texture(window)
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        self.setup_shader()
        self.setup_uniforms()

    def setup_shader(self):
        vertices = np.array([
            -ndc_w, -ndc_h, 0.0, 0.0,
            ndc_w, -ndc_h, 1.0, 0.0,
            ndc_w, ndc_h, 1.0, 1.0,
            -ndc_w, ndc_h, 0.0, 1.0
        ], dtype=np.float32)
        indices = np.array([
            0, 1, 2,
            2, 3, 0
        ], dtype=np.uint32)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(8))
        glEnableVertexAttribArray(1)
        glBindVertexArray(0)
        glUseProgram(self.shader_program)

    def setup_uniforms(self):
        glUniform1i(glGetUniformLocation(self.shader_program, "texture1"), 0)
        self.lightPosLoc = glGetUniformLocation(self.shader_program, "lightPos")
        self.lightRadiusLoc = glGetUniformLocation(self.shader_program, "lightRadius")
        self.lightColorLoc = glGetUniformLocation(self.shader_program, "lightColor")
        self.ambient_loc = glGetUniformLocation(self.shader_program, "ambient")
        self.time_loc = glGetUniformLocation(self.shader_program, "time")
        glUniform1f(self.ambient_loc, self.ambient)
        glUniform1f(self.lightRadiusLoc, 0.25)
        glUniform3f(self.lightColorLoc, *self.torch_colour)

    @staticmethod
    def play_cricket_sounds():
        pygame.mixer.music.unload()
        pygame.mixer.music.load("Sounds/night.wav")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(loops=-1, fade_ms=2000)

    def update(self):
        self.day_count += 1
        if self.day_count > self.day:
            if not self.night_loaded:
                DayNightCycle.play_cricket_sounds()
                self.night_loaded = True
            if self.is_day:
                self.ambient -= 0.002
                if self.ambient <= 0.3:
                    self.ambient = 0.3
                    self.is_day = False
            else:
                self.night_count += 1
            if self.night_count > self.night:
                pygame.mixer.music.fadeout(3000)
                self.ambient += 0.002
                if self.ambient > 1:
                    self.ambient = 1.0
                    self.is_day = True
                    self.night_loaded = False
                    self.night_count = 0
                    self.day_count = 0
            glUniform1f(self.ambient_loc,self.ambient)
            glUniform1f(self.time_loc,pygame.time.get_ticks()/1000)

    def draw(self):
        glUseProgram(self.shader_program)
        update_texture(self.texture_id, window)
        glClear(GL_COLOR_BUFFER_BIT)
        light_x = (player.x + player.rect.width // 2 - camera.x_offset) / window_width
        light_y = 1.0 - (player.y + player.rect.height // 2 - camera.y_offset) / window_height
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glUniform2f(self.lightPosLoc, light_x, light_y)
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

    def cleanup(self):
        glDeleteVertexArrays(1, [self.vao])
        glDeleteBuffers(2, [self.vbo, self.ebo])
        glDeleteTextures(1, [self.texture_id])
        glDeleteProgram(self.shader_program)

class Snake(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = snake_left
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.frames = (snake_left, snake_right)
        self.index = 0
        self.count = 0
        self.squashed = False
        self.falling = True
        self.follow_player = False
        self.kill_timer = 0
        self.kill_time = 800
        self.y_speed = 0
        self.dir = 0
        self.attack_count = 0
        self.attack_damage = 10

    def move(self):
        dx = 0
        dy = 0
        distance_vector = pygame.Vector2(self.x+self.rect.width//2, self.y+self.rect.height//2) - \
                          pygame.Vector2(player.x+player.rect.width//2, player.y+player.rect.height//2)
        distance_vector.y = 0
        if distance_vector.magnitude() < 400 and distance_vector.x != 0 and not player.is_dead:
            self.follow_player = True
            move_vector = pygame.Vector2(distance_vector.x / distance_vector.x * 2, 0)
            if distance_vector.magnitude() > 60:
                self.attack_count = 0
                if distance_vector.x > 0:
                    dx -= move_vector.x
                    self.dir = -1
                    self.image = snake_left
                else:
                    dx += move_vector.x
                    self.dir = 1
                    self.image = snake_right
            else:
                if self.rect.top < player.rect.top:
                    if self.dir == 1:
                        dx += move_vector.x
                        self.image = snake_right
                    elif self.dir == -1:
                        dx -= move_vector.x
                        self.image = snake_left
        else:
            self.follow_player = False
        self.y_speed += 0.48
        dy += self.y_speed
        return dx, dy

    def handle_collision(self, dx, dy):
        for tile in tile_map.tile_list:
            if tile[1].colliderect(self.x + dx, self.y, self.rect.width, self.rect.height):
                dx = 0
            if tile[1].colliderect(self.x, self.y + math.ceil(dy), self.rect.width, self.rect.height):
                if self.y_speed < 0:
                    dy = tile[1].bottom - self.rect.top
                    self.y_speed = 0
                    self.falling = False
                elif self.y_speed >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.y_speed = 0
                    self.falling = False
        return dx, dy

    def run_animations(self):
        if not self.follow_player:
            self.count += 1
            if self.count > 60:
                self.index += 1
                if self.index > len(self.frames) - 1:
                    self.index = 0
                self.image = self.frames[self.index]
                self.rect = self.image.get_rect()
                self.rect.x = self.x
                self.rect.y = self.y
                self.count = 0

    def attack(self):
        if self.rect.colliderect(player.rect):
            self.attack_count += 1
            if self.attack_count > 50:
                self.deal_damage()
                self.attack_count = 0
        else:
            self.attack_count = 0

    def deal_damage(self):
        health_bar_width = player.health_bar.width
        health_bar_width -= self.attack_damage
        if health_bar_width <= 0:
            health_bar_width = 0
            player.is_dead = True
            is_dead_loc = glGetUniformLocation(day_night_cycle.shader_program, "isDead")
            glUniform1i(is_dead_loc, 1)
        damage_sound.play()
        player.health_bar.width = health_bar_width
        player.hurt_cooldown = 0
        player.hurt_count = 0
        player.hurt = True

    def squash(self):
        self.squashed = True
        self.kill_timer = pygame.time.get_ticks()
        if self.dir == -1:
            self.image = pygame.transform.scale(snake_left, (snake_left.get_width(), 14))
        elif self.dir == 1:
            self.image = pygame.transform.scale(snake_right, (snake_right.get_width(), 14))
        snake_sound.play()

    def remove_from_level(self):
        if self.squashed:
            if pygame.time.get_ticks() - self.kill_timer > self.kill_time:
                self.kill()

    def update(self):
        self.falling = True
        dx = 0
        dy = 0
        if not self.squashed:
            dx,dy = self.move()
            dx,dy = self.handle_collision(dx,dy)
            self.run_animations()
            if player.death_count < 20:
                self.attack()

        if player.rect.bottom > self.rect.top and self.rect.left-50 <= player.rect.x <= self.rect.right-15 and player.y_speed > 7 \
            and not self.squashed and player.rect.colliderect(self.rect) and not self.falling:
            self.squash()

        self.remove_from_level()
        if self.falling:
            dx = 0
        self.x += dx
        self.y += dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self):
        if not self.squashed:
            window.blit(self.image, (int(self.x-camera.x_offset),int(self.y-camera.y_offset)))
        else:
            window.blit(self.image,(int(self.x-camera.x_offset), int(self.y-camera.y_offset+58)))

class ParticleSpawner():
    def __init__(self,particle_colours, no_timer, radius):
        self.particles = []
        self.particle_colours = particle_colours
        self.particle_timer = 0
        self.particle_spawn_time = 30
        self.no_timer = no_timer
        self.radius = radius

    def emit(self):
        if self.particles:
            self.delete_particles()
            for particle in self.particles:
                particle[0][0] += particle[2][1]
                particle[0][1] += particle[2][0]
                particle[1] -= 0.4
                pygame.draw.circle(window,particle[3],particle[0],int(particle[1]))

    def create_particle(self,x,y):
        direction_x = random.randint(-3, 3)
        direction_y = random.randint(-3, 3)
        particle_colour = random.choice(self.particle_colours)
        particle_circle = [[x, y],self.radius,[direction_x, direction_y], particle_colour]
        self.particles.append(particle_circle)

    def add_particles(self, x, y):
        if self.particle_timer > 0 and pygame.time.get_ticks() - self.particle_timer > self.particle_spawn_time and not self.no_timer:
            self.create_particle(x,y)
            self.particle_timer = pygame.time.get_ticks()
        else:
            self.create_particle(x,y)

    def delete_particles(self):
        particles_copy = [particle for particle in self.particles if particle[1] > 0]
        self.particles = particles_copy

class Bunny(pygame.sprite.Sprite):
    def __init__(self,x,y,dialogue,dialogue_offsets,bunny_image):
        pygame.sprite.Sprite.__init__(self)
        self.image = bunny_image
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = self.x
        self.rect.y = self.y
        self.y_speed = 0
        self.is_catchable = True
        self.c_prompt = c_prompt
        self.speak_distance = 110
        self.can_prompt = False
        self.prompt_can_play = True
        self.index = 0
        self.dialogue = dialogue
        self.dialogue_offsets = dialogue_offsets
        self.dialogue_offset_index = 0
        self.dialogue_offset = self.dialogue_offsets[self.dialogue_offset_index]
        self.message = self.dialogue[self.index]
        self.dialogue_font = pygame.font.Font("Fonts/pixel.ttf",22)
        self.dialogue_image = None
        self.can_speak = False
        self.can_kill = False
        self.dialogue_counter = 0
        self.dialogue_speed = 2
        self.prompt_presses = 0
        particle_colours = ((213, 175, 93), (81, 62, 21), (188, 150, 69), (164, 132, 65), (100, 81, 39))
        self.particle_spawner = ParticleSpawner(particle_colours,False, 7)
        self.kill_timer = 0
        self.kill_time = 250

    def remove_from_level(self):
        if self.kill_timer > 0 and pygame.time.get_ticks() - self.kill_timer < self.kill_time:
             self.particle_spawner.add_particles(self.x-camera.x_offset+self.rect.width//2,self.y-camera.y_offset+self.rect.height//2)
        elif self.kill_timer > 0 and pygame.time.get_ticks() - self.kill_timer > self.kill_time:
            if not self.particle_spawner.particles:
               player.lock_movement = False
               self.kill()

    def handle_collision(self):
        self.y_speed += 0.25
        self.y += self.y_speed
        for tile in tile_map.tile_list:
            if tile[1].colliderect(self.rect):
                self.y_speed = -3
                
    def scroll_text(self):
        if self.dialogue_counter < self.dialogue_speed * len(self.message):
            self.dialogue_counter += 1
            message_portion = self.message[0:self.dialogue_counter // self.dialogue_speed]
            if message_portion == self.dialogue[self.index]:
                self.can_speak = False
                self.index += 1
                if self.index > len(self.dialogue) - 1:
                    self.index = 0

    def reset_dialogue(self):
        self.can_prompt = False
        self.can_speak = False
        self.dialogue_counter = 0
        self.dialogue_speed = 2
        self.prompt_presses = 0
        self.index = 0
        self.message = self.dialogue[self.index]
        self.prompt_can_play = True

    def speak(self):
            self.can_prompt = True
            keys = pygame.key.get_pressed()
            if keys[pygame.K_c]:
                if not self.can_speak:
                    self.prompt_presses += 1
                    self.dialogue_counter = 0
                    self.message = self.dialogue[self.index]
                    self.dialogue_offset_index = self.index - len(self.dialogue)
                    if self.is_catchable and self.index == 0 and self.prompt_presses > 1:
                        player.bunnies_caught += 1
                        capture_sound.play()
                        if not self.can_kill:
                            self.particle_spawner.particle_timer = pygame.time.get_ticks()
                            self.kill_timer = pygame.time.get_ticks()
                            self.can_kill = True
                            player.lock_movement = True
                self.can_speak = True
            if self.prompt_can_play:
                prompt_sound.play()
                self.prompt_can_play = False

    def update(self):
        self.remove_from_level()
        if self.can_speak:
            self.scroll_text()
        self.handle_collision()
        self.rect.x = self.x
        self.rect.y = self.y
        distance_vector = pygame.Vector2(self.x, self.y) - pygame.Vector2(player.x, player.y)
        distance = distance_vector.magnitude()
        if distance < self.speak_distance:
           self.speak()
        else:
           self.reset_dialogue()
        self.dialogue_image = self.dialogue_font.render(self.message[0:self.dialogue_counter // self.dialogue_speed],
                                                                     True, (20, 20, 20))
    def draw(self):
        if not self.particle_spawner.particles and self.kill_timer == 0:
            window.blit(self.image,(int(self.x-camera.x_offset),int(self.y-camera.y_offset)))
            if self.can_speak or self.can_prompt:
                self.dialogue_offset = self.dialogue_offsets[self.dialogue_offset_index]
                window.blit(self.dialogue_image, (self.rect.x-self.dialogue_offset[0]-camera.x_offset,self.rect.y-self.dialogue_offset[1]-camera.y_offset))
            if self.can_prompt:
                window.blit(self.c_prompt, (int(self.x+25 - camera.x_offset),int(self.y-40-camera.y_offset)))
        else:
            self.particle_spawner.emit()

class MainBunny(Bunny):
    def __init__(self,x,y):
        super().__init__(x,y,("Help find all my bunny friends!", "Please help!"),
                         ((92,70),(15,70)),bunny_right)
        self.camera_count = 0
        self.is_catchable = False
        self.center_on_player = False

    def update(self):
        super().update()
        self.focus_camera()

    def focus_camera(self):
        self.camera_count += 1
        if self.camera_count > 200:
            self.camera_count = 200
        if self.camera_count < 200:
            camera.center_on_entity(self)
        else:
            self.center_on_player = True

class Coin(pygame.sprite.Sprite):
    def __init__(self,x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = gold_coin
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + (tile_width // 2),y)
        self.x = x
        self.y = y
        self.y_pos = 0

    def update(self):
        self.y_pos = self.y + math.sin((pygame.time.get_ticks()/1000)*5) * 10

    def draw(self):
        window.blit(self.image,(int(self.x - camera.x_offset+11),int(self.y_pos - camera.y_offset)))

class Camera():
    def __init__(self):
        self.x_offset = 0
        self.y_offset = 0

    def clamp(self):
        right_of_window = tile_map.width * tile_width - window_width
        bottom_of_window = tile_map.height * tile_height - window_height
        if self.x_offset < 0:
            self.x_offset = 0
        if self.x_offset > right_of_window:
            self.x_offset = right_of_window

        if self.y_offset < 0:
            self.y_offset = 0
        if self.y_offset > bottom_of_window:
            self.y_offset = bottom_of_window

    def move(self, x_amt, y_amt):
        self.x_offset += x_amt
        self.y_offset += y_amt
        self.clamp()

    def center_on_entity(self,entity):
        self.x_offset = entity.x - window_width / 2 + entity.rect.width / 2
        self.y_offset = entity.y - window_height / 2 + entity.rect.height / 2
        self.clamp()

class Player():
    def __init__(self, x, y):
        self.run_frames = (player_left_leg,player_right_leg)
        self.image = player_image
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        self.y_speed =  0
        self.jump_power = 16
        self.jumping = False
        self.running = False
        self.falling = True
        self.can_jump = False
        self.is_dead = False
        self.hurt = False
        self.lock_movement = False
        self.hurt_count = 0
        self.hurt_cooldown = 0
        self.death_count = 0
        self.count = 0
        self.index = 0
        self.bunnies_caught = 0
        self.coins_collected = 0
        particle_colours = ((86,148,64),(125,211,95),(57,96,42))
        self.particle_spawner = ParticleSpawner(particle_colours,True, 5)
        self.max_health = 60
        self.health_bar_outline = pygame.Rect(self.x+6-camera.x_offset,self.y-18-camera.y_offset,self.max_health,11)
        self.health_bar = pygame.Rect(self.x+6-camera.x_offset,self.y-18-camera.y_offset,self.max_health,11)
        self.main_bunny = Player.find_main_bunny()

    @staticmethod
    def find_main_bunny():
        main_bunny = None
        for bunny in bunny_group:
            if hasattr(bunny,"center_on_player"):
                main_bunny = bunny
                break
        return main_bunny

    def move(self):
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.running = True
            dx -= 4.5
        elif keys[pygame.K_d]:
            self.running = True
            dx += 4.5
        if keys[pygame.K_SPACE] and not self.jumping and self.can_jump:
            jump_sound.play()
            self.y_speed = -self.jump_power
            self.jumping = True
            self.can_jump = False
        self.y_speed += 0.58
        dy += self.y_speed
        return dx, dy

    def handle_collision(self, dx, dy):
        for tile in tile_map.tile_list:
            if tile[1].colliderect(self.x + dx, self.y, self.rect.width, self.rect.height):
                dx = 0
            if tile[1].colliderect(self.x, self.y + math.ceil(dy), self.rect.width, self.rect.height):
                if self.y_speed < 0:
                    dy = tile[1].bottom - self.rect.top
                    self.falling = False
                    self.y_speed = 0
                elif self.y_speed >= 0:
                    dy = tile[1].top - self.rect.bottom
                    self.jumping = False
                    self.can_jump = True
                    self.falling = False
                    self.y_speed = 0
        return dx, dy

    def run_animations(self):
        if self.running and not self.falling:
            self.count += 1
            if self.count > 8:
                self.index += 1
                if self.index > len(self.run_frames)-1:
                    self.index = 0
                self.image = self.run_frames[self.index]
                self.rect = self.image.get_rect()
                self.rect.x = self.x
                self.rect.y = self.y
                self.count = 0
        elif not self.running or self.falling:
                self.image = player_image

    def take_damage(self):
        if self.hurt:
          self.hurt_cooldown += 1
          self.hurt_count += 1
          if self.hurt_cooldown > 80:
            self.hurt_cooldown = 0
            self.hurt_count = 0
            self.hurt = False
        if self.hurt_count > 20:
           self.hurt_count = 0

    def focus_camera(self):
        if self.main_bunny.center_on_player:
            camera.center_on_entity(self)

    def collect_coins(self):
        for coin in coin_group:
            if self.rect.colliderect(coin.rect):
                self.coins_collected += 1
                coin.kill()
                coin_sound.play()

    def update(self):
        if not self.is_dead and not self.lock_movement and self.main_bunny.center_on_player:
            self.falling = True
            self.running = False
            dx, dy = self.move()
            dx, dy = self.handle_collision(dx, dy)
            self.take_damage()
            self.run_animations()
            self.x += dx
            self.y += dy
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
            self.collect_coins()
            if self.falling:
                self.can_jump = False
        elif self.is_dead:
            self.death_count += 1
            if self.death_count > 20:
                self.death_count = 20
        self.focus_camera()

    def draw(self):
        if self.death_count < 20 and self.hurt_count < 10:
            window.blit(self.image,(self.x - camera.x_offset, self.y - camera.y_offset))
            self.particle_spawner.emit()

class TileMap():
    def __init__(self, path):
        self.tile_list = []
        self.tiles = None
        self.width = 0
        self.height = 0
        self.spawn_x = 0
        self.spawn_y = 0
        self.load_map(path)

    def update(self):
        pass

    def draw(self):
        x_start = max(0,int(camera.x_offset / tile_width))
        x_end = min(self.width,int((camera.x_offset + window_width) / tile_width + 1))
        y_start = max(0,int(camera.y_offset / tile_height))
        y_end = min(self.height,int((camera.y_offset + window_height) / tile_height + 1))
        for y in range(y_start,y_end):
            for x in range(x_start,x_end):
                tile_index = self.tiles[y][x]
                match tile_index:
                    case 1:
                       window.blit(grass_middle,(int(x * tile_width - camera.x_offset), int(y * tile_height - camera.y_offset)))
                    case 2:
                       window.blit(grass_right,(int(x * tile_width - camera.x_offset), int(y * tile_height - camera.y_offset)))
                    case 3:
                       window.blit(grass_left, (int(x * tile_width - camera.x_offset), int(y * tile_height - camera.y_offset)))
                    case 4:
                       window.blit(grass_small,(int(x * tile_width - camera.x_offset), int(y * tile_height - camera.y_offset)))

    def load_tile(self,tile_image,col_count,row_count):
        rect = tile_image.get_rect()
        rect.x = col_count * tile_width
        rect.y = row_count * tile_height
        tile = (tile_image, rect)
        self.tile_list.append(tile)

    def load_map(self,path):
        with open(path,"r") as file:
            map_data = file.read()
            tokens = map_data.split()
            self.width = int(tokens[0])
            self.height = int(tokens[1])
            self.spawn_x = int(tokens[2])
            self.spawn_y = int(tokens[3])
            self.tiles = [[0 for _ in range(self.width)] for _ in range(self.height)]
            for y in range(self.height):
                for x in range(self.width):
                    char = tokens[(x + y * self.width)+4]
                    if char.isdigit():
                       self.tiles[y][x] = int(char)
                    else:
                       self.tiles[y][x] = char
        row_count = 0
        for row in self.tiles:
            col_count = 0
            for col in row:
                match col:
                    case 1:
                       self.load_tile(grass_middle, col_count, row_count)
                    case 2:
                       self.load_tile(grass_right, col_count, row_count)
                    case 3:
                       self.load_tile(grass_left, col_count, row_count)
                    case 4:
                       self.load_tile(grass_small, col_count, row_count)
                    case 5:
                       coin = Coin(col_count * tile_width, row_count * tile_height)
                       coin_group.add(coin)
                    case 6:
                       main_bunny = MainBunny(col_count * tile_width, row_count * tile_height)
                       bunny_group.add(main_bunny)
                    case 7:
                        dialogue = ("Aw shucks!", "You caught me")
                        dialogue_offsets = ((8,70),(20,70))
                        bunny = Bunny(col_count * tile_width,row_count*tile_height,dialogue,dialogue_offsets,bunny_left)
                        bunny_group.add(bunny)
                    case 8:
                        dialogue = ("How did you find me?",)
                        dialogue_offsets = ((44, 70),)
                        bunny = Bunny(col_count * tile_width,row_count * tile_height, dialogue, dialogue_offsets,bunny_left)
                        bunny_group.add(bunny)
                    case 9:
                        dialogue = ("You spoiled my fun!",)
                        dialogue_offsets = ((46, 70),)
                        bunny = Bunny(col_count * tile_width, row_count * tile_height, dialogue, dialogue_offsets,bunny_right)
                        bunny_group.add(bunny)
                    case "A":
                        dialogue = ("You're good at catching us",)
                        dialogue_offsets = ((66, 70),)
                        bunny = Bunny(col_count * tile_width, row_count * tile_height, dialogue, dialogue_offsets, bunny_left)
                        bunny_group.add(bunny)
                    case "B":
                        dialogue = ("I was hiding",)
                        dialogue_offsets = ((10, 70),)
                        bunny = Bunny(col_count * tile_width, row_count * tile_height, dialogue, dialogue_offsets, bunny_left)
                        bunny_group.add(bunny)
                    case "C":
                        snake = Snake(col_count * tile_width, row_count * tile_height - 20)
                        snake_group.add(snake)
                col_count += 1
            row_count += 1

prepare_screen()
tile_map = TileMap("map.txt")
camera = Camera()
player = Player(tile_map.spawn_x * tile_width, tile_map.spawn_y * tile_height)
day_night_cycle = DayNightCycle()
while running:
    clock.tick(fps)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        if event.type == player_particle:
            generate_particles()
    window.fill("light blue")
    player.update()
    draw_coins()
    tile_map.update()
    tile_map.draw()
    draw_bunnies()
    player.draw()
    display_health_bar()
    draw_snakes()
    display_hud()
    day_night_cycle.update()
    day_night_cycle.draw()
    pygame.display.flip()
day_night_cycle.cleanup()
pygame.quit()
sys.exit()