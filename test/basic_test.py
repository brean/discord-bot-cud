from discord_robot_cud.bot import round_move

def test_move():
    a = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    b = [2, 0, 4, 1, 6, 3, 8, 5, 9, 7]
    c = [4, 2, 6, 0, 8, 1, 9, 3, 7, 5]
    d = [6, 4, 8, 2, 9, 0, 7, 1, 5, 3]
    e = [8, 6, 9, 4, 7, 2, 5, 0, 3, 1]
    f = [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

    # mod = [1, 2, -2, 2, -2, 2, -2, 2, -2, -1]
    assert round_move(a) == b
    assert round_move(b) == c
    assert round_move(c) == d
    assert round_move(d) == e
    assert round_move(e) == f