BUTTONS = {

  # --- universal ---
  "confirm":            {"en": "Confirm",           "ar": "تأكيد"},
  "continue":           {"en": "Continue",           "ar": "متابعة"},
  "done":               {"en": "Done",               "ar": "تم"},
  "back":               {"en": "Back",               "ar": "رجوع"},
  "next":               {"en": "Next",               "ar": "التالي"},
  "skip":               {"en": "Skip",               "ar": "تخطي"},
  "got_it":             {"en": "Got it!",             "ar": "فهمت!"},
  "yes_confirm":        {"en": "Yes, confirm",        "ar": "نعم، تأكيد"},
  "no_choose_again":    {"en": "No, choose again",    "ar": "لا، اختر مجدداً"},

  # --- setup ---
  "start_game":         {"en": "Start Game",                       "ar": "ابدأ اللعبة"},
  "same_phone":         {"en": "On the same phone",                "ar": "على نفس الهاتف"},
  "multiple_phones":    {"en": "On multiple phones",               "ar": "على عدة هواتف"},
  "multiple_phones_help":{"en": "How to play with multiple phones?","ar": "كيف تلعب على عدة هواتف؟"},
  "perfect":            {"en": "Perfect!",                         "ar": "ممتاز!"},
  "join":               {"en": "Join",                             "ar": "انضم"},

  # --- category settings ---
  "category_settings":         {"en": "⚙️ Category Settings",        "ar": "⚙️ إعدادات الفئات"},
  "categories":                {"en": "Categories",                  "ar": "الفئات"},
  "create_category":           {"en": "Create Category",             "ar": "إنشاء فئة"},
  "delete_category":           {"en": "Delete Category",             "ar": "حذف فئة"},
  "delete_another_category":   {"en": "Delete another category",     "ar": "حذف فئة أخرى"},
  "view_category":             {"en": "View Category",               "ar": "عرض فئة"},
  "back_to_category_settings": {"en": "Back to category settings",   "ar": "رجوع لإعدادات الفئات"},
  "back_to_view_categories":   {"en": "Back to view categories",     "ar": "رجوع لعرض الفئات"},
  "back_to_category_selection":{"en": "Back to category selection",  "ar": "رجوع لاختيار الفئة"},
  "change_random_categories":  {"en": "Change Random Categories",    "ar": "تغيير الفئات العشوائية"},
  "yes_delete":                {"en": "Yes, delete it",              "ar": "نعم، احذفه"},
  "no_keep":                   {"en": "No, keep it",                 "ar": "لا، احتفظ به"},

  # --- mode settings ---
  "edit_random":        {"en": "⚙️ Edit Random",      "ar": "⚙️ تعديل العشوائي"},
  "modes":              {"en": "Modes",               "ar": "الأوضاع"},
  "back_to_settings":   {"en": "Back to Settings",    "ar": "رجوع للإعدادات"},
  "back_to_mode_selection": {"en": "Back to mode selection", "ar": "رجوع لاختيار الوضع"},

  # --- gameplay ---
  "start_voting":       {"en": "Start Voting",        "ar": "ابدأ التصويت"},
  "start_questioning":  {"en": "Start Questioning",   "ar": "ابدأ الأسئلة"},
  "vote_words":         {"en": "Vote Words",          "ar": "تصويت الكلمات"},
  "guess_word":         {"en": "Guess Word",          "ar": "خمّن الكلمة"},
  "guess_outsider":     {"en": "Guess Outsider",      "ar": "خمّن الغريب"},
  "guess_team_members": {"en": "Guess Team Members",  "ar": "خمّن أعضاء الفريق"},
  "extra_questions":    {"en": "Extra Questions",     "ar": "أسئلة إضافية"},
  "extra_round":        {"en": "Extra Round",         "ar": "جولة إضافية"},
  "thats_me":           {"en": "That's me!",          "ar": "أنا هو!"},
  "another_player":     {"en": "Another Player",      "ar": "لاعب آخر"},
  "get_back":           {"en": "Get back",            "ar": "رجوع"},

  # --- results ---
  "next_round":         {"en": "Next Round",          "ar": "الجولة التالية"},
  "see_results":        {"en": "See Results",         "ar": "عرض النتائج"},
  "round_report":       {"en": "Round Report",        "ar": "تقرير الجولة"},
  "end_game":           {"en": "End Game",            "ar": "إنهاء اللعبة"},
  "start_new_game":     {"en": "Start a new game",    "ar": "ابدأ لعبة جديدة"},
  "view_game_rules":    {"en": "View game rules",     "ar": "عرض قواعد اللعبة"},
  "edit_score":         {"en": "Edit Score",          "ar": "تعديل النتيجة"},
  "end_it":             {"en": "End it",              "ar": "أنهِها"},
  "start_it":           {"en": "Start it",            "ar": "ابدأها"},
  "dont_start":         {"en": "don't start",         "ar": "لا تبدأ"},
  "random":             {"en": "🎲 Random",           "ar": "🎲 عشوائي"},
  "random_with_number": {"en": "🎲 Random ({min_players_for_random})", "ar": "🎲 عشوائي ({min_players_for_random})"},

  # --- pagination ---
  "prev_page":          {"en": "<<",                  "ar": "<<"},
  "next_page":          {"en": ">>",                  "ar": ">>"},

}


def b(key, lang="en", **kwargs):
  template = BUTTONS[key][lang]
  return template.format(**kwargs) if kwargs else template