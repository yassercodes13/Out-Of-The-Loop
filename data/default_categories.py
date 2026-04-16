from uuid import uuid4
from models.category import Category

default_categories = [
  Category(
    id="builtin_food",
    title="Food",
    words=[
      "Pizza", "Burger", "Sushi", "Pasta", "Salad",
      "Steak", "Taco", "Ice Cream", "Chocolate", "Fries"
    ],
    is_builtin = True
  ),

  Category(
    id="builtin_animals",
    title="Animals",
    words=[
      "Dog", "Cat", "Elephant", "Lion", "Tiger",
      "Giraffe", "Monkey", "Panda", "Kangaroo", "Zebra"
    ],
    is_builtin = True
  ),

  Category(
    id="builtin_countries",
    title="Countries",
    words=[
      "USA", "Canada", "Brazil", "UK", "France",
      "Germany", "Italy", "Spain", "Australia", "Japan"
    ],
    is_builtin = True
  ),

  Category(
    id="builtin_professions",
    title="Professions",
    words=[
      "Doctor", "Engineer", "Teacher", "Artist", "Chef",
      "Pilot", "Musician", "Writer", "Scientist", "Athlete"
    ],
    is_builtin = True
  ),
]
