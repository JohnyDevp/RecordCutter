import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QSlider, QMessageBox
)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


def fmt_seconds(sec):
    sec = int(sec)
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


class MassSongPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mass Song Cutter (Player only)")
        self.resize(700, 250)

        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.on_position_changed)
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.stateChanged.connect(self.on_state_changed)

        self.duration_ms = 0
        self.loop_start_ms = None
        self.loop_end_ms = None

        layout = QVBoxLayout(self)

        # ===== Timeline =====
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setEnabled(False)
        self.slider.sliderMoved.connect(self.seek)
        layout.addWidget(self.slider)

        time_layout = QHBoxLayout()
        self.current_label = QLabel("00:00")
        self.total_label = QLabel("00:00")
        time_layout.addWidget(self.current_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_label)
        layout.addLayout(time_layout)

        # ===== Controls =====
        controls = QHBoxLayout()

        self.load_btn = QPushButton("Load audio")
        self.load_btn.clicked.connect(self.load_audio)
        controls.addWidget(self.load_btn)

        self.play_btn = QPushButton("Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.toggle_play)
        controls.addWidget(self.play_btn)

        controls.addStretch()
        layout.addLayout(controls)

        # ===== Selection =====
        sel = QHBoxLayout()

        self.set_start_btn = QPushButton("Set START")
        self.set_start_btn.clicked.connect(self.set_start)
        self.set_start_btn.setEnabled(False)
        sel.addWidget(self.set_start_btn)

        self.set_end_btn = QPushButton("Set END")
        self.set_end_btn.clicked.connect(self.set_end)
        self.set_end_btn.setEnabled(False)
        sel.addWidget(self.set_end_btn)

        self.play_sel_btn = QPushButton("Play selected")
        self.play_sel_btn.clicked.connect(self.play_selected)
        self.play_sel_btn.setEnabled(False)
        sel.addWidget(self.play_sel_btn)

        layout.addLayout(sel)

        self.sel_label = QLabel("Selection: —")
        layout.addWidget(self.sel_label)

        # Timer to stop playback at end of selection
        self.loop_timer = QTimer()
        self.loop_timer.setInterval(50)
        self.loop_timer.timeout.connect(self.check_loop_end)

    # ================= AUDIO =================

    def load_audio(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select audio file",
            "", "Audio files (*.mp3 *.wav *.m4a *.flac *.ogg)"
        )
        if not path:
            return
        
        # self.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        
        self.play_btn.setEnabled(True)
        self.slider.setEnabled(True)
        self.set_start_btn.setEnabled(True)
        self.set_end_btn.setEnabled(True)
        self.play_sel_btn.setEnabled(False)

        self.loop_start_ms = None
        self.loop_end_ms = None
        self.sel_label.setText("Selection: —")

    def toggle_play(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_state_changed(self, state):
        self.play_btn.setText("Pause" if state == QMediaPlayer.PlayingState else "Play")

    def on_duration_changed(self, dur):
        # dur is milliseconds
        print("Duration changed:", dur)
        self.duration_ms = dur
        self.slider.setRange(0, dur)
        self.total_label.setText(fmt_seconds(dur / 1000))

    def on_position_changed(self, pos):
        self.slider.blockSignals(True)
        self.slider.setValue(pos)
        self.slider.blockSignals(False)

        self.current_label.setText(fmt_seconds(pos / 1000))

    def seek(self, value):
        self.player.setPosition(value)

    # ================= SELECTION =================

    def set_start(self):
        self.loop_start_ms = self.player.position()
        self.update_selection_label()

    def set_end(self):
        self.loop_end_ms = self.player.position()
        self.update_selection_label()

    def update_selection_label(self):
        if self.loop_start_ms is None or self.loop_end_ms is None:
            return

        if self.loop_start_ms >= self.loop_end_ms:
            QMessageBox.warning(self, "Invalid selection", "Start must be before end.")
            self.loop_start_ms = None
            self.loop_end_ms = None
            self.sel_label.setText("Selection: —")
            return

        self.play_sel_btn.setEnabled(True)

        s = fmt_seconds(self.loop_start_ms / 1000)
        e = fmt_seconds(self.loop_end_ms / 1000)
        self.sel_label.setText(f"Selection: {s} → {e}")

    def play_selected(self):
        if self.loop_start_ms is None or self.loop_end_ms is None:
            return

        self.player.setPosition(self.loop_start_ms)
        self.player.play()
        self.loop_timer.start()

    def check_loop_end(self):
        if self.loop_end_ms is not None and self.player.position() >= self.loop_end_ms:
            self.player.pause()
            self.loop_timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MassSongPlayer()
    w.show()
    sys.exit(app.exec_())
