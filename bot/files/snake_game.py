import tkinter as tk
import random

class SnakeGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Змейка")
        self.master.resizable(False, False)

        self.canvas = tk.Canvas(master, bg="black", width=400, height=400)
        self.canvas.pack()

        self.score = 0
        self.direction = "Right"
        self.snake = []
        self.food = None
        self.game_started = False

        self.create_menu()
        self.start_game()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Игра", menu=game_menu)
        game_menu.add_command(label="Новая игра", command=self.start_game)
        game_menu.add_separator()
        game_menu.add_command(label="Выход", command=self.master.quit)

    def start_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.direction = "Right"
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = self.create_food()
        self.game_started = True
        self.draw_elements()
        self.master.bind("<KeyPress>", self.change_direction)
        self.game_loop()

    def draw_elements(self):
        self.canvas.delete("snake")
        self.canvas.delete("food")

        for x, y in self.snake:
            self.canvas.create_rectangle(x, y, x + 10, y + 10, fill="green", tags="snake")

        if self.food:
            self.canvas.create_oval(self.food[0], self.food[1], self.food[0] + 10, self.food[1] + 10, fill="red", tags="food")

        self.canvas.create_text(200, 10, text=f"Счет: {self.score}", fill="white", font=("Arial", 10), tags="score")

    def create_food(self):
        while True:
            x = random.randint(0, 39) * 10
            y = random.randint(0, 39) * 10
            if (x, y) not in self.snake:
                return (x, y)

    def change_direction(self, event):
        if not self.game_started: return

        key = event.keysym
        if key == "Up" and self.direction != "Down":
            self.direction = "Up"
        elif key == "Down" and self.direction != "Up":
            self.direction = "Down"
        elif key == "Left" and self.direction != "Right":
            self.direction = "Left"
        elif key == "Right" and self.direction != "Left":
            self.direction = "Right"

    def game_loop(self):
        if not self.game_started: return

        head_x, head_y = self.snake[0]

        if self.direction == "Up":
            new_head = (head_x, head_y - 10)
        elif self.direction == "Down":
            new_head = (head_x, head_y + 10)
        elif self.direction == "Left":
            new_head = (head_x - 10, head_y)
        elif self.direction == "Right":
            new_head = (head_x + 10, head_y)

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.food = self.create_food()
        else:
            self.snake.pop()

        if self.check_collision():
            self.game_over()
            return

        self.draw_elements()
        self.master.after(100, self.game_loop)

    def check_collision(self):
        head_x, head_y = self.snake[0]

        # Wall collision
        if head_x < 0 or head_x >= 400 or head_y < 0 or head_y >= 400:
            return True

        # Self-collision
        if self.snake[0] in self.snake[1:]:
            return True

        return False

    def game_over(self):
        self.game_started = False
        self.canvas.create_text(200, 200, text="Игра окончена!", fill="white", font=("Arial", 20))
        self.canvas.create_text(200, 230, text=f"Ваш счет: {self.score}", fill="white", font=("Arial", 15))


if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGame(root)
    root.mainloop()


