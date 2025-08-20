# cliente.py
import pygame
import asyncio
import websockets
import json
import os
import user_manager

# --- Configurações ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PLAYER_SPEED, TILE_SIZE = 4, 32
MAP_FILENAME = "meu_mapa.json"
INTERACTION_RADIUS = 50
PROXIMITY_RADIUS = 150 # Distância para iniciar a conexão de áudio/vídeo

# --- Cores ---
WHITE, BLACK, GREY, GREEN, SKIN, RED, BLUE = (255,255,255), (0,0,0), (130,130,130), (40,180,99), (255,220,177), (255, 50, 50), (40, 40, 210)
SHIRT_COLORS = [(210, 40, 40), (40, 210, 40), BLUE, (255, 140, 0)]
PANTS_COLORS = [(30, 30, 150), (50, 50, 50), (139, 69, 19)]
HAIR_COLORS = [(200, 120, 50), (255, 230, 100), (30, 30, 30), (200, 200, 200)]
UI_BG_COLOR = (50, 50, 50); GRID_COLOR = (100, 100, 100)
INTERACTIVE_OBJECTS = ['whiteboard', 'computer', 'notebook']

# --- Funções de Geração de Gráficos e UI (completas) ---
def create_player_sprite(direction, appearance, walk_frame=0):
    sprite = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    shirt_color, pants_color, hair_color = appearance['shirt'], appearance['pants'], appearance['hair']
    leg1_y, leg2_y = (18, 18)
    if walk_frame == 1: leg1_y = 16
    elif walk_frame == 2: leg2_y = 16
    pygame.draw.rect(sprite, pants_color, (8, leg1_y, 7, 10)); pygame.draw.rect(sprite, pants_color, (17, leg2_y, 7, 10))
    pygame.draw.rect(sprite, shirt_color, (8, 10, 16, 12))
    pygame.draw.circle(sprite, SKIN, (16, 8), 6); pygame.draw.rect(sprite, hair_color, (11, 2, 10, 5))
    if direction == 'down': pygame.draw.circle(sprite, BLACK, (14, 8), 1); pygame.draw.circle(sprite, BLACK, (18, 8), 1)
    elif direction == 'left': pygame.draw.circle(sprite, BLACK, (13, 8), 1)
    elif direction == 'right': pygame.draw.circle(sprite, BLACK, (19, 8), 1)
    return sprite

