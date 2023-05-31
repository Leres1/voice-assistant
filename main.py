import json
import time
import struct
import queue
import os
import yaml
import random
from ctypes import POINTER, cast

import openai
from openai import error
import pvporcupine
from pvrecorder import PvRecorder
import vosk
from vosk import Model, KaldiRecognizer
import config
from comtypes import CLSCTX_ALL
import pyaudio
from fuzzywuzzy import fuzz
from rich import print
import subprocess
import tts
import pygame
from pycaw.pycaw import (
    AudioUtilities,
    IAudioEndpointVolume
)

# pyaudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()


# some consts
CDIR = os.getcwd()
VA_CMD_LIST = yaml.safe_load(
    open('commands.yaml', 'rt', encoding='utf8'),
)
WORK_STATUS = False


# init openai
openai.api_key = config.OPENAI_TOKEN


# ChatGPT vars
system_message = {"role": "system", "content": "Ти голосовий ассистент."}
message_log = [system_message]


# VOSK
samplerate = 16000
model = Model('vosk-model-uk-v3')
rec = KaldiRecognizer(model, samplerate)
kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
q = queue.Queue()


# PORCUPINE
porcupine = pvporcupine.create(
    access_key=config.PICOVOICE_TOKEN,
    keywords=['computer'],
    sensitivities=[1]
)

#pygame
pygame.mixer.init()


def gpt_answer():
    global message_log

    model_engine = "gpt-3.5-turbo"
    max_tokens = 512  # default 1024
    try:
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=message_log,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=1,
            stop=None
        )
    except (error.TryAgain, error.ServiceUnavailableError):
        return "ChatGPT перегружен!"
    except openai.OpenAIError as ex:
        if ex.code == "context_length_exceeded":
            message_log = [system_message, message_log[-1]]
            return gpt_answer()
        else:
            return "OpenAI токен не дійсний."

    for choice in response.choices:
        if "text" in choice:
            return choice.text

    return response.choices[0].message.content


def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in VA_CMD_LIST.items():

        for x in v:
            vrt = fuzz.ratio(cmd, x)
            
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt

    return rc


def execute_cmd(cmd: str):
    global WORK_STATUS

    if cmd == 'open_browser':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run browser.exe'])    
        play('doing')

    elif cmd == 'open_youtube':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run youtube.exe'])
        play('doing')
    
    elif cmd == 'open_google':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run google.exe'])
        play('doing')

    elif cmd == 'open_discord':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run discord.exe'])   
        play('doing')   

    elif cmd == 'open_steam':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run steam.exe'])      
        play('doing')

    elif cmd == 'open_music':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Run music.exe'])      
        play('launching')
    
    elif cmd == 'next_music':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Next music.exe'])      
        # play('launching')
    
    elif cmd == 'previos_music':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Previos music.exe'])      
        # play('launching')
    
    elif cmd == 'pause_music':
        subprocess.Popen([f'{CDIR}\\custom-commands\\Pause-continue music.exe'])      
        # play('launching')
    

    elif cmd == 'thanks':
        WORK_STATUS = False  
        play('thanks')

    elif cmd == 'sound_off':
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(1, None)
        play('doing')

    elif cmd == 'sound_on':
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume.SetMute(0, None)
        play('doing')
    
    # Problem 1 - чує сам себе
    # elif cmd == 'stop':
    #     filename += "ON.mp3"
    #     stopSound() 
    

def playSound(filename: str):
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    # while pygame.mixer.music.get_busy():
    #     pass

# Problem 1 - чує сам себе
# def stopSound():
#     tts.va_stop()


def play(phrase):
    global recorder, WORK_STATUS
    filename = f"{CDIR}\\sound\\"

    if phrase == "looking_for_information": 
        filename += f"Looking_for_information_{random.choice([1, 2, 3, 4])}.mp3"

    if phrase == "doing": 
        filename += f"Doing_{random.choice([1, 2, 3, 4, 5])}.mp3"

    if phrase == "thanks": 
        filename += "OFF.mp3"
    
    if phrase == "launching": 
        filename += "OFF.mp3"
 
    if phrase == "short_request": 
        filename += f"Short_request.mp3"
        
    recorder.stop()
    playSound(filename)
    recorder.start()


def va_respond(voice: str):
    global recorder, message_log, first_request
    print(f"Розпізнано: {voice}")

    cmd = recognize_cmd(voice)

    print(cmd)
    if len(cmd['cmd'].strip()) <= 0:
        return False
    elif cmd['percent'] < 70:
        if len(voice) > 15:
            play('looking_for_information')
            message_log.append({"role": "user", "content": voice})
            response = gpt_answer()
            message_log.append({"role": "assistant", "content": response})

            recorder.stop()
            print(response)
            tts.va_speak(response)
            time.sleep(0.5)
            recorder.start()
            return False
        else:
            play('short_request')
    else:
        execute_cmd(cmd['cmd'])
        return True


recorder = PvRecorder(device_index=config.MICROPHONE_INDEX, frame_length=porcupine.frame_length)
recorder.start()

print('Using device: %s' % recorder.selected_device)

time.sleep(0.5)

while True:
    try:
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            recorder.stop()
            filename = filename = f"{CDIR}\\sound\\ON.mp3"
            print("Yes, sir.")
            playSound(filename)
            recorder.start()
            WORK_STATUS = True

        while WORK_STATUS:
            pcm = recorder.read()
            sp = struct.pack("h" * len(pcm), *pcm)

            if kaldi_rec.AcceptWaveform(sp):
                va_respond(json.loads(kaldi_rec.Result())["text"])

    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        raise


# Доступні функції:

# відкрити браузер
# відкрити ютуб
# відкрити діскорд
# відкрити стім
# запустити/перемикати музику
# включення/виключення звуку комп'ютера
# відповіді від ChatGPT
# виключення сприймання команд