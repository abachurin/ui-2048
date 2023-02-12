from .start import *


class GameLogic:
    # This class is a collection of functions which operate with the json-style game object
    pattern = {
        'row': '4 x 4 python list of lists',
        'score': 'current score',
        'moves': 'number of moves made so far',
        'next_move': 'None (if self-play mode), 0,1,2,3 if Agent/Game moving there, or -1 if game is over'
    }

    def __init__(self):
        self.actions = {0: 'left', 1: 'up', 2: 'right', 3: 'down'}
        self.tiles = {i: str(1 << i) if i else '' for i in range(16)}

        self.table = None
        self.create_table()

    @staticmethod
    def empty_game():
        return {
            'row': [[0] * 4 for _ in range(4)],
            'score': 0,
            'moves': 0,
            'next_move': None
        }

    def create_table(self):
        self.table = {}
        for a in range(16):
            for b in range(16):
                for c in range(16):
                    for d in range(16):
                        score = 0
                        line = (a, b, c, d)
                        if (len(set(line)) == 4 and min(line)) or (not max(line)):
                            self.table[line] = (list(line), score, False)
                            continue
                        line_1 = [v for v in line if v]
                        for i in range(len(line_1) - 1):
                            x = line_1[i]
                            if x == line_1[i + 1]:
                                score += 1 << (x + 1)
                                line_1[i], line_1[i + 1] = x + 1, 0
                        line_2 = [v for v in line_1 if v]
                        line_2 = tuple(line_2 + [0] * (4 - len(line_2)))
                        self.table[line] = (list(line_2), score, line != line_2)

    def new_game(self, start=True):
        game = self.empty_game()
        if start:
            self.new_tile(game)
            self.new_tile(game)
        return game

    @staticmethod
    def empty(game):
        return [(i, j) for j in range(4) for i in range(4) if game['row'][i][j] == 0]

    @staticmethod
    def game_over(game):
        row = game['row']
        for i in range(4):
            for j in range(4):
                if row[i][j] == 0 \
                        or (i > 0 and row[i - 1][j] == row[i][j]) \
                        or (j > 0 and row[i][j - 1] == row[i][j]):
                    return False
        return True

    def new_tile(self, game):
        em = self.empty(game)
        if em:
            tile = 1 if random.randrange(10) else 2
            i, j = random.choice(em)
            game['row'][i][j] = tile
            if self.game_over(game):
                game['next_move'] = -1

    def _left(self, game):
        change = False
        new_game = self.empty_game()
        new_game['score'] = game['score']
        for i in range(4):
            line, score, change_line = self.table[tuple(game['row'][i])]
            new_game['row'][i] = line[:]
            if change_line:
                change = True
                new_game['score'] += score
        new_game['moves'] = game['moves'] + (1 if change else 0)
        return new_game, change

    @staticmethod
    def _rotate(game, move):
        new_game = {
            'score': game['score'],
            'moves': game['moves'],
            'next_move': game['next_move']
        }
        row = game['row']
        new_row = [[0] * 4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                match move:
                    case 1:
                        new_row[i][j] = row[j][3 - i]
                    case 2:
                        new_row[i][j] = row[3 - i][3 - j]
                    case 3:
                        new_row[i][j] = row[3 - j][i]
        new_game['row'] = new_row
        return new_game

    def make_move(self, game, move):
        rotated_game = self._rotate(game, move) if move else game
        new_game, change = self._left(rotated_game)
        new_game = self._rotate(new_game, 4 - move) if move else new_game
        return new_game, change


GAME = GameLogic()
