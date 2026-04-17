import random
from config import *
from data.modes import GameMode
from flows.states import GameState
from models.player import Player
from data.default_categories import *

class Game:

  def __init__(self, game_id, owner_id):
    #ids
    self.id        = game_id
    self.owner_id  = owner_id
    self.user_ids  = [owner_id]
    self.chat_ids: list[int]  = [] 

    # Game
    self.type = None
    self.players: list[Player] = []
    self.num_rounds = 0
    self.used_words = []
    self.round_number = 0
    self.random_mode = False
    self.random_category = False
    self.random_mode_options: list[GameMode] = [] # Only used if random mode is chosen, stores the options the owner can choose from
    self.user_categories = []
    self.intial_players_count = 0
    self.final_result_text: str = ""

    # Round
    self.mode: GameMode = None
    self.category: Category = None
    self.word: str = None
    self.pairs: list[tuple] = []
    self.choices: list[str] = []
    self.round_report: str = ""
    self.word_guesser: Player = None
    self.outsiders: list[Player] = []
    self.insiders: list[Player] = []
    self.spy: Player = None
    self.round_result_text: str = ""
    #teams only
    self.alpha_word = None
    self.alpha_choices = []
    self.alphas_guesses = {}
    self.alphas: list[Player] = []
    
    self.beta_word = None
    self.beta_choices= []
    self.betas_guesses = {}
    self.betas: list[Player] = []
    
    self.detective: Player = None


    # State
    self.state = None
    self.sessions_ready = 0
    self.turn_index = 0
    self.names = []
        

  def start_round(self):
    self.reset_round()
    for player in self.players: 
      player.clear_leftovers()
    
    self.round_number += 1
    self.round_report = f"Round {self.round_number} Report\n\n"
    self.assign_roles()
    self.assign_words_and_choices()
    self.pair_players()

    setup_message = f"Round {self.round_number}\n\nCategory is {self.category.title}\n\nMode is {self.mode.label}"
    return setup_message
  
  def prepare_players(self, session_id, players_names):
    length = len(self.players)
    new_names = []
    for name in players_names:
      self.names.append(name)
      if self.names.count(name) > 1:
        r = self.names.count(name)
        name += f"_{r}"
      new_names.append(name)

    new_players = [
      Player(name = n, session_id = session_id, id = length + i)
      for i, n in enumerate(new_names)
    ]

    self.players.extend(new_players)

    return new_players


  def assign_roles(self):
    if self.mode == GameMode.RANDOM:
      self.random_mode = True

    if self.random_mode:
      available_modes = [m for m in self.random_mode_options if m.min_players <= len(self.players) and m != GameMode.RANDOM]
      self.mode = random.choice(available_modes)
    
    roles = []

    if self.mode == GameMode.TEAMS:
      players_per_team = len(self.players) // 2
      roles = ["alpha", "beta"] * players_per_team
      
      if len(self.players) % 2 == 1:
        roles.append("detective")
    
    else:
      num_outsiders = self.mode.num_outsiders
      num_spies = self.mode.num_spies
      num_insiders = len(self.players) - num_outsiders - num_spies
 
      roles = ["outsider"] * num_outsiders + ["spy"] * num_spies + ["insider"] * num_insiders
    
    random.shuffle(roles)
    for player in self.players:
      player.role = roles.pop()
      if player.role == "insider": self.insiders.append(player)
      elif player.role == "outsider": self.outsiders.append(player)
      elif player.role == "alpha": self.alphas.append(player)
      elif player.role == "beta": self.betas.append(player)
      elif player.role == "spy": self.spy = player
      elif player.role == "detective": self.detective = player
  
  def assign_words_and_choices(self):
    if self.category is None:           # pass nothing = passing random (temp)
      self.random_category = True
    
    if self.random_category:
      self.category = random.choice(default_categories + self.user_categories)
    
    og_list = self.category.words.copy()
    word_list = [w for w in og_list if w not in self.used_words] #Only ones not used before
    
    if len(word_list) <= NUM_CHOICES:
      self.used_words = [w for w in self.used_words if w not in og_list] #Refreshing the list

    if self.mode == GameMode.TEAMS:                                # Repeatition is badddd
      self.alpha_word = random.choice(word_list)
      self.used_words.append(self.alpha_word)
      word_list.remove(self.alpha_word)
      
      self.beta_word = random.choice(word_list)
      self.used_words.append(self.beta_word)
      word_list.remove(self.beta_word)

      self.alpha_choices = random.sample(word_list, NUM_CHOICES - 1) + [self.beta_word]
      random.shuffle(self.alpha_choices)

      self.beta_choices = random.sample(word_list, NUM_CHOICES - 1) + [self.alpha_word]
      random.shuffle(self.beta_choices)

      for player in self.players:
        if player.role == "alpha":
          player.word = self.alpha_word
        elif player.role == "beta":
          player.word = self.beta_word
        elif player.role == "detective":
          player.alpha_word = self.alpha_word
          player.beta_word = self.beta_word

    else:
      self.word = random.choice(word_list)
      self.used_words.append(self.word)
      word_list.remove(self.word)
      self.choices = random.sample(word_list, NUM_CHOICES - 1) + [self.word]
      random.shuffle(self.choices)

      for player in self.players:
        if player.role != "outsider":
          player.word = self.word
        else:
          player.word = "??????"

  def pair_players(self):
    askers = self.players[:]
    random.shuffle(askers)
    answerers = askers[1:] + [askers[0]]
    self.pairs =  list(zip(askers, answerers))
  


  def count_votes(self):
  
    for insider in self.insiders:
      
      if insider.voted_on and insider.voted_on.role == "outsider":
        insider.round_score += 10
        self.round_report += f"{insider.name} (insider) voted on {insider.voted_on.name} (outsider) (+10P)\n"
      
      elif insider.voted_on and insider.voted_on.role == "insider":
        self.round_report += f"{insider.name} (insider) voted on {insider.voted_on.name} (insider)\n"

    if self.spy:
      if self.spy.voted_on and self.spy.voted_on.role == "outsider":
        for player in self.spy.votes_against:
          if player.role == "insider":
            self.spy.round_score += 5
            player.round_score -= 5
            self.round_report += f"{player.name} (insider) voted on {player.voted_on.name} (spy) (-5P)\n"
      
      else:
        for player in self.spy.votes_against:
          if player.role == "insider":
            self.spy.round_score -= 5
            player.round_score += 5
            self.round_report += f"{player.name} (insider) voted on {player.voted_on.name} (spy) (+5P)\n"
      
      sign = '+' if self.spy.round_score > 0 else ''
      self.round_report += f"{self.spy.name} (spy) voted on {self.spy.voted_on.name} ({self.spy.voted_on.role}) ({sign}{self.spy.round_score}P)\n"
      

    for outsider in self.outsiders:
      if outsider.voted_on:      #Just for safty
        self.round_report += f"{outsider.name} (outsider) voted on {outsider.voted_on.name} ({outsider.voted_on.role})\n"
      if not outsider.votes_against:
        outsider.round_score += 5
        self.round_report += f"{outsider.name} (outsider) got no votes (+5P)\n"

    
    for alpha in self.alphas:
      
      if alpha.voted_on and alpha.voted_on.role == "beta":
        alpha.round_score += 5
        self.round_report += f"{alpha.name} (alpha) voted on {alpha.voted_on.name} (beta) (+5P)\n"
      
      elif alpha.voted_on and alpha.voted_on.role == "alpha":
        alpha.round_score -= 5
        self.round_report += f"{alpha.name} (alpha) voted on {alpha.voted_on.name} (alpha) (-5P)\n"

      
      elif alpha.voted_on and alpha.voted_on.role == "detective":
        alpha.round_score -= 5
        self.round_report += f"{alpha.name} (alpha) voted on {alpha.voted_on.name} (detective) (-5P)\n"

    
    for beta in self.betas:
      
      if beta.voted_on and beta.voted_on.role == "alpha":
        beta.round_score += 5
        self.round_report += f"{beta.name} (beta) voted on {beta.voted_on.name} (alpha) (+5P)\n"
      
      elif beta.voted_on and beta.voted_on.role == "beta":
        beta.round_score -= 5
        self.round_report += f"{beta.name} (beta) voted on {beta.voted_on.name} (beta) (-5P)\n"
      
      elif beta.voted_on and beta.voted_on.role == "detective":
        beta.round_score -= 5
        self.round_report += f"{beta.name} (beta) voted on {beta.voted_on.name} (detective) (-5P)\n"

    if self.detective:
      self.round_report += f"{self.detective.name} (detective) voted on {self.detective.voted_on.name} ({self.detective.voted_on.role})\n"


    self.round_report += "\n"
  
    if self.outsiders:
      self.outsiders.sort(key=lambda p: (len(p.votes_against), -p.round_score), reverse=True) #highest votes against, then lowest score (bad situations to cheer them up)
    


  def check_word(self, word_choice: str):
    if word_choice == self.word:
      self.word_guesser.round_score += 10
      self.round_report += f"{self.word_guesser.name} guessed the correct word (+10P)\n"
      return True
    else:
      self.round_report += f"{self.word_guesser.name} guessed the wrong word\n"
      return False
  
  def check_suspect(self, suspect: Player):
    guesser = self.outsiders[0]

    if suspect.role == 'outsider':
      guesser.round_score += 20
      self.round_report += f"{guesser.name} guessed the correct outsider ({suspect.name}) (+20P)\n"
      return True
    else:
      guesser.round_score -=10
      self.round_report += f"{guesser.name} guessed the wrong outsider ({suspect.name}) (-10P)\n"
      return False

  def check_detection(self):
    if not self.detective:
      return
    
    correct = 0
    self.round_report += "The Detective suspected:\n"
    
    for sus in self.detective.sus_alphas:
      self.round_report += f"{sus.name} to be in team Alpha: "
      if sus in self.alphas:
        self.detective.round_score += 5
        self.round_report += "Correct (+5P)\n"
        correct += 1
      else:
        self.detective.round_score -= 5
        self.round_report += "Wrong (-5P)\n"
    
    for sus in self.detective.sus_betas:
      self.round_report += f"{sus.name} to be in team Beta: "
      if sus in self.betas:
        self.detective.round_score += 5
        self.round_report += "Correct (+5P)\n"
        correct += 1
      else:
        self.detective.round_score -= 5
        self.round_report += "Wrong (-5P)\n"

    sign = '+' if self.detective.round_score > 0 else ''
    self.round_report += f"Overall score: {sign}{self.detective.round_score}P\n\n"

    result = f"{correct}/{len(self.players)-1} ({sign}{self.detective.round_score}P)"
    self.detective.add_up_score()

    return result

  def check_team_guess(self):
    mini_report = ""

    # What Alphas chose
    
    alpha_guess = ""
    tie_text = ""
    top_voted_words = []
    most_votes = max(self.alphas_guesses.values())
    
    for word,votes in self.alphas_guesses.items():
      if votes == most_votes:
        top_voted_words.append(word)
    if len(top_voted_words) == 1:
      alpha_guess = top_voted_words[0]
    else:
      tie_text = f"The words {", ".join(top_voted_words)} all got most votes ({most_votes}).\nSo the choice was random between them.\n"
      alpha_guess = random.choice(top_voted_words)
    

    # Scoring for Alphas

    if alpha_guess == self.beta_word:
      mini_report += f"Alphas voted on the word {alpha_guess} and it was correct!\n"
      mini_report += tie_text
      mini_report += f"Each team member got +5 points.\n\n"
      for alpha in self.alphas:
        alpha.round_score += 5
    else:
      mini_report += f"Alphas voted on the word {alpha_guess} and it was wrong!\n"
      mini_report += tie_text
      mini_report += f"Each team member lost -5 points.\n\n"
      for alpha in self.alphas:
        alpha.round_score -= 5
    


    # What Betas chose

    beta_guess = ""
    tie_text = ""
    top_voted_words = []
    most_votes = max(self.betas_guesses.values())

    for word,votes in self.betas_guesses.items():
      if votes == most_votes:
        top_voted_words.append(word)
    if len(top_voted_words) == 1:
      beta_guess = top_voted_words[0]
    else:
      tie_text = f"The words {", ".join(top_voted_words)} all got most votes ({most_votes}).\nSo the choice was random between them.\n"
      beta_guess = random.choice(top_voted_words)
    

    # Scoring for Betas

    if beta_guess == self.alpha_word:
      mini_report += f"Betas voted on the word {beta_guess} and it was correct!\n"
      mini_report += tie_text
      mini_report += f"Each team member got +5 points.\n\n"
      for beta in self.betas:
        beta.round_score += 5
    else:
      mini_report += f"Betas voted on the word {beta_guess} and it was wrong!\n"
      mini_report += tie_text
      mini_report += f"Each team member lost -5 points.\n\n"
      for beta in self.betas:
        beta.round_score -= 5

    self.round_report += mini_report

    return mini_report

  def get_player_by_id(self, id: int):
    return next((p for p in self.players if p.id == id), None)
  
  def remove_player(self, id: int):
    self.players = [p for p in self.players if p.id != id]
  
  def round_result(self):
    if self.round_result_text:
      return self.round_result_text
    
    for player in self.players:
      player.add_up_score()
    
    scores_snapshot = [(p, p.score) for p in self.players]
    ranked = sorted(scores_snapshot, key=lambda x: x[1], reverse=True)
    rank_map = {p: i for i, (p, _) in enumerate(ranked)}

    results_text = "🏆 Round Results 🏆\n\n"
    for p, score in ranked:
      prev_rank = p.last_rank
      current_rank = rank_map[p]

      if prev_rank is None:
        arrow = "➡️"
      elif current_rank < prev_rank:
        arrow = "⬆️"
      elif current_rank > prev_rank:
        arrow = "⬇️"
      else:
        arrow = "➡️"

      # update last_rank
      p.last_rank = current_rank

      results_text += f"{arrow} {p.name} | {p.role} | {score}\n"

    self.round_result_text = results_text
    return results_text
  
  def final_result(self):
    if self.final_result_text:
      return self.final_result_text
    
    final_result_text = ""
    
    winning_score = max(p.score for p in self.players)
    losing_score = min(p.score for p in self.players)
    winners = [p for p in self.players if p.score == winning_score]
    losers = [p for p in self.players if p.score == losing_score]
    
    if winning_score == losing_score:
      final_result_text = f"All players got {winning_score} Points!"
    else:
      if len(winners) > 1:
        final_result_text += "Winners are:\n"
      else:
        final_result_text += "Winner is:\n"
      
      final_result_text += "\n".join(["👑 " + winner.name for winner in winners])
      final_result_text += "\n\n"
      
      if len(losers) > 1:
        final_result_text += "Losers are:\n"
      else:
        final_result_text += "Loser is:\n"
      
      final_result_text += "\n".join(["😭 " + loser.name for loser in losers])

    self.final_result_text = final_result_text
    return final_result_text

  def reset_round(self):
    #just in case
    self.final_result_text = ""
    
    # Round
    self.word = None
    self.choices = []
    self.pairs = []
    self.round_report = ""
    self.word_guesser = None
    self.insiders = []
    self.outsiders = []
    self.spy = None
    self.round_result_text = ""
    
    #teams only
    self.detective: Player = None
    self.alphas: list[Player] = []
    self.alpha_word = None
    self.alpha_choices = []
    self.betas: list[Player]  = []
    self.beta_word = None
    self.beta_choices = []
    self.alphas_guesses = {}
    self.betas_guesses = {}

    for player in self.players:
      player.clear_leftovers() 

  def restart_game(self):
    # Game
    self.used_words = []
    self.round_number = 0

    # Round
    self.reset_round()

    # Players
    for player in self.players:
      player.reset()


    # State
    self.state = GameState.SETUP
    self.turn_index = 0