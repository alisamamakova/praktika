import pygame
import sys
import random

pygame.init()

screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
pygame.display.set_caption("Косынка")
icon = pygame.image.load('image/icon.png')
pygame.display.set_icon(icon)

bg = pygame.image.load('image/background.jpg')
click_sound = pygame.mixer.Sound('sound/sound1.mp3')

BUTTON_COLOR = (50, 110, 20)
BUTTON_HOVER_COLOR = (100, 160, 70)
TEXT_COLOR = (255, 255, 255)
SLIDER_COLOR = (200, 200, 200)
SLIDER_HANDLE_COLOR = (100, 100, 100)

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 50
SLIDER_WIDTH = 200
SLIDER_HEIGHT = 20
SLIDER_HANDLE_WIDTH = 10

font = pygame.font.Font(None, 36)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect(center=(x, y))
    surface.blit(textobj, textrect)

def create_button(x, y, width, height, text):
    rect = pygame.Rect(x, y, width, height)
    return {'rect': rect, 'text': text}

buttons = [
    create_button(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT, 'Новая игра'),
    create_button(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT, 'Настройки'),
    create_button(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT, 'Выйти')
]

sound_buttons = [
    create_button(0, 0, BUTTON_WIDTH, BUTTON_HEIGHT, 'Назад')
]

show_settings = False
volume = 0.5
slider = pygame.Rect(0, 0, SLIDER_WIDTH, SLIDER_HEIGHT)
slider_handle = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HEIGHT)
dragging = False

game_started = False

suits = ['hearts', 'diamonds', 'clubs', 'spades']
values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [{'suit': suit, 'value': value} for suit in suits for value in values]

selected_card = None
dragging_cards = []
dragging_offset = (0, 0)

def shuffle_deck(deck):
    random.shuffle(deck)

def setup_game(deck):
    tableau = [[] for _ in range(7)]
    for i in range(7):
        for j in range(i + 1):
            tableau[i].append(deck.pop())
        tableau[i][-1]['face_up'] = True
    stock = deck
    foundations = [[] for _ in range(4)]
    waste = []
    return tableau, stock, foundations, waste

def load_card_images():
    card_images = {}
    for suit in suits:
        for value in values:
            card_key = f'{value}_{suit}'
            card_images[card_key] = pygame.image.load(f'image/{card_key}.png')
    card_images['back'] = pygame.image.load('image/back.png')
    return card_images

card_images = load_card_images()

def draw_game_state(tableau, stock, foundations, waste, scaled_card_width, scaled_card_height, scale_factor):
    screen.fill((0, 128, 0))
    window_width, window_height = screen.get_size()
    x_offset = 20
    y_offset = 20

    # Draw the foundations
    for i, foundation in enumerate(foundations):
        x = x_offset + i * (scaled_card_width + 10)
        y = y_offset
        if foundation:
            card = foundation[-1]
            card_image = card_images[f"{card['value']}_{card['suit']}"]
        else:
            card_image = card_images['back']
        card_image = pygame.transform.scale(card_image, (scaled_card_width, scaled_card_height))
        screen.blit(card_image, (x, y))

    # Draw the waste
    if waste:
        card_image = card_images[f"{waste[-1]['value']}_{waste[-1]['suit']}"]
    else:
        card_image = card_images['back']
    card_image = pygame.transform.scale(card_image, (scaled_card_width, scaled_card_height))
    screen.blit(card_image, (x_offset + 5 * (scaled_card_width + 10), y_offset))

    # Draw the stock
    if stock:
        card_image = card_images['back']
    else:
        card_image = pygame.Surface((scaled_card_width, scaled_card_height), pygame.SRCALPHA)
    card_image = pygame.transform.scale(card_image, (scaled_card_width, scaled_card_height))
    screen.blit(card_image, (x_offset + 6 * (scaled_card_width + 10), y_offset))

    # Draw the tableau
    for i, pile in enumerate(tableau):
        x = x_offset + i * (scaled_card_width + 10)
        y = y_offset + scaled_card_height + 20
        for card in pile:
            if 'face_up' in card and card['face_up']:
                card_image = card_images[f"{card['value']}_{card['suit']}"]
            else:
                card_image = card_images['back']
            card_image = pygame.transform.scale(card_image, (scaled_card_width, scaled_card_height))
            screen.blit(card_image, (x, y))
            y += int(30 * scale_factor)  # Overlapping cards

    # Draw the dragging cards
    if dragging_cards:
        for index, card in enumerate(dragging_cards):
            card_image = card_images[f"{card['value']}_{card['suit']}"]
            card_image = pygame.transform.scale(card_image, (scaled_card_width, scaled_card_height))
            screen.blit(card_image, (pygame.mouse.get_pos()[0] - dragging_offset[0], pygame.mouse.get_pos()[1] - dragging_offset[1] + index * int(30 * scale_factor)))

    pygame.display.update()

def update_button_positions():
    window_width, window_height = screen.get_size()
    center_x = window_width // 2
    start_y = window_height // 2 - 100

    target_buttons = sound_buttons if show_settings else buttons
    if show_settings:
        slider.centerx = center_x
        slider.y = start_y + len(target_buttons) * (BUTTON_HEIGHT + 20)
        slider_handle.center = (slider.x + int(volume * SLIDER_WIDTH), slider.centery)
        sound_buttons[0]['rect'].centerx = center_x
        sound_buttons[0]['rect'].y = slider.bottom + 20
    else:
        for i, button in enumerate(target_buttons):
            button['rect'].centerx = center_x
            button['rect'].y = start_y + i * (BUTTON_HEIGHT + 20)

