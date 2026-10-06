VOICE_NAME = "zari"   
RATE = 170
VOLUME = 1.0          

def _configure(engine):
    engine.setProperty("rate", RATE)
    engine.setProperty("volume", VOLUME)
    for v in engine.getProperty("voices"):
        if VOICE_NAME.lower() in v.name.lower():
            engine.setProperty("voice", v.id)
            break


def speak(text):
    import pyttsx3
    engine = pyttsx3.init()
    _configure(engine)
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    del engine