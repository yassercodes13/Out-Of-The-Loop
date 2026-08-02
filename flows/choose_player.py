from flows.substates import InterruptSubstate
from telegram import Update
from flows.utils import *
from adapters.telegram.messaging import *
from services.game_services import remove_players
from models.player import Player
from texts.refs import TextRef, Button
from typing import TYPE_CHECKING
if TYPE_CHECKING:
  from models.game import Game
  from models.session import Session

async def render_players_screen(game: Game, session: Session, players: list[Player], all_option = False):
  text = TextRef("choose_the_player")
  buttons = [
    [Button(TextRef("text", {"text": f"{p.name}"}), f"i:player:{p.id}")] for p in game.players if p in players
  ]
  if all_option:
    buttons.append([Button(TextRef("all"), "i:remove_all")])
  buttons.append([Button(TextRef("cancel"), "i:cancel")])
  await send_popup_message(session = session, text = text, buttons = buttons, target = session)

async def handle_choose_player(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data if query else None
  if session.interrupt_substate == InterruptSubstate.REMOVE_PLAYER: 
    if data and data.startswith("i:player:"):
      id = int(data.split(":")[2])
      session.interrupt_substate = None
      await delete_popup(session)
      await remove_players(game, [id])

    elif data == "i:remove_all":
      session.interrupt_substate = None
      await delete_popup(session)
      await remove_players(game, [p.id for p in session.players])

    elif data == "i:cancel":
      session.interrupt_substate = None
      await delete_popup(session)
