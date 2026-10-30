from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseDeliveryProvider(ABC):
    """
    Abstract interface for telecom communication providers (Twilio, Exotel, Kaleyra).
    """
    @abstractmethod
    async def send_sms(self, to_phone: str, message: str, advisory_id: str) -> Dict[str, Any]:
        """Send standard SMS message to farmer's mobile phone."""
        pass

    @abstractmethod
    async def make_voice_call(self, to_phone: str, audio_url: str, advisory_id: str) -> Dict[str, Any]:
        """Trigger automated outbound voice call playing the TTS audio."""
        pass

    async def send_whatsapp(self, to_phone: str, message: str, advisory_id: str) -> Dict[str, Any]:
        """Send a WhatsApp message. Providers without WhatsApp support report SKIPPED."""
        return {"provider": "NONE", "status": "SKIPPED", "sid": None, "error": "WhatsApp not supported"}
