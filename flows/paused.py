from models.game import Game
from models.session import Session
from telegram import InlineKeyboardButton, Update
from data.runtime_manager import terminate_game
from texts import t, b
from adapters.telegram.messaging import *

async def render_paused_screen(game: Game, owner_session: Session):
  text = t("game_paused_not_enough_players", current_players=len(game.players))
  buttons = [[InlineKeyboardButton(b("end_game"), callback_data="g:end_paused")]]

  owner_session.waited = True
  await broadcast_message(game=game, mode="edit", text=text, exclude_chat_ids=[owner_session.chat_id])
  await edit_message(owner_session, text, buttons)


async def handle_paused(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None

  if data == "g:end_paused" and session.user_id == game.owner_id:
    await broadcast_message(game=game, mode="edit", text=t("game_ended_by_owner"))
    await terminate_game(game)
    return False

  return False