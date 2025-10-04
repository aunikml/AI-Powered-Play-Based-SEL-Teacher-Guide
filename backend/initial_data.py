# This file contains the initial data to "seed" the database on the first run.
# The structure of this data corresponds to the new, normalized models.

# Data for the AgeCohort table
AGE_COHORTS = [
    {"name": "0-1 years"},
    {"name": "1-2 years"},
    {"name": "2-3 years"},
    {"name": "3-4 years"}
]

# Data for the Domain table
DOMAINS = [
    {"name": "Mathematics"},
    {"name": "Language & Literacy"},
    {"name": "Science & Discovery"},
    {"name": "Socio-Emotional Development"},
    {"name": "Geography"} # Added your new domain
]

# Data for the PlayType table, including different contexts
PLAY_TYPES = [
    {"name": "Free Play", "description": "Child-led exploration using open-ended materials. Encourages creativity and curiosity.", "context": "Standard"},
    {"name": "Guided Play", "description": "Teacher provides gentle structure and scaffolding while allowing choice.", "context": "Standard"},
    {"name": "Structured Activity", "description": "Teacher-led, step-by-step activity designed for specific outcomes.", "context": "Standard"},
    {"name": "Nature Crafting", "description": "Using found natural objects like leaves, twigs, and stones to create art or structures.", "context": "Green Play"},
    {"name": "Recycled Material Building", "description": "Building towers, robots, or anything imaginable using clean recycled materials.", "context": "Green Play"},
    {"name": "Water Conservation Game", "description": "An activity focused on understanding why water is precious and how to save it.", "context": "Climate Vulnerability"},
]

# Data for the Component table.
# Structure: (component_name, age_cohort_name, domain_name)
# The backend seeder will use these names to find the correct database IDs and create the links.
COMPONENTS = [
    # Mathematics
    ("Sensory exploration (touching, stacking, dropping)", "0-1 years", "Mathematics"),
    ("Early spatial awareness", "0-1 years", "Mathematics"),
    ("Early number sense", "1-2 years", "Mathematics"),
    ("Sorting and classification", "1-2 years", "Mathematics"),
    ("Shapes and spatial awareness", "1-2 years", "Mathematics"),
    ("Patterns and sequencing", "2-3 years", "Mathematics"),
    ("Measurement and comparison", "2-3 years", "Mathematics"),
    ("Problem solving and logical thinking", "3-4 years", "Mathematics"),
    ("Mathematical language", "3-4 years", "Mathematics"),

    # Language & Literacy
    ("Listening and responding to voices and sounds", "0-1 years", "Language & Literacy"),
    ("Babbling and imitation", "0-1 years", "Language & Literacy"),
    ("Vocabulary building", "1-2 years", "Language & Literacy"),
    ("Naming familiar objects", "1-2 years", "Language & Literacy"),
    ("Following instructions", "1-2 years", "Language & Literacy"),
    ("Story listening", "2-3 years", "Language & Literacy"),
    ("Expressing needs with words", "2-3 years", "Language & Literacy"),
    ("Rhymes and songs", "2-3 years", "Language & Literacy"),
    ("Describing actions", "2-3 years", "Language & Literacy"),
    ("Storytelling and role play", "3-4 years", "Language & Literacy"),
    ("Letter and sound awareness", "3-4 years", "Language & Literacy"),
    ("Question and answer conversations", "3-4 years", "Language & Literacy"),
    ("Early writing and mark-making", "3-4 years", "Language & Literacy"),

    # Science & Discovery
    ("Exploring textures, sounds, and lights", "0-1 years", "Science & Discovery"),
    ("Observing cause and effect", "0-1 years", "Science & Discovery"),
    ("Simple observation (floating, sinking)", "1-2 years", "Science & Discovery"),
    ("Exploring natural objects", "1-2 years", "Science & Discovery"),
    ("Observing plants, animals, and weather", "2-3 years", "Science & Discovery"),
    ("Describing basic phenomena (hot/cold, light/dark)", "2-3 years", "Science & Discovery"),
    ("Experimenting and predicting outcomes", "3-4 years", "Science & Discovery"),
    ("Understanding living and non-living things", "3-4 years", "Science & Discovery"),
    ("Exploring materials and change (melting, mixing)", "3-4 years", "Science & Discovery"),

    # Socio-Emotional Development
    ("Bonding and trust building", "0-1 years", "Socio-Emotional Development"),
    ("Recognizing familiar faces", "0-1 years", "Socio-Emotional Development"),
    ("Expressing emotions", "1-2 years", "Socio-Emotional Development"),
    ("Parallel play", "1-2 years", "Socio-Emotional Development"),
    ("Recognizing others’ emotions", "1-2 years", "Socio-Emotional Development"),
    ("Sharing and turn-taking", "2-3 years", "Socio-Emotional Development"),
    ("Developing empathy", "2-3 years", "Socio-Emotional Development"),
    ("Managing simple emotions", "2-3 years", "Socio-Emotional Development"),
    ("Cooperative play", "3-4 years", "Socio-Emotional Development"),
    ("Understanding rules and routines", "3-4 years", "Socio-Emotional Development"),
    ("Expressing complex emotions and self-regulation", "3-4 years", "Socio-Emotional Development"),

    # Geography
    ("Basic Map Skills", "3-4 years", "Geography"),
]