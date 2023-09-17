from gtts import gTTS
import speech_recognition as sr
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from decouple import config
import spacy
import re

# creating the recoginzer
recognizer = sr.Recognizer()

# creating these to use later to access spotify api
SPOTIPY_USERNAME = config("SPOTIPY_USERNAME")
SPOTIPY_PASSWORD = config("SPOTIPY_PASSWORD")

# initializing the spotify api
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIPY_USERNAME, client_secret=SPOTIPY_PASSWORD))

# initializing spacy to find names for calling
nlp = spacy.load("en_core_web_sm")

# actually speaking
def speak(text):
    tts = gTTS(text)
    tts.save("temp.mp3")
    os.system("mpg321 temp.mp3")
    os.remove("temp.mp3")



#listen to the input
def listening():
    with sr.Microphone() as source:
        print("Listening for an input....")
        recognizer.adjust_for_ambient_noise(source) # making sure that no ambient noise gets in the way of the input
        audio = recognizer.listen(source)
        print(audio)
    return audio

def recognize_command(audio):
    try:
        command = recognizer.recognize_sphinx(audio)
        print(command)
        return command
    except sr.UnknownValueError:
        print("Sorry, the audio could not be understood.")
        return ""  # return an empty string instead of None
    except sr.RequestError:
        print("Sorry, there are technical difficulties with sphinx.")
        return "" 

def play_music(command):
    music_keywords = ["play", "song", "artist", "by"]

    # split the command
    words = command.lower().split()

    # check if command has all keywords
    if all(keyword in words for keyword in music_keywords):
        # extract the item to play song and artist name
        item_to_play_index = words.index("play") + 1
        item_to_play = words[item_to_play_index]
        
        artist_index = words.index("by") + 1
        artist_name = " ".join(words[artist_index:])

        # perform the actions based on the extracted item and artist
        if "song" in item_to_play:
            # Remove "song" from the item_to_play string
            item_to_play = item_to_play.replace("song", "").strip()
            # search for the song on spotify api
            results = sp.search(q=f"track:{item_to_play} artist:{artist_name}", type="track")
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                song_name = track['name']
                artist_name = track['artists'][0]['name']
                speak(f"Playing '{song_name}' by '{artist_name}'")
            else:
                speak("Sorry, I couldn't find that song.")
        elif "artist" in item_to_play:
            # remove "artist" from the item_to_play string
            item_to_play = item_to_play.replace("artist", "").strip()
            # search for the artist on api
            results = sp.search(q=f"artist:{item_to_play}", type="artist")
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                artist_name = artist['name']
                speak(f"Playing songs by '{artist_name}'")
            else:
                speak("Sorry, I couldn't find that artist.")
        else:
            speak("I'm not sure whether you want to play a song or an artist.")
    else:
        speak("Please say an artist or a song you want to play. Saying both is very helpful")

def adjust_temperature(command):
    try:
        # split the command
        words = command.split()
        
        # find the index of temp
        temperature_index = None
        for i, word in enumerate(words):
            if word.isdigit():
                temperature_index = i
                break

        if temperature_index is not None:
            temperature = int(words[temperature_index])
            speak(f"Adjusting temperature to {temperature} degrees.")
        else:
            speak("Temperature value not found in the command.")
    except Exception:
        speak("An error occurred")

def can_we_make_phone_call(command):
    doc = nlp(command)

    # Extract names from the command
    names = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    phone_numbers = re.findall(r'\d{10}', command)

    # figuring out if it's a name or a number
    if names and phone_numbers:
        contact = names[0]
        phone_number = phone_numbers[0]
        confirmation_command = f"Call {contact} at {phone_number}."
        speak(f"Detected both a name and a phone number. Did you mean to call {contact} at {phone_number}? Please say 'yes' or 'no' to confirm.")
        response = recognize_command()
        if response and "yes" in response.lower():
            make_phone_call(contact, phone_number)
        else:
            speak("Call canceled.")
    elif names:
        contact = names[0] 
        make_phone_call(contact)
    elif phone_numbers:
        phone_number = phone_numbers[0]
        make_phone_call(phone_number)
    else:
        speak("Sorry, I couldn't identify who you wanted to call.")

def make_phone_call(contact):
    speak(f"Currently making a call to {contact}...")

def execute_command(command):
    if "play" in command:
        play_music(command)
        return "Playing music"
    elif "temperature" in command or "degrees" in command or "ac" in command:
        adjust_temperature(command)
        return "Adjusting temperature"
    elif "call" in command or "dial" in command:
        can_we_make_phone_call(command)
        return "Making phone call"
    else:
        return "Sorry, I don't understand that command"
    
if __name__ == "__main__":
    while True:
        audio_input = listening()  # Capture audio input
        command = recognize_command(audio_input)  # Recognize the command
        print("You said:", command)
        response = execute_command(command)  # Execute the command and get a response
        print("Car Assistant:", response)
        speak(response)  # Speak the response
        break
        