def get_procedural_assets():
    assets = {"objects": {}, "floors": {}}
    assets['objects']['desk'] = pygame.Surface((TILE_SIZE * 2, TILE_SIZE * 2), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['desk'], (139, 69, 19), (0, 8, 64, 40)); pygame.draw.rect(assets['objects']['desk'], (91, 46, 12), (0, 4, 64, 8)); pygame.draw.rect(assets['objects']['desk'], (91, 46, 12), (4, 48, 8, 12)); pygame.draw.rect(assets['objects']['desk'], (91, 46, 12), (52, 48, 8, 12))
    assets['objects']['meeting_table'] = pygame.Surface((TILE_SIZE * 4, TILE_SIZE * 2), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['meeting_table'], (110, 50, 10), (0, 8, 128, 56)); pygame.draw.rect(assets['objects']['meeting_table'], (80, 40, 5), (0, 4, 128, 8))
    assets['objects']['chair'] = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['chair'], (200, 200, 200), (6, 14, 20, 16)); pygame.draw.rect(assets['objects']['chair'], (180, 180, 180), (8, 2, 16, 14))
    assets['objects']['computer'] = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['computer'], (30, 30, 30), (2, 2, 28, 20)); pygame.draw.rect(assets['objects']['computer'], (0, 200, 255), (4, 4, 24, 16)); pygame.draw.rect(assets['objects']['computer'], (50, 50, 50), (12, 22, 8, 6))
    assets['objects']['notebook'] = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['notebook'], (80, 80, 80), (6, 12, 20, 4)); pygame.draw.rect(assets['objects']['notebook'], (50, 50, 50), (4, 16, 24, 6))
    assets['objects']['plant'] = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['plant'], (160, 82, 45), (10, 18, 12, 14)); pygame.draw.circle(assets['objects']['plant'], (0, 128, 0), (16, 12), 8); pygame.draw.circle(assets['objects']['plant'], (50, 205, 50), (10, 6), 6); pygame.draw.circle(assets['objects']['plant'], (50, 205, 50), (22, 6), 6)
    assets['objects']['whiteboard'] = pygame.Surface((TILE_SIZE * 3, TILE_SIZE * 2), pygame.SRCALPHA); pygame.draw.rect(assets['objects']['whiteboard'], (240, 240, 240), (0,0, 96, 64)); pygame.draw.rect(assets['objects']['whiteboard'], (100, 100, 100), (0,0, 96, 64), 4)
    assets['floors']['wood'] = pygame.Surface((TILE_SIZE, TILE_SIZE)); assets['floors']['wood'].fill((184, 134, 11)); pygame.draw.line(assets['floors']['wood'], (139, 69, 19), (0, TILE_SIZE - 1), (TILE_SIZE, TILE_SIZE - 1), 2)
    assets['floors']['carpet'] = pygame.Surface((TILE_SIZE, TILE_SIZE)); assets['floors']['carpet'].fill((100, 100, 120))
    final_assets = {"objects": {}, "floors": {}}
    for name, original_sprite in assets['objects'].items(): final_assets['objects'][name] = {'original': original_sprite, 'ui': pygame.transform.scale(original_sprite, (32, 32))}
    for name, original_sprite in assets['floors'].items(): final_assets['floors'][name] = {'original': original_sprite, 'ui': pygame.transform.scale(original_sprite, (32, 32))}
    return final_assets

