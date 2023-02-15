from random import randint


# ====================================================================================================
# ==============================================  Класс эксепшенов
# ====================================================================================================

class BoardException(Exception):  # Родительский класс экспепшенов. Зачем он нужен, если не передаёт в дочерние классы никакие параметры? Почему нельзя было использовать как родительский стандартный класс Exception?
    pass


class BoardOutException(BoardException):
    def __str__(self):
        return "Не попали по полю! Попробуйте ещй раз."


class BoardUsedException(BoardException):
    def __str__(self):
        return "Вы уже стреляли в эти координаты."


class BoardWrongShipException(BoardException):  # отлов ошибок на этапе генерации поля
    pass

# ====================================================================================================
# ==============================================  Класс точек и сравнение координат
# ====================================================================================================

class Dot:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __eq__(self, other):  # будет использоваться для проверки занята ли клетка, стрелял ли ранее по ней игрок
        return self.row == other.row and self.col == other.col

    def __repr__(self):
        return f"Dot({self.row} , {self.col})"

# ================================================ класс кораблей

class Ship:
    def __init__(self, bow, length, orient):
        self.bow = bow
        self.length = length
        self.orient = orient
        self.lives = length

    @property
    def dots(self):
        ship_dots = []
        for i in range(self.length):
            cur_row = self.bow.row
            cur_col = self.bow.col

            if self.orient == 0:
                cur_row += i

            elif self.orient == 1:
                cur_col += i

            ship_dots.append(Dot(cur_row, cur_col))

        return ship_dots

    def shoot(self, shot):
        return shot in self.dots


# ====================================================================================================
# ==============================================  Класс вывода поля
# ====================================================================================================

class Board:
    def __init__(self, hid=False, size=6):
        self.size = size
        self.hid = hid

        self.count_destroyed = 0  # число подбитых кораблей

        self.base_grid = [["O"] * size for i in range(size)]  # двумерный список поля
        # None

        self.busy = []  # список занятых клеток
        self.ships = []  # список кораблей

    # -------------------------------------- спавн кораблей
    def add_ship(self, ship):

        for d in ship.dots:
            if self.out(d) or d in self.busy:
                raise BoardWrongShipException()
        for d in ship.dots:
            self.base_grid[d.row][d.col] = "■"
            self.busy.append(d)

        self.ships.append(ship)
        self.contour(ship)

    # -------------------------------------- вывод контура вокруг кораблей

    def contour(self, ship, verb=False):
        near = [
                (-1, -1), (-1, 0), (-1, 1),  # сдвиг точек для контура относительно положения корабля.
                (0, -1), (0, 0), (0, 1),
                (1, -1), (1, 0), (1, 1)
        ]
        for d in ship.dots:
            for dr, dc in near:
                cur = Dot(d.row + dr, d.col + dc)
                if not (self.out(cur)) and cur not in self.busy:
                    if verb:
                        self.base_grid[cur.row][cur.col] = "."
                    self.busy.append(cur)

    # -------------------------------------- вывод поля

    def __str__(self):
        grid_result = "  |"  # начальная строка к которой добавляются следующие элементы поля через +=
        top_row = [f" {j + 1} |" for j in range(self.size)]  # генератор верхней строки с разделителями "|" и "-"
        grid_result += f"{''.join(top_row)}\n{'-' * 27}\n"
        for i, row in enumerate(self.base_grid):
            grid_result += f"{i + 1} | {' | '.join(row)} |\n\n"  # генератор матрицы, .join приводит к типу str
        if self.hid:
            grid_result = grid_result.replace("■", "O")
        return grid_result

    def out(self, d):
        return not ((0 <= d.row < self.size) and (0 <= d.col < self.size))

    def shot(self, d):     # -------------------------------------- Стрельба
        if self.out(d):
            raise BoardOutException

        if d in self.busy:
            raise BoardUsedException

        self.busy.append(d)

        for ship in self.ships:
            if d in ship.dots:
                ship.lives -= 1
                self.base_grid[d.row][d.col] = "X"
                if ship.lives == 0:
                    self.count_destroyed += 1
                    self.contour(ship, verb=True)  # подбитый корабль обводится контуром
                    print("Корабль уничтожен")
                    return False
                else:
                    print("Есть пробитие!")
                    return True

        self.base_grid[d.row][d.col] = "."
        print("Мимо!")
        return False

    def begin(self):
        self.busy = []


# ====================================================================================================
# ==============================================  Класс игрока
# ====================================================================================================

class Player:
    def __init__(self, board, enemy):
        self.board = board
        self.enemy = enemy

    def ask(self):
        raise NotImplementedError()

    def move(self):
        while True:
            try:
                target = self.ask()
                repeat = self.enemy.shot(target)
                return repeat
            except BoardException as e:
                print(e)

# ====================================================================================================
# ==============================================  Класс оппонента
# ====================================================================================================


class AI(Player):
    def ask(self):
        d = Dot(randint(0.5), randint(0.5))
        print(f"Ход компьютера: {d.row + 1} {d.col + 1}")
        return d


class User(Player):
    def ask(self):
        while True:
            cords = input("Ваш ход: ").split()

            if len(cords) != 2:
                print("Введите 2 координаты")
                continue

            row, col = cords

            if not (row.isdigit()) or not (col.isdigit()):
                print("Введите числа")
                continue

            row, col = int(row), int(col)

            return Dot(row - 1, col - 1)

# ====================================================================================================
# ==============================================  Класс генерации поля
# ====================================================================================================

class Game:
    def __init__(self, size=6):
        self.size = size
        pl = self.random_board()
        co = self.random_board()
        co.hid = True

        self.ai = AI(co, pl)
        self.us = User(pl, co)

    def random_board(self):
        board = None
        while board is None:
            board = self.random_place()
        return board

    def random_place(self):
        lens = [3, 2, 2, 1, 1, 1, 1]
        board = Board(size=self.size)
        attempts = 0
        for i in lens:
            while True:
                attempts += 1
                if attempts > 2000:
                    return None
                ship = Ship(Dot(randint(0, self.size), randint(0, self.size)), i, randint(0, 1))
                try:
                    board.add_ship(ship)
                    break
                except BoardWrongShipException:
                    pass
        board.begin()
        return board

    def greet(self):
        print("-------------------")
        print("  Приветсвуем вас  ")
        print("      в игре       ")
        print("    морской бой    ")
        print("-------------------")
        print(" формат ввода: x y ")
        print(" x - номер строки  ")
        print(" y - номер столбца ")

    def loop(self):
        num = 0
        while True:
            print("-" * 20)
            print("Доска пользователя:")
            print(self.us.board)
            print("-" * 20)
            print("Доска компьютера:")
            print(self.ai.board)
            if num % 2 == 0:
                print("-" * 20)
                print("Ходит пользователь!")
                repeat = self.us.move()
            else:
                print("-" * 20)
                print("Ходит компьютер!")
                repeat = self.ai.move()
            if repeat:
                num -= 1

            if self.ai.board.count == 7:
                print("-" * 20)
                print("Пользователь выиграл!")
                break

            if self.us.board.count == 7:
                print("-" * 20)
                print("Компьютер выиграл!")
                break
            num += 1

    def start(self):
        self.greet()
        self.loop()

g = Game()
g.start()