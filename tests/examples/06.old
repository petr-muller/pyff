"""Log of a single VtES game"""

from typing import Sequence

class Game:
    """Represents a VtES game"""
    # pylint: disable=too-few-public-methods
    def __init__(self, table: Sequence[str]) -> None:
        self.table: Sequence[str] = table
        self.winning_points: float = None
        self.winner: str = None
        self.players: Sequence[str] = []
        self.points: Sequence[float] = []

        for item in self.table:
            if ":" in item:
                player, points_as_str = item.split(':')
                points = float(points_as_str)
            else:
                player = item
                points = 0.0

            self.players.append(player)
            self.points.append(points)

            if points > 1 and points > (self.winning_points or 0):
                self.winning_points = points
                self.winner = player
            elif points > 1 and points == self.winning_points:
                self.winning_points = None
                self.winner = None


    def __str__(self) -> str:
        players = []
        for player, points in zip(self.players, self.points):
            if points:
                players.append(f"{player} {points:g}VP")
            else:
                players.append(player)
            if player == self.winner:
                players[-1] += " GW"

        return " \u25b6 ".join(players)
