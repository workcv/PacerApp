from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.window import Window

STEP_M = 1.4

def vibrate(ms):
    if platform == 'android':
        try:
            from android.vibrator import vibrate as android_vibrate
            android_vibrate(ms / 1000.0)  # android.vibrator takes seconds
            return
        except Exception as e1:
            print('android.vibrator failed:', e1)
        # fallback via jnius
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Context        = autoclass('android.content.Context')
            activity       = PythonActivity.mActivity
            vibrator       = activity.getSystemService(Context.VIBRATOR_SERVICE)
            try:
                VibrationEffect = autoclass('android.os.VibrationEffect')
                effect = VibrationEffect.createOneShot(
                    ms, VibrationEffect.DEFAULT_AMPLITUDE)
                vibrator.vibrate(effect)
            except Exception:
                vibrator.vibrate(ms)
        except Exception as e2:
            print('jnius vibrate failed:', e2)

def speed_to_interval(kmh):
    return STEP_M / (kmh * 1000 / 3600)

class PacerLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', padding=30, spacing=16, **kwargs)
        Window.clearcolor = (0.08, 0.08, 0.12, 1)

        self.running     = False
        self.speed       = 7.0
        self.buzz_ms     = 80
        self.clock_event = None

        self.add_widget(Label(
            text='STEP PACER',
            font_size='28sp', bold=True,
            color=(0.6, 0.9, 1, 1), size_hint_y=0.10,
        ))

        self.speed_label = Label(
            text=self._speed_text(self.speed),
            font_size='52sp', bold=True,
            color=(1, 1, 1, 1), size_hint_y=0.20,
        )
        self.add_widget(self.speed_label)

        self.interval_label = Label(
            text=self._interval_text(self.speed),
            font_size='15sp',
            color=(0.55, 0.75, 0.85, 1), size_hint_y=0.08,
        )
        self.add_widget(self.interval_label)

        slider_box = BoxLayout(orientation='vertical', size_hint_y=0.20, spacing=4)
        tick_row = BoxLayout(size_hint_y=0.35)
        for kmh in range(4, 12):
            tick_row.add_widget(Label(
                text=str(kmh), font_size='13sp',
                color=(0.5, 0.7, 0.8, 1),
            ))
        slider_box.add_widget(tick_row)
        self.slider = Slider(
            min=4.0, max=11.0, value=self.speed, step=0.1,
            size_hint_y=0.50, cursor_size=(36, 36),
            value_track=True, value_track_color=(0.3, 0.75, 1, 1),
        )
        self.slider.bind(value=self.on_slider)
        slider_box.add_widget(self.slider)
        slider_box.add_widget(Label(
            text='km / h', font_size='13sp',
            color=(0.45, 0.65, 0.75, 1), size_hint_y=0.20,
        ))
        self.add_widget(slider_box)

        self.pace_label = Label(
            text=self._pace_desc(self.speed),
            font_size='16sp', color=(0.75, 0.9, 0.65, 1), size_hint_y=0.08,
        )
        self.add_widget(self.pace_label)

        buzz_box = BoxLayout(orientation='vertical', size_hint_y=0.15, spacing=4)
        self.buzz_label = Label(
            text='Buzz length:  SHORT  (80 ms)',
            font_size='14sp', color=(1, 0.75, 0.35, 1), size_hint_y=0.4,
        )
        buzz_box.add_widget(self.buzz_label)
        buzz_row = BoxLayout(size_hint_y=0.6, spacing=8)
        buzz_row.add_widget(Label(text='SHORT', font_size='11sp',
                                  color=(0.5,0.5,0.5,1), size_hint_x=0.15))
        self.buzz_slider = Slider(
            min=30, max=300, value=self.buzz_ms, step=10,
            size_hint_x=0.70, cursor_size=(30, 30),
            value_track=True, value_track_color=(1, 0.65, 0.1, 1),
        )
        self.buzz_slider.bind(value=self.on_buzz_slider)
        buzz_row.add_widget(self.buzz_slider)
        buzz_row.add_widget(Label(text='LONG', font_size='11sp',
                                  color=(1,0.75,0.35,1), size_hint_x=0.15))
        buzz_box.add_widget(buzz_row)
        self.add_widget(buzz_box)

        self.status_label = Label(
            text='● Stopped',
            font_size='13sp', color=(0.6, 0.6, 0.6, 1), size_hint_y=0.07,
        )
        self.add_widget(self.status_label)

        self.btn = Button(
            text='START', font_size='24sp', bold=True,
            size_hint_y=0.15,
            background_color=(0.18, 0.55, 0.85, 1),
            background_normal='',
        )
        self.btn.bind(on_press=self.toggle)
        self.add_widget(self.btn)

    def _speed_text(self, kmh):
        return f'{kmh:.1f} km/h'

    def _interval_text(self, kmh):
        t = speed_to_interval(kmh)
        return f'Vibration every  {t:.2f} s  ·  step = {STEP_M} m'

    def _pace_desc(self, kmh):
        if kmh < 5.5:    return '🚶 Slow walk'
        elif kmh < 6.5:  return '🚶 Normal walk'
        elif kmh < 7.5:  return '🚶 Brisk walk'
        elif kmh < 9.0:  return '🏃 Fast walk / jog'
        elif kmh < 10.0: return '🏃 Easy run'
        else:             return '🏃 Running'

    def _buzz_desc(self, ms):
        if ms <= 60:    return 'SHORT'
        elif ms <= 130: return 'MEDIUM'
        elif ms <= 210: return 'LONG'
        else:           return 'VERY LONG'

    def on_slider(self, instance, value):
        self.speed = value
        self.speed_label.text    = self._speed_text(value)
        self.interval_label.text = self._interval_text(value)
        self.pace_label.text     = self._pace_desc(value)
        if self.running:
            self._restart_clock()

    def on_buzz_slider(self, instance, value):
        self.buzz_ms = int(value)
        self.buzz_label.text = (
            f'Buzz length:  {self._buzz_desc(value)}  ({int(value)} ms)'
        )

    def _restart_clock(self):
        if self.clock_event:
            self.clock_event.cancel()
        self.clock_event = Clock.schedule_interval(
            self._buzz, speed_to_interval(self.speed)
        )

    def _buzz(self, dt):
        vibrate(self.buzz_ms)

    def toggle(self, instance):
        if self.running:
            self.running = False
            if self.clock_event:
                self.clock_event.cancel()
                self.clock_event = None
            self.btn.text             = 'START'
            self.btn.background_color = (0.18, 0.55, 0.85, 1)
            self.status_label.text    = '● Stopped'
            self.status_label.color   = (0.6, 0.6, 0.6, 1)
        else:
            self.running = True
            vibrate(self.buzz_ms)
            self._restart_clock()
            self.btn.text             = 'STOP'
            self.btn.background_color = (0.75, 0.22, 0.22, 1)
            self.status_label.text    = '● Running — use split screen to multitask'
            self.status_label.color   = (0.4, 0.9, 0.4, 1)


class PacerApp(App):
    def build(self):
        self.title = 'Step Pacer'
        return PacerLayout()

if __name__ == '__main__':
    PacerApp().run()