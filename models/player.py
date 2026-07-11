class Player:
  def __init__(self, name, session_id, id = 0,):
    self.id = id
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