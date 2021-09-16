from pathlib import Path
import logging

# Constants
LOG_LEVEL = logging.DEBUG

# Flags
KEEP_GENERATED_TEX = True
KEEP_LOG_FILES = True

# Timeouts
LATEXMK_TIMEOUT = 10
TIMEOUT = 5

# Paths
SOCIAL_PROFILES_PATH = Path("./assets/data/social_profiles.json")