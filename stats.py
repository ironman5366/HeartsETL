# External imports
import pprint


class Player:

    def __init__(self, rating: float, first_name: str, last_name: str, tag: str, player_id: int):
        self.rating = rating
        self.first_name = first_name
        self.last_name = last_name
        self.tag = tag
        self.player_id = player_id

    def __str__(self):
        return f'Player #{self.player_id} ({self.tag}): {self.first_name} {self.last_name}\nRating:{self.rating}'


class Game:


    def __init__(self, game_chunk):
        self.right = {}
        self.left = {}
        self.across = {}
        self.hold = {}
        self.points = {}
        self.game_id = game_chunk[0]['game_id']
        self.players = [p for k, p in game_chunk[0].items() if type(p) == Player ]
        for player, right_point in game_chunk[3].items():
            if player != 'identifier':
                self.right.update({player: right_point})
        for player, left_point in game_chunk[4].items():
            if player != 'identifier':
                self.left.update({player: left_point})
        for player, across_point in game_chunk[5].items():
            if player != 'identifier':
                self.across.update({player: across_point})
        for player, hold_point in game_chunk[6].items():
            if player != 'identifier':
                self.hold.update({player: hold_point})
        for player, point in game_chunk[7].items():
            if player != 'identifier':
                self.points.update({player: point})

        #print(self.players)

    def __str__(self):
        min_points = max(self.points.values())
        winner = None
        for player, pts in self.points.items():
            #print(player, points)
            if pts == min_points:
                if winner:
                    winner = f"Tie: {winner}/{player.first_name}"
                else:
                    winner = player.first_name
            elif pts < min_points:
                winner = player.first_name
                min_points = pts
        #return str(self.points)
        return f"Game {self.game_id}. Players: {', '.join([p.first_name for p in self.players])}\n" \
            f"Winner: {winner}, {min_points} points"
        #return self.players

def compare(p_1: Player, p_2: Player, g: Game):
    """
    Compare 2 players for a given game

    :param p_1: Player 1
    :param p_2: Player 2
    :param g: The game for which we're comparing them
    :return comparison: A float that compares these two players
    """
    if p_1.rating < p_2.rating:
        if g.points[p_1] < g.points[p_2]:
            return (abs(p_1.rating - p_2.rating)/10) + (abs(g.points[p_1] - g.points[p_2])/10)
        else:
            return -(abs((g.points[p_1] - g.points[p_2]))/10)
    else:
        if g.points[p_1] < g.points[p_2]:
            return abs(g.points[p_1]-g.points[p_2])/10
        else:
            return -((abs(p_1.rating - p_2.rating)/10) + ((abs(g.points[p_1]-g.points[p_2])/10)*
                                                         (1+(abs(p_1.rating - p_2.rating)/75))))