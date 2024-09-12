import random as random
from pathlib import Path
from typing import List, Dict
from config import instruct1, instruct2, instruct3, instruct4, instruct5, instruct6, instruct7

# Define file paths using Pathlib for robustness across platforms
BASE_DIR = Path(__file__).parent.absolute()
POOLS_DIR = BASE_DIR / "pools"

# Paths to the text files
# Word lists from Greenwald et al. 1998
FILE_INSECTS = POOLS_DIR / "insects.txt"
FILE_FLOWERS = POOLS_DIR / "flowers.txt"
FILE_POSITIVES = POOLS_DIR / "positives.txt"
FILE_NEGATIVES = POOLS_DIR / "negatives.txt"


def load_words_from_file(filename: Path) -> List[str]:
    """Helper function to load and split words from a file."""
    with filename.open("r") as f:
        words = f.read().splitlines()
    return words


# Load the word lists
stim_list_insects = load_words_from_file(FILE_INSECTS)
stim_list_flowers = load_words_from_file(FILE_FLOWERS)
stim_list_positives = load_words_from_file(FILE_POSITIVES)
stim_list_negatives = load_words_from_file(FILE_NEGATIVES)


def generate_blocks(type: int) -> List[Dict[str, any]]:
    """
    Generate the blocks for the experiment.

    Parameters:
    type (int): Indicates whether to return the critical compatible lists (type 1) 
                or critical incompatible lists (type 2).

    Returns:
    List[Dict]: A list of dictionaries representing blocks of word pairs with instructions.
    """

    # Sample 10 words from each list
    sample_insects = random.sample(stim_list_insects, 10)
    sample_flowers = random.sample(stim_list_flowers, 10)
    sample_positives = random.sample(stim_list_positives, 10)
    sample_negatives = random.sample(stim_list_negatives, 10)

    # Block 1: Flower (left) vs Insect (right)
    block1 = {
        "left_word": "flower",
        "right_word": "insect",
        "instruct": instruct1,
        "words": ([{"correct": "right", "center_word": I} for I in sample_insects] +
                  [{"correct": "left", "center_word": F} for F in sample_flowers])
    }

    # Block 2: Positive (left) vs Negative (right)
    block2 = {
        "left_word": "positive",
        "right_word": "negative",
        "instruct": instruct2,
        "words": ([{"correct": "left", "center_word": P} for P in sample_positives] +
                  [{"correct": "right", "center_word": N} for N in sample_negatives])
    }

    # Block 3: Flower Positive (left) vs Insect Negative (right) - 5 samples each
    block3 = {
        "left_word": "flower positive",
        "right_word": "insect negative",
        "instruct": instruct3,
        "words": ([{"correct": "right", "center_word": I} for I in random.sample(sample_insects[:], 5)] +
                  [{"correct": "left", "center_word": F} for F in random.sample(sample_flowers[:], 5)] +
                  [{"correct": "left", "center_word": P} for P in random.sample(sample_positives[:], 5)] +
                  [{"correct": "right", "center_word": N} for N in random.sample(sample_negatives[:], 5)])
    }

    # Block 4: Flower Positive (left) vs Insect Negative (right) - all 10 samples
    block4 = {
        "left_word": "flower positive",
        "right_word": "insect negative",
        "instruct": instruct4,
        "words": ([{"correct": "right", "center_word": I} for I in sample_insects] +
                  [{"correct": "left", "center_word": F} for F in sample_flowers] +
                  [{"correct": "left", "center_word": P} for P in sample_positives] +
                  [{"correct": "right", "center_word": N} for N in sample_negatives])
    }

    # Block 5: Insect (left) vs Flower (right)
    block5 = {
        "left_word": "insect",
        "right_word": "flower",
        "instruct": instruct5,
        "words": ([{"correct": "left", "center_word": I} for I in sample_insects] +
                  [{"correct": "right", "center_word": F} for F in sample_flowers])
    }

    # Block 6: Insect Positive (left) vs Flower Negative (right) - 5 samples each
    block6 = {
        "left_word": "insect positive",
        "right_word": "flower negative",
        "instruct": instruct6,
        "words": ([{"correct": "left", "center_word": I} for I in random.sample(sample_insects[:], 5)] +
                  [{"correct": "right", "center_word": F} for F in random.sample(sample_flowers[:], 5)] +
                  [{"correct": "left", "center_word": P} for P in random.sample(sample_positives[:], 5)] +
                  [{"correct": "right", "center_word": N} for N in random.sample(sample_negatives[:], 5)])
    }

    # Block 7: Insect Positive (left) vs Flower Negative (right) - all 10 samples
    block7 = {
        "left_word": "insect positive",
        "right_word": "flower negative",
        "instruct": instruct7,
        "words": ([{"correct": "left", "center_word": I} for I in sample_insects] +
                  [{"correct": "right", "center_word": F} for F in sample_flowers] +
                  [{"correct": "left", "center_word": P} for P in sample_positives] +
                  [{"correct": "right", "center_word": N} for N in sample_negatives])
    }

    # Shuffle the word blocks for randomization
    for block in [block1, block2, block3, block4, block5, block6, block7]:
        random.shuffle(block['words'])

    # Return the blocks based on the type parameter
    if type == 1:
        # Critical compatible blocks
        return [block1, block2, block3, block4, block5, block6, block7]
    else:
        # Critical incompatible blocks
        return [block5, block2, block6, block7, block1, block3, block4]


BLOCKS = generate_blocks(1)
