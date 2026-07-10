from data.modes import GameMode
from flows.states import GameState
from flows.substates import VoteSubstate
from telegram import InlineKeyboardButton, Update
from flows.utils import *
from models.game import Game, Player
from texts import t, b
from adapters.telegram.messaging import *

# --- screen renderers ---

async def render_start_vote_broadcast(session: Session, game: Game):
  buttons = [[InlineKeyboardButton(text=b("start_voting"), callback_data="g:revote")]]
  await broadcast_message(game=game, mode="edit", text=session.text, buttons=buttons, exclude_chat_ids=[session.chat_id])

async def render_end_vote_screen(session: Session, game: Game, ready: bool):
  text = t("done_voting")
  waiting_text = t("waiting_others_vote")  
  
  button_txt = b("reveal_outsider")
  if game.mode == GameMode.TEAMS and game.detective:
    button_txt = b("reveal_detective")
  elif game.mode == GameMode.TEAMS:
    button_txt = b("reveal_teams")
    
  buttons = [[InlineKeyboardButton(button_txt, callback_data="g:reveal")]]
  
  if session.user_id == game.owner_id and ready:
    await edit_message(session, text, buttons)
  else:
    text += waiting_text
    await edit_message(session, text)

    if ready:
      owner_session = get_session_of_owner(game=game)
      await edit_message(owner_session, t("done_voting"), buttons)

async def render_confirm_vote_screen(session: Session, voter: Player, voted_player: Player):
  text = t("confirm_vote_prompt", voter_name=voter.name, voted_name=voted_player.name)
  buttons = [
    [InlineKeyboardButton(b("yes_confirm"), callback_data="g:confirm")],
    [InlineKeyboardButton(b("no_choose_again"), callback_data="g:revote")]
  ]
  await edit_message(session, text, buttons)

async def render_select_vote_screen(session: Session, game: Game, voter: Player):
  buttons = []
  for p in game.players:
    if p != voter:
      buttons.append([InlineKeyboardButton(p.name, callback_data=f"g:vote_{p.id}")])

  if game.mode == GameMode.TEAMS:
    text = t("vote_other_team", voter_name=voter.name)
  else:
    text = t("vote_outsider", voter_name=voter.name)
  
  await edit_message(session, text, buttons)

# --- dispatch ---

async def handle_voting(update: Update, game: Game, session: Session):
  query = update.callback_query
  data = query.data

  # --- INITIALIZE ---
  if data == 'g:start_vote':
    game.sessions_ready = 0
    game.turn_index = 0
    reset_turn_indices(game)
    set_all_substates(game, VoteSubstate.SELECT)
    await render_start_vote_broadcast(session, game)
  
  elif data == 'g:revote':
    session.game_substate = VoteSubstate.SELECT

  elif data == "g:reveal" and session.game_substate == VoteSubstate.END:
    game.count_votes()
    game.state = GameState.REVEAL
    set_all_substates(game, None)
    return True

  # --- confirmation ---
  if data == "g:confirm" and session.game_substate == VoteSubstate.CONFIRM:
    voter = session.players[session.turn_index] 
    voter.confirm_vote()
    session.turn_index += 1
  
    session.game_substate = VoteSubstate.SELECT
  
    # --- END CONDITION ---

    if session.turn_index >= len(session.players):
      session.game_substate = VoteSubstate.END
      game.sessions_ready += 1
     
      ready = True if game.sessions_ready >= len(game.chat_ids) else False
      await render_end_vote_screen(session, game, ready)
      return False

  # --- handle vote selection ---

  if data.startswith("g:vote_") and session.game_substate == VoteSubstate.SELECT:
    voter = session.players[session.turn_index]  
    voted_id = int(data.replace("g:vote_", ""))
    
    voted_player = game.get_player_by_id(voted_id)
    voter.vote_on(voted_player)

    session.game_substate = VoteSubstate.CONFIRM
    await render_confirm_vote_screen(session, voter, voted_player)
    return False

  if session.game_substate == VoteSubstate.SELECT:
    # --- render current voter choices ---
    voter = session.players[session.turn_index] 
    await render_select_vote_screen(session, game, voter)
    
    return False