def is_valid_move(card, target_pile):
    if not target_pile:
        return card['value'] == 'K'
    top_card = target_pile[-1]
    valid_suit = (card['suit'] in ['hearts', 'diamonds'] and top_card['suit'] in ['clubs', 'spades']) or \
                 (card['suit'] in ['clubs', 'spades'] and top_card['suit'] in ['hearts', 'diamonds'])
    valid_value = values.index(card['value']) == values.index(top_card['value']) - 1
    return valid_suit and valid_value

def is_valid_foundation_move(card, foundation):
    if not foundation:
        return card['value'] == 'A'
    top_card = foundation[-1]
    valid_suit = card['suit'] == top_card['suit']
    valid_value = values.index(card['value']) == values.index(top_card['value']) + 1
    return valid_suit and valid_value

def check_win(foundations):
    return all(len(foundation) == 13 for foundation in foundations)

run = True
tableau, stock, foundations, waste = [], [], [], []

while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            update_button_positions()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if show_settings and slider.collidepoint(mouse_pos):
                dragging = True
            else:
                target_buttons = sound_buttons if show_settings else buttons
                for button in target_buttons:
                    if button['rect'].collidepoint(mouse_pos):
                        click_sound.play()
                        if button['text'] == 'Новая игра':
                            shuffle_deck(deck)
                            tableau, stock, foundations, waste = setup_game(deck)
                            game_started = True
                        elif button['text'] == 'Настройки':
                            show_settings = True
                            update_button_positions()
                        elif button['text'] == 'Выйти':
                            run = False
                        elif button['text'] == 'Назад':
                            show_settings = False
                            update_button_positions()
                if game_started:
                    window_width, window_height = screen.get_size()
                    card_width = card_images['back'].get_width()
                    card_height = card_images['back'].get_height()
                    scale_factor = min((window_width - 20 * 2) / (7 * (card_width + 10)),
                                       (window_height - 20 * 2) / (len(tableau[0]) * 30 + card_height))
                    scaled_card_width = int(card_width * scale_factor)
                    scaled_card_height = int(card_height * scale_factor)
                    for i, pile in enumerate(tableau):
                        x = 20 + i * (scaled_card_width + 10)
                        y = 20 + scaled_card_height + 20
                        for j, card in enumerate(pile):
                            card_rect = pygame.Rect(x, y, scaled_card_width, scaled_card_height)
                            if card_rect.collidepoint(mouse_pos) and 'face_up' in card and card['face_up']:
                                selected_card = (i, j)
                                dragging_cards = pile[j:]
                                dragging_offset = (mouse_pos[0] - x, mouse_pos[1] - y - j * int(30 * scale_factor))
                                pile[j:] = []
                                break
                            y += int(30 * scale_factor)
                        if selected_card:
                            break
        elif event.type == pygame.MOUSEBUTTONUP:
            if selected_card:
                window_width, window_height = screen.get_size()
                card_width = card_images['back'].get_width()
                card_height = card_images['back'].get_height()
                scale_factor = min((window_width - 20 * 2) / (7 * (card_width + 10)),
                                   (window_height - 20 * 2) / (len(tableau[0]) * 30 + card_height))
                scaled_card_width = int(card_width * scale_factor)
                scaled_card_height = int(card_height * scale_factor)
                for i, pile in enumerate(tableau):
                    x = 20 + i * (scaled_card_width + 10)
                    y = 20 + len(pile) * int(30 * scale_factor)
                    card_rect = pygame.Rect(x, y, scaled_card_width, scaled_card_height)
                    if card_rect.collidepoint(event.pos):
                        if is_valid_move(dragging_cards[0], pile):
                            pile.extend(dragging_cards)
                            if tableau[selected_card[0]]:
                                tableau[selected_card[0]][-1]['face_up'] = True
                        else:
                            tableau[selected_card[0]].extend(dragging_cards)
                        break
                else:
                    tableau[selected_card[0]].extend(dragging_cards)
                selected_card = None
                dragging_cards = []
            dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                mouse_x = event.pos[0]
                slider_handle.centerx = min(max(mouse_x, slider.left), slider.right)
                volume = (slider_handle.centerx - slider.left) / SLIDER_WIDTH
                pygame.mixer.Sound.set_volume(click_sound, volume)

    update_button_positions()

    window_size = screen.get_size()
    scaled_bg = pygame.transform.scale(bg, window_size)
    screen.blit(scaled_bg, (0, 0))

    if game_started:
        window_width, window_height = screen.get_size()
        card_width = card_images['back'].get_width()
        card_height = card_images['back'].get_height()
        scale_factor = min((window_width - 20 * 2) / (7 * (card_width + 10)),
                           (window_height - 20 * 2) / (len(tableau[0]) * 30 + card_height))
        scaled_card_width = int(card_width * scale_factor)
        scaled_card_height = int(card_height * scale_factor)
        draw_game_state(tableau, stock, foundations, waste, scaled_card_width, scaled_card_height, scale_factor)
    else:
        mouse_pos = pygame.mouse.get_pos()
        target_buttons = sound_buttons if show_settings else buttons
        for button in target_buttons:
            color = BUTTON_HOVER_COLOR if button['rect'].collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(screen, color, button['rect'])
            draw_text(button['text'], font, TEXT_COLOR, screen, button['rect'].centerx, button['rect'].centery)

        if show_settings:
            pygame.draw.rect(screen, SLIDER_COLOR, slider)
            pygame.draw.rect(screen, SLIDER_HANDLE_COLOR, slider_handle)
            draw_text(f'Volume: {int(volume * 100)}%', font, TEXT_COLOR, screen, slider.centerx, slider.y - 30)

    pygame.display.update()

pygame.quit()
