import json
from typing import List, Dict, Any
from app.config import settings
from app.schemas.rules import AdviceItem

class PromptBuilder:
    """
    Constructs high-precision few-shot prompts grounded in GKMS advisory style.
    Instructs the LLM strictly to act as a vernacular translator and simplifier,
    NEVER as an agronomy decision-maker.
    """
    GKMS_FEW_SHOT_EXAMPLES = {
        "hi": [
            {
                "input": "फसल: गेहूं, अवस्था: ताज जड़ (21 दिन), सलाह: हल्की सिंचाई करें (नमी 25% कम है, 48 घंटे में बारिश नहीं)",
                "output": "किसान साथी: गेहूं में ताज जड़ फूटने की अवस्था है। अगले 2 दिनों में बारिश की संभावना नहीं है और मिट्टी में नमी कम है। आज ही पहली हल्की सिंचाई अवश्य करें।"
            },
            {
                "input": "फसल: सोयाबीन, अवस्था: फूल आना (45 दिन), सलाह: कीटनाशक छिड़काव टालें (हवा 20 किमी/घंटा तेज है)",
                "output": "किसान साथी: सोयाबीन में फूल आ रहे हैं। हवा की गति 20 किमी/घंटा तेज होने से दवा उड़ने का खतरा है। आज कीटनाशक छिड़काव टालें।"
            }
        ],
        "mr": [
            {
                "input": "पीक: गहू, अवस्था: मुकुट मुळे (21 दिवस), सल्ला: हलके पाणी द्या (जमिनीत ओलावा 25% कमी, 48 तासात पाऊस नाही)",
                "output": "किसान साथी: गव्हाची मुकुट मुळांची नाजूक अवस्था आहे. पुढील 2 दिवसांत पावसाची शक्यता नाही आणि ओलावा कमी आहे. आजच पिकास हलके पाणी द्यावे."
            },
            {
                "input": "पीक: सोयाबीन, अवस्था: फुलोरा (45 दिवस), सल्ला: फवारणी पुढे ढकला (वारे 20 किमी/तास वेगाने आहेत)",
                "output": "किसान साथी: सोयाबीन फुलोरा अवस्थेत आहे. वाऱ्याचा वेग 20 किमी/तास जास्त असल्याने औषध वाहून जाईल. आज फवारणी करू नका."
            }
        ],
        "en": [
            {
                "input": "Crop: Wheat, Stage: CRI (21 DAS), Action: IRRIGATE (Soil moisture 25%, 0mm rain forecast)",
                "output": "KisanSaathi: Wheat is at Crown Root stage. No rain forecast in next 48h and soil moisture is low. Apply light irrigation today to protect root growth."
            }
        ]
    }

    @classmethod
    def build_prompt(
        cls,
        crop_name: str,
        stage_name: str,
        das: int,
        advice_items: List[AdviceItem],
        language: str = "hi"
    ) -> str:
        lang = language if language in ("hi", "mr", "en") else "hi"
        lang_names = {"hi": "Hindi (सरल ग्रामीण हिंदी)", "mr": "Marathi (सोपी ग्रामीण मराठी)", "en": "Simple Rural English"}

        # Serialize structured items into concise text
        items_desc = []
        for idx, item in enumerate(advice_items[:3], 1):
            items_desc.append(
                f"{idx}. Action: {item.action.value}, Urgency: {item.urgency.value}, Reason: {item.reason_code}, "
                f"Parameters: {json.dumps(item.params, ensure_ascii=False)}"
            )
        structured_text = "\n".join(items_desc)

        few_shots = cls.GKMS_FEW_SHOT_EXAMPLES.get(lang, cls.GKMS_FEW_SHOT_EXAMPLES["hi"])
        examples_text = ""
        for ex in few_shots:
            examples_text += f"\nExample Input: {ex['input']}\nExample Output: {ex['output']}\n"

        prompt = f"""You are KisanSaathi, an empathetic agricultural communicator for rural Indian farmers.
Convert the following structured agronomy advice into a short, natural SMS message in {lang_names[lang]}.

STRICT RULES:
1. START IMMEDIATELY with the most urgent action in the very first sentence.
2. Include a simple 1-line reason explaining why based on the parameters.
3. Message length MUST BE STRICTLY UNDER 320 CHARACTERS (SMS limit).
4. NEVER invent or mention any chemical names, pesticide brands, fertilizers, or unmentioned actions.
5. NEVER mention any numbers that are not provided in the input parameters.
6. Tone: Direct, warm, authoritative, rural.

FEW-SHOT EXAMPLES:{examples_text}

CURRENT INPUT:
Crop: {crop_name}
Growth Stage: {stage_name} (DAS: {das})
Structured Advice:
{structured_text}

Write only the final SMS text (under 320 characters) with no preamble, quotes, or markdown:"""
        return prompt
