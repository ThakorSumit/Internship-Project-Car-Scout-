import json
import threading
from groq import Groq
from django.conf import settings
from datetime import date
from scout.models import Listing, InspectionReport


def run_ai_inspection(listing_id):
    thread = threading.Thread(target=_inspect, args=(listing_id,))
    thread.daemon = True
    thread.start()


def _inspect(listing_id):

    try:
        listing = Listing.objects.select_related('vehicle').get(id=listing_id)
        report = listing.inspection
        vehicle = listing.vehicle

        current_year = date.today().year
        vehicle_age = current_year - vehicle.year
        expected_mileage = vehicle_age * 15000  # avg 15,000 km/year in India
        mileage_vs_expected = vehicle.mileage - expected_mileage

        is_new = vehicle.condition.lower() == 'new' or vehicle.mileage == 0
        is_low_mileage = not is_new and vehicle.mileage < (expected_mileage * 0.6)
        is_high_mileage = vehicle.mileage > (expected_mileage * 1.4)

        has_real_accident = (
            report.accident_history in ['minor', 'major'] and
            report.accident_details and
            len(report.accident_details.strip()) > 10 and
            report.accident_details.strip().lower() not in [
                'none', 'no', 'n/a', 'na', 'nil', 'nothing', 'no accident',
                'no accidents', 'not applicable', '-', 'no history', 'clean'
            ]
        )

        has_service_history = (
            report.service_history and
            len(report.service_history.strip()) > 15 and
            report.service_history.strip().lower() not in ['none', 'no', 'n/a', 'na', 'not provided', '-']
        )

        # Rough Indian market price benchmarks by age
        if vehicle_age <= 1:
            market_low, market_high = listing.price * 0.90, listing.price * 1.10
        elif vehicle_age <= 3:
            depreciation = 0.75
            market_low = listing.price * 0.85
            market_high = listing.price * 1.10
        elif vehicle_age <= 6:
            market_low = listing.price * 0.80
            market_high = listing.price * 1.15
        else:
            market_low = listing.price * 0.75
            market_high = listing.price * 1.20

        prompt = f"""
            You are SCOUT-AI, a senior automotive inspection engine for CarScout — a premium used car marketplace in India.
            Your reports are read by real buyers making high-value financial decisions.
            Be precise, honest, and data-driven. Never guess. Never hallucinate issues that aren't supported by the data.

            ════════════════════════════════════════
            VEHICLE PROFILE
            ════════════════════════════════════════
            Make / Model     : {vehicle.company} {vehicle.model} ({vehicle.year})
            Vehicle Age      : {vehicle_age} year{'s' if vehicle_age != 1 else ''} old
            Condition        : {vehicle.condition}
            Mileage          : {vehicle.mileage:,} km
            Expected Mileage : {expected_mileage:,} km (for age — India avg 15,000 km/yr)
            Mileage Status   : {'⚠ HIGHER than expected by ' + f'{abs(mileage_vs_expected):,} km' if is_high_mileage else ('✓ LOWER than expected by ' + f'{abs(mileage_vs_expected):,} km — positive signal' if is_low_mileage else '✓ Within normal range')}
            Fuel Type        : {vehicle.fuel_type}
            Transmission     : {vehicle.transmission}
            Engine           : {vehicle.engine_size}
            Color            : {vehicle.color}
            Doors / Seats    : {vehicle.num_doors} / {vehicle.seating_capacity}
            Modifications    : {vehicle.modifications or 'None declared'}
            Description      : {vehicle.description}

            ════════════════════════════════════════
            OWNERSHIP & HISTORY
            ════════════════════════════════════════
            Previous Owners  : {report.previous_owners} {'(single owner — positive signal)' if report.previous_owners == 1 else '(multiple owners — factor into score)' if report.previous_owners > 2 else ''}
            Service History  : {'✓ PROVIDED — ' + report.service_history if has_service_history else '✗ NOT PROVIDED — treat as unknown, mild negative signal'}
            Accident History : {report.get_accident_history_display()}
            {"Accident Details : " + report.accident_details if has_real_accident else "Accident Details  : None — treat vehicle as accident-free. DO NOT reference accidents anywhere in your output."}

            ════════════════════════════════════════
            PRICING CONTEXT
            ════════════════════════════════════════
            Asking Price     : ₹{listing.price:,}
            Vehicle Age      : {vehicle_age} yr  |  Mileage: {vehicle.mileage:,} km
            Guidance         : For a {vehicle_age}-year-old {vehicle.company} {vehicle.model} in {vehicle.condition} condition,
            a fair market range in India is approximately ₹{market_low:,.0f} – ₹{market_high:,.0f}.
            Assess whether the asking price is justified, high, or a good deal based on condition + mileage.

            ════════════════════════════════════════
            SCORING RULES  (FOLLOW EXACTLY)
            ════════════════════════════════════════
            {"★ NEW / ZERO KM VEHICLE: Score MUST be 9.5–10.0. Condition = Excellent. issues_detected = []. Recommendation = buy_confident. Risk = low." if is_new else f"""
            Score based on the following additive model:

            BASE SCORE by condition:
            New / 0 km       → 9.5–10.0
            Excellent        → 8.5–9.4
            Good             → 7.0–8.4
            Fair             → 5.5–6.9
            Poor             → 0.0–5.4

            DEDUCTIONS (apply only if data supports it):
            High mileage (>{expected_mileage*1.4:,.0f} km for age) → −0.3 to −0.8
            Multiple owners (3+)                                   → −0.2 to −0.5
            No service history                                     → −0.2 to −0.4
            Minor accident (if reported)                           → −0.5 to −1.0
            Major accident (if reported)                           → −1.5 to −3.0
            Modifications present                                  → −0.1 to −0.3

            BONUSES (apply only if data supports it):
            Low mileage (<{expected_mileage*0.6:,.0f} km for age)  → +0.2 to +0.5
            Single owner                                           → +0.1 to +0.3
            Full service history provided                          → +0.2 to +0.4
            Well-maintained description with specific detail       → +0.1 to +0.2

            Final score must be ONE decimal place. Do not round to whole numbers.
            """}

            ════════════════════════════════════════
            ACCIDENT RULES  (FOLLOW EXACTLY)
            ════════════════════════════════════════
            {"★ CLEAN HISTORY: No accident has been reported. You MUST NOT mention accidents, collision, damage, crash, or repair work anywhere — not in summary, issues_detected, buyer_tips, or accident_impact. Set accident_impact to null." if not has_real_accident else "★ ACCIDENT REPORTED: Incorporate the accident details honestly into score deduction, issues_detected, accident_impact, and buyer_tips. Be specific about the type and likely impact."}

            ════════════════════════════════════════
            OUTPUT FORMAT RULES
            ════════════════════════════════════════
            recommendation → MUST be one of: buy_confident | negotiate | inspect_further | avoid
            risk_level     → MUST be one of: low | medium | high
            overall_condition → MUST be one of: Excellent | Good | Fair | Poor

            Tone rules:
            - summary       : factual, professional, 2–3 sentences max, no filler phrases
            - issues_detected: specific and observable (e.g. "High mileage for age" not "possible wear")
            - positives     : genuine strengths from the data (e.g. "Single owner since new")
            - buyer_tips    : actionable advice a buyer can actually use before purchasing
            - price_assessment: compare against the ₹{market_low:,.0f}–₹{market_high:,.0f} guidance range

            Return ONLY a valid JSON object. No markdown. No backticks. No explanation outside the JSON.

            {{
            "ai_score": <float, one decimal>,
            "overall_condition": "<Excellent | Good | Fair | Poor>",
            "summary": "<2–3 factual sentences>",
            "risk_level": "<low | medium | high>",
            "recommendation": "<buy_confident | negotiate | inspect_further | avoid>",
            "issues_detected": {('[]' if is_new else '["<issue 1>", "<issue 2>"]')},
            "positives": ["<positive 1>", "<positive 2>"],
            "mileage_assessment": "<1 sentence comparing mileage to expected for age>",
            "price_assessment": "<1 sentence referencing the ₹{market_low:,.0f}–₹{market_high:,.0f} range>",
            "accident_impact": {"null" if not has_real_accident else '"<1 sentence>"'},
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