import pygame
import sys
import random
import pytchat
import pyperclip

pygame.init()

# ---------------------------------------------------------
# WINDOW / RESOLUTION
# ---------------------------------------------------------
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Falling Pickaxe")
clock = pygame.time.Clock()

BLOCK_SIZE = 64
PICK_W, PICK_H = 64, 64

font_small = pygame.font.SysFont("arial", 24)
font_big = pygame.font.SysFont("arial", 48)

# ---------------------------------------------------------
# TEXTURES (PLACEHOLDERS IF MISSING, PER-BLOCK RANDOM COLOUR)
# ---------------------------------------------------------
def load_tex(name):
    try:
        img = pygame.image.load(name).convert_alpha()
        return pygame.transform.scale(img, (BLOCK_SIZE, BLOCK_SIZE))
    except:
        return None  # per-block random colour handled in Block

tex_grass   = load_tex("grass.png")
tex_dirt    = load_tex("dirt.png")
tex_stone   = load_tex("stone.png")

tex_iron    = load_tex("iron.png")
tex_diamond = load_tex("diamond.png")
tex_coal    = load_tex("coal.png")
tex_copper  = load_tex("copper.png")
tex_lapis   = load_tex("lapis.png")
tex_gold    = load_tex("gold.png")
tex_redstone= load_tex("redstone.png")
tex_emerald = load_tex("emerald.png")
tex_amethyst= load_tex("amethyst.png")
tex_ruby    = load_tex("ruby.png")
tex_sapphire= load_tex("sapphire.png")
tex_titanium= load_tex("titanium.png")
tex_void    = load_tex("void_crystal.png")
tex_scrap   = load_tex("netherite_scrap.png")

tex_tnt     = load_tex("tnt.png")

# ---------------------------------------------------------
# BLOCK CLASS
# ---------------------------------------------------------
class Block:
    def __init__(self, x, y, tex, kind):
        self.rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        self.kind = kind
        if tex is None:
            surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            colour = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255),
                200
            )
            surf.fill(colour)
            self.tex = surf
        else:
            self.tex = tex

    def draw(self, surf):
        surf.blit(self.tex, self.rect)

# ---------------------------------------------------------
# WORLD GENERATION
# ---------------------------------------------------------
blocks = []

def choose_texture(depth):
    if depth == 0:
        return tex_grass, "grass"
    if depth <= 3:
        return tex_dirt, "dirt"

    if depth <= 10:
        table = [
            (tex_stone, "stone", 80),
            (tex_dirt,  "dirt", 10),
            (tex_coal,  "coal", 5),
            (tex_copper,"copper",5),
        ]
    elif depth <= 30:
        table = [
            (tex_stone,   "stone", 60),
            (tex_coal,    "coal", 10),
            (tex_copper,  "copper",10),
            (tex_iron,    "iron", 10),
            (tex_lapis,   "lapis",3),
            (tex_gold,    "gold",3),
            (tex_redstone,"redstone",3),
            (tex_tnt,     "tnt", 1),
        ]
    else:
        table = [
            (tex_stone,   "stone", 40),
            (tex_iron,    "iron", 10),
            (tex_gold,    "gold", 8),
            (tex_redstone,"redstone",8),
            (tex_emerald, "emerald",5),
            (tex_amethyst,"amethyst",5),
            (tex_ruby,    "ruby",5),
            (tex_sapphire,"sapphire",5),
            (tex_titanium,"titanium",4),
            (tex_void,    "void_crystal",3),
            (tex_scrap,   "netherite_scrap",3),
            (tex_diamond, "diamond",4),
            (tex_tnt,     "tnt",2),
        ]

    total = sum(w for _, _, w in table)
    r = random.randint(1, total)
    acc = 0
    for tex, kind, w in table:
        acc += w
        if r <= acc:
            return tex, kind
    return tex_stone, "stone"

def spawn_row(depth, y):
    cols = WIDTH // BLOCK_SIZE + 2
    for c in range(cols):
        tex, kind = choose_texture(depth)
        blocks.append(Block(c * BLOCK_SIZE, y, tex, kind))

def get_lowest_y():
    return max(b.rect.y for b in blocks) if blocks else 0

def get_highest_y():
    return min(b.rect.y for b in blocks) if blocks else 0

def generate_initial():
    blocks.clear()
    depth = 0
    y = 0
    while y < HEIGHT + BLOCK_SIZE * 2:
        spawn_row(depth, y)
        depth += 1
        y += BLOCK_SIZE
    return depth

# ---------------------------------------------------------
# HEALTH / RESET
# ---------------------------------------------------------
MAX_HEALTH = 100
health = MAX_HEALTH

