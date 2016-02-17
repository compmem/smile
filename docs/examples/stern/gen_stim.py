# generate sternberg trial
def stern_trial(nitems=2, lure_trial=False,):
    if lure_trial:
        condition = 'lure'
        items = random.sample(ITEMS,nitems+1)
    else:
        condition = 'target'
        items = random.sample(ITEMS,nitems)
        # append a test item
        items.append(random.sample(items,1)[0])
    trial = {'nitems':nitems,
             'study_items':items[:-1],
             'test_item':items[-1],
             'condition':condition,}
    return trial

trials = []
for i in NUM_ITEMS:
    # add target trials
    trials.extend([stern_trial(i,lure_trial=False) for t in range(NUM_TRIALS)])
    # add lure trials
    trials.extend([stern_trial(i,lure_trial=True) for t in range(NUM_TRIALS)])

# shuffle and number
random.shuffle(trials)
for t in range(len(trials)):
    trials[t]['trial_num'] = t
