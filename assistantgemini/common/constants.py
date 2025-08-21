# Gemini Models and their token limits
MODELS = {
    "gemini-1.5-flash": 1048576,  # 1M tokens
    "gemini-1.5-pro": 1048576,    # 1M tokens
    "gemini-2.0-flash": 1048576,  # 1M tokens
    "gemini-2.0-pro": 1048576,    # 1M tokens
    "gemini-2.5-flash": 1048576,  # 1M tokens
    "gemini-2.5-pro": 1048576,    # 1M tokens
}

# Models that support function calling
SUPPORTS_FUNCTIONS = [
    "gemini-1.5-pro",
    "gemini-2.0-pro", 
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

# Models that support vision
SUPPORTS_VISION = [
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-2.0-flash",
    "gemini-2.0-pro",
    "gemini-2.5-flash",
    "gemini-2.5-pro"
]

# Default model
DEFAULT_MODEL = "gemini-2.5-flash"

# Function calling constants
CREATE_MEMORY = "create_memory"
EDIT_MEMORY = "edit_memory"
SEARCH_MEMORIES = "search_memories"
LIST_MEMORIES = "list_memories"
SEARCH_INTERNET = "search_internet"
GENERATE_IMAGE = "generate_image"
EDIT_IMAGE = "edit_image"
RESPOND_AND_CONTINUE = "respond_and_continue"

# Default settings
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 1000
DEFAULT_MAX_CONVERSATION_TOKENS = 4000 