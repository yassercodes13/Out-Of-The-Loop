class Player:
  def __init__(self, name, session_id, id = 0,):
    self.id = id                 #simple incremental id to identify players in a game, not related to user id
    self.name = name
    self.session_id = session_id

    self.role = None
    self.word = None
    self.last_rank = None
    self.pending_vote: Player = None
    self.votes_against: list[Player] = []
    self.voted_on:Player = None
    self.saw_info = 0
    self.score = 0
    self.round_score = 0
    
    #For detectives only
    self.alpha_word = None
    self.beta_word = None
    self.sus_alphas = []
    self.sus_betas = []
    self.team_guess = {}

  
  def clear_leftovers(self):
    self.role = None
    self.word = None
    self.voted_on = None
    self.pending_vote = None
    self.votes_against = []
    self.saw_info = 0
    self.round_score = 0
    self.alpha_word = None
    self.beta_word = None
    self.sus_alphas = []
    self.sus_betas = []
    self.team_guess = {}


  def reset(self):
    self.clear_leftovers()
    self.score = 0
    self.last_rank = None

  
  def vote_on(self, player):
    self.pending_vote = player

  def confirm_vote(self):
    self.voted_on = self.pending_vote
    self.pending_vote.votes_against.append(self)
    self.pending_vote = None

  
  def add_up_score(self):
    self.score += self.round_score
    self.round_score = 0

  
  def info(self):
    info_text = "info text"

    if self.role in ["outsider", "insider", "spy"]:
      info_text = (
        f"<b>{self.name}</b>\n\n"
        f"Your role is <tg-spoiler>{self.role}</tg-spoiler>\n"
        f"Your word is <tg-spoiler>{self.word}</tg-spoiler>\n\n"
        f"Current Score: {self.score}"
      )
    elif self.role in ["alpha", "beta"]:
      info_text = (
        f"<b>{self.name}</b>\n\n"
        f"Your team is <tg-spoiler>{self.role}</tg-spoiler>\n"
        f"Your word is <tg-spoiler>{self.word}</tg-spoiler>\n\n"
        f"Current Score: {self.score}"
      )
    elif self.role == "detective":
      info_text = (
        f"<b>{self.name}</b>\n\n"
        f"Your role is <tg-spoiler>{self.role}</tg-spoiler>\n"
        f"Alpha word is <tg-spoiler>{self.alpha_word}</tg-spoiler>\n"
        f"Beta word is <tg-spoiler>{self.beta_word}</tg-spoiler>\n\n"
        f"Current Score: {self.score}"
      )
    return info_text