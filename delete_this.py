#stascr_main_new.py
#https://kivyspacegame.wordpress.com/2014/06/20/flappy-ship-a-step-by-step-game-tutorial-part-1/
#from smile.common import *
#from smile.common import Parallel
#from smile.common import MouseCursor
from video import WidgetState

 
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.floatlayout import *
from kivy.uix.screenmanager import *
from kivy.uix.checkbox import CheckBox
from kivy.graphics import InstructionGroup



CONFIG_FONT_SIZE = Window.height*.025


class StartMenu(Screen):
	def __init__(self, **kwargs):
		super(StartMenu, self).__init__(**kwargs)
		Window.clearcolor=(.35,.35,.35,1.0)
		Window.fullscreen = True

	#def start(self):

		float_layout = FloatLayout(size=(Window.width, Window.height))

		#--- Text Placement ---
		title_l = Label(text="CognitiveBattery", 
			font_size=CONFIG_FONT_SIZE, 
			size_hint=(.2,.2), 
			pos_hint={'x':.4,'y':.9})
		float_layout.add_widget(title_l)

		subj_l = Label(text='Subject ID: ',
			font_size=CONFIG_FONT_SIZE, 
			size_hint=(.2,.2),
			pos_hint={'x':.3, 'y':.7})
		float_layout.add_widget(subj_l)

		input_l = TextInput(#text='Subject Id', 
			multiline=False, 
			size_hint=(.2,.05), 
			pos_hint={'x':.5, 'y':.78})
		float_layout.add_widget(input_l)

		#--- Image Placement ---
		img = Image(source='face-smile.png',
			pos_hint={'x':.4, 'y':.4},
			size_hint=(.2,.2),
			opacity=.25)
		float_layout.add_widget(img)

		#--- Button Placement ---
		cont_btn = Button(text='Continue',
			size_hint=(.2,.05), 
			pos_hint={'x':.52, 'y':.1})
		cont_btn.bind(on_release=self.exitApp)
		float_layout.add_widget(cont_btn)

		setting_btn = Button(text='Settings',
			size_hint=(.2,.05), 
			pos_hint={'x': .28, 'y':.1})
		setting_btn.bind(on_release=self.toSetting)
		float_layout.add_widget(setting_btn)

		#--- Outer Rectangle ---
		self.bind(size=self._update_rect, pos=self._update_rect)
		with self.canvas.before:
			Color(51./255., 107./255., 135./255.)
			self.rectOut = Rectangle(pos=self.pos, size=self.size)

		#--- Inner Rectangle ---
		self.bind(size=self.update_rect, pos=self.update_rect)
		with self.canvas.before:
			Color(144./255., 175./255., 197./255.)
			self.rectIn = Rectangle(pos=self.pos, size=self.size)

		self.add_widget(float_layout)

	def _update_rect(self, instance, value):
		self.rectOut.pos = (Window.width/10, 45)
		self.rectOut.size = (Window.height*.5, Window.height*1)

	def update_rect(self, instance, value):
		self.rectIn.pos = ((Window.width/10)+15, 60)
		self.rectIn.size = (Window.height*.47, Window.height*.46)

	def toSetting(self, instance):
		self.manager.current = 'setting'

	def exitApp(self, instance):
		Window.hide()
		ClientApp().stop()

class SettingScreen(Screen):
	def __init__(self, **kwargs):
		super(SettingScreen, self).__init__(**kwargs)

	#def start(self):
		float_layout = FloatLayout(size=(Window.width, Window.height))

		#--- Checkbox Placement ---
		cb_locksubj = CheckBox(active=False)
		cb_locksubj.pos_hint = {'x':-.08, 'y':.28}
		float_layout.add_widget(cb_locksubj)

		#--- Text Placement ---
		locksubj_l = Label(text='Lock Subject',
			font_size=CONFIG_FONT_SIZE,
			size_hint=(.2,.2),
			pos_hint={'x':.45, 'y':.68})
		float_layout.add_widget(locksubj_l)

		fraRate_l = Label(text='Frame Rate',
			font_size=CONFIG_FONT_SIZE,
			size_hint=(.2,.2),
			pos_hint={'x':.38, 'y':.48})
		float_layout.add_widget(fraRate_l)

		#--- Text Input ---
		fraRate_input = TextInput(multiline=False,
			size_hint=(.07,.05),
			pos_hint={'x':.3, 'y':.55})
		float_layout.add_widget(fraRate_input)

		#--- Button Placement ---
		cancel_btn = Button(text='Cancel',
			size_hint=(.2, .05),
			pos_hint={'x':.28, 'y':.1})
		cancel_btn.bind(on_release=self.toMenu)
		float_layout.add_widget(cancel_btn)

		apply_btn = Button(text='Apply',
			size_hint=(.2,.05),
			pos_hint={'x':.52, 'y':.1})
		apply_btn.bind(on_release=self.applySetting)
		float_layout.add_widget(apply_btn)

		test_btn = Button(text='Test',
			size_hint=(.15,.05),
			pos_hint={'x':.6 ,'y':.55})
		float_layout.add_widget(test_btn)

		#--- Outer Rectangle ---
		self.bind(size=self._update_rect, pos=self._update_rect)
		with self.canvas.before:
			Color(51./255., 107./255., 135./255.)
			self.rectOut = Rectangle(pos=self.pos, size=self.size)

		#--- Inner Rectangle ---
		self.bind(size=self.update_rect, pos=self.update_rect)
		with self.canvas.before:
			Color(144./255., 175./255., 197./255.)
			self.rectIn = Rectangle(pos=self.pos, size=self.size)

		self.add_widget(float_layout)

	def _update_rect(self, instance, value):
		self.rectOut.pos = (Window.width/10, 15)
		self.rectOut.size = (Window.height*.5, Window.height*1)

	def update_rect(self, instance, value):
		self.rectIn.pos = ((Window.width/10)+15, 30)

	def toMenu(self, instance):
		self.manager.current = 'menu'

	def applySetting(self, instance):
		self.manager.current = 'menu'

	def on_locksubj_Active(self, checkboxInstance, isActive):
		if isActive:
			pass
		else:
			pass

class ScrManager(Widget):
	def __init__(self, **kwargs):
		super(ScrManager, self).__init__(**kwargs)



	def start(self):
		sm = ScreenManager(transition=NoTransition(), size=(Window.width/2, Window.height/2))
		#StartMenu().start()
		#SettingScreen().start()
		sm.add_widget(StartMenu(name = 'menu'))
		sm.add_widget(SettingScreen(name='setting'))

		#sm.add_widget(StartMenu(name = 'menu').start())
		#sm.add_widget(SettingScreen(name = 'setting').start())
		self.add_widget(sm)

	#def start(self):
	#	StartMenu.start()
	#	SettingScreen.start()

###--- Run Application ---###
class ClientApp(App):
	def build(self):
		return ScrManager()
	def on_stop(self):
		return True

if __name__ == '__main__':
	ClientApp().run()

'''class MenuScreen(WidgetState.wrap(ScrManager)):
	def show(self):
		self._widget.start()
		super(MenuScreen, self).show()

	def unshow(self):
		super(MenuScreen, self).unshow()
		self._widget.stop()

if __name__ == '__main__':
	from experiment import Experiment 
	from video import Ellipse
	#from smile.common import MouseCursor
	exp = Experiment()
#	with Parallel():
	#MouseCursor()
	MenuScreen(width=500, height=700)
	exp.run()'''