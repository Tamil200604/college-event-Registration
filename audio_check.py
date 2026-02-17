import speech_recognition as sr

BAD_WORDS = ["badword1", "badword2", "abuse"]

def check_audio(audio_path):
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio).lower()

        for word in BAD_WORDS:
            if word in text:
                return "Needs Review"

        return "Approved"

    except:
        return "Needs Review"
