from models.user import User
from models.game import Game
from models.session import Session

active_users: dict[int, User] = {}
active_games: dict[str, Game] = {}
active_sessions: dict[int, Session] = {}