import socket
import threading
import time

# Server setup
ip = '0.0.0.0'
port = 12345
current_clients = 0
clients = []
max_score = 64
scores = {}
names = {}
client_ids = {}
client_colors = {}
used_colors = set()
available_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]

board_locks = [[threading.Lock() for _ in range(8)] for _ in range(8)]
owners = [[-1 for _ in range(8)] for _ in range(8)]
lockers = [[-1 for _ in range(8)] for _ in range(8)]

game_started = False
game_won = False
lock = threading.Lock()

def broadcast(msg):
    for c in clients:
        try:
            c.sendall((msg + "\n").encode())
        except:
            pass

def get_unique_color():
    for color in available_colors:
        if color not in used_colors:
            used_colors.add(color)
            return color
    return (0, 0, 0)

def check_scores():
    # Win condition 1: > half the board
    for client in clients:
        if scores.get(client, 0) > max_score // 2:
            return [client]                      # <-- list with one winner

    # Win condition 2: board full – highest score wins
    total_claimed = sum(1 for row in owners for cell in row if cell != -1)
    if total_claimed == max_score:
        max_val = max(scores.values(), default=0)
        return [c for c, s in scores.items() if s == max_val]  # <-- list (len≥1)
    return []                                     # nobody yet



def handle_client(client, pid):
    global game_won
    try:
        color = get_unique_color()
        client_colors[client] = color
        client_ids[client] = pid

        # Assign and broadcast player color
        client.sendall(f"id_and_color,{pid},{color[0]},{color[1]},{color[2]}\n".encode())
        broadcast(f"player_color,{pid},{color[0]},{color[1]},{color[2]}")

        while not game_started:
            time.sleep(0.1)

        while not game_won:
            msg = client.recv(1024).decode().strip()
            for line in msg.split("\n"):
                parts = line.strip().split(",")

                if parts[0] == "name":
                    names[client] = parts[1]
                    broadcast(f"player_name,{pid},{parts[1]}")

                elif parts[0] == "hold_start":
                    r, c = int(parts[1]), int(parts[2])
                    with board_locks[r][c]:
                        if owners[r][c] == -1 and lockers[r][c] == -1:
                            lockers[r][c] = pid
                            broadcast(f"hold_status,{r},{c},{pid},{time.time()}")

                elif parts[0] == "hold_end":
                    r, c = int(parts[1]), int(parts[2])
                    duration = float(parts[3])

                    if lockers[r][c] == pid:
                        if duration >= 2.9: # hold time
                            owners[r][c] = pid
                            lockers[r][c] = -1

                            if client in scores:
                                scores[client] += 1

                            color = client_colors[client]
                            broadcast(f"claim,{r},{c},{pid},{color[0]},{color[1]},{color[2]}")
                            broadcast(f"player_score,{pid},{scores.get(client, 0)}")

                            winners = check_scores()
                            if winners:                           # one or many
                                for w in winners:
                                    w_id    = client_ids[w]
                                    w_name  = names.get(w, f"P{w_id}")
                                    broadcast(f"player_won,{w_id},{w_name},0,0,0")
                                with lock:
                                    game_won = True

                        else:
                            lockers[r][c] = -1
                            broadcast(f"void,{r},{c}")

    except Exception as e:
        print(f"[ERROR] Client {pid}: {e}")

    finally:
        with lock:
            used_colors.discard(client_colors.get(client, ()))
            client_colors.pop(client, None)
            client_ids.pop(client, None)
            names.pop(client, None)
            scores.pop(client, None)
            if client in clients:
                clients.remove(client)
            client.close()

def start_server():
    global current_clients, game_started
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen(4)
    print("Server listening...")

    start_time = time.time()
    pid = 0
    countdown_sent = False

    while not game_started:
        now = time.time()
        # Start 10-second countdown when 3 or more players have joined
        if current_clients >= 3 and not countdown_sent:
            target = now + 10
            broadcast(f"start_time,{target}")
            countdown_sent = True
        # After countdown, start the game regardless of player count    
        if countdown_sent and now >= target:
            game_started = True
            break

          # Wait for new players
        try:
            server.settimeout(0.1)
            client, addr = server.accept()
            print(f"New client: {addr}")
            with lock:
                clients.append(client)
                current_clients += 1
                scores[client] = 0
            threading.Thread(target=handle_client, args=(client, pid)).start()
            pid += 1
        except socket.timeout:
            continue

if __name__ == "__main__":
    start_server()
