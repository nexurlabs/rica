# Rica - Imagen (Image Generation via Vertex AI)
# Ported and adapted from ultimate_haggu

import asyncio
from google import genai
from google.genai import types


class ImageGenerator:
    """Generate images using Imagen 4."""

    def __init__(self):
        self.model = "imagen-4.0-generate-001"
        self.location = "us-central1"

    def _get_client(self, api_key: str = None, project_id: str = None):
        """Create a client — supports both API key and Vertex AI."""
        if project_id:
            return genai.Client(vertexai=True, project=project_id, location=self.location)
        elif api_key:
            return genai.Client(api_key=api_key)
        raise ValueError("Either api_key or project_id required for Imagen")

    async def generate(self, prompt: str, api_key: str = None,
                       project_id: str = None, size: str = "1024x1024") -> bytes:
        """
        Generate an image from text prompt.
        Returns: image bytes (PNG)
        """
        client = self._get_client(api_key, project_id)

        try:
            print(f"[Imagen] Generating: {prompt[:50]}...")

            width, height = map(int, size.split("x"))
            aspect = "1:1" if width == height else "16:9"

            response = await asyncio.to_thread(
                client.models.generate_images,
                model=self.model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=aspect,
                    safety_filter_level="BLOCK_ONLY_HIGH",
                    person_generation="ALLOW_ADULT",
                )
            )

            if response.generated_images:
                print("[Imagen] Generated successfully!")
                return response.generated_images[0].image.image_bytes
            else:
                raise Exception("No images generated")

        except Exception as e:
            print(f"[Imagen] Error: {e}")
            raise e


# Global instance
imagen = ImageGenerator()
