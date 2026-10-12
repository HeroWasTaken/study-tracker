__version__ = "1.0.0"

import json
import os
import time
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.properties import ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

# Calm dark theme
BG = (0.055, 0.075, 0.12, 1)
PANEL = (0.10, 0.13, 0.19, 1)
MUTED = (0.66, 0.71, 0.80, 1)
WHITE = (0.95, 0.97, 1, 1)
GREEN = (0.20, 0.78, 0.52, 1)
BLUE = (0.30, 0.55, 0.98, 1)
ORANGE = (1.00, 0.62, 0.30, 1)
RED = (0.95, 0.32, 0.36, 1)

SUBJECTS = ["Physics", "Maths", "Chemistry"]
SUBJECT_COLORS = {"Physics": GREEN, "Maths": BLUE, "Chemistry": ORANGE}


class RoundedButton(Button):
    """A Button with a rounded, theme-colored background."""
    fill_color = ListProperty([0.10, 0.13, 0.19, 1])

    def __init__(self, **kwargs):
        initial_color = kwargs.pop("background_color", [0.10, 0.13, 0.19, 1])
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        super().__init__(background_color=(0, 0, 0, 0), **kwargs)
        self.fill_color = initial_color
        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            self._fill_instruction = Color(*self.fill_color)
            self._rounded_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(14)]
            )
        self.bind(pos=self._update_rounded_rect, size=self._update_rounded_rect,
                  fill_color=self._update_fill_color)

    def _update_rounded_rect(self, *_):
        self._rounded_rect.pos = self.pos
        self._rounded_rect.size = self.size

    def _update_fill_color(self, *_):
        self._fill_instruction.rgba = self.fill_color


def time_string(seconds):
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


