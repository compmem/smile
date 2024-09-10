import random
from config import NUM_BLOCKS, stim_list, NUM_PER_BLOCK, MIN_FREE_KEY_DURATION

# Shuffle the stimulus list for randomness
random.shuffle(stim_list)

blocks = []
for block_index in range(NUM_BLOCKS):
    study_items = []

    # Select stimuli for the current block based on NUM_PER_BLOCK
    num_items_in_block = NUM_PER_BLOCK[block_index % len(NUM_PER_BLOCK)]
    for _ in range(num_items_in_block):
        study_items.append(stim_list.pop())

    # Create a block dictionary with study items and duration
    block_duration = MIN_FREE_KEY_DURATION + \
        10 * (block_index % len(NUM_PER_BLOCK))
    blocks.append({
        "study": study_items,
        "duration": block_duration
    })

# Shuffle the blocks to ensure random order of blocks
random.shuffle(blocks)