def reset_world():
    global current_depth, pickaxe_x, pickaxe_y, pickaxe_vx, pickaxe_vy, health
    current_depth = generate_initial()
    pickaxe_x = WIDTH // 2
    pickaxe_y = 50
    pickaxe_vx = 0
    pickaxe_vy = 0
    health = MAX_HEALTH

# ---------------------------------------------------------
# TNT EXPLOSION
# ---------------------------------------------------------
def explode_at(cx, cy, launch=True):
    global blocks, health, pickaxe_vy
    radius_blocks = random.randint(2, 5)
    radius_pixels = radius_blocks * BLOCK_SIZE

    damage = radius_blocks * 10
    health -= damage

    if launch:
        pickaxe_vy = -radius_blocks * 8

    new_blocks = []
    r2 = radius_pixels * radius_pixels
    for b in blocks:
        dx = b.rect.centerx - cx
        dy = b.rect.centery - cy
        if dx*dx + dy*dy <= r2:
            continue
        new_blocks.append(b)
    blocks = new_blocks

# ---------------------------------------------------------
# PICKAXE PHYSICS
# ---------------------------------------------------------
pickaxe_x = WIDTH // 2
pickaxe_y = 50
pickaxe_vx = 0
pickaxe_vy = 0
gravity = 0.5
bounce = -0.3

def get_pickaxe_rect():
    return pygame.Rect(pickaxe_x, pickaxe_y, PICK_W, PICK_H)

