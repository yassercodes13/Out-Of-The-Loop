from models.game import Game
from models.session import Session
from telegram import Update
from services.lifecycle_services import terminate_game
from adapters.telegram.messaging import *
from texts.refs import TextRef, Button


async def render_paused_screen(game: Game, owner_session: Session):
  text = TextRef("game_paused_not_enough_players", {"current_players": len(game.players)})
  buttons = [[Button(TextRef("end_game"), "g:end_paused")]]

  owner_session.waited = True
  await broadcast_message(game=game, mode="edit", text=text, exclude_session_ids=[owner_session.id])
  await edit_message(owner_session, text, buttons)


async def handle_paused(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:end_paused" and session.user_id == game.owner_id:
    await broadcast_message(game = game, mode = "edit", text = TextRef("game_ended_by_owner"))
    await terminate_game(game)
    return False

  return False