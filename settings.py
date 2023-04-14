import json

with open("settings.json", 'r', encoding="utf-8") as jsf:
  settings = json.load(jsf)

FFPMEG_PATH = settings['ffmpeg-path']
GEN_VIDEO_PATH = settings['generated-video-path']
GEN_IMAGE_PATH = settings['generated-image-path']
TAKEN_AUDIO_PATH = settings['taken-audio-path']
