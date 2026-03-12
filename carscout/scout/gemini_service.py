import json
import threading
from groq import Groq
from django.conf import settings


def run_ai_inspection(listing_id):
    thread = threading.Thread(target=_inspect, args=(listing_id,))
    thread.daemon = True
    thread.start()


def _inspect(listing_id):
    from scout.models import Listing, InspectionReport

    try:
        listing = Listing.objects.select_related('vehicle').get(id=listing_id)
        report = listing.inspection
        vehicle = listing.vehicle

        prompt = f"""
You are an expert automotive inspector AI for a luxury car marketplace.
Analyze this vehicle and return a JSON inspection report.

Vehicle Details:
- Make/Model: {vehicle.company} {vehicle.model} ({vehicle.year})
- Condition: {vehicle.condition}
- Mileage: {vehicle.mileage:,} miles
- Fuel Type: {vehicle.fuel_type}
- Transmission: {vehicle.transmission}
- Engine: {vehicle.engine_size}
- Color: {vehicle.color}
- Doors: {vehicle.num_doors} | Seats: {vehicle.seating_capacity}
- Description: {vehicle.description}
- Modifications: {vehicle.modifications or 'None listed'}

Seller-Provided History:
- Accident History: {'Yes' if report.accident_history else 'No'}
- Accident Details: {report.accident_details or 'N/A'}
- Service History: {report.service_history or 'Not provided'}
- Previous Owners: {report.previous_owners}
- Asking Price: ${listing.price:,}

Return ONLY a valid JSON object with these exact keys (no markdown, no backticks):
{{
  "ai_score": <float 0.0-10.0>,
  "overall_condition": "<one of: Excellent / Good / Fair / Poor>",
  "summary": "<2-3 sentence summary>",
  "risk_level": "<one of: Low / Medium / High>",
  "recommendation": "<Buy / Buy with Caution / Avoid>",
  "issues_detected": ["<issue 1>", "<issue 2>"],
  "positives": ["<positive 1>", "<positive 2>"],
  "mileage_assessment": "<1 sentence>",
  "price_assessment": "<1 sentence>",
  "accident_impact": "<1 sentence>",
  "buyer_tips": ["<tip 1>", "<tip 2>", "<tip 3>"]
}}
"""

        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3,
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()

        data = json.loads(raw)

        report.score              = float(data.get('ai_score', 0))
        report.overall_condition  = data.get('overall_condition', '')
        report.ai_summary         = data.get('summary', '')
        report.risk_level         = data.get('risk_level', 'Low').lower()
        report.recommendation     = data.get('recommendation', '')
        report.issues_detected    = data.get('issues_detected', [])
        report.positives          = data.get('positives', [])
        report.mileage_assessment = data.get('mileage_assessment', '')
        report.price_assessment   = data.get('price_assessment', '')
        report.accident_impact    = data.get('accident_impact', '')
        report.buyer_tips         = data.get('buyer_tips', [])
        report.save()

        # ── After AI scan, go to pending_review (not live) ──
        # Admin must approve before buyers can see it
        listing.status = 'pending_review'
        listing.save()

        print(f"[AI Inspection Complete] listing_id={listing_id} score={report.score} → pending_review")

    except Exception as e:
        print(f"[AI Inspection Error] listing_id={listing_id}: {e}")
        import traceback
        traceback.print_exc()
        try:
            from scout.models import Listing
            listing = Listing.objects.get(id=listing_id)
            listing.status = 'pending_review'
            listing.save()
        except Exception:
            pass