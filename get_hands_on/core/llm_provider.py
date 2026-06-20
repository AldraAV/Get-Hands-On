import json
import asyncio
from groq import AsyncGroq
from PyQt6.QtCore import QSettings

class GroqProvider:
    """Proveedor LLM usando Groq para Nona."""

    def __init__(self, model="llama3-70b-8192"):
        self.model = model
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        settings = QSettings("Aldra", "MeterMano")
        api_key = settings.value("GROQ_API_KEY", "")
        if api_key:
            self.client = AsyncGroq(api_key=api_key)

    async def get_response(self, messages, tools=None):
        """Envía los mensajes y las herramientas disponibles a Groq."""
        if not self.client:
            self._initialize_client()
        
        if not self.client:
            raise ValueError("API Key de Groq no configurado.")

        try:
            # Preparar payload
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Baja temperatura para Function Calling preciso
            }
            if tools:
                # Formato de tools para OpenAI/Groq compatible
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except Exception as e:
            raise Exception(f"Error de Groq: {str(e)}")
