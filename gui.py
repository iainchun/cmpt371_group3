# gui.py

import tkinter as tk
import random

GRID_SIZE = 8
CELL_SIZE = 60
CANVAS_WIDTH = GRID_SIZE * CELL_SIZE
CANVAS_HEIGHT = GRID_SIZE * CELL_SIZE

PLAYER_NAME = input("Enter your player name: ")
PLAYER_COLOR = random.choice(["red", "blue", "green", "orange", "purple", "brown"])

class GameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Deny and Conquer - Multiplayer Strategy Grid")

        # Player label
        self.label = tk.Label(root, text=f"Player: {PLAYER_NAME}",
                              fg=PLAYER_COLOR, font=("Helvetica", 14, "bold"))
        self.label.pack(pady=5)

        # Canvas
        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="#f0f0f0")
        self.canvas.pack()

        self.player_color = PLAYER_COLOR
        self.board = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.rects = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.drawing = False
        self.draw_area = set()
        self.locked_square = None

        self.draw_grid()

        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def draw_grid(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x0 = col * CELL_SIZE
                y0 = row * CELL_SIZE
                x1 = x0 + CELL_SIZE
                y1 = y0 + CELL_SIZE
                rect = self.canvas.create_rectangle(x0, y0, x1, y1,
                                                    fill="white", outline="black")
                self.rects[row][col] = rect

    def on_mouse_down(self, event):
        row, col = event.y // CELL_SIZE, event.x // CELL_SIZE
        if self.board[row][col] is None:
            # Highlight only this square
            for r in range(GRID_SIZE):
                for c in range(GRID_SIZE):
                    self.canvas.itemconfig(self.rects[r][c], outline="black", width=1)
            self.canvas.itemconfig(self.rects[row][col], outline="gold", width=3)

            self.locked_square = (row, col)
            self.drawing = True
            self.draw_area = set()

    def on_mouse_drag(self, event):
        if not self.drawing or not self.locked_square:
            return
        row, col = self.locked_square
        x, y = event.x, event.y
        cell_x0 = col * CELL_SIZE
        cell_y0 = row * CELL_SIZE
        if cell_x0 <= x < cell_x0 + CELL_SIZE and cell_y0 <= y < cell_y0 + CELL_SIZE:
            pixel = (x, y)
            if pixel not in self.draw_area:
                self.draw_area.add(pixel)
                # Shadow
                self.canvas.create_oval(x+1, y+1, x+5, y+5, fill="black", outline="black")
                # Color
                self.canvas.create_oval(x, y, x+4, y+4,
                                        fill=self.player_color,
                                        outline=self.player_color)

    def on_mouse_up(self, event):
        self.drawing = False
        self.draw_area = set()
        self.locked_square = None

if __name__ == "__main__":
    root = tk.Tk()
    app = GameGUI(root)
    root.mainloop()
