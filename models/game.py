import random
from config import POINTS_SMALL, POINTS_STANDARD, POINTS_LARGE, NUM_WORD_CHOICES
from data.modes import GameMode
from flows.states import GameState
from models.player import Player
from data.default_categories import *


class Game:

  def __init__(self, game_id, owner_id):
    self.id        = game_id
    self.owner_id  = owner_id
    self.user_ids  = [owner_id]
    self.chat_ids: list[int] = []

    # Game
    self.type = None
    self.players: list[Player] = []
    self.num_rounds = 0
    self.used_words = []
    self.round_number = 0
    self.random_mode = False
    self.random_category = False
    self.all_categories: list[Category] = []
    self.random_mode_options: list[GameMode] = []
    self.random_category_options: list[Category] = []
    self.initial_players_count = 0
    self.final_result_data: dict = {}

    # Round
    self.mode: GameMode = None
    self.category: Category = None
    self.word: str = None
    self.pairs: list[tuple] = []
    self.choices: list[str] = []
    self.round_report: list[tuple] = []  # list of (text_key, kwargs) for the flow to render
    self.word_guesser: Player = None
    self.outsiders: list[Player] = []
    self.insiders: list[Player] = []
    self.spy: Player = None
    self.round_result_data: list[dict] = []

    # teams only
    self.alpha_word = None
    self.alpha_choices = []
    self.alphas_guesses = {}
    self.alphas: list[Player] = []
    self.beta_word = None
    self.beta_choices = []
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
    self.assign_roles()
    self.assign_words_and_choices()
    self.pair_players()

    return {
      "round_number": self.round_number,
      "category":     self.category.title,
      "mode":         self.mode.label,
    }


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
      Player(name=n, session_id=session_id, id=length + i)
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
      if   player.role == "insider":    self.insiders.append(player)
      elif player.role == "outsider":   self.outsiders.append(player)
      elif player.role == "alpha":      self.alphas.append(player)
      elif player.role == "beta":       self.betas.append(player)
      elif player.role == "spy":        self.spy = player
      elif player.role == "detective":  self.detective = player


  def assign_words_and_choices(self):
    if self.category is None:
      self.random_category = True

    if self.random_category:
      self.category = random.choice(self.random_category_options)

    og_list = self.category.words.copy()
    word_list = [w for w in og_list if w not in self.used_words]

    if len(word_list) <= NUM_WORD_CHOICES:
      self.used_words = [w for w in self.used_words if w not in og_list]

    if self.mode == GameMode.TEAMS:
      self.alpha_word = random.choice(word_list)
      self.used_words.append(self.alpha_word)
      word_list.remove(self.alpha_word)

      self.beta_word = random.choice(word_list)
      self.used_words.append(self.beta_word)
      word_list.remove(self.beta_word)

      self.alpha_choices = random.sample(word_list, NUM_WORD_CHOICES - 1) + [self.beta_word]
      random.shuffle(self.alpha_choices)

      self.beta_choices = random.sample(word_list, NUM_WORD_CHOICES - 1) + [self.alpha_word]
      random.shuffle(self.beta_choices)

      for player in self.players:
        if   player.role == "alpha":      player.word = self.alpha_word
        elif player.role == "beta":       player.word = self.beta_word
        elif player.role == "detective":
          player.alpha_word = self.alpha_word
          player.beta_word  = self.beta_word
    else:
      self.word = random.choice(word_list)
      self.used_words.append(self.word)
      word_list.remove(self.word)
      self.choices = random.sample(word_list, NUM_WORD_CHOICES - 1) + [self.word]
      random.shuffle(self.choices)

      for player in self.players:
        player.word = self.word if player.role != "outsider" else "??????"


  def pair_players(self):
    askers = self.players[:]
    random.shuffle(askers)
    answerers = askers[1:] + [askers[0]]
    self.pairs = list(zip(askers, answerers))


  def count_votes(self):

    for insider in self.insiders:
      if insider.voted_on and insider.voted_on.role == "outsider":
        insider.round_score += POINTS_STANDARD
        self.round_report.append(("report_insider_voted_outsider", {"name": insider.name, "target": insider.voted_on.name}))
      elif insider.voted_on and insider.voted_on.role == "insider":
        self.round_report.append(("report_insider_voted_insider", {"name": insider.name, "target": insider.voted_on.name}))

    if self.spy:
      if self.spy.voted_on and self.spy.voted_on.role == "outsider":
        for player in self.spy.votes_against:
          if player.role == "insider":
            self.spy.round_score += POINTS_SMALL
            player.round_score  -= POINTS_SMALL
            self.round_report.append(("report_insider_voted_spy_minus", {"name": player.name, "target": player.voted_on.name}))
      else:
        for player in self.spy.votes_against:
          if player.role == "insider":
            self.spy.round_score -= POINTS_SMALL
            player.round_score  += POINTS_SMALL
            self.round_report.append(("report_insider_voted_spy_plus", {"name": player.name, "target": player.voted_on.name}))

      sign = '+' if self.spy.round_score > 0 else ''
      self.round_report.append(("report_spy_voted", {
        "name":        self.spy.name,
        "target":      self.spy.voted_on.name,
        "target_role": self.spy.voted_on.role,   # role identifier — flow translates via t("role_X")
        "score":       f"{sign}{self.spy.round_score}",
      }))

    for outsider in self.outsiders:
      if outsider.voted_on:
        self.round_report.append(("report_outsider_voted", {
          "name":        outsider.name,
          "target":      outsider.voted_on.name,
          "target_role": outsider.voted_on.role,  # role identifier — flow translates
        }))
      if not outsider.votes_against:
        outsider.round_score += POINTS_SMALL
        self.round_report.append(("report_outsider_no_votes", {"name": outsider.name}))

    for alpha in self.alphas:
      if   alpha.voted_on and alpha.voted_on.role == "beta":
        alpha.round_score += POINTS_SMALL
        self.round_report.append(("report_alpha_voted_beta",       {"name": alpha.name, "target": alpha.voted_on.name}))
      elif alpha.voted_on and alpha.voted_on.role == "alpha":
        alpha.round_score -= POINTS_SMALL
        self.round_report.append(("report_alpha_voted_alpha",      {"name": alpha.name, "target": alpha.voted_on.name}))
      elif alpha.voted_on and alpha.voted_on.role == "detective":
        alpha.round_score -= POINTS_SMALL
        self.round_report.append(("report_alpha_voted_detective",  {"name": alpha.name, "target": alpha.voted_on.name}))

    for beta in self.betas:
      if   beta.voted_on and beta.voted_on.role == "alpha":
        beta.round_score += POINTS_SMALL
        self.round_report.append(("report_beta_voted_alpha",       {"name": beta.name, "target": beta.voted_on.name}))
      elif beta.voted_on and beta.voted_on.role == "beta":
        beta.round_score -= POINTS_SMALL
        self.round_report.append(("report_beta_voted_beta",        {"name": beta.name, "target": beta.voted_on.name}))
      elif beta.voted_on and beta.voted_on.role == "detective":
        beta.round_score -= POINTS_SMALL
        self.round_report.append(("report_beta_voted_detective",   {"name": beta.name, "target": beta.voted_on.name}))

    if self.detective:
      self.round_report.append(("report_detective_voted", {
        "name":        self.detective.name,
        "target":      self.detective.voted_on.name,
        "target_role": self.detective.voted_on.role,  # role identifier — flow translates
      }))

    if self.outsiders:
      self.outsiders.sort(key=lambda p: (len(p.votes_against), -p.round_score), reverse=True)


  def check_word(self, word_choice: str):
    if word_choice == self.word:
      self.word_guesser.round_score += POINTS_STANDARD
      self.round_report.append(("report_correct_word", {"name": self.word_guesser.name}))
      return True
    else:
      self.round_report.append(("report_wrong_word", {"name": self.word_guesser.name}))
      return False


  def check_suspect(self, suspect: Player):
    guesser = self.outsiders[0]
    if suspect.role == 'outsider':
      guesser.round_score += POINTS_LARGE
      self.round_report.append(("report_correct_outsider", {"name": guesser.name, "suspect": suspect.name}))
      return True
    else:
      guesser.round_score -= POINTS_STANDARD
      self.round_report.append(("report_wrong_outsider", {"name": guesser.name, "suspect": suspect.name}))
      return False


  def check_detection(self):
    if not self.detective:
      return None

    correct = 0
    self.round_report.append(("report_detective_header", {}))

    for sus in self.detective.sus_alphas:
      self.round_report.append(("report_detective_sus_alpha", {"name": sus.name}))
      if sus in self.alphas:
        self.detective.round_score += POINTS_SMALL
        self.round_report.append(("report_detective_correct", {}))
        correct += 1
      else:
        self.detective.round_score -= POINTS_SMALL
        self.round_report.append(("report_detective_wrong", {}))

    for sus in self.detective.sus_betas:
      self.round_report.append(("report_detective_sus_beta", {"name": sus.name}))
      if sus in self.betas:
        self.detective.round_score += POINTS_SMALL
        self.round_report.append(("report_detective_correct", {}))
        correct += 1
      else:
        self.detective.round_score -= POINTS_SMALL
        self.round_report.append(("report_detective_wrong", {}))

    round_score = self.detective.round_score  # save before add_up_score() resets it to 0
    sign = '+' if round_score > 0 else ''
    self.round_report.append(("report_detective_overall", {"score": f"{sign}{round_score}"}))
    self.detective.add_up_score()

    return {
      "correct": correct,
      "total":   len(self.players) - 1,
      "score":   round_score,
    }


  def check_team_guess(self):
    mini_report = []

    # --- Alphas ---
    tie_entries = []
    top_voted_words = []
    most_votes = max(self.alphas_guesses.values())
    for word, votes in self.alphas_guesses.items():
      if votes == most_votes:
        top_voted_words.append(word)

    if len(top_voted_words) > 1:
      tie_entries = [("report_team_tie", {"words": ", ".join(top_voted_words), "votes": most_votes})]
    alpha_guess = top_voted_words[0] if len(top_voted_words) == 1 else random.choice(top_voted_words)

    if alpha_guess == self.beta_word:
      mini_report.append(("report_team_correct", {"team": "alpha", "word": alpha_guess}))
      mini_report += tie_entries
      mini_report.append(("report_team_scored_plus", {}))
      for alpha in self.alphas:
        alpha.round_score += POINTS_SMALL
    else:
      mini_report.append(("report_team_wrong", {"team": "alpha", "word": alpha_guess}))
      mini_report += tie_entries
      mini_report.append(("report_team_scored_minus", {}))
      for alpha in self.alphas:
        alpha.round_score -= POINTS_SMALL

    # --- Betas ---
    tie_entries = []
    top_voted_words = []
    most_votes = max(self.betas_guesses.values())
    for word, votes in self.betas_guesses.items():
      if votes == most_votes:
        top_voted_words.append(word)

    if len(top_voted_words) > 1:
      tie_entries = [("report_team_tie", {"words": ", ".join(top_voted_words), "votes": most_votes})]
    beta_guess = top_voted_words[0] if len(top_voted_words) == 1 else random.choice(top_voted_words)

    if beta_guess == self.alpha_word:
      mini_report.append(("report_team_correct", {"team": "beta", "word": beta_guess}))
      mini_report += tie_entries
      mini_report.append(("report_team_scored_plus", {}))
      for beta in self.betas:
        beta.round_score += POINTS_SMALL
    else:
      mini_report.append(("report_team_wrong", {"team": "beta", "word": beta_guess}))
      mini_report += tie_entries
      mini_report.append(("report_team_scored_minus", {}))
      for beta in self.betas:
        beta.round_score -= POINTS_SMALL

    self.round_report += mini_report
    return mini_report


  def round_result(self, rewrite=False):
    if self.round_result_data and not rewrite:
      return self.round_result_data

    for player in self.players:
      player.add_up_score()

    scores_snapshot = [(p, p.score) for p in self.players]
    ranked = sorted(scores_snapshot, key=lambda x: x[1], reverse=True)
    rank_map = {p: i for i, (p, _) in enumerate(ranked)}

    rows = []
    for p, score in ranked:
      prev_rank    = p.last_rank
      current_rank = rank_map[p]

      if   prev_rank is None:          arrow = "➡️"
      elif current_rank < prev_rank:   arrow = "⬆️"
      elif current_rank > prev_rank:   arrow = "⬇️"
      else:                            arrow = "➡️"

      p.last_rank = current_rank
      rows.append({"arrow": arrow, "name": p.name, "role": p.role, "score": score})

    self.round_result_data = rows
    return rows


  def final_result(self):
    if self.final_result_data:
      return self.final_result_data

    winning_score = max(p.score for p in self.players)
    losing_score  = min(p.score for p in self.players)
    winners = [p.name for p in self.players if p.score == winning_score]
    losers  = [p.name for p in self.players if p.score == losing_score]

    self.final_result_data = {
      "tie":           winning_score == losing_score,
      "winning_score": winning_score,
      "winners":       winners,
      "losers":        losers,
    }
    return self.final_result_data


  def reset_round(self):
    self.final_result_data  = {}
    self.word               = None
    self.choices            = []
    self.pairs              = []
    self.round_report       = []
    self.word_guesser       = None
    self.insiders           = []
    self.outsiders          = []
    self.spy                = None
    self.round_result_data  = []
    self.detective          = None
    self.alphas             = []
    self.alpha_word         = None
    self.alpha_choices      = []
    self.betas              = []
    self.beta_word          = None
    self.beta_choices       = []
    self.alphas_guesses     = {}
    self.betas_guesses      = {}

    for player in self.players:
      player.clear_leftovers()


  def restart_game(self):
    self.used_words    = []
    self.round_number  = 0
    self.reset_round()
    for player in self.players:
      player.reset()
    self.state      = GameState.SETUP
    self.turn_index = 0


  def get_player_by_id(self, id: int):
    return next((p for p in self.players if p.id == id), None)

  def remove_player(self, id: int):
    self.players = [p for p in self.players if p.id != id]