from models.category import Category

default_categories = [
  Category(
    id="builtin_food",
    title="Food",
    words=[
      "Pizza", "Burger", "Sushi", "Pasta", "Salad", "Steak", "Taco", "Ice Cream", "Chocolate", "Fries",
      "Pancakes", "Waffles", "Burrito", "Ramen", "Dumplings", "Curry", "Omelette", "Lasagna", "Sandwich", "Soup",
      "Croissant", "Bagel", "Donut", "Muffin", "Brownie", "Cheesecake", "Paella", "Risotto", "Guacamole", "Hummus",
      "Noodles", "Kebab", "Falafel", "Quiche", "Shrimp", "Lobster", "Bacon", "Sausage", "Popcorn", "Pretzel"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_animals",
    title="Animals",
    words=[
      "Dog", "Cat", "Elephant", "Lion", "Tiger", "Giraffe", "Monkey", "Panda", "Kangaroo", "Zebra",
      "Dolphin", "Whale", "Shark", "Penguin", "Eagle", "Owl", "Snake", "Turtle", "Frog", "Rabbit",
      "Horse", "Wolf", "Bear", "Cheetah", "Hippo", "Rhino", "Gorilla", "Koala", "Sloth", "Otter",
      "Fox", "Deer", "Octopus", "Butterfly", "Bee", "Parrot", "Flamingo", "Camel", "Bat", "Hamster"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_countries",
    title="Countries",
    words=[
      "USA", "Canada", "Brazil", "UK", "France", "Germany", "Italy", "Spain", "Australia", "Japan",
      "China", "India", "Mexico", "Russia", "South Korea", "Egypt", "Greece", "Turkey", "Sweden", "Norway",
      "Switzerland", "Netherlands", "Argentina", "Chile", "South Africa", "Nigeria", "Kenya", "Thailand", "Vietnam", "Singapore",
      "New Zealand", "Ireland", "Portugal", "Belgium", "Austria", "Poland", "Denmark", "Finland", "Iceland", "Peru"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_professions",
    title="Professions",
    words=[
      "Doctor", "Engineer", "Teacher", "Artist", "Chef", "Pilot", "Musician", "Writer", "Scientist", "Athlete",
      "Nurse", "Architect", "Lawyer", "Firefighter", "Police Officer", "Farmer", "Photographer", "Dentist", "Programmer", "Astronaut",
      "Electrician", "Plumber", "Carpenter", "Baker", "Barista", "Journalist", "Actor", "Designer", "Mechanic", "Librarian",
      "Veterinarian", "Pharmacist", "Psychologist", "Accountant", "Soldier", "Tailor", "Coach", "Judge", "Sailor", "Miner"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_places",
    title="Places",
    words=[
      "Airport", "Hospital", "School", "Library", "Museum", "Park", "Beach", "Mountain", "Forest", "Desert",
      "Restaurant", "Hotel", "Supermarket", "Cinema", "Theater", "Gym", "Stadium", "Church", "Temple", "Castle",
      "Island", "Bridge", "Harbor", "Factory", "Office", "Bank", "Pharmacy", "Bakery", "Zoo", "Aquarium",
      "Bakery", "Cafe", "Subway Station", "University", "Gallery", "Skyscraper", "Cottage", "Farm", "Harbor", "Plaza"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_famous_people",
    title="Famous People",
    words=[
      "Albert Einstein", "Leonardo da Vinci", "Marie Curie", "Isaac Newton", "Charles Darwin", "Nikola Tesla", "Abraham Lincoln", "Mahatma Gandhi", "Nelson Mandela", "Martin Luther King Jr",
      "William Shakespeare", "Jane Austen", "Vincent van Gogh", "Pablo Picasso", "Mozart", "Beethoven", "Elvis Presley", "Michael Jackson", "Marilyn Monroe", "Audrey Hepburn",
      "Steve Jobs", "Bill Gates", "Elon Musk", "Oprah Winfrey", "Walt Disney", "Stephen Hawking", "Malala Yousafzai", "Mother Teresa", "Amelia Earhart", "Neil Armstrong",
      "Queen Elizabeth II", "Winston Churchill", "Napoleon Bonaparte", "Julius Caesar", "Cleopatra", "Aristotle", "Socrates", "Plato", "Galileo Galilei", "Marco Polo"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_hobbies",
    title="Hobbies",
    words=[
      "Gardening", "Painting", "Hiking", "Cooking", "Photography", "Dancing", "Reading", "Fishing", "Camping", "Yoga",
      "Knitting", "Running", "Gaming", "Swimming", "Baking", "Surfing", "Cycling", "Pottery", "Bird Watching", "Chess",
      "Singing", "Woodworking", "Skydiving", "Bowling", "Skiing", "Skateboarding", "Drawing", "Sewing", "Collecting Stamps", "Magic Tricks",
      "Traveling", "Origami", "Meditation", "Journaling", "Scuba Diving", "Rock Climbing", "Gardening", "Karaoke", "Billiards", "Darts"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_mythical",
    title="Mythical Creatures",
    words=[
      "Dragon", "Unicorn", "Mermaid", "Vampire", "Werewolf", "Zombie", "Ghost", "Phoenix", "Centaur", "Griffin",
      "Bigfoot", "Loch Ness Monster", "Leprechaun", "Elf", "Dwarf", "Troll", "Goblin", "Fairies", "Cyclops", "Medusa",
      "Minotaur", "Pegasus", "Sphinx", "Yeti", "Mummy", "Alien", "Wizard", "Witch", "Genie", "Gnome",
      "Hydra", "Kraken", "Cerberus", "Banshee", "Valkyrie", "Chupacabra", "Gremlin", "Ogre", "Kappa", "Chimera"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_sports",
    title="Sports & Games",
    words=[
      "Soccer", "Basketball", "Tennis", "Baseball", "Golf", "Football", "Hockey", "Volleyball", "Boxing", "Karate",
      "Cricket", "Rugby", "Badminton", "Table Tennis", "Dodgeball", "Billiards", "Poker", "Monopoly", "Scrabble", "Chess",
      "Checkers", "Paintball", "Laser Tag", "Bowling", "Softball", "Lacrosse", "Swimming", "Gymnastics", "Wrestling", "Fencing",
      "Archery", "Surfing", "Snowboarding", "Skateboarding", "Darts", "Ultimate Frisbee", "Handball", "Pickleball", "Water Polo", "Cornhole"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_household",
    title="Around the House",
    words=[
      "Toaster", "Microwave", "Refrigerator", "Washing Machine", "Vacuum Cleaner", "Television", "Blender", "Coffee Maker", "Dishwasher", "Hair Dryer",
      "Sofa", "Dining Table", "Bookshelf", "Wardrobe", "Mirror", "Curtains", "Pillow", "Blanket", "Clock", "Lamp",
      "Hammer", "Screwdriver", "Broom", "Dustpan", "Trash Can", "Toiler Paper", "Toothbrush", "Soap", "Shampoo", "Towel",
      "Laptop", "Remote Control", "Keyring", "Flashlight", "Umbrella", "Iron", "Kettle", "Picture Frame", "Candle", "Vase"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_clothing",
    title="Clothing & Fashion",
    words=[
      "T-shirt", "Blue Jeans", "Hoodie", "Leather Jacket", "Sneakers", "High Heels", "Sandals", "Boots", "Sunglasses", "Baseball Cap",
      "Wristwatch", "Necklace", "Backpack", "Scarf", "Gloves", "Winter Coat", "Swimsuit", "Pyjamas", "Socks", "Suit and Tie",
      "Skirt", "Dress", "Raincoat", "Beanie", "Belt", "Bow Tie", "Tuxedo", "Leggings", "Cardigan", "Vest",
      "Flip Flops", "Slippers", "Bathrobe", "Uniform", "Sweatpants", "Handbag", "Earrings", "Tights", "Overalls", "Briefcase"
    ],
    is_builtin=True
  ),

  Category(
    id="builtin_transport",
    title="Getting Around",
    words=[
      "Sports Car", "Motorcycle", "Bicycle", "Helicopter", "Airplane", "Submarine", "Skateboard", "Tractor", "Monster Truck", "Bus",
      "Train", "Scooter", "Speedboat", "Jet Ski", "Spaceship", "Ambulance", "Fire Truck", "Police Car", "Tank", "Hot Air Balloon",
      "Cruise Ship", "Taxi", "Pickup Truck", "Van", "Electric Car", "Forklift", "Bulldozer", "Fighter Jet", "Rocket", "Yacht",
      "Golf Cart", "Snowmobile", "Cargo Ship", "Hang Glider", "Subway", "Tram", "Parachute", "Unicycle", "Amphibious Vehicle", "Hovercraft"
    ],
    is_builtin=True
  ),


  Category(
    id="builtin_action_heroes",
    title="Heroes & Icons",
    words=[
      "Batman", "Superman", "Spider-Man", "Iron Man", "The Hulk", "Thor", "Captain America", "Black Panther", "The Joker", "Wolverine",
      "Deadpool", "Wonder Woman", "Flash", "Aquaman", "James Bond", "Indiana Jones", "Sherlock Holmes", "Luke Skywalker", "Darth Vader", "John Wick",
      "Ethan Hunt", "Rocky Balboa", "Terminator", "Robocop", "Neo", "Master Chief", "Kratos", "Lara Croft", "Harry Potter", "Gandalf",
      "Robin Hood", "Hercules", "Tarzan", "King Kong", "Godzilla", "Zorro", "The Mandalorian", "Black Widow", "Doctor Strange", "Groot"
    ],
    is_builtin=True
  ),

]