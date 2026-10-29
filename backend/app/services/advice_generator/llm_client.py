import logging
import hashlib
from typing import Dict, Any, Optional, List
from app.config import settings
from app.schemas.rules import AdviceItem, AdviceAction
from app.services.advice_generator.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)

class GeminiAdviceClient:
    """
    Swappable LLM Interface for Gemini API.
    Features:
    - In-memory bucketed response cache to minimize API calls.
    - Full deterministic mock mode for local dev without paid API keys.
    """
    _response_cache: Dict[str, str] = {}

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self._model = None
        if self.api_key and not settings.DRY_RUN:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._model = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Initialized Gemini 1.5 Flash client.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini SDK: {e}. Falling back to mock generator.")

    def _get_cache_key(
        self,
        crop_id: str,
        stage_id: str,
        primary_action: str,
        language: str,
        weather_bucket: str
    ) -> str:
        raw = f"{crop_id}:{stage_id}:{primary_action}:{language}:{weather_bucket}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    async def generate_message(
        self,
        crop_id: str,
        crop_name: str,
        stage_id: str,
        stage_name: str,
        das: int,
        advice_items: List[AdviceItem],
        language: str = "hi"
    ) -> str:
        if not advice_items:
            return ""

        primary_item = advice_items[0]
        # Weather bucket for caching: round rain to 5mm steps, temp to 2C steps
        params = primary_item.params or {}
        rain = int(params.get("rain_mm", params.get("rain_48h_mm", 0.0)) // 5 * 5)
        temp = int(params.get("temp_c", params.get("max_temp_c", 30.0)) // 2 * 2)
        weather_bucket = f"r{rain}_t{temp}"

        cache_key = self._get_cache_key(crop_id, stage_id, primary_item.action.value, language, weather_bucket)
        if cache_key in self._response_cache:
            logger.info("Advice generator cache hit. Reusing cached vernacular message.")
            return self._response_cache[cache_key]

        # Use Live Gemini API if configured and not dry-run
        if self._model and not settings.DRY_RUN:
            try:
                prompt = PromptBuilder.build_prompt(crop_name, stage_name, das, advice_items, language)
                response = self._model.generate_content(prompt)
                generated = response.text.strip()
                self._response_cache[cache_key] = generated
                return generated
            except Exception as e:
                logger.error(f"Gemini API generation error: {e}. Falling back to synthetic mock generator.")

        # Deterministic Mock Vernacular Generator (zero external credentials required)
        mock_text = self._generate_mock_vernacular(crop_name, stage_name, das, primary_item, language)
        self._response_cache[cache_key] = mock_text
        return mock_text

    def _generate_mock_vernacular(
        self,
        crop_name: str,
        stage_name: str,
        das: int,
        item: AdviceItem,
        language: str
    ) -> str:
        action = item.action
        params = item.params or {}

        if language == "mr":
            if action == AdviceAction.IRRIGATE:
                return f"किसान साथी: आपल्या {crop_name} पिकास ({stage_name}) ताबडतोब हलके पाणी द्यावे. पुढील 48 तासांत पाऊस नाही आणि जमिनीत ओलावा कमी आहे."
            elif action == AdviceAction.SKIP_IRRIGATION:
                rain_mm = round(params.get("rain_mm", 0.0), 1)
                return f"किसान साथी: {crop_name} पिकासाठी सिंचन पुढे ढकला. पुढील 48 तासांत {rain_mm} मिमी पावसाचा अंदाज असून शेतात पाणी साचू नये."
            elif action == AdviceAction.AVOID_SPRAY:
                wind = round(params.get("wind_kmh", 15.0), 1)
                return f"किसान साथी: {crop_name} पिकावर आज कोणतीही फवारणी करू नका. वाऱ्याचा वेग {wind} किमी/तास असल्याने औषध वाहून जाईल."
            elif action == AdviceAction.SAFE_SPRAY:
                return f"किसान साथी: {crop_name} पिकावर फवारणीसाठी आज हवामान अनुकूल आहे. दुपारपूर्वी आवश्यक फवारणी पूर्ण करा."
            elif action == AdviceAction.HEAT_ALERT:
                temp = round(params.get("temp_c", 36.0), 1)
                return f"किसान साथी: हवामान इशारा! {crop_name} पिकासाठी तापमान {temp} अंश सेल्सिअसपर्यंत वाढेल. संध्याकाळी हलके पाणी द्या."
            elif action == AdviceAction.RAIN_ALERT:
                rain_mm = round(params.get("rain_mm", 40.0), 1)
                return f"किसान साथी: मुसळधार पाऊस इशारा! {crop_name} शेतातून पाण्याचा निचरा त्वरित करा. पुढील 24 तासांत {rain_mm} मिमी पावसाची शक्यता आहे."
            elif action == AdviceAction.HARVEST_READY:
                return f"किसान साथी: आपले {crop_name} पीक काढणीस तयार आहे. पुढील 7 दिवस हवामान कोरडे असल्याने काढणीचे नियोजन करा."
            elif action == AdviceAction.DROUGHT_ALERT:
                dry_days = int(params.get("dry_days", 14))
                return f"किसान साथी: कोरड्या हवामानाचा इशारा! {dry_days} दिवस पाऊस नाही. {crop_name} पिकासाठी पाण्याची सोय त्वरित करा."
            elif action == AdviceAction.FROST_ALERT:
                min_temp = round(params.get("min_temp_c", 5.0), 1)
                return f"किसान साथी: थंडीचा इशारा! तापमान {min_temp} अंश सेल्सिअसपर्यंत घसरू शकते. {crop_name} पिकाचे संरक्षण करा."
            else:
                return f"किसान साथी: आपल्या {crop_name} पिकाची पाहणी करा. सद्यस्थितीत हवामान सर्वसाधारण राहील."

        elif language == "en":
            if action == AdviceAction.IRRIGATE:
                return f"KisanSaathi: Provide light irrigation to your {crop_name} ({stage_name}) today. No rain forecast in next 48 hours and soil moisture is low."
            elif action == AdviceAction.SKIP_IRRIGATION:
                rain_mm = round(params.get("rain_mm", 0.0), 1)
                return f"KisanSaathi: Postpone irrigation for {crop_name}. {rain_mm}mm rainfall expected in next 48 hours."
            elif action == AdviceAction.AVOID_SPRAY:
                wind = round(params.get("wind_kmh", 15.0), 1)
                return f"KisanSaathi: Avoid spraying on {crop_name} today. Wind speed is high at {wind} km/h causing chemical drift."
            elif action == AdviceAction.SAFE_SPRAY:
                return f"KisanSaathi: Weather is calm and dry for your {crop_name}. Safe window for crop protection spraying today."
            elif action == AdviceAction.HEAT_ALERT:
                temp = round(params.get("temp_c", 36.0), 1)
                return f"KisanSaathi: High heat alert! Temperatures may reach {temp}C. Apply evening irrigation to protect {crop_name}."
            elif action == AdviceAction.RAIN_ALERT:
                rain_mm = round(params.get("rain_mm", 40.0), 1)
                return f"KisanSaathi: Heavy rain alert! {rain_mm}mm rain expected in 24 hours. Ensure drainage in your {crop_name} field."
            elif action == AdviceAction.HARVEST_READY:
                return f"KisanSaathi: Your {crop_name} is ready for harvest. Dry weather expected for the next 7 days. Plan harvesting."
            elif action == AdviceAction.DROUGHT_ALERT:
                dry_days = int(params.get("dry_days", 14))
                return f"KisanSaathi: Dry spell warning! No rain for {dry_days} days. Arrange water for your {crop_name} urgently."
            elif action == AdviceAction.FROST_ALERT:
                min_temp = round(params.get("min_temp_c", 5.0), 1)
                return f"KisanSaathi: Frost warning! Temperature may fall to {min_temp}C. Protect your {crop_name} crop."
            else:
                return f"KisanSaathi: Monitor your {crop_name} field. Current weather is stable."

        else: # Default Hindi
            if action == AdviceAction.IRRIGATE:
                return f"किसान साथी: अपनी {crop_name} फसल ({stage_name}) को तुरंत हल्की सिंचाई दें। अगले 48 घंटों में बारिश नहीं होगी और मिट्टी में नमी कम है।"
            elif action == AdviceAction.SKIP_IRRIGATION:
                rain_mm = round(params.get("rain_mm", 0.0), 1)
                return f"किसान साथी: {crop_name} में सिंचाई टालें। अगले 48 घंटों में {rain_mm} मिमी बारिश का अनुमान है ताकि जलजमाव न हो।"
            elif action == AdviceAction.AVOID_SPRAY:
                wind = round(params.get("wind_kmh", 15.0), 1)
                return f"किसान साथी: {crop_name} पर आज दवा का छिड़काव न करें। हवा की गति {wind} किमी/घंटे तेज होने से दवा उड़ने का खतरा है।"
            elif action == AdviceAction.SAFE_SPRAY:
                return f"किसान साथी: {crop_name} पर दवा छिड़काव के लिए आज का मौसम शांत और अनुकूल है। दोपहर से पहले छिड़काव पूरा करें।"
            elif action == AdviceAction.HEAT_ALERT:
                temp = round(params.get("temp_c", 36.0), 1)
                return f"किसान साथी: भीषण गर्मी की चेतावनी! तापमान {temp} डिग्री सेल्सियस तक पहुंच सकता है। {crop_name} को शाम के समय हल्की सिंचाई दें।"
            elif action == AdviceAction.RAIN_ALERT:
                rain_mm = round(params.get("rain_mm", 40.0), 1)
                return f"किसान साथी: भारी बारिश की चेतावनी! अगले 24 घंटों में {rain_mm} मिमी बारिश का अनुमान है। {crop_name} के खेतों से पानी निकासी सुनिश्चित करें।"
            elif action == AdviceAction.HARVEST_READY:
                return f"किसान साथी: आपकी {crop_name} फसल कटाई के लिए तैयार है। अगले 7 दिनों तक मौसम साफ रहने का अनुमान है। कटाई शुरू करें।"
            elif action == AdviceAction.DROUGHT_ALERT:
                dry_days = int(params.get("dry_days", 14))
                return f"किसान साथी: सूखे की चेतावनी! {dry_days} दिनों से बारिश नहीं हुई है। {crop_name} फसल के लिए पानी का इंतज़ाम तुरंत करें।"
            elif action == AdviceAction.FROST_ALERT:
                min_temp = round(params.get("min_temp_c", 5.0), 1)
                return f"किसान साथी: पाले की चेतावनी! तापमान {min_temp} डिग्री सेल्सियस तक गिर सकता है। {crop_name} फसल को बचाएं।"
            else:
                return f"किसान साथी: अपनी {crop_name} फसल की नियमित निगरानी रखें। वर्तमान मौसम अनुकूल है।"
