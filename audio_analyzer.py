import static

import os
import subprocess

from scipy.interpolate import make_interp_spline
from scipy.fft import rfft, rfftfreq

import numpy as np
from scipy.io import wavfile
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import FFMpegWriter

def convert_audio_to_wav(input_audio, output_audio):
  cmd = f'ffmpeg -y -i \"{input_audio}\" \"{output_audio}\"'
  return_status = subprocess.call(cmd, shell=True)
  os.remove(input_audio)
  return return_status

def add_audio_on_video(input_video_path, audio_path, output_video_path):
  cmd = f'ffmpeg -y -i \"{input_video_path}\" -i \"{audio_path}\" -c:v copy -map 0:v:0 -map 1:a:0 \"{output_video_path}\"'
  return subprocess.call(cmd, shell=True)

def create_jumping_wave_video(file_in: str, file_out: str, fps=60, background_color='black', foreground_color='green', line_width=1, print_func=print):
  """
  Функция, раскладывающая аудиофайл по частотам, и показывающая, насколько интенсивна каждая частота в диапазоне от 256 до 16500 Гц
  """
  HEARING_BORDERS = (256, 16500)

  samplerate, data = wavfile.read(file_in)
  data = data.astype("float64")
  
  if len(data.T.shape) > 1:
    audio_data = np.mean(data.T, axis = 0)
  else:
    audio_data = data.T
  normalized_fcd = np.int16((audio_data / audio_data.max()) * 32767)

  duration = len(audio_data) / samplerate

  # раздеяем на блоки для каждого кадра
  sample_per_frame = samplerate // fps
  frames_count = int(duration * fps)

  frames_data = np.split(normalized_fcd[0:sample_per_frame * frames_count], frames_count)

  fig = plt.figure(figsize=(19.2, 10.8), linewidth = line_width)
  ax = plt.axes(xlim = HEARING_BORDERS, ylim=(-10, 5 * 10 ** 6))

  line, = ax.plot([], [], lw=line_width)
  
  fig.set_facecolor(background_color)
  ax.set_facecolor(background_color)

  def init():
    line.set_data([], [])
    line.set_color(foreground_color)
    return line,

  N = len(frames_data[0])
  xf = rfftfreq(N, 1 / samplerate)
  def animate(i):

    yf = rfft(frames_data[i])
    if i % 100 == 0:
      print_func(f'{i} / {frames_count}')

    x = xf
    y = np.abs(yf)
    X_Y_Spline = make_interp_spline(x, y)
    
    X_ = np.linspace(x.min(), x.max(), len(x) * 4)
    Y_ = X_Y_Spline(X_)

    line.set_data(X_ , Y_)
    return line, 

  plt.rcParams['animation.ffmpeg_path'] = static.FFPMEG_PATH

  interval = 1 / fps
  ax.set_xscale('log', base=10)
  anim = FuncAnimation(fig, animate, init_func=init, frames=frames_count, interval=interval)

  ax.tick_params(axis='x', colors=foreground_color)
  anim.save('tmp.mp4', writer = FFMpegWriter(fps=fps))
  add_audio_on_video('tmp.mp4', file_in, file_out)
  os.remove('tmp.mp4')

def create_amplitude_image(file_in: str, file_out: str, bps: float = 300, background_color: str = 'black', foreground_color: str = 'red'):
  """
  Создаёт картинку, которая отражает амплитуду (громкость) звука в аудио файле в каждый момент времени
  """
  
  samplerate, data = wavfile.read(file_in)

  bps = np.min((len(data), bps))
  to_substract = 0
  if data.dtype == 'uint8':
    to_substract = 2 ** 7 - 1
  elif data.dtype == 'uint16':
    to_substract = 2 ** 15 - 1
  elif data.dtype == 'uint32':
    to_substract = 2 ** 31 - 1
  elif data.dtype == 'uint64':
    to_substract = 2 ** 63 - 1
  elif data.dtype == 'uint128':
    to_substract = 2 ** 127 - 1
  elif data.dtype == 'uint256':
    to_substract = 2 ** 255 - 1

  data = data.astype("float64")
  data -= to_substract

  if len(data.T.shape) > 1:
    audio_data = np.mean(data.T, axis = 0)
  else:
    audio_data = data.T
  
  bars_count = int(len(audio_data) / samplerate * bps)
  sample_per_bar = len(audio_data) // bars_count
  splited_data = np.split(audio_data[0:sample_per_bar * bars_count], bars_count)
  bars_data = np.array(list(map(np.mean, splited_data)))
  x = np.linspace(0, len(data) / samplerate, len(bars_data))
  y = np.abs(bars_data) - 1
  yn = -np.abs(bars_data) + 1
  
  plt.figure(figsize=(19.2, 10.8), facecolor=background_color)
  ax = plt.axes([0, 0.1, 1, 0.8], frameon=False)
  ax.set_facecolor(background_color)
  
  plt.fill_between(x, y, np.zeros_like(y), color=foreground_color)
  plt.fill_between(x, y, np.zeros_like(x), color=foreground_color)
  plt.fill_between(x, yn, np.zeros_like(y), color=foreground_color)
  plt.fill_between(x, yn, np.zeros_like(x), color=foreground_color)
  ax.tick_params(axis='x', colors=foreground_color)
  ax.get_yaxis().set_ticks([])
  plt.savefig(file_out)

if __name__ == "__main__":
  print("Program is running...")
  # create_amplitude_image(static.TAKEN_AUDIO_PATH + "XILOFONE.wav", static.GEN_IMAGE_PATH + "XYLOFONE.jpg", foreground_color="pink")
  convert_audio_to_wav(static.TAKEN_AUDIO_PATH + "bs.mp3", static.TAKEN_AUDIO_PATH + "bs.wav")