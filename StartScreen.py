from video import WidgetState
 

# def _cont():
 #	self.flag = "cont"
 #	self.stop()
 #from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.graphics import *
from kivy.uix.floatlayout import *

from kivy.uix.checkbox import CheckBox

CONFIG_FONT_SIZE = "25sp"

class _StartScreen(Widget):
	def __init__(self, flag, **kwargs):
		super(_StartScreen, self).__init__(**kwargs)
		self.flag=flag

	def start(self):
		float_layout = FloatLayout(size=self.size, pos=self.pos)

		#--- Text Placement ---
		title_l = Label(text="CognitiveBattery", 
			font_size=CONFIG_FONT_SIZE, 
			size_hint=(.2,.2), 
			pos_hint={'x':.4,'y':.75})
		float_layout.add_widget(title_l)

		subj_l = Label(text='Subject ID : ',
			font_size=CONFIG_FONT_SIZE, 
			size_hint=(.2,.2),
			pos_hint={'x':.35, 'y':.602})
		float_layout.add_widget(subj_l)

		input_l = TextInput(#text='Subject Id', 
			multiline=False, 
			size_hint=(.15,.03), 
			pos_hint={'x':.5, 'y':.69})
		float_layout.add_widget(input_l)

		#--- Image Placement ---
		img = Image(source='face-smile.png',
			pos_hint={'x':.4, 'y':.4},
			size_hint=(.2,.2),
			opacity=.25)
		float_layout.add_widget(img)

		#--- Button Placement ---
		setting_btn = Button(text='Settings',
			size_hint=(.2,.05), 
			pos_hint={'x': .28, 'y':.15})
		setting_btn.bind(on_release=self.toSetting)
		float_layout.add_widget(setting_btn)

		cont_btn = Button(text='Continue',
			size_hint=(.2,.05), 
			pos_hint={'x':.52, 'y':.15})
		cont_btn.bind(on_release=self.exitApp)
		float_layout.add_widget(cont_btn)


		#--- Outer Rectangle ---
		with self.canvas.before:
			Color(51./255., 107./255., 135./255.)
			self.rectOut = Rectangle(pos=((self.size[0]/7, self.size[1]/10.5)), size=(self.size[0]*.7, self.size[1]*.85))

		#--- Inner Rectangle ---
		with self.canvas.before:
			Color(144./255., 175./255., 197./255.)
			self.rectIn = Rectangle(pos=(self.size[0]/6, self.size[1]/8.5), size=(self.size[0]*.65, self.size[1]*.80))

		self.add_widget(float_layout)

	def toSetting(self, instance):
		pass
	def setFlag(self, flag):
		self.flag = flag

	def exitApp(self, instance):
		self.setFlag("stop")
		#self.flag = "stop"
		print("I've set the flag!")
		print(self.flag)
		#self.stop()
		#self.flag = "cont"
		#self.stop()
		#self.hide()
		#ClientApp().stop()

	
	'''def getFlag(self):
					return self.flag'''
# def _cont():
 #	self.flag = "cont"
 #	self.stop()

