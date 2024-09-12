from random import shuffle, randint, choice
from typing import List, Dict
from config import NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK


def randomize_color(word: str, index: int) -> str:
    """
    Randomly select a color from the available colors that does not match the given word.

    Args:
        word (str): The word representing the color.
        index (int): The index used for color randomization.

    Returns:
        str: A mismatched color.
    """
    word_color_map = {
        'red': ["BLUE", "GREEN", "ORANGE"],
        'blue': ["RED", "GREEN", "ORANGE"],
        'green': ["RED", "BLUE", "ORANGE"],
        'orange': ["RED", "BLUE", "GREEN"]
    }
    return word_color_map[word][index % 3]


def create_trial(word: str, matched: bool = True, color: str = None) -> Dict[str, str]:
    """
    Creates a trial dictionary with word, color, and matched status.

    Args:
        word (str): The word for the trial.
        matched (bool): Whether the word matches the color.
        color (str): Optional color to use for the trial, only for mismatched trials.

    Returns:
        dict: A dictionary representing a single trial.
    """
    trial_color = color if not matched else word.upper()
    return {
        'word': word,
        'color': trial_color,
        'matched': matched
    }


def generate_block(number_of_trials_per_block: int) -> List[Dict[str, str]]:
    """
    Generate a block of trials with a specified length.

    Args:
        number_of_trials_per_block (int): The desired number of trials in the block.

    Returns:
        List[Dict[str, str]]: A list of trial dictionaries.
    """
    block = []
    words = ["red", "blue", "green", "orange"]

    num_matched_trials = number_of_trials_per_block // 2

    # Add matched trials
    for _ in range(num_matched_trials):  # Half of the trials are matched
        block.append(create_trial(choice(words), matched=True))

    # Add mismatched trials
    # Half of the trials are mismatched
    for _ in range(number_of_trials_per_block - num_matched_trials):
        random_word = choice(words)
        block.append(create_trial(random_word, matched=False,
                     color=randomize_color(random_word, randint(0, 2))))

    shuffle(block)  # Shuffle the block for randomization
    return block


def generate_blocks(num_of_blocks: int, number_of_trials_per_block: int) -> List[List[Dict[str, str]]]:
    """
    Generate a list of blocks, where each block contains a number of trials.

    Each trial is represented as a dictionary with string keys and values.

    Args:
        num_of_blocks (int): The number of blocks to generate.
        number_of_trials_per_block (int): The number of trials in each block.

    Returns:
        List[List[Dict[str, str]]]: A list of blocks, where each block is a list of trials. 
        Each trial is represented as a dictionary with string keys and values.
    """
    blocks = []

    for _ in range(num_of_blocks):
        # Generate a block with the specified number of trials
        block = generate_block(number_of_trials_per_block)
        blocks.append(block)

    shuffle(blocks)  # Shuffle the list of blocks to randomize their order
    return blocks


BLOCKS = generate_blocks(NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK)


# Example usage
if __name__ == "__main__":
    BLOCKS = generate_blocks(NUMBER_OF_BLOCKS, NUMBER_OF_TRIALS_PER_BLOCK)
    print(len(BLOCKS))
    print(BLOCKS)
