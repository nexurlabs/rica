# Rica - Veo (Video Generation via Vertex AI)

import asyncio
import time
from google import genai
from google.genai import types


class VideoGenerator:
    """Generate videos using Veo 3."""

    def __init__(self):
        self.model = "veo-3.0-generate-preview"
        self.location = "us-central1"

    def _get_client(self, api_key: str = None, project_id: str = None):
        if project_id:
            return genai.Client(vertexai=True, project=project_id, location=self.location)
        elif api_key:
            return genai.Client(api_key=api_key)
        raise ValueError("Either api_key or project_id required for Veo")

    async def generate(self, prompt: str, api_key: str = None,
                       project_id: str = None, duration: int = 5) -> bytes:
        """
        Generate a video from text prompt.
        Returns: video bytes (MP4)
        """
        client = self._get_client(api_key, project_id)

        try:
            print(f"[Veo] Generating {duration}s video: {prompt[:50]}...")

            # Veo uses async generation (long-running operation)
            operation = await asyncio.to_thread(
                client.models.generate_videos,
                model=self.model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    number_of_videos=1,
                    duration_seconds=duration,
                    person_generation="allow_adult",
                ),
            )

            # Poll until complete
            while not operation.done:
                await asyncio.sleep(10)
                operation = await asyncio.to_thread(
                    client.operations.get, operation=operation
                )
                print(f"[Veo] Still generating...")

            if operation.result and operation.result.generated_videos:
                video = operation.result.generated_videos[0]
                # Download video
                video_data = await asyncio.to_thread(
                    video.video.download
                )
                print("[Veo] Generated successfully!")
                return video_data

            raise Exception("No video generated")

        except Exception as e:
            print(f"[Veo] Error: {e}")
            raise e


# Global instance
veo = VideoGenerator()
