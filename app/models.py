#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random

from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from typing import List, Tuple, TypeVar, Optional
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login

class User(db.Model, UserMixin):
    __tablename__ = "user"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    games = db.relationship("Game", backref="game", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return "<User #{id}: {username}>".format(
            id=self.id, 
            username=self.username
        )

## Game Models and Constructs ##

class GameStatus(Enum):
    IN_PROGRESS = 1
    WON = 2
    LOST = 3

class Cell(db.Model):
    __tablename__ = "cell"
    __table_args__ = {"mysql_engine": "InnoDB"}

    id = db.Column(db.Integer, primary_key=True)
    row = db.Column(db.Integer)
    col = db.Column(db.Integer)
    value = db.Column(db.Integer, default=0)
    is_mine = db.Column(db.Boolean, default=False)
    is_hit = db.Column(db.Boolean, default=False)
    is_marked_as_mine = db.Column(db.Boolean, default=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), 
        onupdate="cascade")

    def equals(self, cell):
        return cell.row == self.row and cell.col == self.col

class Game(db.Model):
    """
    A game of Minesweeper revolves around an n x n grid-game.
    * At the start of the game, a number of mines are initialized at random
      coordinates on the grid.
    * Each coordinate i, j (representing the cell grid[i][j] such that i < n && 
      j < n) that does not contain a mine, will indicate to the player how many
      mines are contained in the set of cells bordering grid[i][j]:
      { grid[a][b] | a in (i-1, i+1) && b in (j-1, j+1) }
    * Each turn, the player gets to indicate which co-ordinate they would like to
      play.
        * If the co-ordinate they chose contains a mine, the player loses.
        * If the co-ordinate they chose borders at least 1 mine, the value of
          that cell is revealed to the player.
        * If the co-ordinate they chose borders 0 mines, the entire area of cells
          up until the line of cells with a non 0 value are revealed to the player.

    Requires that num_mines <= int((grid_length**2) / 2). - i.e. the maximum
        number of mines allowed = half the total number of cells.
    Creates the following instance variables:
    ==> num_mines: The number of mines that are initialized on the grid.
    ==> grid_length: The length of one side of the grid.
    """

    __tablename__ = "game"
    __table_args__ = {"mysql_engine": "InnoDB"}

    DEFAULT_NUM_MINES = 10
    DEFAULT_GRID_LENGTH = 10
    CELL_TYPE = TypeVar("Cell", bound=Cell)

    id = db.Column(db.Integer, primary_key=True)
    num_mines = db.Column(db.Integer, default=DEFAULT_NUM_MINES)
    grid_length = db.Column(db.Integer, default=DEFAULT_GRID_LENGTH)
    num_cells = db.Column(db.Integer, default=DEFAULT_GRID_LENGTH ** 2)
    num_hit = db.Column(db.Integer, default=0)
    game_status = db.Column(db.Integer, default=GameStatus.IN_PROGRESS)
    
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), 
        onupdate="cascade")
    cells = db.relationship("Cell", backref="cell", lazy="dynamic")

    def __init__(self, user_id):
        self.user_id = user_id
        self._initialize_new_game()
        
    ## INITIALIZE GRID ##

    def _initialize_new_game(self) -> None:
        # initialize cells
        for row in range(self.grid_length):
            for col in range(self.grid_length):
                cell = Cell(row=row, col=col, game_id=self.id)
        # initialize mines
        mine_coords = self._get_mine_coords()
        for row, col in mine_coords:
            mine = self._get_cell(row, col)
            mine.is_mine = True # initialize a mine
            self._increment_mine_borders(mine)
        return grid

    def _increment_mine_borders(self, grid: List[List[CELL_TYPE]], mine: CELL_TYPE) -> None:
        row_lower = self._get_valid_coord(mine.row - 1)
        row_upper = self._get_valid_coord(mine.row + 1)
        col_lower = self._get_valid_coord(mine.col - 1)
        col_upper = self._get_valid_coord(mine.col + 1)
        for row in range(row_lower, row_upper + 1):
            for col in range(col_lower, col_upper + 1):
                cell = self._get_cell(row, col)
                if not cell.is_mine:
                    cell.value += 1

    def _get_valid_coord(self, value: int) -> int:
        return_value = value
        return_value = max(0, return_value)
        return_value = min(self.grid_length - 1, return_value)
        return return_value

    def _get_mine_coords(self) -> List[Tuple[int]]:
        mine_coords = []
        for _ in range(self.num_mines):
            # get a new unique mine
            new_mine = self._get_random_mine()
            while new_mine in mine_coords:
                new_mine = self._get_random_mine()
            mines.append(new_mine)
        return mine_coords

    def _get_random_mine(self) -> Tuple[int]:
        row = random.randint(0, self.grid_length - 1)
        col = random.randint(0, self.grid_length - 1)
        return row, col

    def _get_cell(self, row, col) -> Optional[CELL_TYPE]:
        matching_cells = [c for c in self.cells if c.row == row and c.col == col]
        assert len(matching_cells) < 2
        if len(matching_cells) == 1:
            return matching_cells[0]

    ## PLAY MOVE ##

    def play_move(self, row: int, col: int) -> None:
        """
        Updates the game to accomodate for a move at row, col
        """
        assert self.game_status == GameStatus.IN_PROGRESS
        assert self._is_valid_move(row, col)
        self._update_hit_status(row, col)
        self._update_game_status()

    def mark_mine(self, row: int, col: int):
        """
        Updates the game to accomodate for player marking a mine at
        row, col
        """
        assert self.game_status == GameStatus.IN_PROGRESS
        assert self._is_valid_move(row, col)
        self._get_cell(row, col).is_marked_as_mine = True

    def _update_hit_status(self, row: int, col: int) -> None:
        # base cases: if cell has already been hit,
        # or if these are no longer valid coordinates
        if not self._is_valid_coord(row) or \
                not self._is_valid_coord(col):
            return
        
        cell = self._get_cell(row, col)
        if cell.is_hit:
            return

        self.cell.is_hit = True
        self.num_hit += 1

        # If it doesn't border any mines, recursively 'fill' neighbor cells
        if self.cell.value == 0:
            self._update_hit_status(row - 1, col)
            self._update_hit_status(row + 1, col)
            self._update_hit_status(row, col - 1)
            self._update_hit_status(row, col + 1)

    def _is_valid_coord(self, value: int) -> bool:
        return 0 <= value < self.grid_length

    def _is_valid_move(self, row: int, col: int) -> bool:
        return self._is_valid_coord(row) and self._is_valid_coord(col) and \
               not self._get_cell(row, col).is_hit

    def _update_game_status(self) -> None:
        has_lost = any([mine.is_hit for mine in self.mines])
        has_won = self.num_cells - self.num_mines == self.num_hit
        if has_lost:
            self.game_status = GameStatus.LOST
        elif has_won:
            self.game_status = GameStatus.WON


# functions

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