class StudyTrackerApp(App):
    def build(self):
        self.title = "Study Tracker"
        Window.clearcolor = BG
        self.counts = {s: 0 for s in SUBJECTS}
        self.current_subject = "Physics"
        self.accumulated = 0.0
        self.started_at = None
        self.running = False
        self.session_active = False
        self.session_started = None
        self.history = []
        self.load_history()

        root = BoxLayout(orientation="vertical", padding=[dp(18), dp(38), dp(18), dp(18)], spacing=dp(12))

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(62), spacing=dp(2))
        header.add_widget(Label(text="STUDY TRACKER", font_size=sp(13), bold=True,
                                color=GREEN, size_hint_y=None, height=dp(20)))
        header.add_widget(Label(text="Small steps. Real progress.", font_size=sp(20), bold=True,
                                color=WHITE))
        root.add_widget(header)

        timer_panel = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(132),
                                padding=[dp(12), dp(12)], spacing=dp(5))
        timer_panel.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with timer_panel.canvas.before:
            Color(*PANEL)
            self.timer_bg = RoundedRectangle(pos=timer_panel.pos, size=timer_panel.size, radius=[dp(18)])
        timer_panel.bind(pos=lambda w, p: setattr(self.timer_bg, "pos", p),
                         size=lambda w, s: setattr(self.timer_bg, "size", s))
        timer_panel.add_widget(Label(text="STUDY TIME", font_size=sp(12), color=MUTED,
                                     size_hint_y=None, height=dp(22)))
        self.timer_label = Label(text="00:00:00", font_size=sp(36), bold=True, color=WHITE)
        timer_panel.add_widget(self.timer_label)
        self.timer_status = Label(text="Timer ready", font_size=sp(11), color=MUTED,
                                  size_hint_y=None, height=dp(20))
        timer_panel.add_widget(self.timer_status)
        root.add_widget(timer_panel)

        root.add_widget(Label(text="QUESTIONS SOLVED", font_size=sp(12), bold=True,
                              color=MUTED, size_hint_y=None, height=dp(22)))

        cards = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(102))
        self.count_labels = {}
        for subject in SUBJECTS:
            card = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(2))
            with card.canvas.before:
                Color(*PANEL)
                bg_rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(14)])
            card.bind(pos=lambda w, p, r=bg_rect: setattr(r, "pos", p),
                      size=lambda w, s, r=bg_rect: setattr(r, "size", s))
            card.add_widget(Label(text=subject, font_size=sp(12), color=SUBJECT_COLORS[subject],
                                  size_hint_y=None, height=dp(22)))
            count = Label(text="0", font_size=sp(27), bold=True, color=WHITE)
            self.count_labels[subject] = count
            card.add_widget(count)
            cards.add_widget(card)
        root.add_widget(cards)

        root.add_widget(Label(text="CURRENT SUBJECT", font_size=sp(12), bold=True,
                              color=MUTED, size_hint_y=None, height=dp(20)))
        subject_row = GridLayout(cols=3, spacing=dp(8), size_hint_y=None, height=dp(46))
        self.subject_buttons = {}
        for subject in SUBJECTS:
            btn = RoundedButton(text=subject, font_size=sp(14), bold=True,
                                fill_color=SUBJECT_COLORS[subject] if subject == self.current_subject else PANEL,
                                color=BG if subject == self.current_subject else WHITE)
            btn.bind(on_release=lambda instance, s=subject: self.select_subject(s))
            self.subject_buttons[subject] = btn
            subject_row.add_widget(btn)
        root.add_widget(subject_row)

        self.selected_label = Label(text="Adding questions to Physics",
                                    font_size=sp(13), color=MUTED,
                                    size_hint_y=None, height=dp(24))
        root.add_widget(self.selected_label)

        add_btn = RoundedButton(text="+1  QUESTION SOLVED", size_hint_y=None, height=dp(62),
                                font_size=sp(17), bold=True, fill_color=GREEN, color=BG)
        self.add_btn = add_btn
        add_btn.bind(on_release=self.add_question)
        root.add_widget(add_btn)

        controls = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(48))
        self.pause_btn = RoundedButton(text="▶  Start timer", font_size=sp(14),
                                       fill_color=PANEL, color=WHITE)
        self.pause_btn.bind(on_release=self.toggle_timer)
        controls.add_widget(self.pause_btn)

        finish_btn = RoundedButton(text="Finish session", font_size=sp(14), bold=True,
                                   fill_color=(0.35, 0.15, 0.19, 1), color=(1, 0.72, 0.74, 1))
        self.finish_btn = finish_btn
        finish_btn.bind(on_release=self.confirm_finish)
        controls.add_widget(finish_btn)
        root.add_widget(controls)

        history_btn = RoundedButton(text="View saved session history", size_hint_y=None, height=dp(38),
                                    font_size=sp(12), fill_color=BG, color=MUTED)
        history_btn.bind(on_release=self.show_history)
        root.add_widget(history_btn)

        root.add_widget(Widget())
        self.reported = False
        self._set_session_controls()
        Clock.schedule_interval(self.update_timer, 1)
        return root

    def elapsed(self):
        if self.running and self.started_at is not None:
            return self.accumulated + (time.monotonic() - self.started_at)
        return self.accumulated

    def _set_session_controls(self):
        if not self.session_active:
            self.pause_btn.text = "▶  Start timer"
            self.pause_btn.fill_color = PANEL
            self.finish_btn.disabled = True
            self.add_btn.disabled = True
        else:
            self.pause_btn.text = "Ⅱ  Pause timer" if self.running else "▶  Resume timer"
            self.pause_btn.fill_color = PANEL
            self.finish_btn.disabled = False
            self.add_btn.disabled = False

    def update_timer(self, _dt):
        self.timer_label.text = time_string(self.elapsed())
        if not self.session_active:
            self.timer_status.text = "Timer ready — press Start"
            self.timer_status.color = MUTED
        elif self.running:
            self.timer_status.text = "STUDYING"
            self.timer_status.color = GREEN
        else:
            self.timer_status.text = "TIMER PAUSED"
            self.timer_status.color = ORANGE

    def select_subject(self, subject):
        self.current_subject = subject
        self.selected_label.text = f"Adding questions to {subject}"
        for name, btn in self.subject_buttons.items():
            selected = name == subject
            btn.fill_color = SUBJECT_COLORS[name] if selected else PANEL
            btn.color = BG if selected else WHITE

    def add_question(self, *_):
        if not self.session_active:
            return
        self.counts[self.current_subject] += 1
        self.count_labels[self.current_subject].text = str(self.counts[self.current_subject])

    def toggle_timer(self, *_):
        if not self.session_active:
            self.counts = {s: 0 for s in SUBJECTS}
            for subject in SUBJECTS:
                self.count_labels[subject].text = "0"
            self.accumulated = 0.0
            self.started_at = time.monotonic()
            self.session_started = datetime.now().isoformat(timespec="seconds")
            self.session_active = True
            self.running = True
            self.reported = False
        elif self.running:
            self.accumulated += time.monotonic() - self.started_at
            self.started_at = None
            self.running = False
        else:
            self.started_at = time.monotonic()
            self.running = True
        self._set_session_controls()
        self.update_timer(0)

    def load_history(self):
        try:
            with open(self.history_path(), "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except (OSError, ValueError, TypeError):
            self.history = []

    def history_path(self):
        return os.path.join(self.user_data_dir, "study_history.json")

    def save_history(self):
        try:
            with open(self.history_path(), "w", encoding="utf-8") as f:
                json.dump(self.history[-100:], f, indent=2)
        except OSError:
            pass

    def confirm_finish(self, *_):
        if self.reported:
            return
        content = BoxLayout(orientation="vertical", padding=dp(14), spacing=dp(12))
        content.add_widget(Label(text="Finish this study session and save the report?",
                                 color=WHITE, halign="center", valign="middle"))
        row = GridLayout(cols=2, spacing=dp(10), size_hint_y=None, height=dp(46))
        popup = Popup(title="Finish session?", content=content, size_hint=(0.88, None),
                      height=dp(190), separator_color=GREEN, background_color=PANEL)
        cancel = RoundedButton(text="Keep studying", fill_color=PANEL)
        finish = RoundedButton(text="Finish", fill_color=GREEN, color=BG)
        cancel.bind(on_release=popup.dismiss)
        finish.bind(on_release=lambda *_: (popup.dismiss(), self.finish_session()))
        row.add_widget(cancel)
        row.add_widget(finish)
        content.add_widget(row)
        popup.open()

    def finish_session(self):
        if self.reported:
            return
        if self.running:
            self.accumulated += time.monotonic() - self.started_at
            self.running = False
        self.reported = True
        total = sum(self.counts.values())
        record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "duration_seconds": int(self.accumulated),
            "counts": dict(self.counts),
            "total": total,
        }
        self.history.append(record)
        self.save_history()

        # Reset the live session immediately; the saved report uses the snapshot above.
        completed_duration = record["duration_seconds"]
        completed_counts = dict(record["counts"])
        self.accumulated = 0.0
        self.started_at = None
        self.running = False
        self.session_active = False
        self.session_started = None
        self.counts = {s: 0 for s in SUBJECTS}
        for subject in SUBJECTS:
            self.count_labels[subject].text = "0"
        self.reported = False
        self._set_session_controls()
        self.update_timer(0)

        content = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        content.add_widget(Label(text="SESSION COMPLETE", color=GREEN, bold=True,
                                 font_size=sp(13), size_hint_y=None, height=dp(25)))
        content.add_widget(Label(text=time_string(completed_duration), color=WHITE,
                                 bold=True, font_size=sp(30), size_hint_y=None, height=dp(45)))
        content.add_widget(Label(text="Total study time", color=MUTED, size_hint_y=None, height=dp(22)))
        for subject in SUBJECTS:
            content.add_widget(Label(text=f"{subject}: {completed_counts[subject]} questions",
                                     color=WHITE, size_hint_y=None, height=dp(24)))
        content.add_widget(Label(text=f"Total: {total} questions", color=GREEN, bold=True,
                                 size_hint_y=None, height=dp(28)))
        close = RoundedButton(text="Done", size_hint_y=None, height=dp(46),
                              fill_color=GREEN, color=BG)
        content.add_widget(close)
        popup = Popup(title="Study report", content=content, size_hint=(0.88, 0.72),
                      separator_color=GREEN, background_color=PANEL, auto_dismiss=False)
        close.bind(on_release=popup.dismiss)
        popup.open()

    def show_history(self, *_):
        self.load_history()
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(8))
        scroll = ScrollView()
        items = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        items.bind(minimum_height=items.setter("height"))
        if not self.history:
            items.add_widget(Label(text="No saved sessions yet.", color=MUTED,
                                   size_hint_y=None, height=dp(45)))
        else:
            for record in reversed(self.history):
                counts = record.get("counts", {})
                text = (f"{record.get('date', 'Unknown date')}\n"
                        f"Time: {time_string(record.get('duration_seconds', 0))}  •  "
                        f"Total: {record.get('total', 0)} questions\n"
                        f"P: {counts.get('Physics', 0)}   "
                        f"M: {counts.get('Maths', 0)}   "
                        f"C: {counts.get('Chemistry', 0)}")
                items.add_widget(Label(text=text, color=WHITE, halign="left", valign="middle",
                                       size_hint_y=None, height=dp(78),
                                       text_size=(Window.width * 0.72, None)))
        scroll.add_widget(items)
        content.add_widget(scroll)
        close = RoundedButton(text="Close", size_hint_y=None, height=dp(44),
                              fill_color=GREEN, color=BG)
        content.add_widget(close)
        popup = Popup(title="Saved sessions", content=content, size_hint=(0.92, 0.78),
                      separator_color=GREEN, background_color=PANEL)
        close.bind(on_release=popup.dismiss)
        popup.open()


if __name__ == "__main__":
    StudyTrackerApp().run()
