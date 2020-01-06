from smile.experiment import Experiment
from smile.state import Subroutine, Debug, Meanwhile, Loop, UntilDone, Wait, \
                        Func, Serial, Parallel, While, If, Elif, Else, Log, \
                        PrintTraceback, _DelayedValueTest, Done, When, \
                        Record
from smile.ref import val
from smile.audio import *


def print_actual_duration(target):
    print(val(target.end_time - target.start_time))


def print_periodic():
    print("PERIODIC!")


@Subroutine
def DoTheThing(self, a, b, c=7, d="ssdfsd"):
    PrintTraceback(name="inside DoTheThing")
    self.foo = c * 2
    Wait(1.0)
    Debug(a=a, b=b, c=c, d=d, foo=self.foo,
          screen_size=self.exp.screen.size, name="inside DoTheThing")


@Subroutine
def DoTheOtherThing(self):
    Debug(name="before the yield")
    with Serial():
        yield
    with Meanwhile():
        PrintTraceback(name="during the yield")
    Debug(name="after the yield")


exp = Experiment(debug=True)

Debug(width=exp.screen.width, height=exp.screen.height)

with Loop(5) as loop:
    Log(a=1, b=2, c=loop.i, name="aaa")
Log({"q": loop.i, "w": loop.i}, x=4, y=2, z=1, name="bbb")
Log([{"q": loop.i, "w": n} for n in range(5)], x=4, y=2, z=1, name="ccc")

exp.for_the_thing = 3
dtt = DoTheThing(3, 4, name="first")
Debug(foo=dtt.foo, name="outside DoTheThing")
dtt = DoTheThing(3, 4, d="bbbbbbb", c=exp.for_the_thing)
Debug(foo=dtt.foo, name="outside DoTheThing")

with DoTheOtherThing():
    PrintTraceback(name="top of body")
    Wait(2.0)
    PrintTraceback(name="bottom of body")

Wait(1.0)
dvt = _DelayedValueTest(1.0, 42)
Done(dvt)
Debug(dvt_out=dvt.value_out)

exp.bar = False
with Parallel():
    with Serial():
        Wait(2.0)
        # force variable assignment
        # to wait until correct time
        Func(lambda: None)
        exp.bar = True
        Wait(2.0)
        # force variable assignment to wait until correct time
        Func(lambda: None)
        exp.bar = False
        Wait(1.0)
    When(exp.bar, Debug(name="when test"))
    with While(exp.bar):
        with Loop():
            Wait(0.2)
            Debug(name="while test")
    with Loop(blocking=False):
        Wait(0.5)
        Debug(name="non-blocking test")

exp.foo = 1
Record(foo=exp.foo)
with UntilDone():
    Debug(name="FOO!")
    Wait(1.0)
    Debug(name="FOO!")
    exp.foo = 2
    Debug(name="FOO!")
    Wait(1.0)
    Debug(name="FOO!")
    exp.foo = 3
    Debug(name="FOO!")
    Wait(1.0)
    Debug(name="FOO!")

with Parallel():
    with Serial():
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        exp.foo = 4
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
        exp.foo = 5
        Debug(name="FOO!")
        Wait(1.0)
        Debug(name="FOO!")
    with Serial():
        Debug(name="FOO!!!")
        Wait(until=exp.foo == 5, name="wait until")
        Debug(name="foo=5!")

with Loop(10) as loop:
    with If(loop.current > 6):
        Debug(name="True")
    with Elif(loop.current > 4):
        Debug(name="Trueish")
    with Elif(loop.current > 2):
        Debug(name="Falsish")
    with Else():
        Debug(name="False")

# with implied parents
block = [{'val': i} for i in range(3)]
exp.not_done = True
with Loop(conditional=exp.not_done) as outer:
    Debug(i=outer.i)
    with Loop(block, shuffle=True) as trial:
        Debug(current_val=trial.current['val'])
        Wait(1.0)
        If(trial.current['val'] == block[-1],
           Wait(2.0))
    with If(outer.i >= 3):
        exp.not_done = False

block = range(3)
with Loop(block) as trial:
    Debug(current=trial.current)
    Wait(1.0)
    If(trial.current == block[-1],
       Wait(2.))


If(True,
   Debug(name="True"),
   Debug(name="False"))
Wait(1.0)
If(False,
   Debug(name="True"),
   Debug(name="False"))
Wait(2.0)
If(False, Debug(name="ACK!!!"))  # won't do anything
Debug(name="two")
Wait(3.0)
with Parallel():
    with Serial():
        Wait(1.0)
        Debug(name='three')
    Debug(name='four')
Wait(2.0)

block = [{'text': 'a'}, {'text': 'b'}, {'text': 'c'}]
with Loop(block) as trial:
    Debug(current_text=trial.current['text'])
    Wait(1.0)

Debug(name='before meanwhile 1')
Wait(1.0)
with Meanwhile(name="First Meanwhile") as mw:
    Wait(15.0)
Debug(name='after meanwhile 1')
Func(print_actual_duration, mw)

Debug(name='before meanwhile 2')
Wait(5.0)
with Meanwhile() as mw:
    PrintTraceback()
    Wait(1.0)
Debug(name='after meanwhile 2')
Func(print_actual_duration, mw)

Debug(name='before untildone 1')
Wait(15.0)
with UntilDone(name="UntilDone #1") as ud:
    Wait(1.0)
    PrintTraceback()
Debug(name='after untildone 1')
Func(print_actual_duration, ud)

Debug(name='before untildone 2')
Wait(1.0)
with UntilDone() as ud:
    Wait(5.0)
Debug(name='after untildone 2')
Func(print_actual_duration, ud)

with Serial() as s:
    with Meanwhile():
        Wait(100.0)
    Wait(1.0)
Func(print_actual_duration, s)
with Serial() as s:
    with UntilDone():
        Wait(1.0)
    Wait(100.0)
Func(print_actual_duration, s)

Debug(name='before parallel')
with Parallel() as p:
    Debug(name='in parallel')
    with Loop(5) as l:
        with p.insert():
            with Serial():
                Wait(l.i)
                Debug(name='in insert after n second wait', n=l.i)
            with Serial():
                Wait(2.0)
                Debug(name='in insert after 2s wait', n=l.i)
            Debug(name='in insert', n=l.i)
        p.insert(Debug(name='in insert #2', n=l.i))
Debug(name='after parallel')

Wait(2.0)

exp.run(trace=False)