class _SettingScreen(Widget):
	def __init__(self, **kwargs):
		super(_SettingScreen, self).__init__(**kwargs)

	def start(self):
		float_layout = FloatLayout(size=self.size, pos=self.pos)

		#--- Checkbox Placement ---
		cb_locksubj = CheckBox(active=True)
		cb_locksubj.pos_hint = {'x':.45, 'y':.694}
		cb_locksubj.size_hint=(.01,.01)
		cb_locksubj.size=(25,25)
		float_layout.add_widget(cb_locksubj)
		
		#--- Text Placement ---
		locksubj_l = Label(text='Lock Subject',
			font_size=CONFIG_FONT_SIZE,
			size_hint=(.2,.2),
			pos_hint={'x':.42, 'y':.6})
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
			pos_hint={'x': .28, 'y':.15})
		cancel_btn.bind(on_release=self.toMenu)
		float_layout.add_widget(cancel_btn)

		apply_btn = Button(text='Apply',
			size_hint=(.2,.05),
			pos_hint={'x':.52, 'y':.15})
		apply_btn.bind(on_release=self.applySetting)
		float_layout.add_widget(apply_btn)

		test_btn = Button(text='Test',
			size_hint=(.15,.05),
			pos_hint={'x':.6 ,'y':.55})
		float_layout.add_widget(test_btn)
		
		#--- Outer Rectangle ---
		with self.canvas.before:
			Color(51./255., 107./255., 135./255.)
			self.rectOut = Rectangle(pos=((self.size[0]/7, self.size[1]/10.5)), size=(self.size[0]*.7, self.size[1]*.85))

		#--- Inner Rectangle ---
		with self.canvas.before:
			Color(144./255., 175./255., 197./255.)
			self.rectIn = Rectangle(pos=(self.size[0]/6, self.size[1]/8.5), size=(self.size[0]*.65, self.size[1]*.80))

		self.add_widget(float_layout)

	def toMenu(self, instance):
		self.manager.current = 'menu'

	def applySetting(self, instance):
		self.manager.current = 'menu'

	def on_locksubj_Active(self, checkboxInstance, isActive):
		if isActive:
			pass
		else:
			pass

class StartScreen(WidgetState.wrap(_StartScreen)):
	def show(self):
		self._widget.start()
		super(StartScreen, self).show()

	def unshow(self):
		super(StartScreen, self).unshow()
		self._widget.stop()

	'''def getFlag(self):
					self._widget.getFlag = self.getFlag
					return self._widget.getFlag'''

class SettingScreen(WidgetState.wrap(_SettingScreen)):
	def show(self):
		self._widget.start()
		super(SettingScreen, self).show()

	def unshow(self):
		super(SettingScreen, self).unshow()
		self._widget.stop()

if __name__ == '__main__':
	from experiment import Experiment 
	from state import *
	from mouse import MouseCursor

	exp = Experiment(name="Flanker_ONLY_20180418",
		background_color=(.35,.35,.35,1.0))		


	exp.dont_stop = True
	with Parallel():
		startScreen=StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
		Debug(a=startScreen.flag)
		MouseCursor()
		with If (startScreen.flag == "stop"):
			Debug(x=startScreen.flag)
			exp.dont_stop=False

			
	'''
	if (ctn_btn == pressed) {
		StartScreen.unshow();
		SettingScreen.show();
	}
	'''
	'''exp = Experiment()
	exp.dont_stop = True
	with Loop(conditional=(exp.dont_stop)):
		with Parallel():
			startScreen = StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
			MouseCursor(blocking=False)
			Debug(var=startScreen.flag)
			with If(startScreen.flag == "continue"):
				exp.dont_stop = False

	exp.run()'''
	#with Parallel():
	#exp.dont_stop = True
	#startScreen = StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
	#Debug(x=startScreen.flag)
	'''with Parallel():
					startScreen = StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
					MouseCursor(blocking=False)
					with Loop(conditional=(exp.dont_stop)):
						with If(startScreen.flag == "stop"):
							exp.dont_stop=False'''
	'''with Loop(conditional=(exp.dont_stop)):
					with Parallel():
						startScreen = StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
						MouseCursor(blocking=False)
						Debug(var=startScreen.getFlag())
						with If(startScreen.getFlag() =="stop"):
							exp.dont_stop=False
							Debug(x="CONTINUE BUTTON CLICKED")
				Debug(x="slkdfjsfd")'''
	'''	with Parallel():
		#SettingScreen(width=exp.screen.height/.3, height=exp.screen.height/.3)
		#StartScreen(width=exp.screen.height/3., height=exp.screen.height/3.)
		#MouseCursor()
		#SettingScreen()

		startScreen = StartScreen(width=exp.screen.width, height=exp.screen.height, flag="none")
		#SettingScreen(width=exp.screen.width, height=exp.screen.height)
		MouseCursor()

		with Serial():
			with Loop(conditional=(startScreen.flag != "stop")):
				Debug(z="I continue")
			#with If(startScreen.flag == "none"):
			#	Debug(z="skdjfh")
			Debug(y = startScreen.flag)
			Debug(x = "continue btn has been clicked")'''

	exp.run()
