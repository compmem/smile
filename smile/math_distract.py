from .video import Label
from .state import Subroutine, If, Else, UntilDone, Loop, Wait, Log
from .audio import Beep
from .keyboard import KeyPress
from .ref import Ref
from .scale import scale as s
import random

def _gen_questions(num_vars, max_num, min_num, max_probs, plus_and_minus, ans_mod, ans_prob, keys):
        #List Gen
        trials=[]
        for i in range(max_probs):
            factors=[]
            #generate the Factors of the Equation
            for b in range(num_vars):
                factors.append(random.randint(min_num, max_num+1))
            opperators=[]
            random.shuffle(factors)
            total = factors[0]
            #Generate num_factors - 1 number of operators
            if plus_and_minus:
                for x in range(num_vars-1):
                    if(random.randrange(2)==0):
                        total = total + factors[x+1]
                        opperators.append('+')
                    else:
                        total = total - factors[x+1]
                        opperators.append('-')
            else:
                rand_element = random.randrange(2)
                for x in range(num_vars-1):
                    if rand_element:
                        total = total + factors[x+1]
                        opperators.append('+')
                    else:
                        total = total - factors[x+1]
                        opperators.append('-')

            last_prob = 0
            rand_per = random.random()
            for i in range(len(ans_prob)):
                if rand_per > last_prob and rand_per < last_prob+ans_prob[i]:
                    new_total = total + ans_mod[i]
                last_prob += ans_prob[i]
            condition=True
            if new_total != total:
                condition = False


            # Build the Equation String
            temp = str(factors[0])
            for y in range(num_vars-1):
                temp = temp + opperators[y] + str(factors[y+1])
            temp = temp + '=' + str(new_total)
            # Append the list of trials with the currently
            # generated stimuli
            trials.append({
                    'text':temp,
                    'condition':condition,
                    'correct_key':keys[str(condition)]
            })
        random.shuffle(trials)
        return trials

@Subroutine
def MathDistract(self,
                 num_vars=2,
                 min_num=1,
                 max_num=9,
                 max_probs=50,
                 duration=30,
                 keys={'True':'F','False':'J'},
                 plus_and_minus=False,
                 font_size=70,
                 correct_beep_dur=.5,
                 correct_beep_freq=400,
                 correct_beep_rf=0.5,
                 incorrect_beep_dur=.5,
                 incorrect_beep_freq=200,
                 incorrect_beep_rf=0.5,
                 ans_mod=[0,1,-1,10,-10],
                 ans_prob=[.5,.125,.125,.125,.125],
                 visual_feedback=True):
    """
    Math distractor for specified period of time.  Logs to a subroutine_0.slog
    INPUT ARGS:
      duration - set this param for non-self-paced distractor;
                         buzzer sounds when time's up; you get at least
                         minDuration/problemTimeLimit problems.
      num_vars - Number of variables in the problem.
      max_num - Max possible number for each variable.
      min_num - Min possible number for each varialbe.
      max_probs - Max number of problems.
      plus_and_minus - True will have both plus and minus.
      min_duration - Minimum duration of distractor.
      text_size - Vertical height of the text.
      correct_beep_dur - Duration of correct beep.
      correct_beep_freq - Frequency of correct beep.
      correct_beep_rf - Rise/Fall of correct beep.
      incorrect_beep_dur - Duration of incorrect beep.
      incorrect_beep_freq - Frequency of incorrect beep.
      incorrect_beep_rf - Rise/Fall of incorrect beep
      keys - dictionary of keys for true/false problems. e.g., tfKeys = ('True':'T','False':'F')
      ans_mod - For True/False problems, the possible values to add to correct answer.
      ans_prob - The probability of each modifer on ansMod (must add to 1).
      visual_feedback - Whether to provide visual feedback to indicate correctness.

    """

    self.responses = []
    
    trials = Ref(_gen_questions,num_vars, max_num, min_num, max_probs, plus_and_minus, ans_mod, ans_prob, keys)
    with Loop(trials) as trial:
        Label(text='+', duration=1.0, font_size=s(font_size), color='white')
        curtext = Label(text=trial.current['text'], font_size=s(font_size), color='white')
        with UntilDone():
            kp = KeyPress(keys=(keys['True'],keys['False']), correct_resp=trial.current['correct_key'])
            # If visual_feedback is True, display a the words Correct! or Incorrect! in red or green
            # for the remainder of the trial duration.
            with If(visual_feedback):
                with If(kp.correct):
                    Label(text='Correct!', center_x=self.exp.screen.center_x, center_y=self.exp.screen.center_y/2.0,
                            font_size=s(font_size), duration=0.5, color='green')
                with Else():
                    Label(text='Incorrect!', center_x=self.exp.screen.center_x, center_y=self.exp.screen.center_y/2.0,
                            font_size=s(font_size), duration=0.5, color='red')
            # If visual_feedback is False, queue a beep to be played, at the specified frequencies,
            # durations, and volumes depending on if they got it correct or incorrect.
            with Else():
                with If(kp.correct):
                    Beep(duration=correct_beep_dur, freq=correct_beep_freq, volume=correct_beep_rf)
                with Else():
                    Beep(duration=incorrect_beep_dur, freq=incorrect_beep_freq, volume=incorrect_beep_rf)
        Log(trial.current,
            name='math_distract',
            correct=kp.correct,
            resp=kp.pressed,
            rt=kp.rt)
    with UntilDone():
        Wait(duration)
