# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Default values for the prompt-tuning module.

Note: These values get accessed from the CLI to set default behavior.
To maintain fast responsiveness from the CLI, do not add long-running code in this file and be mindful of imports.
"""

DEFAULT_TASK = """
Identify the relations and structure of the community of interest, specifically within the {domain} domain.
"""

SOFTWARE_TASK = """
Identify the relations and structure of the software provided. Focus on fucntion calls and ralationhships between classes, methods, and functions.
"""

K = 15
LIMIT = 15
MAX_TOKEN_COUNT = 2000
MIN_CHUNK_SIZE = 200
N_SUBSET_MAX = 300
MIN_CHUNK_OVERLAP = 0
PROMPT_TUNING_MODEL_ID = "default_chat_model"
