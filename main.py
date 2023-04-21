import static
import audio_analyzer
from matplotlib.colors import is_color_like

import telebot
from telebot import types

kwargs = None
act_func = None

# todo реализовать для каждого чата отдельную инфу
editing_message_id = {}

args_to_pass = [
  'file_in',
  'file_out',
  'fps',
  'bps',
  'line_width',
  'print_func',
]
actions = {
  'Видео частотного спектра': audio_analyzer.create_jumping_wave_video,
  'Изображение амплитуд': audio_analyzer.create_amplitude_image,
}
status = {
  'command_choosing': True,
  'looking_for_audio': False,
  'is_editing_message_set': False,
}
status.update(dict(map(lambda item: (item[0], False), actions.items())))

bot = telebot.TeleBot(static.BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
  status['command_choosing'] = True
  sending_msg = static.messages['greetings'].format(message.from_user.first_name)
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  buttons = []
  for action_name in actions:
    buttons.append(types.KeyboardButton(action_name))
  markup.add(*buttons)
  bot.send_message(message.chat.id, sending_msg, reply_markup=markup)

@bot.message_handler(content_types=['text', 'audio', 'voice'])
def functions_handler(message):
  global kwargs, act_func

  if status['command_choosing']:
    action_name = message.text
    if action_name not in actions:
      bot.send_message(message.chat.id, static.messages['unknown_command'])
      return None 

    status['command_choosing'] = False
    status[action_name] = True
    act_about = get_action_about_text(action_name)
    bot.send_message(message.chat.id, act_about)
  else:
    for action_name in actions:
      if status[action_name]:
        if not status['looking_for_audio']:
          given_args = message.text.split()
          act_func = actions[action_name]
          var_names = act_func.__code__.co_varnames[:act_func.__code__.co_argcount]
          to_provide_vars = list(filter(lambda name: name not in args_to_pass, var_names))
          if len(given_args) != len(to_provide_vars):
            bot.send_message(message.chat.id, static.messages['args_count_incorrect'])
          else:
            kwargs = dict(zip(to_provide_vars, given_args))
            isok = True
            for arg in kwargs:
              if arg == "background_color" or arg == "foreground_color":
                if not is_color_like(kwargs[arg]):
                  isok = False
                  break
            if isok:
              bot.send_message(message.chat.id, static.messages['now_send_audio'])
              status['looking_for_audio'] = True
            else:
              bot.send_message(message.chat.id, static.messages['incorrect_colors'])
        else:
          # получить основную информацию о файле и подготовить его к загрузке
          if message.content_type == "audio":
            file_id = message.audio.file_id
            file_name = message.audio.file_name
          elif message.content_type == "voice":
            file_id = message.voice.file_id
            file_name = "voice_msg.ogg"
          else:
            bot.send_message(message.chat.id, static.messages['audio_is_not_found'])
            return None
          
          file_info = bot.get_file(file_id)
          downloaded_file = bot.download_file(file_info.file_path)
          src = static.TAKEN_AUDIO_PATH + file_name
          with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
          
          tmp_audio_name = static.TAKEN_AUDIO_PATH + "tmp.wav"
          audio_analyzer.convert_audio_to_wav(src, tmp_audio_name)

          if action_name == "Изображение амплитуд":
            kwargs['file_in'] = tmp_audio_name
            kwargs['file_out'] = static.GEN_IMAGE_PATH + "tmp.jpg"
            act_func(**kwargs)
            with open(kwargs['file_out'], 'rb') as video_to_send:
              bot.send_photo(message.chat.id, video_to_send)
          elif action_name == "Видео частотного спектра":
            kwargs['file_in'] = tmp_audio_name
            kwargs['file_out'] = static.GEN_VIDEO_PATH + "tmp.mp4"
            act_func(**kwargs)
            with open(kwargs['file_out'], 'rb') as video_to_send:
              bot.send_video(message.chat.id, video_to_send)

          status['looking_for_audio'] = False
          status[action_name] = False
          status['command_choosing'] = True 


def get_action_about_text(action_name):
  act_func = actions[action_name]
  var_names = act_func.__code__.co_varnames[:act_func.__code__.co_argcount]
  to_provide_vars = list(filter(lambda name: name not in args_to_pass, var_names))

  if act_func.__doc__ == None:
    act_func.__doc__ = static.messages['no_func_description']

  text = static.messages['args_below'].format(act_func.__doc__, ' '.join(to_provide_vars))
  
  for arg in to_provide_vars:
    text += f"{arg} - {static.messages['arguments'][arg]}\n"

  return text

if __name__ == "__main__":
  bot.polling(none_stop=True)
