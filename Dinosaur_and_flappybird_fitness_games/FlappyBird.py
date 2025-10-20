import os
import pygame
import sys
import random
import cv2
import numpy as np
import time
import PoseModule as pm

# For numpy.angle
angle = np.angle
os.environ['SDL_VIDEO_WINDOW_POS'] = "50,50"  # x=50, y=50

wCam, hCam = 1280, 720

def play_flappy_bird():
    cap = cv2.VideoCapture(0)
    cap.set(3, wCam)
    cap.set(4, hCam)

    detector = pm.poseDetector()
    count = 0
    dir = 0
    pastTime = 0

    # -------------------------------
    # Helper to get absolute asset path
    # -------------------------------
    SCRIPT_DIR = os.path.dirname(__file__)
    def asset_path(*paths):
        return os.path.join(SCRIPT_DIR, *paths)

    # -------------------------------
    # Pygame init
    # -------------------------------
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()
    screen = pygame.display.set_mode((432, 768))
    clock = pygame.time.Clock()

    # -------------------------------
    # Load font
    # -------------------------------
    game_font = pygame.font.Font(asset_path('04B_19.TTF'), 35)

    # -------------------------------
    # Load images
    # -------------------------------
    bg = pygame.image.load(asset_path('assets', 'background-night.png')).convert()
    bg = pygame.transform.scale2x(bg)
    floor = pygame.image.load(asset_path('assets', 'floor.png')).convert()
    floor = pygame.transform.scale2x(floor)
    floor_x_pos = 0

    bird_down = pygame.transform.scale2x(pygame.image.load(asset_path('assets', 'yellowbird-downflap.png')).convert_alpha())
    bird_mid = pygame.transform.scale2x(pygame.image.load(asset_path('assets', 'yellowbird-midflap.png')).convert_alpha())
    bird_up = pygame.transform.scale2x(pygame.image.load(asset_path('assets', 'yellowbird-upflap.png')).convert_alpha())
    bird_list = [bird_down, bird_mid, bird_up]
    bird_index = 0
    bird = bird_list[bird_index]
    bird_rect = bird.get_rect(center=(100, 384))

    pipe_surface = pygame.image.load(asset_path('assets', 'pipe-green.png')).convert()
    pipe_surface = pygame.transform.scale2x(pipe_surface)
    pipe_list = []
    pipe_height = range(250, 500)

    game_over_surface = pygame.transform.scale2x(pygame.image.load(asset_path('assets', 'message.png')).convert_alpha())
    game_over_rect = game_over_surface.get_rect(center=(216, 384))

    # -------------------------------
    # Load sounds
    # -------------------------------
    flap_sound = pygame.mixer.Sound(asset_path('sound', 'sfx_wing.wav'))
    hit_sound = pygame.mixer.Sound(asset_path('sound', 'sfx_hit.wav'))
    score_sound = pygame.mixer.Sound(asset_path('sound', 'sfx_point.wav'))
    score_sound_countdown = 100

    # -------------------------------
    # Game variables
    # -------------------------------
    gravity = 0.45
    bird_movement = 0
    game_active = True
    score = 0
    high_score = 0

    # -------------------------------
    # Timers
    # -------------------------------
    birdflap = pygame.USEREVENT + 1
    pygame.time.set_timer(birdflap, 200)
    spawnpipe = pygame.USEREVENT
    pygame.time.set_timer(spawnpipe, 2500)

    # -------------------------------
    # Helper functions
    # -------------------------------
    def draw_floor():
        screen.blit(floor, (floor_x_pos, 650))
        screen.blit(floor, (floor_x_pos + 432, 650))

    def create_pipe():
        random_pipe_pos = random.choice(pipe_height)
        bottom_pipe = pipe_surface.get_rect(midtop=(500, random_pipe_pos))
        top_pipe = pipe_surface.get_rect(midtop=(500, random_pipe_pos - 750))
        return bottom_pipe, top_pipe

    def move_pipe(pipes):
        for pipe in pipes:
            pipe.centerx -= 5
        return pipes

    def draw_pipe(pipes):
        for pipe in pipes:
            if pipe.bottom >= 600:
                screen.blit(pipe_surface, pipe)
            else:
                flip_pipe = pygame.transform.flip(pipe_surface, False, True)
                screen.blit(flip_pipe, pipe)

    def check_collision(pipes):
        for pipe in pipes:
            if bird_rect.colliderect(pipe):
                hit_sound.play()
                return False
        if bird_rect.top <= -75 or bird_rect.bottom >= 650:
            return False
        return True

    def rotate_bird(bird1):
        return pygame.transform.rotozoom(bird1, -bird_movement*3, 1)

    def bird_animation():
        new_bird = bird_list[bird_index]
        new_bird_rect = new_bird.get_rect(center=(100, bird_rect.centery))
        return new_bird, new_bird_rect

    def score_display(game_state):
        if game_state == 'main game':
            score_surface = game_font.render(str(int(score)), True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(216, 100))
            screen.blit(score_surface, score_rect)
        if game_state == 'game_over':
            score_surface = game_font.render(f'Score: {int(score)}', True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(216, 100))
            screen.blit(score_surface, score_rect)
            high_score_surface = game_font.render(f'High Score: {int(high_score)}', True, (255, 255, 255))
            high_score_rect = high_score_surface.get_rect(center=(216, 630))
            screen.blit(high_score_surface, high_score_rect)
    def update_score(score, high_score):
        if score > high_score:
            high_score = score
        return high_score

    # -------------------------------
    # Main game loop
    # -------------------------------
    while True:
        success, img = cap.read()
        img = detector.findPose(img, False)
        lmList = detector.findPosition(img, False)

        # Pose detection for jumps
        if len(lmList) != 0:
            angleRight = detector.findAngle(img, 14, 12, 24)
            angleLeft = detector.findAngle(img, 13, 11, 23)
            perRight = np.interp(angleRight, (30, 80), (0, 100))
            perLeft = np.interp(angleLeft, (30, 80), (0, 100))

            if (perRight == 100) and (perLeft == 100) and dir == 0:
                count += 0.5
                dir = 1
            if (perRight == 0) and (perLeft == 0) and dir == 1:
                count += 0.5
                dir = 0

            cv2.rectangle(img, (25, 125), (125, 25), (0, 255, 0), cv2.FILLED)
            cv2.putText(img, str(int(count-0.5)), (50, 100),
                        cv2.FONT_HERSHEY_COMPLEX, 2, (255, 0, 0), 2)
        # cv2.namedWindow("Image",img)
        # cv2.moveWindow("Image", 500, 50)  # x=500, y=50

        cv2.imshow("Image", img)
        key = cv2.waitKey(1)
        if key == ord("q"):
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if count != 0:
                if game_active:
                    bird_movement = -8
                    flap_sound.play()
                    count = 0
                elif not game_active:
                    game_active = True
                    pipe_list.clear()
                    bird_rect.center = (100, 384)
                    bird_movement = 0
                    score = 0
                    count = 0
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if game_active:
                        bird_movement = -8
                        flap_sound.play()
                    else:
                        game_active = True
                        pipe_list.clear()
                        bird_rect.center = (100,384)
                        bird_movement = 0
                        score = 0
            if event.type == spawnpipe:
                pipe_list.extend(create_pipe())
            if event.type == birdflap:
                bird_index = (bird_index + 1) % 3
                bird, bird_rect = bird_animation()

        screen.blit(bg, (0, 0))
        if game_active:
            bird_movement += gravity
            rotated_bird = rotate_bird(bird)
            bird_rect.centery += bird_movement
            screen.blit(rotated_bird, bird_rect)
            game_active = check_collision(pipe_list)
            pipe_list = move_pipe(pipe_list)
            draw_pipe(pipe_list)
            score += 0.01
            score_display('main game')
            score_sound_countdown -= 1
            if score_sound_countdown <= 0:
                score_sound.play()
                score_sound_countdown = 100
        else:
            screen.blit(game_over_surface, game_over_rect)
            high_score = update_score(score, high_score)
            score_display('game_over')

        floor_x_pos -= 1
        draw_floor()
        if floor_x_pos <= -432:
            floor_x_pos = 0

        pygame.display.update()
        clock.tick(120)

if __name__ == "__main__":
    play_flappy_bird()
    
