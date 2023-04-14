import settings

from scipy.interpolate import make_interp_spline
from scipy.fft import rfft, rfftfreq

import numpy as np
from scipy.io import wavfile
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import FFMpegWriter

def create_jumping_wave_video(file_in: str, file_out: str, fps=60, background_color='black', line_color='green', line_width=1):
  HEARING_BORDERS = (256, 16500)

  samplerate, data = wavfile.read(file_in)
  data = data.astype("float64")
  audio_data = np.mean(data.T, axis = 0)
  normalized_fcd = np.int16((audio_data / audio_data.max()) * 32767)

  duration = len(audio_data) / samplerate

  # раздеяем на блоки для каждого кадра
  sample_per_frame = samplerate // fps
  frames_count = int(duration * fps)

  frames_data = np.split(normalized_fcd[0:sample_per_frame * frames_count], frames_count)

  fig = plt.figure(figsize=(10.8, 7.2), linewidth = line_width)
  ax = plt.axes(xlim = HEARING_BORDERS, ylim=(-10, 5 * 10 ** 6))

  line, = ax.plot([], [], lw=line_width)

  fig.set_facecolor(background_color)
  ax.set_facecolor(background_color)

  def init():
    line.set_data([], [])
    line.set_color(line_color)
    return line,

  N = len(frames_data[0])
  xf = rfftfreq(N, 1 / samplerate)
  def animate(i):

    yf = rfft(frames_data[i])
    if (i % 100 == 0):
      print(f'{i} / {frames_count}')

    x = xf
    y = np.abs(yf)
    X_Y_Spline = make_interp_spline(x, y)
    
    X_ = np.linspace(x.min(), x.max(), len(x) * 4)
    Y_ = X_Y_Spline(X_)

    line.set_data(X_ , Y_)
    return line, 

  plt.rcParams['animation.ffmpeg_path'] = settings.FFPMEG_PATH

  interval = 1 / fps
  ax.set_xscale('log', base=10)
  anim = FuncAnimation(fig, animate, init_func=init, frames=frames_count, interval=interval) #, blit=True)

  ax.tick_params(axis='x', colors=line_color)
  anim.save(file_out, writer = FFMpegWriter(fps=fps))

if __name__ == "__main__":
  print("Program is running...")
  create_jumping_wave_video(settings.TAKEN_AUDIO_PATH + "Big-cities.wav", settings.GEN_VIDEO_PATH + "Big-cities.mp4", line_width=2, line_color="#FF9A26")
