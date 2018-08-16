from smile.common import *

# Standard Demographics Logging

@Subroutine
def Demographics(self):
    buttons = []
    buttons2 = []
    buttons3 = []
    with Parallel():
        # Gotta have a cursor
        MouseCursor()

        # background rectangle
        rc = Rectangle(color='GRAY', top=self._exp.screen.top,
                       height=self._exp.screen.height,
                       width=600)
        # Age
        lbAge = Label(text='Age : ', left=rc.left+50,
                      top=self._exp.screen.top-20)
        txi1 = TextInput(left=lbAge.right + 10, height=lbAge.height+10,
                         center_y=lbAge.center_y, input_filter='int')

        # Gender
        lbSex = Label(text='Gender : ', left=rc.left+50, top=lbAge.bottom-40)
        with ButtonPress() as bp1:
            lb1 = Label(text='Male', left=lbSex.right+10,
                        center_y=lbSex.center_y)
            buttons.append(ToggleButton(name='Male', left=lb1.right+5,
                                        center_y=lb1.center_y,
                                        group='sex',
                                        width=20, height=20))
            lb2 = Label(text='Female', left=buttons[0].right+50,
                        center_y=lb1.center_y)
            buttons.append(ToggleButton(name='Female',
                                        center_y=lb2.center_y,
                                        group='sex',
                                        width=20, height=20,
                                        left=lb2.right+5),)
            lb3 = Label(text='Other', left=buttons[1].right+50,
                        center_y=lb1.center_y)
            buttons.append(ToggleButton(name='Other', width=20,
                                        height=20,
                                        center_y=lb1.center_y,
                                        left=lb3.right+5,
                                        group='sex'))

        # Hispanic Or Latino
        lbHis = Label(text='Are you Hispanic or Latino? (Having origins in Cuban, Mecian, Puerto Rican, South or Central American, or other Spanish culture, regardless of race.)',
                      left=rc.left+50, top=lbSex.bottom-40,
                      text_size=(rc.width*.75, None))
        with ButtonPress() as bp2:
            lbYes = Label(text='Yes', left=rc.left+50, top=lbHis.bottom-20)
            buttons2.append(ToggleButton(name='yes',
                                         left=lbYes.right+5,
                                         center_y=lbYes.center_y,
                                         width=20, height=20,
                                         group='latino'))
            lbNo = Label(text='No', left=buttons2[0].right+50,
                         top=lbHis.bottom-20)
            buttons2.append(ToggleButton(name='no',
                                         left=lbNo.right+5,
                                         center_y=lbNo.center_y,
                                         width=20, height=20,
                                         group='latino'))

        # Racial Origin
        lbRace = Label(text='Racial Origin (Mark all that apply)',
                       left=rc.left+50, top=lbHis.bottom-80)
        #Black African-American
        buttons3.append(ToggleButton(name='black_or_aftican-american',
                                     left=rc.left+50,
                                     top=lbRace.bottom-20,
                                     width=20, height=20))
        Label(text='Black or African-American', left=buttons3[0].right+5,
              center_y=buttons3[0].center_y)

        # Middle Eastern
        buttons3.append(ToggleButton(name='middle_eastern',
                                     left=rc.left+50,
                                     top=buttons3[0].bottom-10,
                                     width=20, height=20))
        Label(text='Middle Eastern', left=buttons3[1].right+5,
              center_y=buttons3[1].center_y)

        # North African
        buttons3.append(ToggleButton(name='north_african',
                                     left=rc.left+50,
                                     top=buttons3[1].bottom-10,
                                     width=20, height=20))
        Label(text='North African', left=buttons3[2].right+5,
              center_y=buttons3[2].center_y)

        # Asian
        buttons3.append(ToggleButton(name='asian',
                                     left=rc.left+50,
                                     top=buttons3[2].bottom-10,
                                     width=20, height=20))
        Label(text='Asian', left=buttons3[3].right+5,
              center_y=buttons3[3].center_y)

        # White
        buttons3.append(ToggleButton(name='white',
                                     left=rc.left+50,
                                     top=buttons3[3].bottom-10,
                                     width=20, height=20))
        Label(text='White', left=buttons3[4].right+5,
              center_y=buttons3[4].center_y)

        # Native American, American Indian, or Alaskan Native
        buttons3.append(ToggleButton(name='native_american_or_alaskan',
                                     left=rc.left+50,
                                     top=buttons3[4].bottom-10,
                                     width=20, height=20))
        Label(text='Native American, American Indian, or Alaskan Native',
              left=buttons3[5].right+5, center_y=buttons3[5].center_y)

        # Native Hawaiian, or other Pacific Islander
        buttons3.append(ToggleButton(name='native_hawaiian_or_islander',
                                     left=rc.left+50,
                                     top=buttons3[5].bottom-10,
                                     width=20, height=20))
        Label(text='Native Hawaiian, or other Pacific Islander',
              left=buttons3[6].right+5, center_y=buttons3[6].center_y)

    with UntilDone():
        with ButtonPress() as bp3:
            Button(name='enter', text='CONTINUE',
                   bottom=self._exp.screen.bottom+10,
                   height=40)
        Log(name='demographics',
            subj_id=self._exp.subject,
            age=txi1.text,
            male=buttons[0].state=='down',
            female=buttons[1].state=='down',
            other=buttons[2].state=='down',
            latino=buttons2[0].state=='down',
            non_latino=buttons2[1].state=='down',
            black_african_american=buttons3[0].state=='down',
            middle_eastern=buttons3[1].state=='down',
            north_african=buttons3[2].state=='down',
            asian=buttons3[3].state=='down',
            white=buttons3[4].state=='down',
            native_american=buttons3[5].state=='down',
            native_hawaiian_or_islander=buttons3[6].state=='down',)