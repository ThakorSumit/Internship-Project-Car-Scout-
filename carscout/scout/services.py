import google.generativeai as genai
from django.conf import settings

def get_car_ai_summary(vehicle_obj):
    # 1. Setup Gemini using the key from your settings.py
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # 2. Build the prompt using data from your Vehicle model
    prompt = (
        f"You are a professional car inspector for 'Car Scout'. "
        f"Summarize the condition and market appeal of a {vehicle_obj.year} "
        f"{vehicle_obj.company} {vehicle_obj.model} ({vehicle_obj.FuelType}). "
        f"Keep the summary under 60 words and professional."
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Summary temporarily unavailable. (Error: {str(e)})"