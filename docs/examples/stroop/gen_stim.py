from random import shuffle
from config import NUM_BLOCKS, LEN_BLOCKS


def gen_lists(num_of_blocks, len_of_blocks):
    # First, let's define some variables.
    dict_list = []  # The list to hold the dictionaries
    # This list will hold a few dictionaries in order to provide a sample.
    sample_list = []

    """
	We will be creating dictionaries with the following keys:
		word		The actual word.
		color		The color the word will be presented as.
		matched		True or false (True if the word describes its own color, false otherwise.)

	"""

    # So, now we begin to create the lists.
    for y in range(num_of_blocks):
        for x in range(len_of_blocks/8):
            block_list = []
            # This block will create the matched word/color pairs.
            r_trial = {'word': 'red', 'color': 'RED', 'matched': True}
            block_list.append(r_trial)
            sample_list.append(r_trial)
            b_trial = {'word': 'blue', 'color': 'BLUE', 'matched': True}
            block_list.append(b_trial)
            sample_list.append(b_trial)
            g_trial = {'word': 'green', 'color': 'GREEN', 'matched': True}
            block_list.append(g_trial)
            sample_list.append(g_trial)
            o_trial = {'word': 'orange', 'color': 'ORANGE', 'matched': True}
            block_list.append(o_trial)
            sample_list.append(o_trial)

            # This set of four will create the mismatched color lists.
            rf_trial = {'word': 'red', 'color': randomize_color(
                'red', x % 3), 'matched': False}
            block_list.append(rf_trial)
            sample_list.append(rf_trial)
            bf_trial = {'word': 'blue', 'color': randomize_color(
                'blue', x % 3), 'matched': False}
            block_list.append(bf_trial)
            sample_list.append(bf_trial)
            gf_trial = {'word': 'green', 'color': randomize_color(
                'green', x % 3), 'matched': False}
            block_list.append(gf_trial)
            sample_list.append(gf_trial)
            of_trial = {'word': 'orange', 'color': randomize_color(
                'orange', x % 3), 'matched': False}
            block_list.append(of_trial)
            sample_list.append(of_trial)

            # And now we shuffle the lists to ensure randomness.
            shuffle(block_list)
            dict_list.append(block_list)
    shuffle(dict_list)
    return (dict_list, sample_list)


# This function will essentially select a random color from blue, orange, green, and red from amongst the colors that the inputted word is not.
def randomize_color(sColor, iColor):

    final_color = ''
    if (sColor == 'red'):
        if (iColor == 0):
            final_color = 'BLUE'
        elif (iColor == 1):
            final_color = 'ORANGE'
        else:
            final_color = 'GREEN'
    elif (sColor == 'blue'):
        if (iColor == 0):
            final_color = 'RED'
        elif (iColor == 1):
            final_color = 'GREEN'
        else:
            final_color = 'ORANGE'
    elif (sColor == 'green'):
        if (iColor == 0):
            final_color = 'ORANGE'
        elif (iColor == 1):
            final_color = 'BLUE'
        else:
            final_color = 'RED'
    elif (sColor == 'orange'):
        if (iColor == 0):
            final_color = 'RED'
        elif (iColor == 1):
            final_color = 'GREEN'
        else:
            final_color = 'BLUE'
    return final_color


# Generate the Stimulus
trials, sample_list = gen_lists(NUM_BLOCKS, LEN_BLOCKS)