def character_creation_screen(screen):
    options = ["shirt", "pants", "hair"]; option_names = {"shirt": "Camisa", "pants": "Calças", "hair": "Cabelo"}
    palettes = {"shirt": SHIRT_COLORS, "pants": PANTS_COLORS, "hair": HAIR_COLORS}
    selected_option = 0; color_indices = [0, 0, 0]
    font_title = pygame.font.Font(None, 50); font_option = pygame.font.Font(None, 36); font_instr = pygame.font.Font(None, 30)
    button_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: selected_option = (selected_option - 1) % len(options)
                if event.key == pygame.K_DOWN: selected_option = (selected_option + 1) % len(options)
                if event.key == pygame.K_LEFT: color_indices[selected_option] = (color_indices[selected_option] - 1) % len(palettes[options[selected_option]])
                if event.key == pygame.K_RIGHT: color_indices[selected_option] = (color_indices[selected_option] + 1) % len(palettes[options[selected_option]])
            if event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos): running = False
        screen.fill(GREY)
        current_appearance = {"shirt": SHIRT_COLORS[color_indices[0]],"pants": PANTS_COLORS[color_indices[1]],"hair": HAIR_COLORS[color_indices[2]],}
        preview_sprite = pygame.transform.scale(create_player_sprite("down", current_appearance), (128, 128))
        screen.blit(preview_sprite, (SCREEN_WIDTH // 2 - 64, 200))
        title_text = font_title.render("Personalize o seu Avatar", True, WHITE); screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 50))
        for i, option in enumerate(options):
            color = WHITE if i == selected_option else (180, 180, 180)
            option_text = font_option.render(f"{option_names[option]}", True, color); screen.blit(option_text, (SCREEN_WIDTH // 2 + 80, 250 + i * 50))
        instr_text = font_instr.render("Cima/Baixo para selecionar, Esquerda/Direita para mudar", True, WHITE); screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, 150))
        pygame.draw.rect(screen, GREEN, button_rect); ready_text = font_title.render("Pronto", True, WHITE); screen.blit(ready_text, (button_rect.x + (button_rect.width - ready_text.get_width())//2, button_rect.y + 5))
        pygame.display.flip()
    return current_appearance

def map_editor_loop(screen, assets):
    map_width, map_height = 25 * TILE_SIZE, 18 * TILE_SIZE; map_surface = pygame.Surface((map_width, map_height))
    ui_panel_width = 160; ui_panel = pygame.Rect(SCREEN_WIDTH - ui_panel_width, 0, ui_panel_width, SCREEN_HEIGHT)
    placed_objects = []; floor_grid = [['carpet' for _ in range(map_width // TILE_SIZE)] for _ in range(map_height // TILE_SIZE)]
    editor_mode = 'place'; selected_asset_name = None
    object_buttons = {name: {'rect': pygame.Rect(ui_panel.x + 20, 100 + i * 40, 32, 32), 'sprite': data['ui']} for i, (name, data) in enumerate(assets['objects'].items())}
    floor_buttons = {name: {'rect': pygame.Rect(ui_panel.x + 20, 100 + i * 40, 32, 32), 'sprite': data['ui']} for i, (name, data) in enumerate(assets['floors'].items())}
    mode_button_place = pygame.Rect(ui_panel.x + 10, 10, 140, 30); mode_button_paint = pygame.Rect(ui_panel.x + 10, 50, 140, 30); ready_button_rect = pygame.Rect(ui_panel.x + 10, SCREEN_HEIGHT - 70, ui_panel_width - 20, 50)
    font = pygame.font.Font(None, 24)
    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos(); mouse_buttons = pygame.mouse.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if ready_button_rect.collidepoint(mouse_pos): running = False; continue
                if mode_button_place.collidepoint(mouse_pos): editor_mode = 'place'; selected_asset_name = None
                if mode_button_paint.collidepoint(mouse_pos): editor_mode = 'paint'; selected_asset_name = None
                clicked_on_ui = False
                buttons = object_buttons if editor_mode == 'place' else floor_buttons
                for name, button in buttons.items():
                    if button['rect'].collidepoint(mouse_pos): selected_asset_name = name; clicked_on_ui = True; break
                if not clicked_on_ui and editor_mode == 'place' and selected_asset_name and mouse_pos[0] < map_width:
                    original_sprite = assets['objects'][selected_asset_name]['original']
                    grid_x, grid_y = mouse_pos[0] // TILE_SIZE, mouse_pos[1] // TILE_SIZE
                    new_object = {"name": selected_asset_name, "rect": original_sprite.get_rect(topleft=(grid_x * TILE_SIZE, grid_y * TILE_SIZE))}
                    placed_objects.append(new_object)
        if editor_mode == 'paint' and selected_asset_name and mouse_buttons[0] and mouse_pos[0] < map_width:
            grid_x, grid_y = mouse_pos[0] // TILE_SIZE, mouse_pos[1] // TILE_SIZE
            floor_grid[grid_y][grid_x] = selected_asset_name
        screen.fill(BLACK); map_surface.fill((40, 40, 40))
        for y, row in enumerate(floor_grid):
            for x, tile_name in enumerate(row): map_surface.blit(assets['floors'][tile_name]['original'], (x * TILE_SIZE, y * TILE_SIZE))
        for obj in placed_objects: map_surface.blit(assets['objects'][obj['name']]['original'], obj['rect'].topleft)
        screen.blit(map_surface, (0, 0)); pygame.draw.rect(screen, UI_BG_COLOR, ui_panel)
        pygame.draw.rect(screen, GREEN if editor_mode == 'place' else GREY, mode_button_place); screen.blit(font.render("Colocar Objetos", True, WHITE), (mode_button_place.x + 10, mode_button_place.y + 5))
        pygame.draw.rect(screen, GREEN if editor_mode == 'paint' else GREY, mode_button_paint); screen.blit(font.render("Pintar Chão", True, WHITE), (mode_button_paint.x + 20, mode_button_paint.y + 5))
        buttons_to_show = object_buttons if editor_mode == 'place' else floor_buttons
        for name, button in buttons_to_show.items():
            screen.blit(button['sprite'], button['rect'].topleft)
            if name == selected_asset_name: pygame.draw.rect(screen, GREEN, button['rect'], 2)
        pygame.draw.rect(screen, GREEN, ready_button_rect); screen.blit(pygame.font.Font(None, 40).render("Pronto", True, WHITE), (ready_button_rect.x + 35, ready_button_rect.y + 10))
        if selected_asset_name and mouse_pos[0] < map_width:
            grid_x, grid_y = mouse_pos[0] // TILE_SIZE, mouse_pos[1] // TILE_SIZE
            asset_dict = assets['objects'] if editor_mode == 'place' else assets['floors']
            ghost_sprite = asset_dict[selected_asset_name]['original'].copy(); ghost_sprite.set_alpha(150)
            screen.blit(ghost_sprite, (grid_x * TILE_SIZE, grid_y * TILE_SIZE))
        pygame.display.flip()
    return {"floor_grid": floor_grid, "objects": placed_objects}

def show_message_box(screen, text):
    font = pygame.font.Font(None, 28); words = [word.split(' ') for word in text.splitlines()]; space = font.size(' ')[0]; max_width = 600
    lines = [];
    for line in words:
        for word in line:
            if not lines or font.size(lines[-1] + ' ' + word)[0] > max_width - 40: lines.append(word)
            else: lines[-1] += ' ' + word
    text_surfaces = [font.render(line, True, BLACK) for line in lines]
    box_height = sum(surf.get_height() for surf in text_surfaces) + 40; box_rect = pygame.Rect(0, 0, max_width, box_height); box_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
    pygame.draw.rect(screen, WHITE, box_rect); pygame.draw.rect(screen, BLACK, box_rect, 2)
    y_offset = box_rect.y + 20
    for surf in text_surfaces: screen.blit(surf, (box_rect.x + 20, y_offset)); y_offset += surf.get_height()
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: waiting = False

def check_collision(hitbox, wall_rects):
    return hitbox.collidelist(wall_rects) != -1

def login_register_screen(screen):
    font_title = pygame.font.Font(None, 60); font_input = pygame.font.Font(None, 36); font_feedback = pygame.font.Font(None, 28)
    username, password = "", ""; active_field = "username"; feedback_msg, feedback_color = "", WHITE
    input_user_rect = pygame.Rect(250, 200, 300, 40); input_pass_rect = pygame.Rect(250, 280, 300, 40)
    btn_login_rect = pygame.Rect(250, 360, 140, 50); btn_register_rect = pygame.Rect(410, 360, 140, 50)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_user_rect.collidepoint(event.pos): active_field = "username"
                elif input_pass_rect.collidepoint(event.pos): active_field = "password"
                else: active_field = None
                if btn_login_rect.collidepoint(event.pos):
                    if user_manager.check_user(username, password):
                        feedback_msg, feedback_color = "Login bem-sucedido!", GREEN
                        pygame.display.flip(); pygame.time.wait(1000)
                        return user_manager.get_user(username)
                    else: feedback_msg, feedback_color = "Utilizador ou palavra-passe incorretos.", RED
                if btn_register_rect.collidepoint(event.pos):
                    if user_manager.add_user(username, password): feedback_msg, feedback_color = "Utilizador registado com sucesso!", GREEN
                    else: feedback_msg, feedback_color = "Este nome de utilizador já existe.", RED
            if event.type == pygame.KEYDOWN:
                if active_field == "username":
                    if event.key == pygame.K_BACKSPACE: username = username[:-1]
                    else: username += event.unicode
                elif active_field == "password":
                    if event.key == pygame.K_BACKSPACE: password = password[:-1]
                    else: password += event.unicode
        screen.fill(GREY)
        title_surf = font_title.render("Bem-vindo!", True, WHITE); screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
        pygame.draw.rect(screen, WHITE, input_user_rect); pygame.draw.rect(screen, GREEN if active_field == "username" else BLACK, input_user_rect, 2)
        user_surf = font_input.render(username, True, BLACK); screen.blit(user_surf, (input_user_rect.x + 10, input_user_rect.y + 5))
        pygame.draw.rect(screen, WHITE, input_pass_rect); pygame.draw.rect(screen, GREEN if active_field == "password" else BLACK, input_pass_rect, 2)
        pass_surf = font_input.render("*" * len(password), True, BLACK); screen.blit(pass_surf, (input_pass_rect.x + 10, input_pass_rect.y + 5))
        pygame.draw.rect(screen, GREEN, btn_login_rect); login_text = font_input.render("Login", True, WHITE); screen.blit(login_text, (btn_login_rect.centerx - login_text.get_width() // 2, btn_login_rect.centery - login_text.get_height() // 2))
        pygame.draw.rect(screen, BLUE, btn_register_rect); register_text = font_input.render("Registar", True, WHITE); screen.blit(register_text, (btn_register_rect.centerx - register_text.get_width() // 2, btn_register_rect.centery - register_text.get_height() // 2))
        feedback_surf = font_feedback.render(feedback_msg, True, feedback_color); screen.blit(feedback_surf, (SCREEN_WIDTH // 2 - feedback_surf.get_width() // 2, 450))
        pygame.display.flip()

def room_selection_screen(screen, user_data):
    user_rooms = user_manager.get_rooms_for_user(user_data['id'])
    font_title = pygame.font.Font(None, 50); font_room = pygame.font.Font(None, 36)
    room_buttons = {}
    btn_create_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, 250, 50)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None, None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_create_rect.collidepoint(event.pos): return 'create_new', None
                for room_id, rect in room_buttons.items():
                    if rect.collidepoint(event.pos): return 'enter_room', room_id
        screen.fill(GREY)
        title_surf = font_title.render(f"Salas de {user_data['username']}", True, WHITE); screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 50))
        y_offset = 150
        if not user_rooms:
            no_rooms_surf = font_room.render("Você ainda não tem salas.", True, WHITE); screen.blit(no_rooms_surf, (SCREEN_WIDTH // 2 - no_rooms_surf.get_width()//2, 200))
        else:
            for room in user_rooms:
                room_rect = pygame.Rect(100, y_offset, SCREEN_WIDTH - 200, 40); room_buttons[room['id']] = room_rect
                pygame.draw.rect(screen, UI_BG_COLOR, room_rect); room_surf = font_room.render(room['name'], True, WHITE); screen.blit(room_surf, (room_rect.x + 10, room_rect.y + 5))
                y_offset += 50
        pygame.draw.rect(screen, GREEN, btn_create_rect)
        create_text = font_room.render("Criar Nova Sala", True, WHITE); screen.blit(create_text, (btn_create_rect.centerx - create_text.get_width()//2, btn_create_rect.centery - create_text.get_height()//2))
        pygame.display.flip()

def get_text_input(screen, prompt):
    font = pygame.font.Font(None, 36); input_text = ""
    input_rect = pygame.Rect(250, 280, 300, 40)
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: running = False
                elif event.key == pygame.K_BACKSPACE: input_text = input_text[:-1]
                else: input_text += event.unicode
        screen.fill(GREY)
        prompt_surf = font.render(prompt, True, WHITE); screen.blit(prompt_surf, (SCREEN_WIDTH // 2 - prompt_surf.get_width() // 2, 200))
        pygame.draw.rect(screen, WHITE, input_rect); pygame.draw.rect(screen, BLACK, input_rect, 2)
        text_surf = font.render(input_text, True, BLACK); screen.blit(text_surf, (input_rect.x + 5, input_rect.y + 5))
        pygame.display.flip()
    return input_text

# --- Loop do Jogo (com nova lógica de proximidade e sinalização) ---
async def game(my_appearance, map_data, assets, logged_in_user):
    my_player = {"x": 64, "y": 64, "direction": "down", "is_moving": False, "anim_frame": 0, "anim_timer": 0}
    other_players, player_sprites = {}, {}
    webrtc_connections = {}
    screen = pygame.display.get_surface(); clock = pygame.time.Clock()
    wall_rects = [pygame.Rect(obj['rect']) for obj in map_data['objects']]
    interactive_map_objects = [obj for obj in map_data['objects'] if obj['name'] in INTERACTIVE_OBJECTS]
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            my_player_state_for_server = {**my_player, "appearance": my_appearance, "username": logged_in_user['username']}
            await websocket.send(json.dumps({"action": "join", "state": my_player_state_for_server}))
            
            running = True
            while running:
                my_player_pos = pygame.math.Vector2(my_player['x'], my_player['y'])
                nearby_interactive_object = None
                for obj in interactive_map_objects:
                    if my_player_pos.distance_to(pygame.Rect(obj['rect']).center) < INTERACTION_RADIUS:
                        nearby_interactive_object = obj; break
                
                # --- LÓGICA DE PROXIMIDADE E SINALIZAÇÃO ---
                for other_id, other_data in other_players.items():
                    if 'state' in other_data:
                        other_pos = pygame.math.Vector2(other_data['state']['x'], other_data['state']['y'])
                        distance = my_player_pos.distance_to(other_pos)
                        if distance < PROXIMITY_RADIUS and other_id not in webrtc_connections:
                            print(f"INFO: Jogador {other_data['state'].get('username', other_id)} está perto! A iniciar sinalização...")
                            webrtc_connections[other_id] = "connecting" 
                            await websocket.send(json.dumps({"action": "signal", "type": "request", "to": other_id}))
                        elif distance >= PROXIMITY_RADIUS and other_id in webrtc_connections:
                            print(f"INFO: Jogador {other_data['state'].get('username', other_id)} afastou-se. A terminar conexão.")
                            del webrtc_connections[other_id]

                for event in pygame.event.get():
                    if event.type == pygame.QUIT: running = False
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_x and nearby_interactive_object:
                        if nearby_interactive_object['name'] == 'whiteboard': show_message_box(screen, "Quadro de Ideias:\n- Plano de Ação Q3\n- Brainstorming para novo projeto")
                        elif nearby_interactive_object['name'] in ['computer', 'notebook']: show_message_box(screen, "A executar código... Parece familiar.")
                
                keys = pygame.key.get_pressed(); old_x, old_y = my_player['x'], my_player['y']; my_player['is_moving'] = False
                hitbox_offset_x, hitbox_offset_y = 8, 16; hitbox_width, hitbox_height = 16, 16
                dx, dy = 0, 0
                if keys[pygame.K_LEFT]: dx = -PLAYER_SPEED; my_player['direction'] = 'left'
                elif keys[pygame.K_RIGHT]: dx = PLAYER_SPEED; my_player['direction'] = 'right'
                if keys[pygame.K_UP]: dy = -PLAYER_SPEED; my_player['direction'] = 'up'
                elif keys[pygame.K_DOWN]: dy = PLAYER_SPEED; my_player['direction'] = 'down'
                if dx != 0 or dy != 0: my_player['is_moving'] = True
                test_hitbox_x = pygame.Rect(my_player['x'] + dx + hitbox_offset_x, my_player['y'] + hitbox_offset_y, hitbox_width, hitbox_height)
                if not check_collision(test_hitbox_x, wall_rects): my_player['x'] += dx
                test_hitbox_y = pygame.Rect(my_player['x'] + hitbox_offset_x, my_player['y'] + dy + hitbox_offset_y, hitbox_width, hitbox_height)
                if not check_collision(test_hitbox_y, wall_rects): my_player['y'] += dy
                
                if my_player['x'] != old_x or my_player['y'] != old_y:
                    my_player_state_for_server = {**my_player, "appearance": my_appearance, "username": logged_in_user['username']}
                    await websocket.send(json.dumps({"action": "move", "state": my_player_state_for_server}))
                
                if my_player['is_moving']:
                    my_player['anim_timer'] += clock.get_time()
                    if my_player['anim_timer'] > 150: my_player['anim_timer'] = 0; my_player['anim_frame'] = (my_player['anim_frame'] + 1) % 2
                else: my_player['anim_frame'] = 0
                
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                    data = json.loads(message)
                    if data.get('type') == 'gameState': other_players = data.get('data', {})
                    elif data.get('type') == 'playerUpdate': other_players.update(data.get('data', {}))
                    elif data.get('type') == 'playerDisconnect':
                        p_id = data.get('id')
                        if p_id in other_players: del other_players[p_id]
                        if p_id in webrtc_connections: del webrtc_connections[p_id]
                    elif data.get('action') == 'signal':
                        sender_id = data.get('from')
                        signal_type = data.get('type')
                        sender_username = other_players.get(sender_id, {}).get('state', {}).get('username', sender_id)
                        print(f"INFO: Recebido sinal do tipo '{signal_type}' de {sender_username}!")
                        if signal_type == 'request': webrtc_connections[sender_id] = "requested"
                except asyncio.TimeoutError: pass
                
                screen.fill(BLACK)
                for y, row in enumerate(map_data['floor_grid']):
                    for x, tile_name in enumerate(row): screen.blit(assets['floors'][tile_name]['original'], (x * TILE_SIZE, y * TILE_SIZE))
                
                drawable_entities = []
                for obj in map_data['objects']: drawable_entities.append({'y': obj['rect'][1] + obj['rect'][3], 'sprite': assets['objects'][obj['name']]['original'], 'pos': (obj['rect'][0], obj['rect'][1])})
                
                all_player_data = {**other_players, 'my_player': {'state': {**my_player, "appearance": my_appearance}}}
                for p_id, p_data in all_player_data.items():
                    if 'state' in p_data:
                        state = p_data['state']
                        appearance = state.get('appearance')
                        if appearance:
                            walk_frame = state.get('anim_frame', 0) if state.get('is_moving', False) else 0
                            sprite = create_player_sprite(state.get('direction', 'down'), appearance, walk_frame)
                            drawable_entities.append({'y': state['y'] + TILE_SIZE, 'sprite': sprite, 'pos': (state['x'], state['y'])})
                
                drawable_entities.sort(key=lambda e: e['y'])
                for entity in drawable_entities: screen.blit(entity['sprite'], entity['pos'])
                
                if nearby_interactive_object:
                    font_hint = pygame.font.Font(None, 22)
                    hint_surf = font_hint.render(" Pressione X ", True, BLACK, WHITE)
                    obj_rect = pygame.Rect(nearby_interactive_object['rect'])
                    hint_pos = (obj_rect.centerx - hint_surf.get_width() // 2, obj_rect.y - hint_surf.get_height() - 5)
                    screen.blit(hint_surf, hint_pos)
                
                pygame.display.flip(); clock.tick(60)
    except ConnectionRefusedError: print("Erro: Servidor não encontrado.")
    pygame.quit()

if __name__ == "__main__":
    pygame.init()
    main_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    all_assets = get_procedural_assets()
    
    while True:
        pygame.display.set_caption("Clone do Gather - Login")
        user_info = login_register_screen(main_screen)
        if not user_info: break
        
        logged_in = True
        while logged_in:
            pygame.display.set_caption(f"Clone do Gather - Salas de {user_info['username']}")
            action, room_id = room_selection_screen(main_screen, user_info)
            if action is None: logged_in = False; continue

            if action == 'create_new':
                room_name = get_text_input(main_screen, "Nome da nova sala:")
                if room_name:
                    pygame.display.set_caption("Clone do Gather - Editor de Mapas")
                    created_map_data = map_editor_loop(main_screen, all_assets)
                    if created_map_data:
                        user_manager.add_room(user_info['id'], room_name, created_map_data)
            
            elif action == 'enter_room':
                map_data_from_db = user_manager.get_room_data(room_id)
                if map_data_from_db:
                    pygame.display.set_caption("Clone do Gather - Criação de Avatar")
                    chosen_appearance = character_creation_screen(main_screen)
                    pygame.display.set_caption(f"Clone do Gather - {user_info['username']}")
                    asyncio.run(game(chosen_appearance, map_data_from_db, all_assets, user_info))
                else:
                    print(f"Erro: não foi possível carregar os dados da sala ID {room_id}")

    pygame.quit()
    print("Programa terminado.")