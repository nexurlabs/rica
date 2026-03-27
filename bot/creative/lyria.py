# Rica - Lyria (Music Generation via Google GenAI)
# Uses Gemini's audio generation capabilities for music creation.

import asyncio
from google import genai
from google.genai import types


class MusicGenerator:
    """Generate music using Gemini's native audio generation."""

    def __init__(self):
        self.model = "gemini-2.5-flash-preview-tts"
        self.location = "us-central1"

    def _get_client(self, api_key: str = None, project_id: str = None):
        if project_id:
            return genai.Client(vertexai=True, project=project_id, location=self.location)
        elif api_key:
            return genai.Client(api_key=api_key)
        raise ValueError("Either api_key or project_id required for Lyria")

    async def generate(self, prompt: str, api_key: str = None,
                       project_id: str = None, duration: int = 30) -> bytes:
        """
        Generate music from text prompt using Gemini's audio generation.

        The prompt is enriched to specifically request instrumental music rather
        than speech, leveraging the model's audio generation capabilities.

        Args:
            prompt: Description of the music to generate
            api_key: Google AI API key
            project_id: GCP project ID (for Vertex AI)
            duration: Approximate duration in seconds (advisory)

        Returns: audio bytes (WAV)
        """
        client = self._get_client(api_key, project_id)

        # Enrich prompt for music generation (not speech/TTS)
        music_prompt = (
            f"Generate a {duration}-second instrumental music track. "
            f"Style and mood: {prompt}. "
            f"No vocals, no speech, pure instrumental music."
        )

        try:
            print(f"[Lyria] Generating {duration}s track: {prompt[:50]}...")

            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self.model,
                contents=music_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore"
                            )
                        )
                    ),
                ),
            )

            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        print("[Lyria] Generated successfully!")
                        return part.inline_data.data

            raise Exception("No audio generated — model returned no audio content")

        except Exception as e:
            print(f"[Lyria] Error: {e}")
            raise e


# Global instance
lyria = MusicGenerator()
