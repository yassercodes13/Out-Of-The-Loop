from flows.substates import InterruptSubstate
from telegram import Update
from adapters.telegram.messaging import delete_popup
from services.lifecycle_services import remove_players
from models import Game, Session

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