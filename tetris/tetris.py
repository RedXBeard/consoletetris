# coding=utf-8
from __future__ import print_function

import os
import signal
import sys
import threading
import time
from random import choice

import click

from shapes import COLORS, SHAPES


EXIT_TEXT = 'Please, CNTR+c one more time.\r'
EXIT_COUNT = 0


class ServiceExit(Exception):
    pass


def service_shutdown(signum, frame):
    global EXIT_COUNT
    if EXIT_COUNT < 1:
        print(EXIT_TEXT)
    EXIT_COUNT += 1
    raise ServiceExit


class Shape(threading.Thread):
    rotate = 0
    current_shape = None
    current_rotate = None
    board = None

    def __init__(self):
        threading.Thread.__init__(self)
        self.shutdown_flag = threading.Event()

    @staticmethod
    def reset():
        Shape.current_shape = Shape.current_rotate = Shape.rotate = None

    @staticmethod
    def get_shape(board):
        Shape.current_shape = Shape.current_shape or SHAPES[choice(SHAPES.keys())]
        Shape.rotate = Shape.rotate is None and choice(range(len(Shape.current_shape))) or Shape.rotate
        Shape.current_rotate = Shape.current_rotate or Shape.current_shape[Shape.rotate or 0]
        Shape.board = board

    def run(self):
        while not self.shutdown_flag.is_set():
            if not Shape.current_shape:
                continue

            try:
                key = click.getchar().lower()
                if key == ' ':
                    try:
                        Shape.rotate = Shape.rotate + 1
                        Shape.current_rotate = Shape.current_shape[Shape.rotate]
                    except IndexError:
                        Shape.rotate = 0
                        Shape.current_rotate = Shape.current_shape[Shape.rotate]
                    except TypeError:
                        continue
                    finally:
                        out = self.board.col - 1 - self.board.col_count - len(Shape.current_rotate)
                        self.board.col_count += min(0, out)
                        self.board.update()
                elif key == 'a':
                    try:
                        if self.board.check_rl_movement(-1):
                            self.board.col_count -= 1
                            self.board.update()
                    except TypeError:
                        continue
                elif key == 'd':
                    try:
                        if self.board.check_rl_movement(1):
                            self.board.col_count += 1
                            self.board.update()
                    except TypeError:
                        continue
                elif key == 's':
                    try:
                        self.board.move_down()
                    except TypeError:
                        continue
                elif key == 'q':
                    raise KeyboardInterrupt
            except KeyboardInterrupt:
                os.kill(os.getpid(), signal.SIGINT)


