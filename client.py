import pygame
import socket
import threading
import sys
import time

WIDTH, HEIGHT = 640, 710
ROWS, COLS = 8, 8
SQUARE_SIZE = WIDTH // COLS

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
player_color = (255, 0, 0)
player_id = -1
player_name = ""
player_colors = {}
player_scores = {}
player_names = {}
winner_names = []


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

grid = [[WHITE for _ in range(COLS)] for _ in range(ROWS)]
hold_map = {}

lock = threading.Lock()
start_time = None
game_started = False

# Winner display flags
winner_declared = False
winner_text = ""
winner_color = (0, 0, 0)

# Sends a message to the server
def send_to_server(sock, msg):
    try:
        sock.sendall((msg + "\n").encode())
    except Exception as e:
        print(f"[ERROR] Failed to send: {e}")
        pygame.quit()
        sys.exit()

# Receives and handles messages from the server
def recv_from_server(sock, win):
    global player_color, player_id, start_time, game_started
    global winner_declared, winner_text, winner_color
    buffer = ""
    while True:
        try:
            data = sock.recv(1024).decode()
            if not data:
                break
            buffer += data
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                parts = line.strip().split(",")

                if parts[0] == "id_and_color":
                    player_id = int(parts[1])
                    r, g, b = int(parts[2]), int(parts[3]), int(parts[4])
                    player_color = (r, g, b)
                    player_colors[player_id] = player_color

                elif parts[0] == "player_color":
                    pid = int(parts[1])
                    r, g, b = int(parts[2]), int(parts[3]), int(parts[4])
                    player_colors[pid] = (r, g, b)

                elif parts[0] == "player_name":
                    pid = int(parts[1])
                    name = parts[2]
                    player_names[pid] = name

                elif parts[0] == "player_score":
                    pid = int(parts[1])
                    score = int(parts[2])
                    player_scores[pid] = score

                elif parts[0] == "claim":
                    game_started = True
                    r, c = int(parts[1]), int(parts[2])
                    pid = int(parts[3])
                    color = (int(parts[4]), int(parts[5]), int(parts[6]))
                    with lock:
                        grid[r][c] = color
                        hold_map.pop((r, c), None)

                elif parts[0] == "void":
                    r, c = int(parts[1]), int(parts[2])
                    with lock:
                        grid[r][c] = WHITE
                        hold_map.pop((r, c), None)

                elif parts[0] == "hold_status":
                    r, c = int(parts[1]), int(parts[2])
                    pid = int(parts[3])
                    duration = float(parts[4])
                    with lock:
                        hold_map[(r, c)] = (pid, duration)

                elif parts[0] == "start_time":
                    start_time = float(parts[1])

                elif parts[0] == "player_won":
                    win_id   = int(parts[1])
                    win_name = parts[2]
                    if win_id == player_id:
                        win_name = "You"
                    winner_names.append(win_name)

                    # Turn ["You", "Alice"] → "Winners: You & Alice"
                    winner_text   = f"Winners: {' & '.join(winner_names)}"
                    winner_color  = (0, 0, 0)
                    winner_declared = True


        except Exception as e:
            print(f"[ERROR] recv failed: {e}")
            break

def draw_grid(win, font):
    for row in range(ROWS):
        for col in range(COLS):
            pygame.draw.rect(win, grid[row][col],
                             (col * SQUARE_SIZE, row * SQUARE_SIZE + 40, SQUARE_SIZE, SQUARE_SIZE))
            pygame.draw.rect(win, BLACK,
                             (col * SQUARE_SIZE, row * SQUARE_SIZE + 40, SQUARE_SIZE, SQUARE_SIZE), 1)
            key = (row, col)
            if key in hold_map:
                pid, start_ts = hold_map[key]

                # seconds still needed to complete the 3-s hold
                remaining = max(0.0, 3.0 - (time.time() - start_ts))

                text_color = player_colors.get(pid, (0, 0, 0))
                txt = font.render(f"{remaining:0.1f}s", True, text_color)
                win.blit(txt, (col * SQUARE_SIZE + 5, row * SQUARE_SIZE + 45))


def draw_scoreboard(win, font):
    x = 10
    y = 5
    sorted_scores = sorted(player_scores.items(), key=lambda x: -x[1])
    for pid, score in sorted_scores:
        name = player_names.get(pid, f"P{pid}")
        color = player_colors.get(pid, (0, 0, 0))
        text = font.render(f"{name}: {score}", True, color)
        win.blit(text, (x, y))
        x += text.get_width() + 20

# countdown before game starts
def draw_countdown(win, font):
    if start_time and not game_started and not winner_declared:
        remaining = int(start_time - time.time())
        if remaining > 0:
            text = font.render(f"Waiting for players... Game starts in {remaining}s", True, BLACK)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            win.blit(text, text_rect)

def main():
    global player_name
    player_name = input("Enter your name: ")

    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Deny and Conquer")
    font = pygame.font.SysFont(None, 24)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
        send_to_server(sock, f"name,{player_name}")
    except:
        print("Connection failed.")
        return

    threading.Thread(target=recv_from_server, args=(sock, win), daemon=True).start()

    clock = pygame.time.Clock()
    holding = False
    start_time_local = 0
    current_cell = None

    while True:
        clock.tick(60)
        win.fill((240, 240, 240))
        draw_scoreboard(win, font)
        draw_grid(win, font)
        draw_countdown(win, font)

        # Show hold time
        if holding and current_cell:
            remaining = max(0.0, 3.0 - (time.time() - start_time_local))
            row, col = current_cell
            txt = font.render(f"{remaining:0.1f}s", True, player_color)
            win.blit(txt, (col * SQUARE_SIZE + 30, row * SQUARE_SIZE + 70))

        # Show winner screen and exit
        if winner_declared:
            font_big = pygame.font.SysFont(None, 48)
            text = font_big.render(winner_text, True, winner_color)
            rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            win.blit(text, rect)
            pygame.display.update()
            pygame.time.delay(5000)
            pygame.quit()
            sys.exit()

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and not winner_declared:
                x, y = pygame.mouse.get_pos()
                if y < 40:
                    continue
                row, col = (y - 40) // SQUARE_SIZE, x // SQUARE_SIZE
                current_cell = (row, col)
                holding = True
                start_time_local = time.time()
                send_to_server(sock, f"hold_start,{row},{col}")

            if event.type == pygame.MOUSEBUTTONUP and holding and not winner_declared:
                holding = False
                row, col = current_cell
                held_duration = time.time() - start_time_local
                send_to_server(sock, f"hold_end,{row},{col},{held_duration}")
                current_cell = None

if __name__ == "__main__":
    main()
