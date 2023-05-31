import sounddevice as sd
import torch
import time
from num2words import num2words

language = 'ua'
model_id = 'v3_ua'
sample_rate = 48000
speaker = 'mykyta'
put_accent = True
put_yo = True
device = torch.device('cpu')


model, _ = torch.hub.load(repo_or_dir='snakers4/silero-models',
               model='silero_tts',
               language=language,
               speaker=model_id
)

model.to(device)
def va_speak(what: str):
    textToSpeech = changeNumToWord(what)

    audio = model.apply_tts(text=textToSpeech,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)

    sd.play(audio, sample_rate * 1.05)
    time.sleep((len(audio) / sample_rate) + 0.5)
    sd.stop()

def changeNumToWord(text: str):
    length = len(text)
    integers = []
    i = 0 
    
    while i < length:
        s_int = ''  # строка для нового числа
        while i < length and '0' <= text[i] <= '9':
            s_int += text[i]
            i += 1
        i += 1
        if s_int != '':
            if len(s_int) < 33: # 33 максимальна кількість переводу числа в текст у num2words
                integers.append(s_int)
    
    for item in integers:
        text = text.replace(item, str(num2words(item, lang='uk')))

    return text