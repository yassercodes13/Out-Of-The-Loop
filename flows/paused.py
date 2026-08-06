from models.game import Game
from models.session import Session
from telegram import Update
from services.lifecycle_services import terminate_game
from adapters.telegram.messaging import broadcast_message
from views.common import render_game_ended_by_owner_screen

async def handle_paused(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:end_paused" and session.user_id == game.owner_id:
    screen = render_game_ended_by_owner_screen()
    await broadcast_message(game=game, mode="edit", text=screen.textref, buttons=screen.buttons)
    await terminate_game(game)
    return False

  return False