class Tetris(threading.Thread):
    placeholder = '* '
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'

    def __init__(self, row=40, col=40):
        threading.Thread.__init__(self)
        self.row, self.col = row, col
        self.current_shape = None
        self.ended_shapes = []
        self.shutdown_flag = threading.Event()
        self.row_count = 0
        self.col_count = (self.col - 2) / 2
        self.board_matrix = {}
        self.point = 0
        self.level = 1
        self.clear_board(reset=True)

    def clear_board(self, reset=False):
        if reset:
            self.board_matrix = {(i, j): 0 for i in range(self.col + 1) for j in range(self.row + 1)}
        else:
            matrix = self.board_matrix.items()
            for index in range(len(matrix)):
                first, rest = matrix[index]
                if 0 < rest < 10:
                    matrix[index] = (first, 0)
            self.board_matrix = dict(matrix)

    def clear_console(self):
        for i in range(0, self.row + 100):
            sys.stdout.write(self.CURSOR_UP_ONE)

    def create_board(self):
        row_print = ''
        score_text = '  SCORE'
        level_text = '  LEVEL'
        score = ' ' * (7 - len(str(self.point))) + str(self.point)
        level = ' ' * (7 - len(str(self.level))) + str(self.level)
        for row in range(self.row + 1):
            for col in range(self.col + 1 + 1 + 5):
                if row == 0 and col == self.col:
                    row_print += '┬'
                elif row == 0 and col == self.col + 6:
                    row_print += '┐'
                elif row == 1 and col > self.col:
                    row_print += score_text[col - self.col]
                    if col == self.col + 6:
                        row_print += ' '*4 + '│'
                elif row == 2 and col > self.col:
                    row_print += score[col - self.col]
                    if col == self.col + 6:
                        row_print += ' '*4 + '│'
                elif row == 5 and col > self.col:
                    row_print += level_text[col - self.col]
                    if col == self.col + 6:
                        row_print += ' ' * 4 + '│'
                elif row == 6 and col > self.col:
                    row_print += level[col - self.col]
                    if col == self.col + 6:
                        row_print += ' ' * 4 + '│'
                elif row == col == 0:
                    row_print += '┌'
                elif row == self.row and col == 0:
                    row_print += '└'
                elif row == self.row and col == self.col:
                    row_print += '┴'
                elif row == self.row and col == self.col + 6:
                    row_print += '┘'
                elif row == self.row or row == 0:
                    row_print += '─'*2
                elif col == 0 or col == self.col or col == self.col + 6:
                    row_print += '│'
                else:
                    row_print += '{}{} '.format(COLORS[str(self.board_matrix.get((col, row), 0))], ' ')
            row_print += '\r\n'
        return row_print

    def check_rl_movement(self, movement):
        if movement > 0:
            if self.col_count + len(Shape.current_rotate) + movement >= self.col:
                return False
            shape_height = len(Shape.current_rotate[0])
            shape_width = len(Shape.current_rotate)
            x_index = self.col_count + shape_width
            y_indexes = range(self.row_count, self.row_count + shape_height)
            board_points = map(lambda y: (x_index, y), y_indexes)

            shape_y_indexes = range(shape_height)
            shape_points = map(lambda y: (shape_width - 1, y), shape_y_indexes)

            board_indexes = map(lambda point: self.board_matrix.get(point), board_points)
            shape_indexes = map(lambda point: Shape.current_rotate[point[0]][point[1]], shape_points)

            if filter(lambda x: 10 < x[0] and 0 < x[1], zip(board_indexes, shape_indexes)):
                return False

        elif movement < 0:
            if self.col_count < 2:
                return False
            shape_height = len(Shape.current_rotate[0])
            shape_width = len(Shape.current_rotate)
            x_index = self.col_count
            y_indexes = range(self.row_count, self.row_count + shape_height)
            board_points = map(lambda y: (x_index, y), y_indexes)

            shape_y_indexes = range(shape_height)
            shape_points = map(lambda y: (0, y), shape_y_indexes)

            board_indexes = map(lambda point: self.board_matrix.get(point), board_points)
            shape_indexes = map(lambda point: Shape.current_rotate[point[0]][point[1]], shape_points)

            if filter(lambda x: 10 < x[0] and 0 < x[1], zip(board_indexes, shape_indexes)):
                return False
        return True

    def draw_shape(self, persist=False):
        Shape.get_shape(self)
        for i, row in enumerate(Shape.current_rotate):
            for k, col in enumerate(row):
                point = [i + self.col_count, k + self.row_count]
                if col:
                    self.board_matrix[point[0], point[1]] = col + int(persist and 10)

    def make_board_persist(self):
        self.draw_shape(persist=True)
        self.row_count = 0
        self.col_count = (self.col - 2) / 2

    def check_board_persistence(self):
        Shape.get_shape(self)
        shape_height = len(Shape.current_rotate[0])
        shape_width = len(Shape.current_rotate)

        y_index = self.row_count + shape_height - 1
        x_indexes = range(self.col_count, self.col_count + shape_width)
        board_points = map(lambda x: (x, y_index + 1), x_indexes)

        shape_x_indexes = range(shape_width)
        shape_points = map(lambda x: (x, shape_height - 1), shape_x_indexes)

        if y_index + 1 == self.row:
            return True

        board_indexes = map(lambda point: self.board_matrix.get(point), board_points)
        shape_indexes = map(lambda point: Shape.current_rotate[point[0]][point[1]], shape_points)

        if filter(lambda x: 10 < x[0] and 0 < x[1], zip(board_indexes, shape_indexes)):
            return True
        return False

    def check_rows(self):
        full_rows = []
        count = self.col - 2
        for row in range(self.row):
            row_data = filter(lambda x: x != 0, map(lambda col: self.board_matrix.get((col + 1, row)), range(count)))
            if len(row_data) == count:
                full_rows.append(row)
        for row in full_rows:
            self.point += 10
            for col in range(1, count + 1):
                self.board_matrix[(col, row)] = 0
        return full_rows

    def rearrange_board(self, rows):
        if not rows:
            return True
        count = self.col - 2

        for row in range(rows[0], 0, -1):
            for col in range(1, count + 1):
                self.board_matrix[(col, row)] = self.board_matrix[(col, row - 1)]

        for col in range(count):
            self.board_matrix[(col + 1, 0)] = 0

        _ = rows.pop(0)
        return self.rearrange_board(rows)

    def update(self):
        self.clear_console()
        self.clear_board()
        self.draw_shape()
        if self.check_board_persistence():
            self.make_board_persist()
            rows = self.check_rows()
            self.rearrange_board(rows)
            Shape.reset()
        print(self.create_board())

    def move_down(self):
        self.update()
        self.row_count += 1

    def run(self):
        while not self.shutdown_flag.is_set():
            self.move_down()
            time.sleep(.2)


def main():
    signal.signal(signal.SIGTERM, service_shutdown)
    signal.signal(signal.SIGINT, service_shutdown)
    try:
        tetris = Tetris(col=12, row=30)
        shape = Shape()
        tetris.start()
        shape.start()
        while True:
            time.sleep(0.5)
    except (KeyboardInterrupt, SystemExit, ServiceExit):
        tetris.shutdown_flag.set()
        shape.shutdown_flag.set()
        tetris.join()
        shape.join()
        raise ServiceExit


if __name__ == '__main__':
    try:
        main()
    except ServiceExit:
        sys.exit()