def draw_triangle_pickaxe(surf, x, y, angle_deg):
    points = [
        (0, 0),
        (PICK_W, 0),
        (PICK_W // 2, PICK_H),
    ]
    tri_surf = pygame.Surface((PICK_W, PICK_H), pygame.SRCALPHA)
    pygame.draw.polygon(tri_surf, (220, 220, 220), points)
    rotated = pygame.transform.rotate(tri_surf, angle_deg)
    rect = rotated.get_rect(center=(x + PICK_W // 2, y + PICK_H // 2))
    surf.blit(rotated, rect.topleft)

# ---------------------------------------------------------
# CHAT + COMMANDS + DRAGGABLE UI
# ---------------------------------------------------------
chat_log = []
MAX_CHAT_LOG = 10

# Commands panel (bottom-left by default)
commands_panel_rect = pygame.Rect(20, HEIGHT - 300, 380, 220)
dragging_panel = False
drag_offset = (0, 0)

# Chat box (bottom-left by default)
chat_box_rect = pygame.Rect(20, HEIGHT - 180, 400, 200)
dragging_chat = False
chat_drag_offset = (0, 0)

available_commands = [
    "!left right left left right right",
    "!tnt",
]

local_chat_input = ""

def add_chat_line(text):
    chat_log.append(text)
    if len(chat_log) > MAX_CHAT_LOG:
        chat_log.pop(0)

def dig_side(direction):
    pick_rect = get_pickaxe_rect()
    if direction == "left":
        tx = pick_rect.left - 1
    else:
        tx = pick_rect.right + 1
    ty = pick_rect.centery

    for b in blocks[:]:
        if b.rect.collidepoint(tx, ty):
            if b.kind == "tnt":
                explode_at(b.rect.centerx, b.rect.centery, launch=False)
            blocks.remove(b)
            break

def move_one_block(direction):
    global pickaxe_x
    if direction == "left":
        pickaxe_x -= BLOCK_SIZE
    elif direction == "right":
        pickaxe_x += BLOCK_SIZE

    if pickaxe_x < 0:
        pickaxe_x = 0
    if pickaxe_x > WIDTH - PICK_W:
        pickaxe_x = WIDTH - PICK_W

    dig_side(direction)

def parse_command(text, author=""):
    words = text.strip().split()
    if not words:
        return

    if words[0].startswith("!"):
        words[0] = words[0][1:]

    for w in words:
        lw = w.lower()
        if lw == "left":
            move_one_block("left")
        elif lw == "right":
            move_one_block("right")
        elif lw == "tnt":
            rect = get_pickaxe_rect()
            explode_at(rect.centerx, rect.centery, launch=True)

    if author:
        add_chat_line(f"{author}: {text}")
    else:
        add_chat_line(f"DEV: {text}")

def draw_commands_panel():
    pygame.draw.rect(screen, (20, 20, 20), commands_panel_rect)
    pygame.draw.rect(screen, (255, 255, 255), commands_panel_rect, 2)
    y = commands_panel_rect.y + 10
    title = font_small.render("Commands:", True, (255, 255, 0))
    screen.blit(title, (commands_panel_rect.x + 10, y))
    y += 30
    for cmd in available_commands:
        line = font_small.render(cmd, True, (220, 220, 220))
        screen.blit(line, (commands_panel_rect.x + 10, y))
        y += 24

def draw_chat_box():
    pygame.draw.rect(screen, (0, 0, 0), chat_box_rect)
    pygame.draw.rect(screen, (255, 255, 255), chat_box_rect, 2)
    y = chat_box_rect.y + 10
    for line in chat_log:
        txt = font_small.render(line, True, (255, 255, 255))
        screen.blit(txt, (chat_box_rect.x + 10, y))
        y += 22

# ---------------------------------------------------------
# LOBBY / MENU / DEV MODE / LIVESTREAM URL
# ---------------------------------------------------------
in_lobby = True
dev_mode = False
backspace_spam = 0
BACKSPACE_THRESHOLD = 20

start_button_rect = pygame.Rect(0, 0, 200, 60)

stream_url = ""
url_active = False
url_rect = pygame.Rect(0, 0, 500, 40)

yt_chat = None
video_id = ""

def extract_video_id(url):
    if "v=" in url:
        part = url.split("v=", 1)[1]
        part = part.split("&", 1)[0]
        return part.strip()
    return url.strip().split("/")[-1]

def connect_youtube_chat():
    global yt_chat, video_id
    yt_chat = None
    if not stream_url.strip():
        return
    video_id = extract_video_id(stream_url)
    if not video_id:
        return
    try:
        yt_chat = pytchat.create(video_id=video_id)
    except Exception as e:
        print("Failed to connect chat:", e)
        yt_chat = None

def draw_lobby():
    screen.fill((15, 15, 30))

    title = font_big.render("Falling Pickaxe", True, (255, 255, 255))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    url_width = 500
    url_height = 40
    url_rect.w = url_width
    url_rect.h = url_height
    url_rect.x = WIDTH // 2 - url_width // 2
    url_rect.y = HEIGHT // 2 - 60

    label = font_small.render("Livestream URL:", True, (200, 200, 200))
    screen.blit(label, (url_rect.x, url_rect.y - 28))

    pygame.draw.rect(screen, (30, 30, 30), url_rect)
    pygame.draw.rect(screen, (255, 255, 255), url_rect, 2)
    url_txt = font_small.render(stream_url, True, (255, 255, 255))
    screen.blit(url_txt, (url_rect.x + 5, url_rect.y + 8))

    start_button_rect.w = 200
    start_button_rect.h = 60
    start_button_rect.x = WIDTH // 2 - start_button_rect.w // 2
    start_button_rect.y = url_rect.y + 70

    pygame.draw.rect(screen, (0, 150, 0), start_button_rect)
    start_txt = font_small.render("START", True, (255, 255, 255))
    screen.blit(start_txt, (
        start_button_rect.centerx - start_txt.get_width() // 2,
        start_button_rect.centery - start_txt.get_height() // 2
    ))

    info = font_small.render("Drag commands + chat before starting.", True, (200, 200, 200))
    screen.blit(info, (WIDTH // 2 - info.get_width() // 2, start_button_rect.y + 80))

    if dev_mode:
        dev_txt = font_small.render("DEV MODE (local chat enabled)", True, (255, 80, 80))
        screen.blit(dev_txt, (WIDTH - dev_txt.get_width() - 20, 20))

    draw_commands_panel()
    draw_chat_box()

# ---------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------
def game_loop():
    global WIDTH, HEIGHT, screen
    global pickaxe_x, pickaxe_y, pickaxe_vx, pickaxe_vy
    global in_lobby, dragging_panel, drag_offset, local_chat_input
    global dev_mode, backspace_spam, current_depth, health
    global stream_url, url_active, yt_chat
    global dragging_chat, chat_drag_offset

    fullscreen = False
    reset_world()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if yt_chat is not None:
                    yt_chat.terminate()
                pygame.quit()
                sys.exit()

            if event.type == pygame.VIDEORESIZE and not fullscreen:
                WIDTH, HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    in_lobby = True
                    reset_world()
                    chat_log.clear()
                    local_chat_input = ""
                    if yt_chat is not None:
                        yt_chat.terminate()
                        yt_chat = None

                if event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        info = pygame.display.Info()
                        WIDTH, HEIGHT = info.current_w, info.current_h
                    else:
                        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

                if in_lobby:
                    if not url_active and event.key == pygame.K_BACKSPACE:
                        backspace_spam += 1
                        if backspace_spam >= BACKSPACE_THRESHOLD:
                            dev_mode = True

                    if url_active:
                        if event.key == pygame.K_BACKSPACE:
                            stream_url = stream_url[:-1]
                        elif event.key == pygame.K_RETURN:
                            url_active = False
                        elif event.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                            try:
                                paste_text = pyperclip.paste()
                                if paste_text:
                                    stream_url += paste_text
                            except:
                                pass
                        else:
                            if event.unicode.isprintable():
                                stream_url += event.unicode
                else:
                    if dev_mode:
                        if event.key == pygame.K_RETURN:
                            text = local_chat_input.strip()
                            if text:
                                parse_command(text, author="DEV")
                            local_chat_input = ""
                        elif event.key == pygame.K_BACKSPACE:
                            local_chat_input = local_chat_input[:-1]
                        else:
                            if event.unicode.isprintable():
                                local_chat_input += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if in_lobby and start_button_rect.collidepoint(event.pos):
                        in_lobby = False
                        backspace_spam = 0
                        connect_youtube_chat()

                    if commands_panel_rect.collidepoint(event.pos):
                        dragging_panel = True
                        drag_offset = (event.pos[0] - commands_panel_rect.x,
                                       event.pos[1] - commands_panel_rect.y)

                    if chat_box_rect.collidepoint(event.pos):
                        dragging_chat = True
                        chat_drag_offset = (event.pos[0] - chat_box_rect.x,
                                            event.pos[1] - chat_box_rect.y)

                    if in_lobby and url_rect.collidepoint(event.pos):
                        url_active = True
                    elif in_lobby:
                        url_active = False

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging_panel = False
                    dragging_chat = False

            if event.type == pygame.MOUSEMOTION:
                if dragging_panel:
                    commands_panel_rect.x = event.pos[0] - drag_offset[0]
                    commands_panel_rect.y = event.pos[1] - drag_offset[1]
                if dragging_chat:
                    chat_box_rect.x = event.pos[0] - chat_drag_offset[0]
                    chat_box_rect.y = event.pos[1] - chat_drag_offset[1]

        if in_lobby:
            draw_lobby()
            pygame.display.flip()
            clock.tick(60)
            continue

        if yt_chat is not None and yt_chat.is_alive():
            try:
                for c in yt_chat.get().sync_items():
                    msg = c.message
                    author = c.author.name
                    if msg.startswith("!"):
                        parse_command(msg, author=author)
                    else:
                        add_chat_line(f"{author}: {msg}")
            except Exception as e:
                print("Chat error:", e)

        pickaxe_vy += gravity
        pickaxe_x += pickaxe_vx
        pickaxe_y += pickaxe_vy

        if pickaxe_x < 0:
            pickaxe_x = 0
            pickaxe_vx *= -0.5
        if pickaxe_x > WIDTH - PICK_W:
            pickaxe_x = WIDTH - PICK_W
            pickaxe_vx *= -0.5

        threshold = HEIGHT * 0.6
        if pickaxe_y > threshold:
            dy = pickaxe_y - threshold
            pickaxe_y -= dy
            for b in blocks:
                b.rect.y -= dy

        if get_highest_y() < -BLOCK_SIZE * 2:
            blocks[:] = [b for b in blocks if b.rect.y > -BLOCK_SIZE * 2]

        while get_lowest_y() < HEIGHT + BLOCK_SIZE * 2:
            spawn_row(current_depth, get_lowest_y() + BLOCK_SIZE)
            current_depth += 1

        pick_rect = get_pickaxe_rect()
        hit = None
        for b in blocks:
            if pick_rect.colliderect(b.rect):
                hit = b
                break

        if hit:
            if hit.kind == "tnt":
                explode_at(hit.rect.centerx, hit.rect.centery, launch=False)
                blocks.remove(hit)
            else:
                blocks.remove(hit)

            if pickaxe_vy > 0:
                pickaxe_y = hit.rect.top - PICK_H
            else:
                pickaxe_y = hit.rect.bottom
            pickaxe_vy *= bounce

        if health <= 0:
            reset_world()

        screen.fill((10, 10, 30))

        for b in blocks:
            b.draw(screen)

        vel = pygame.math.Vector2(pickaxe_vx, pickaxe_vy)
        angle = -vel.angle_to((1, 0)) if vel.length() > 0 else 0
        draw_triangle_pickaxe(screen, pickaxe_x, pickaxe_y, angle)

        draw_commands_panel()
        draw_chat_box()

        if dev_mode:
            label = font_small.render("DEV chat:", True, (200, 200, 200))
            screen.blit(label, (20, HEIGHT - 40))
            txt = font_small.render(local_chat_input, True, (255, 255, 255))
            screen.blit(txt, (130, HEIGHT - 40))
        else:
            info = font_small.render("Chat: YouTube only (DEV mode enables local typing)", True, (200, 200, 200))
            screen.blit(info, (20, HEIGHT - 40))

        hp_text = font_small.render(f"HP: {health}", True, (255, 255, 255))
        screen.blit(hp_text, (WIDTH - hp_text.get_width() - 20, 20))

        if dev_mode:
            dev_txt = font_small.render("DEV MODE", True, (255, 80, 80))
            screen.blit(dev_txt, (WIDTH - dev_txt.get_width() - 20, 50))

        pygame.display.flip()
        clock.tick(60)

# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------
if __name__ == "__main__":
    current_depth = generate_initial()
    game_loop()
