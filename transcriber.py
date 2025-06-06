import re
import time
import inflect
from groq import Groq
from inference import brain
from key_retriever import get_groq_key
from synthesis import synthesize_audio

# Initialize inflect engine for number-to-word conversion
p = inflect.engine()

def transcribe_audio(audio_bytes):
    # Initialize the Groq client
    client = Groq(api_key = get_groq_key())

    # Ensures the pointer is at the beginning of the buffer
    audio_bytes.seek(0)

    # Generate the transcription of the audio
    api_call_latency_start = time.time()
    transcription = client.audio.transcriptions.create(
        file = audio_bytes,
        # Available models - "whisper-large-v3", "whisper-large-v3-turbo", "distil-whisper-large-v3-en"
        model = "distil-whisper-large-v3-en",
        prompt = "Generate transcription in English",
        response_format = "text",
        language = "en",
        temperature = 0.0
    )
    api_call_latency_end = time.time()

    # Gets rid of control tokens if they are ever generated by whispher
    user_input = re.sub(r"<\|.*?\|>", "", str(transcription)).strip()
    print()
    # Print the Transcription
    print(f"Human: {user_input}")
    print(f"Latency - {round((api_call_latency_end - api_call_latency_start) * 1000)} ms")
    print()

    # Replaces phone number to its spelled out equivalent
    def phone_replacer(text: str) -> str:
        def replacer(match):
            return ", ".join(" ".join(p.number_to_words(int(digit)) for digit in group) for group in match.groups())
        
        # Apply the replacement for phone numbers in the format 123-123-1234
        return re.sub(r"(\d{3})-(\d{3})-(\d{4})", replacer, text)
    
    # Generate Reponse
    response = brain(phone_replacer(user_input))
    print(f"AI: {response}")
    print()

    # Generate Speech
    pronounciation = re.sub("callia", "Kallia", response, flags=re.IGNORECASE) # Fixes ambiguity in Callia Pronounciation
    synthesize_audio(pronounciation)
    return
