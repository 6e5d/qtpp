from subprocess import run, Popen
from math import log, exp
from time import sleep
from pathlib import Path
import socket, os, sys
from qtpy.QtWidgets import QApplication, QSlider, QWidget, QLabel
from qtpy.QtCore import Qt

class Slider(QSlider):
	def __init__(self, parent, pmin, pmax, pinit, idx):
		super().__init__(Qt.Orientation.Horizontal, parent)
		if isinstance(pmin, float):
			self.log = pmin != 0 and pmax / pmin > 100
			if self.log:
				pmin = log(pmin)
				pmax = log(pmax)
				pinit = log(pinit)
			self.setMinimum(0)
			self.setMaximum(100)
			initval = (pinit - pmin) / (pmax - pmin) * 100
			self.setValue(int(initval))
			self.float = True
		else:
			self.setMinimum(pmin)
			self.setMaximum(pmax)
			self.setValue(pinit)
			self.setTickInterval(1)
			self.setSingleStep(1)
			self.float = False
		self.pmin = pmin
		self.pmax = pmax
		self.pinit = pinit
		self.idx = idx
	def get_value(self):
		val = self.value()
		if self.float:
			val = val / 100 * (self.pmax - self.pmin) + self.pmin
			if self.log:
				val = exp(val)
		return val

class Main(QWidget):
	def value_change(self):
		sender = self.sender()
		v = sender.get_value()
		self.sliders[sender.idx][2].setText(str(v))
	def send_value(self):
		msg = []
		for slider in self.sliders:
			msg.append(slider[1].get_value())
		s = " ".join([str(m) for m in msg])
		print(s)
		print(s, file = self.s)
		self.s.flush()
	def __init__(self, keys, ps, s):
		super().__init__(None)
		self.s = s
		self.keys = keys
		self.sliders = []
		dy = 20
		x1 = 50
		x2 = 200
		for idx, key in enumerate(self.keys):
			pmin = ps[0][idx]
			pmax = ps[1][idx]
			pinit = ps[2][idx]
			lt = QLabel(key, self)
			lt.setFixedWidth(x1)
			lt.move(0, dy * idx)
			lt.show()
			slider = Slider(self, pmin, pmax, pinit, idx)
			slider.move(x1, dy * idx)
			slider.show()
			slider.valueChanged.connect(self.value_change);
			slider.sliderReleased.connect(self.send_value);
			lv = QLabel(str(pinit), self)
			slider.resize(x2 - x1, dy)
			lv.move(x2, dy * idx)
			lv.show()
			lv.setFixedWidth(50)
			self.sliders.append((lt, slider, lv))
		self.send_value()

def main(keys, ps, s):
	app = QApplication([])
	main = Main(keys, ps, s)
	main.show()
	app.exec()

def parse():
	keys = []
	ps = [[], [], []]
	for line in open(sys.argv[1]):
		sp = line.strip().split()
		keys.append(sp[0])
		for i in range(3):
			if "." in sp[i + 1]:
				sp[i + 1] = float(sp[i + 1])
			else:
				sp[i + 1] = int(sp[i + 1])
			ps[i].append(sp[i + 1])
	return keys, ps

path = Path(sys.argv[1]).resolve().parent
proj = path.name
p = Popen(
	["cargo", "run", "--release", "--manifest-path", path / "Cargo.toml"],
	stderr = sys.stderr,
	stdout = sys.stdout,
)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
while True:
	try:
		s.connect(os.environ["XDG_CACHE_HOME"] + f"/{proj}.sock")
		break
	except Exception as e:
		print("Retry...", e)
		sleep(1)
run(["myl", "fcon", "keyboard", "polysplit", "headphone"])
try:
	s = s.makefile(mode = "rw")
	keys, ps = parse()
	print(keys)
	main(keys, ps, s)
finally:
	s.close()
	p.kill()
