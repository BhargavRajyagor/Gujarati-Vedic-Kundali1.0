# -*- coding: utf-8 -*-
"""Rule-based Vedic astrology prediction engine for Gujarat Vedic Kundali."""

from datetime import datetime
import pandas as pd
import swisseph as swe

swe.set_sid_mode(swe.SIDM_LAHIRI)
PLANET_FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
    "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS,
    "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
}
RASHIS = [
    ("Mesha", "Aries"), ("Vrishabha", "Taurus"), ("Mithuna", "Gemini"),
    ("Karka", "Cancer"), ("Simha", "Leo"), ("Kanya", "Virgo"),
    ("Tula", "Libra"), ("Vrishchika", "Scorpio"), ("Dhanu", "Sagittarius"),
    ("Makara", "Capricorn"), ("Kumbha", "Aquarius"), ("Meena", "Pisces")
]

def get_rashi(longitude):
    longitude = longitude % 360
    index = int(longitude // 30)
    return index, RASHIS[index][0], RASHIS[index][1], longitude % 30

# ============================================================
# CELL 7A — COMPLETE RULE-BASED VEDIC ASTROLOGY PREDICTION ENGINE
# ============================================================
#
# This module uses the already calculated D1/D9 planetary data and
# Vimshottari Dasha from this application. It is deliberately
# deterministic and explainable: every score is accompanied by rules.
#
# IMPORTANT:
# This is a traditional Jyotish interpretation engine, not a scientific
# predictor. It should not be used for medical, legal, financial or other
# high-stakes decisions.
# ============================================================

SIGN_LORDS = {
    "Mesha": "Mars", "Vrishabha": "Venus", "Mithuna": "Mercury",
    "Karka": "Moon", "Simha": "Sun", "Kanya": "Mercury",
    "Tula": "Venus", "Vrishchika": "Mars", "Dhanu": "Jupiter",
    "Makara": "Saturn", "Kumbha": "Saturn", "Meena": "Jupiter"
}

SIGN_INDEX_BY_NAME = {name: i for i, (name, _) in enumerate(RASHIS)}

OWN_SIGNS = {
    "Sun": ["Simha"],
    "Moon": ["Karka"],
    "Mars": ["Mesha", "Vrishchika"],
    "Mercury": ["Mithuna", "Kanya"],
    "Jupiter": ["Dhanu", "Meena"],
    "Venus": ["Vrishabha", "Tula"],
    "Saturn": ["Makara", "Kumbha"],
}

EXALTATION_SIGNS = {
    "Sun": "Mesha", "Moon": "Vrishabha", "Mars": "Makara",
    "Mercury": "Kanya", "Jupiter": "Karka", "Venus": "Meena",
    "Saturn": "Tula"
}

DEBILITATION_SIGNS = {
    "Sun": "Tula", "Moon": "Vrishchika", "Mars": "Karka",
    "Mercury": "Meena", "Jupiter": "Makara", "Venus": "Kanya",
    "Saturn": "Mesha"
}

NATURAL_BENEFICS = {"Jupiter", "Venus", "Mercury", "Moon"}
NATURAL_MALEFICS = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}

HOUSE_THEMES = {
    1: "self, personality, vitality",
    2: "wealth, family, speech and values",
    3: "courage, communication, skills and initiative",
    4: "home, education, mother, property and inner comfort",
    5: "intelligence, creativity, learning and children",
    6: "service, competition, obstacles and routines",
    7: "marriage, partnerships and public dealings",
    8: "transformation, uncertainty, inheritance and research",
    9: "fortune, higher learning, mentors and dharma",
    10: "career, profession, authority and public status",
    11: "income, gains, networks and fulfilment of ambitions",
    12: "expenses, foreign links, retreat and release"
}

HOUSE_GROUPS = {
    "kendra": {1, 4, 7, 10},
    "trikona": {1, 5, 9},
    "dusthana": {6, 8, 12},
    "upachaya": {3, 6, 10, 11},
    "wealth": {2, 5, 9, 11},
    "dharma": {1, 5, 9},
    "moksha": {4, 8, 12}
}

PLANET_TRAITS = {
    "Sun": ["leadership", "authority", "confidence", "administration"],
    "Moon": ["emotional intelligence", "adaptability", "public connection", "intuition"],
    "Mars": ["initiative", "courage", "technical drive", "competition"],
    "Mercury": ["analysis", "communication", "technology", "commerce"],
    "Jupiter": ["wisdom", "teaching", "research", "guidance"],
    "Venus": ["creativity", "relationships", "design", "diplomacy"],
    "Saturn": ["discipline", "persistence", "structure", "long-term work"],
    "Rahu": ["ambition", "innovation", "unconventional thinking", "foreign links"],
    "Ketu": ["research", "detachment", "specialization", "introspection"]
}

CAREER_DOMAINS = {
    "Sun": ["administration", "government/public institutions", "leadership", "management"],
    "Moon": ["public relations", "hospitality", "healthcare support", "travel/service"],
    "Mars": ["engineering", "technology", "defence", "operations", "sports"],
    "Mercury": ["IT/software", "data analysis", "communication", "commerce", "business"],
    "Jupiter": ["teaching", "research", "law", "finance", "consulting"],
    "Venus": ["design", "media", "arts", "fashion", "public-facing creative work"],
    "Saturn": ["engineering", "infrastructure", "manufacturing", "administration", "large organizations"],
    "Rahu": ["technology", "digital media", "foreign organizations", "emerging industries"],
    "Ketu": ["research", "analytics", "specialized technical work", "spiritual/academic study"]
}


def _clamp(value, low=0, high=100):
    return max(low, min(high, float(value)))


def _add_reason(bucket, text, weight=0):
    bucket.append({"text": text, "weight": weight})


def _planet_map(rows):
    return {r["Planet"]: r for r in rows}


def _house_of(planet_map, planet):
    return planet_map.get(planet, {}).get("House")


def _sign_of(planet_map, planet):
    return planet_map.get(planet, {}).get("Rashi")


def _lord_of_sign(sign):
    return SIGN_LORDS.get(sign)


def _house_lords(asc_index):
    result = {}
    for house in range(1, 13):
        sign_index = (asc_index + house - 1) % 12
        sign = RASHIS[sign_index][0]
        result[house] = SIGN_LORDS[sign]
    return result


def _planet_house_from_lord(planet_map, lord):
    return _house_of(planet_map, lord)


def _lord_house_for_house(house_lords, planet_map, house):
    lord = house_lords[house]
    return lord, _planet_house_from_lord(planet_map, lord)


def _house_relation(h1, h2):
    if h1 is None or h2 is None:
        return None
    return ((h2 - h1) % 12) + 1


def _is_connected(planet_map, p1, p2):
    h1 = _house_of(planet_map, p1)
    h2 = _house_of(planet_map, p2)
    if h1 is None or h2 is None:
        return False
    if h1 == h2:
        return True
    # Mutual 7th-house placement / direct conjunction relationship.
    return _house_relation(h1, h2) == 7


def _planet_aspects(planet, source_house):
    """Return houses aspected by a planet using Parashari special aspects."""
    if source_house is None:
        return set()
    aspects = {((source_house + 7 - 1) % 12) + 1}  # 7th aspect
    if planet == "Mars":
        aspects |= {((source_house + 4 - 1) % 12) + 1,
                    ((source_house + 8 - 1) % 12) + 1}
    elif planet == "Jupiter":
        aspects |= {((source_house + 5 - 1) % 12) + 1,
                    ((source_house + 9 - 1) % 12) + 1}
    elif planet == "Saturn":
        aspects |= {((source_house + 3 - 1) % 12) + 1,
                    ((source_house + 10 - 1) % 12) + 1}
    elif planet in {"Rahu", "Ketu"}:
        # Node aspects vary by Jyotish school. This implementation uses
        # 5th/7th/9th for consistency with the app's traditional mode.
        aspects |= {((source_house + 5 - 1) % 12) + 1,
                    ((source_house + 9 - 1) % 12) + 1}
    return aspects


def _planets_in_house(planet_map, house):
    return [p for p, r in planet_map.items() if r.get("House") == house]


def _aspects_house(planet_map, house):
    result = []
    for planet, row in planet_map.items():
        if house in _planet_aspects(planet, row.get("House")):
            result.append(planet)
    return result


def _dignity(planet, sign):
    if planet in EXALTATION_SIGNS and sign == EXALTATION_SIGNS[planet]:
        return "exalted", 25
    if planet in DEBILITATION_SIGNS and sign == DEBILITATION_SIGNS[planet]:
        return "debilitated", -25
    if sign in OWN_SIGNS.get(planet, []):
        return "own sign", 18
    if planet == "Rahu" or planet == "Ketu":
        return "node", 0
    return "neutral", 0


def _planet_strength(planet, row, functional_benefic=None):
    score = 50.0
    reasons = []
    sign = row.get("Rashi")
    house = row.get("House")
    dignity, delta = _dignity(planet, sign)
    score += delta
    if delta:
        reasons.append(f"{planet} is {dignity} in {sign}")
    if house in HOUSE_GROUPS["kendra"]:
        score += 5
    if house in HOUSE_GROUPS["trikona"]:
        score += 7
    if house in HOUSE_GROUPS["dusthana"]:
        score -= 6
    if house in HOUSE_GROUPS["upachaya"]:
        score += 3
    if row.get("Retrograde") and planet in {"Mars", "Mercury", "Jupiter", "Venus", "Saturn"}:
        score += 2
        reasons.append(f"{planet} is retrograde")
    if functional_benefic is True:
        score += 5
    elif functional_benefic is False:
        score -= 4
    return _clamp(score), reasons


def _functional_nature(planet, house_lords):
    owned = [h for h, lord in house_lords.items() if lord == planet]
    # Lagna lord is always treated as supportive in this rule engine.
    if 1 in owned:
        return True
    # Trikona ownership supports beneficence; 6/8/12 ownership can reduce it.
    has_trikona = bool(set(owned) & {5, 9})
    has_dusthana = bool(set(owned) & {6, 8, 12})
    if has_trikona and not has_dusthana:
        return True
    if has_dusthana and not has_trikona:
        return False
    return None


def _combustion_threshold(planet):
    return {
        "Moon": 12, "Mars": 17, "Mercury": 14, "Jupiter": 11,
        "Venus": 10, "Saturn": 15
    }.get(planet, 0)


def _angular_distance(a, b):
    d = abs((a - b) % 360.0)
    return min(d, 360.0 - d)


def _combust_status(planet_map, planet):
    if planet not in planet_map or "Sun" not in planet_map:
        return False
    threshold = _combustion_threshold(planet)
    if not threshold:
        return False
    return _angular_distance(
        float(planet_map[planet]["Longitude"]),
        float(planet_map["Sun"]["Longitude"])
    ) <= threshold


def _house_score(planet_map, house, house_lords, category):
    score = 50.0
    reasons = []
    occupants = _planets_in_house(planet_map, house)
    lord = house_lords[house]
    lord_house = _house_of(planet_map, lord)

    if lord_house in {1, 4, 5, 7, 9, 10, 11}:
        score += 10
        reasons.append(f"Lord of house {house} occupies a supportive house ({lord_house})")
    elif lord_house in {6, 8, 12}:
        score -= 8
        reasons.append(f"Lord of house {house} occupies a dusthana ({lord_house})")

    for p in occupants:
        if p in NATURAL_BENEFICS:
            score += 6
            reasons.append(f"{p} occupies house {house}")
        elif p in NATURAL_MALEFICS:
            score -= 4
            reasons.append(f"{p} influences house {house}")

    for p in _aspects_house(planet_map, house):
        if p in NATURAL_BENEFICS:
            score += 5
            reasons.append(f"{p} aspects house {house}")
        elif p in NATURAL_MALEFICS:
            score -= 3
            reasons.append(f"{p} aspects house {house}")

    # Specific category connections.
    if category == "career" and house == 10:
        if any(p in occupants for p in ["Sun", "Saturn", "Mercury", "Jupiter"]):
            score += 8
    if category == "wealth" and house == 11:
        if any(p in occupants for p in ["Jupiter", "Venus", "Mercury"]):
            score += 8
    return _clamp(score), reasons


def _best_planet_for_area(planet_map, area_houses):
    candidates = []
    for planet, row in planet_map.items():
        if row.get("House") in area_houses:
            candidates.append((planet, row.get("House")))
    return candidates


def _trait_analysis(planet_map, asc, house_lords):
    score = 50.0
    reasons = []
    traits = []
    lagna_house = 1

    lagna_lord = house_lords[1]
    lagna_lord_house = _house_of(planet_map, lagna_lord)
    if lagna_lord_house in {1, 4, 5, 9, 10, 11}:
        score += 15
        reasons.append(f"Lagna lord {lagna_lord} is in supportive house {lagna_lord_house}")
    elif lagna_lord_house in {6, 8, 12}:
        score -= 7
        reasons.append(f"Lagna lord {lagna_lord} is in house {lagna_lord_house}")

    for p in _planets_in_house(planet_map, 1):
        traits.extend(PLANET_TRAITS.get(p, []))
        if p in NATURAL_BENEFICS:
            score += 8
        else:
            score += 3
        reasons.append(f"{p} occupies the Ascendant")

    for p in _aspects_house(planet_map, 1):
        traits.extend(PLANET_TRAITS.get(p, []))
        if p in NATURAL_BENEFICS:
            score += 4
        else:
            score += 2
        reasons.append(f"{p} aspects the Ascendant")

    moon_house = _house_of(planet_map, "Moon")
    if moon_house in {1, 4, 5, 9, 10, 11}:
        score += 5
        reasons.append(f"Moon occupies supportive house {moon_house}")
    if moon_house in {6, 8, 12}:
        score -= 3

    sun_house = _house_of(planet_map, "Sun")
    if sun_house in {1, 5, 9, 10}:
        traits.append("leadership orientation")
        score += 4

    # Remove duplicate traits while preserving order.
    traits = list(dict.fromkeys(traits))[:10]
    return {
        "score": _clamp(score),
        "traits": traits,
        "reasons": reasons[:10]
    }


def _intelligence_analysis(planet_map, house_lords):
    score = 50.0
    reasons = []
    for house in [5, 9]:
        hs, rs = _house_score(planet_map, house, house_lords, "education")
        score += (hs - 50) * 0.45
        reasons.extend(rs[:3])
    for p in ["Mercury", "Jupiter", "Moon"]:
        h = _house_of(planet_map, p)
        if h in {1, 4, 5, 9, 10, 11}:
            score += 5
            reasons.append(f"{p} supports learning through house {h}")
    return _clamp(score), reasons[:10]


def _education_analysis(planet_map, house_lords):
    score = 50.0
    reasons = []
    for house in [4, 5, 9]:
        hs, rs = _house_score(planet_map, house, house_lords, "education")
        score += (hs - 50) * 0.55
        reasons.extend(rs[:3])
    for p in ["Mercury", "Jupiter"]:
        if _house_of(planet_map, p) in {4, 5, 9, 10, 11}:
            score += 7
            reasons.append(f"{p} is connected with education")
    return _clamp(score), reasons[:10]


def _career_analysis(planet_map, house_lords, d9_rows=None):
    score = 50.0
    reasons = []
    domain_scores = {d: 0.0 for p in CAREER_DOMAINS for d in CAREER_DOMAINS[p]}

    for house in [6, 10, 11]:
        hs, rs = _house_score(planet_map, house, house_lords, "career")
        score += (hs - 50) * 0.75
        reasons.extend(rs[:4])

    for p, row in planet_map.items():
        h = row.get("House")
        if h in {2, 6, 10, 11}:
            for domain in CAREER_DOMAINS.get(p, []):
                domain_scores[domain] += 2.0

    # 10th lord identity is especially important.
    tenth_lord = house_lords[10]
    if tenth_lord in CAREER_DOMAINS:
        for domain in CAREER_DOMAINS[tenth_lord]:
            domain_scores[domain] += 8.0
        reasons.append(f"10th lord is {tenth_lord}, highlighting its career themes")

    # Strong planets in 10th are major career signatures.
    for p in _planets_in_house(planet_map, 10):
        for domain in CAREER_DOMAINS.get(p, []):
            domain_scores[domain] += 6.0
        reasons.append(f"{p} occupies the 10th house")

    # D9 support is used as a secondary modifier, not as a replacement for D1.
    if d9_rows:
        d9_map = _planet_map(d9_rows)
        strong_d9 = [p for p in ["Sun", "Mercury", "Jupiter", "Saturn"]
                     if p in d9_map and d9_map[p].get("Navamsa_Index") is not None]
        if strong_d9:
            score += min(5, len(strong_d9))
            reasons.append("D9 provides secondary support for planetary maturity")

    top_domains = [x[0] for x in sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)[:6]]
    return _clamp(score), reasons[:12], top_domains


def _wealth_analysis(planet_map, house_lords):
    score = 50.0
    reasons = []
    for house in [2, 5, 9, 11]:
        hs, rs = _house_score(planet_map, house, house_lords, "wealth")
        score += (hs - 50) * 0.60
        reasons.extend(rs[:3])
    for h1, h2 in [(2, 11), (5, 11), (9, 11), (2, 9)]:
        l1 = house_lords[h1]
        l2 = house_lords[h2]
        if _is_connected(planet_map, l1, l2):
            score += 10
            reasons.append(f"Connection between lords of houses {h1} and {h2}")
    return _clamp(score), reasons[:12]


def _marriage_analysis(planet_map, house_lords, d9_rows=None):
    score = 50.0
    reasons = []
    for house in [2, 7, 8, 11]:
        hs, rs = _house_score(planet_map, house, house_lords, "marriage")
        score += (hs - 50) * 0.55
        reasons.extend(rs[:2])

    venus_h = _house_of(planet_map, "Venus")
    jup_h = _house_of(planet_map, "Jupiter")
    if venus_h in {1, 5, 7, 9, 11}:
        score += 8
        reasons.append("Venus is in a traditionally supportive relationship house")
    if jup_h in {1, 5, 7, 9, 11}:
        score += 6
        reasons.append("Jupiter supports partnership through a favorable house")
    if 7 in [_house_of(planet_map, p) for p in planet_map]:
        for p in _planets_in_house(planet_map, 7):
            if p == "Saturn":
                score -= 5
                reasons.append("Saturn in the 7th can emphasize responsibility or delay")
            elif p == "Jupiter":
                score += 8
                reasons.append("Jupiter in the 7th supports partnership themes")
            elif p == "Venus":
                score += 8
                reasons.append("Venus in the 7th strongly emphasizes relationship themes")

    # D9 7th-house condition as a secondary check.
    if d9_rows:
        d9_map = _planet_map(d9_rows)
        d9_7 = _planets_in_house(d9_map, 7)
        if "Venus" in d9_7 or "Jupiter" in d9_7:
            score += 5
            reasons.append("D9 contains a supportive relationship significator in the 7th")
        if "Saturn" in d9_7:
            score -= 3
            reasons.append("D9 Saturn emphasizes maturity/responsibility in partnership")

    return _clamp(score), reasons[:12]


def _foreign_analysis(planet_map, house_lords):
    score = 40.0
    reasons = []
    for h in [3, 9, 12]:
        hs, rs = _house_score(planet_map, h, house_lords, "foreign")
        score += (hs - 50) * 0.45
        reasons.extend(rs[:2])
    if _is_connected(planet_map, house_lords[9], house_lords[12]):
        score += 15
        reasons.append("9th and 12th lords are connected")
    if _is_connected(planet_map, house_lords[4], house_lords[12]):
        score += 10
        reasons.append("4th and 12th lords are connected, suggesting relocation/foreign themes")
    for p in ["Rahu", "Saturn"]:
        if _house_of(planet_map, p) in {9, 12}:
            score += 8
            reasons.append(f"{p} occupies a foreign/travel-related house")
    return _clamp(score), reasons[:12]


def _health_routine_analysis(planet_map, house_lords):
    # This is intentionally framed as vitality/routine themes, not diagnosis.
    score = 55.0
    reasons = []
    h1, r1 = _house_score(planet_map, 1, house_lords, "health")
    h6, r6 = _house_score(planet_map, 6, house_lords, "health")
    score += (h1 - 50) * 0.35
    score += (h6 - 50) * 0.25
    reasons.extend(r1[:4])
    reasons.extend(r6[:4])
    return _clamp(score), reasons[:10]


def _yoga_detection(planet_map, house_lords):
    yogas = []

    # Raja Yoga: a Kendra lord connected with a Trikona lord.
    kendra_lords = [house_lords[h] for h in [1, 4, 7, 10]]
    trikona_lords = [house_lords[h] for h in [1, 5, 9]]
    raja_pairs = []
    for kp in set(kendra_lords):
        for tp in set(trikona_lords):
            if kp != tp and _is_connected(planet_map, kp, tp):
                raja_pairs.append((kp, tp))
    if raja_pairs:
        yogas.append({
            "name": "Raja Yoga connection",
            "strength": "Moderate",
            "reason": "Kendra and Trikona lords have a conjunction or 7th-house relationship."
        })

    # Dharma-Karmadhipati Yoga: 9th and 10th lords connected.
    if _is_connected(planet_map, house_lords[9], house_lords[10]):
        yogas.append({
            "name": "Dharma-Karmadhipati Yoga",
            "strength": "Strong",
            "reason": "The 9th and 10th lords are connected."
        })

    # Dhana Yoga connections.
    wealth_pairs = [(2, 11), (5, 11), (9, 11), (2, 5), (2, 9)]
    wealth_hits = [(a, b) for a, b in wealth_pairs
                   if _is_connected(planet_map, house_lords[a], house_lords[b])]
    if wealth_hits:
        yogas.append({
            "name": "Dhana Yoga connection",
            "strength": "Moderate",
            "reason": "Wealth-related house lords have supportive connections."
        })

    # Gaja Kesari: Jupiter in a Kendra from Moon.
    moon_h = _house_of(planet_map, "Moon")
    jup_h = _house_of(planet_map, "Jupiter")
    if moon_h and jup_h and _house_relation(moon_h, jup_h) in {1, 4, 7, 10}:
        yogas.append({
            "name": "Gaja Kesari Yoga",
            "strength": "Context-dependent",
            "reason": "Jupiter is in a Kendra from the Moon. Final strength depends on dignity and affliction."
        })

    # Budha-Aditya: Sun and Mercury in same sign/house.
    if _house_of(planet_map, "Sun") == _house_of(planet_map, "Mercury"):
        yogas.append({
            "name": "Budha-Aditya Yoga",
            "strength": "Context-dependent",
            "reason": "Sun and Mercury occupy the same house/sign. Combustion and dignity should also be considered."
        })

    # Vipareeta Raja Yoga: lords of 6/8/12 placed in another dusthana.
    vip_hits = []
    for source in [6, 8, 12]:
        lord = house_lords[source]
        lord_h = _house_of(planet_map, lord)
        if lord_h in {6, 8, 12}:
            vip_hits.append((source, lord, lord_h))
    if vip_hits:
        yogas.append({
            "name": "Vipareeta Raja Yoga indication",
            "strength": "Context-dependent",
            "reason": "A dusthana lord is placed in another dusthana."
        })

    # Neecha placements.
    deb = [p for p, r in planet_map.items()
           if p in DEBILITATION_SIGNS and r.get("Rashi") == DEBILITATION_SIGNS[p]]
    if deb:
        yogas.append({
            "name": "Neecha placement",
            "strength": "Requires cancellation analysis",
            "reason": ", ".join(deb) + " is in debilitation. A full Neecha Bhanga analysis is required before judging the result."
        })

    return yogas


def _manglik_analysis(planet_map):
    mars_house = _house_of(planet_map, "Mars")
    if mars_house in {1, 4, 7, 8, 12}:
        return True, mars_house, "Manglik indication is present from the Lagna under the commonly used rule."
    return False, mars_house, "No Manglik indication from the Lagna under the commonly used rule."


def _sade_sati_status(natal_moon_sign_index, transit_saturn_sign_index):
    previous_sign = (natal_moon_sign_index - 1) % 12
    current_sign = natal_moon_sign_index
    next_sign = (natal_moon_sign_index + 1) % 12
    if transit_saturn_sign_index == previous_sign:
        return "Phase 1"
    if transit_saturn_sign_index == current_sign:
        return "Phase 2"
    if transit_saturn_sign_index == next_sign:
        return "Phase 3"
    return None


def _coerce_datetime(value, reference_tz=None):
    """Convert common date/datetime values to a comparable datetime.

    The app may pass an aware datetime (for example Asia/Kolkata), while
    Dasha tables may contain date-only strings.  We normalize both sides
    to the same awareness state before comparison.
    """
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        value = value.to_pydatetime()

    if isinstance(value, datetime):
        dt = value
    else:
        raw = str(value).strip()
        dt = None

        # Try the formats commonly produced by pandas / the app.
        for fmt in (
            "%d-%m-%Y",
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%d-%m-%Y %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except ValueError:
                pass

        if dt is None:
            try:
                dt = pd.to_datetime(raw).to_pydatetime()
            except Exception:
                return None

    # If a reference timezone is supplied, localize naive values to it.
    if reference_tz is not None:
        if getattr(dt, "tzinfo", None) is None:
            try:
                dt = dt.replace(tzinfo=reference_tz)
            except Exception:
                pass
        return dt

    return dt


def _dasha_rows_to_datetimes(dasha_df, reference_when=None):
    rows = []
    if dasha_df is None:
        return rows

    # Defensive handling for malformed / empty objects.
    try:
        if len(dasha_df) == 0:
            return rows
    except Exception:
        return rows

    ref_tz = getattr(reference_when, "tzinfo", None)

    for _, r in dasha_df.iterrows():
        try:
            start = _coerce_datetime(r["Start"], ref_tz)
            end = _coerce_datetime(r["End"], ref_tz)

            if start is None or end is None:
                continue

            # Make the end inclusive through the end of the day for
            # date-only Dasha tables.
            if str(r["End"]).strip() and (
                len(str(r["End"]).strip()) <= 10
            ):
                end = end.replace(hour=23, minute=59, second=59)

            rows.append({
                "Mahadasha": str(r["Mahadasha"]),
                "Antardasha": str(r["Antardasha"]),
                "Start": start,
                "End": end
            })
        except Exception:
            continue

    return rows


def _active_dasha(dasha_df, when=None):
    """Return one plain dict; never return a pandas Series.

    This prevents both:
      * offset-naive vs offset-aware datetime errors
      * 'truth value of a Series is ambiguous' errors
    """
    when = _coerce_datetime(when)

    if when is None:
        when = datetime.now()

    rows = _dasha_rows_to_datetimes(dasha_df, reference_when=when)

    if not rows:
        return None

    # Normalize every row to exactly the same timezone-awareness state.
    aware = getattr(when, "tzinfo", None) is not None

    normalized = []
    for r in rows:
        start = r["Start"]
        end = r["End"]

        if aware:
            tz = when.tzinfo
            if start.tzinfo is None:
                start = start.replace(tzinfo=tz)
            else:
                start = start.astimezone(tz)

            if end.tzinfo is None:
                end = end.replace(tzinfo=tz)
            else:
                end = end.astimezone(tz)
        else:
            if start.tzinfo is not None:
                start = start.replace(tzinfo=None)
            if end.tzinfo is not None:
                end = end.replace(tzinfo=None)

        normalized.append({
            "Mahadasha": r["Mahadasha"],
            "Antardasha": r["Antardasha"],
            "Start": start,
            "End": end
        })

    for r in normalized:
        try:
            if r["Start"] <= when <= r["End"]:
                return r
        except TypeError:
            # Final defensive fallback: compare naive wall-clock values.
            start = r["Start"].replace(tzinfo=None)
            end = r["End"].replace(tzinfo=None)
            w = when.replace(tzinfo=None)
            if start <= w <= end:
                return r

    # If current date is beyond generated table, use the last period.
    return normalized[-1] if normalized else None


def _dasha_area_modifier(md, ad, planet_map, house_lords):
    if not md or not ad:
        return 0, []
    score = 0
    reasons = []
    for label, p in [("Mahadasha", md), ("Antardasha", ad)]:
        h = _house_of(planet_map, p)
        if h in {1, 5, 9, 10, 11}:
            score += 8 if label == "Mahadasha" else 5
            reasons.append(f"{label} lord {p} activates supportive house {h}")
        elif h in {6, 8, 12}:
            score -= 4 if label == "Mahadasha" else 2
            reasons.append(f"{label} lord {p} activates house {h}")
        for target in [1, 5, 7, 9, 10, 11]:
            if h == target:
                break
    return score, reasons


def _transit_planet_row(jd_ut, planet_name):
    planet_id = PLANETS.get(planet_name)
    if planet_id is None:
        return None
    values, _ = swe.calc_ut(jd_ut, planet_id, PLANET_FLAGS)
    lon = values[0] % 360
    rashi_index, rashi, english, degree = get_rashi(lon)
    return {
        "Planet": planet_name,
        "Longitude": lon,
        "Rashi_Index": rashi_index,
        "Rashi": rashi,
        "Sign": english,
        "Degree_in_Rashi": degree
    }


def _jd_for_date(dt):
    return swe.julday(dt.year, dt.month, dt.day,
                       dt.hour + dt.minute / 60.0,
                       swe.GREG_CAL)


def _annual_transit_profile(natal_asc_index, natal_moon_index, year):
    # Use 1 July as a stable annual reference point. This is a trend indicator,
    # not an event-level transit calculator.
    dt = datetime(year, 7, 1, 12, 0)
    jd = _jd_for_date(dt)
    j = _transit_planet_row(jd, "Jupiter")
    s = _transit_planet_row(jd, "Saturn")
    result = {"year": year}
    for label, row in [("Jupiter", j), ("Saturn", s)]:
        if row:
            sign_index = row["Rashi_Index"]
            result[label] = {
                "sign_index": sign_index,
                "house_from_lagna": ((sign_index - natal_asc_index) % 12) + 1,
                "house_from_moon": ((sign_index - natal_moon_index) % 12) + 1
            }
    result["sade_sati"] = _sade_sati_status(natal_moon_index, s["Rashi_Index"]) if s else None
    return result


def _annual_prediction(year, base_scores, transit_profile, dasha_df, planet_map, house_lords):
    scores = dict(base_scores)
    reasons = []

    jt = transit_profile.get("Jupiter", {})
    st = transit_profile.get("Saturn", {})
    jh = jt.get("house_from_lagna")
    sh = st.get("house_from_lagna")

    if jh in {1, 2, 5, 7, 9, 10, 11}:
        scores["career"] += 5
        scores["education"] += 4
        scores["wealth"] += 4
        reasons.append(f"Jupiter transit is supportive from the Lagna (house {jh})")
    elif jh in {6, 8, 12}:
        scores["career"] -= 3
        reasons.append(f"Jupiter transit is more reflective from the Lagna (house {jh})")

    if sh in {3, 6, 10, 11}:
        scores["career"] += 5
        scores["discipline"] += 4
        reasons.append(f"Saturn transit emphasizes effort/results through house {sh}")
    elif sh in {8, 12}:
        scores["career"] -= 3
        scores["discipline"] -= 2
        reasons.append(f"Saturn transit emphasizes restructuring through house {sh}")

    if transit_profile.get("sade_sati"):
        scores["discipline"] -= 4
        reasons.append(f"Saturn is in Sade Sati {transit_profile['sade_sati']} relative to natal Moon")

    active = _active_dasha(dasha_df, datetime(year, 7, 1))
    if active is not None:
        mod, rs = _dasha_area_modifier(active["Mahadasha"], active["Antardasha"], planet_map, house_lords)
        scores["career"] += mod * 0.45
        scores["wealth"] += mod * 0.35
        scores["education"] += mod * 0.25
        scores["relationships"] += mod * 0.25
        reasons.extend(rs)

    for k in scores:
        scores[k] = round(_clamp(scores[k]), 1)

    return scores, reasons[:6], active


def _status(score):
    if score >= 80:
        return "Highly supportive"
    if score >= 65:
        return "Favorable"
    if score >= 50:
        return "Mixed / manageable"
    if score >= 35:
        return "Needs caution"
    return "Challenging"


# ============================================================
# GUJARATI PRESENTATION / INTERPRETATION LAYER
# ============================================================

PLANET_GUJARATI = {
    "Sun": "સૂર્ય",
    "Moon": "ચંદ્ર",
    "Mars": "મંગળ",
    "Mercury": "બુધ",
    "Jupiter": "ગુરુ",
    "Venus": "શુક્ર",
    "Saturn": "શનિ",
    "Rahu": "રાહુ",
    "Ketu": "કેતુ",
}

RASHI_GUJARATI = {
    "Mesha": "મેષ",
    "Vrishabha": "વૃષભ",
    "Mithuna": "મિથુન",
    "Karka": "કર્ક",
    "Simha": "સિંહ",
    "Kanya": "કન્યા",
    "Tula": "તુલા",
    "Vrishchika": "વૃશ્ચિક",
    "Dhanu": "ધનુ",
    "Makara": "મકર",
    "Kumbha": "કુંભ",
    "Meena": "મીન",
}

NAKSHATRA_GUJARATI = {
    "Ashwini": "અશ્વિની",
    "Bharani": "ભરણી",
    "Krittika": "કૃત્તિકા",
    "Rohini": "રોહિણી",
    "Mrigashira": "મૃગશીર્ષ",
    "Ardra": "આર્દ્રા",
    "Punarvasu": "પુનર્વસુ",
    "Pushya": "પુષ્ય",
    "Ashlesha": "આશ્લેષા",
    "Magha": "મઘા",
    "Purva Phalguni": "પૂર્વ ફાલ્ગુની",
    "Uttara Phalguni": "ઉત્તર ફાલ્ગુની",
    "Hasta": "હસ્ત",
    "Chitra": "ચિત્રા",
    "Swati": "સ્વાતિ",
    "Vishakha": "વિશાખા",
    "Anuradha": "અનુરાધા",
    "Jyeshtha": "જ્યેષ્ઠા",
    "Mula": "મૂળ",
    "Purva Ashadha": "પૂર્વાષાઢા",
    "Uttara Ashadha": "ઉત્તરાષાઢા",
    "Shravana": "શ્રવણ",
    "Dhanishta": "ધનિષ્ઠા",
    "Shatabhisha": "શતભિષા",
    "Purva Bhadrapada": "પૂર્વાભાદ્રપદ",
    "Uttara Bhadrapada": "ઉત્તરાભાદ્રપદ",
    "Revati": "રેવતી",
}

STATUS_GUJARATI = {
    "Highly supportive": "અતિશય સહાયક",
    "Favorable": "અનુકૂળ",
    "Mixed / manageable": "મિશ્ર / સંભાળી શકાય તેવું",
    "Needs caution": "સાવચેતી જરૂરી",
    "Challenging": "પડકારજનક",
}

TRAIT_GUJARATI = {
    "leadership": "નેતૃત્વ ક્ષમતા",
    "authority": "અધિકારભાવ",
    "confidence": "આત્મવિશ્વાસ",
    "administration": "વહીવટી ક્ષમતા",
    "emotional intelligence": "ભાવનાત્મક સમજ",
    "adaptability": "પરિસ્થિતિ અનુસાર અનુકૂલન",
    "public connection": "લોકો સાથે જોડાવાની ક્ષમતા",
    "intuition": "અંતઃપ્રેરણા",
    "initiative": "પહેલ કરવાની ક્ષમતા",
    "courage": "હિંમત",
    "technical drive": "તકનીકી ક્ષેત્ર તરફ ઝોક",
    "competition": "સ્પર્ધાત્મક વલણ",
    "analysis": "વિશ્લેષણાત્મક વિચારસરણી",
    "communication": "સારી સંવાદ ક્ષમતા",
    "technology": "ટેક્નોલોજી પ્રત્યે રસ",
    "commerce": "વાણિજ્યિક સમજ",
    "wisdom": "જ્ઞાન અને વિવેક",
    "teaching": "અધ્યાપન ક્ષમતા",
    "research": "સંશોધન વલણ",
    "guidance": "માર્ગદર્શન આપવાની ક્ષમતા",
    "creativity": "સર્જનાત્મકતા",
    "relationships": "સંબંધ નિર્માણ ક્ષમતા",
    "design": "ડિઝાઇન પ્રત્યે રસ",
    "diplomacy": "કૂટનીતિક અભિગમ",
    "discipline": "શિસ્તબદ્ધ સ્વભાવ",
    "persistence": "સતત પ્રયત્ન કરવાની ક્ષમતા",
    "structure": "વ્યવસ્થિત અભિગમ",
    "long-term work": "દીર્ઘકાલીન કાર્યક્ષમતા",
    "ambition": "મહત્વાકાંક્ષા",
    "innovation": "નવતર વિચારસરણી",
    "unconventional thinking": "પરંપરાથી અલગ વિચારવાની ક્ષમતા",
    "foreign links": "વિદેશી જોડાણ તરફ ઝોક",
    "detachment": "અલિપ્તતા",
    "specialization": "વિશિષ્ટ ક્ષેત્રમાં નિપુણતા",
    "introspection": "આત્મચિંતન",
    "leadership orientation": "નેતૃત્વ તરફ ઝોક",
}

DOMAIN_GUJARATI = {
    "administration": "વહીવટ",
    "government/public institutions": "સરકારી / જાહેર સંસ્થાઓ",
    "leadership": "નેતૃત્વ",
    "management": "મેનેજમેન્ટ",
    "public relations": "જનસંપર્ક",
    "hospitality": "હોસ્પિટાલિટી",
    "healthcare support": "હેલ્થકેર સહાય",
    "travel/service": "પ્રવાસ / સેવા ક્ષેત્ર",
    "engineering": "એન્જિનિયરિંગ",
    "technology": "ટેક્નોલોજી",
    "defence": "રક્ષણ ક્ષેત્ર",
    "operations": "ઓપરેશન્સ",
    "sports": "રમતગમત",
    "IT/software": "IT / સોફ્ટવેર",
    "data analysis": "ડેટા વિશ્લેષણ",
    "communication": "સંચાર અને સંવાદ",
    "commerce": "વાણિજ્ય",
    "business": "વ્યવસાય",
    "teaching": "અધ્યાપન",
    "research": "સંશોધન",
    "law": "કાયદા ક્ષેત્ર",
    "finance": "નાણાંકીય ક્ષેત્ર",
    "consulting": "કન્સલ્ટિંગ",
    "design": "ડિઝાઇન",
    "media": "મીડિયા",
    "arts": "કલા",
    "fashion": "ફેશન",
    "public-facing creative work": "લોકસંપર્ક આધારિત સર્જનાત્મક કાર્ય",
    "infrastructure": "માળખાકીય વિકાસ",
    "manufacturing": "ઉત્પાદન ક્ષેત્ર",
    "large organizations": "મોટી સંસ્થાઓ",
    "digital media": "ડિજિટલ મીડિયા",
    "foreign organizations": "વિદેશી સંસ્થાઓ",
    "emerging industries": "ઉભરતા ઉદ્યોગો",
    "analytics": "એનાલિટિક્સ",
    "specialized technical work": "વિશિષ્ટ તકનીકી કાર્ય",
    "spiritual/academic study": "આધ્યાત્મિક / શૈક્ષણિક અભ્યાસ",
}

HOUSE_ORDINAL = {
    1: "પ્રથમ", 2: "દ્વિતીય", 3: "તૃતીય", 4: "ચતુર્થ",
    5: "પંચમ", 6: "ષષ્ઠ", 7: "સપ્તમ", 8: "અષ્ટમ",
    9: "નવમ", 10: "દશમ", 11: "એકાદશ", 12: "દ્વાદશ",
}

HOUSE_THEME_GUJARATI = {
    1: "વ્યક્તિત્વ, શરીર અને જીવનશક્તિ",
    2: "ધન, કુટુંબ, વાણી અને મૂલ્યો",
    3: "સાહસ, સંવાદ, કૌશલ્ય અને પ્રયત્ન",
    4: "ઘર, શિક્ષણ, માતા, મિલકત અને આંતરિક સુખ",
    5: "બુદ્ધિ, સર્જનાત્મકતા, અભ્યાસ અને સંતાન",
    6: "સેવા, સ્પર્ધા, અવરોધો અને દૈનિક રૂટિન",
    7: "લગ્ન, ભાગીદારી અને જાહેર વ્યવહાર",
    8: "પરિવર્તન, અનિશ્ચિતતા, વારસો અને સંશોધન",
    9: "ભાગ્ય, ઉચ્ચ શિક્ષણ, માર્ગદર્શન અને ધર્મ",
    10: "કારકિર્દી, વ્યવસાય, સત્તા અને જાહેર પ્રતિષ્ઠા",
    11: "આવક, લાભ, નેટવર્ક અને મહત્વાકાંક્ષાની પૂર્ણતા",
    12: "ખર્ચ, વિદેશી જોડાણ, એકાંત અને મુક્તિ",
}


def _guj_planet(value):
    return PLANET_GUJARATI.get(str(value), str(value))


def _guj_rashi(value):
    return RASHI_GUJARATI.get(str(value), str(value))


def _guj_nakshatra(value):
    return NAKSHATRA_GUJARATI.get(str(value), str(value))


def _guj_status(value):
    return STATUS_GUJARATI.get(str(value), str(value))


def _guj_trait(value):
    value = str(value)
    if value in TRAIT_GUJARATI:
        return TRAIT_GUJARATI[value]
    return value


def _guj_domain(value):
    value = str(value)
    if value in DOMAIN_GUJARATI:
        return DOMAIN_GUJARATI[value]
    return value


def _guj_house(house):
    try:
        h = int(house)
        return HOUSE_ORDINAL.get(h, str(h)) + " ભાવ"
    except Exception:
        return str(house)


def _guj_reason(reason):
    """Translate deterministic engine rule explanations to Gujarati."""
    text = str(reason)

    # Longer phrases first.
    replacements = {
        "Lagna lord": "લગ્નેશ",
        "Lord of house": "ભાવેશ",
        "10th lord": "દશમ ભાવેશ",
        "9th lord": "નવમ ભાવેશ",
        "12th lord": "દ્વાદશ ભાવેશ",
        "4th and 12th lords": "ચતુર્થ અને દ્વાદશ ભાવેશો",
        "9th and 12th lords": "નવમ અને દ્વાદશ ભાવેશો",
        "Kendra and Trikona lords": "કેન્દ્ર અને ત્રિકોણ ભાવેશો",
        "Wealth-related house lords": "ધન સંબંધિત ભાવેશો",
        "supportive house": "સહાયક ભાવ",
        "dusthana": "દુષ્ઠાન",
        "occupies a dusthana": "દુષ્ઠાન ભાવમાં સ્થિત છે",
        "occupies the Ascendant": "લગ્નમાં સ્થિત છે",
        "aspects the Ascendant": "લગ્ન પર દૃષ્ટિ કરે છે",
        "occupies the 10th house": "દશમ ભાવમાં સ્થિત છે",
        "occupies house": "ભાવમાં સ્થિત છે",
        "aspects house": "ભાવ પર દૃષ્ટિ કરે છે",
        "supports learning through house": "ભાવ દ્વારા અભ્યાસને સહકાર આપે છે",
        "is connected with education": "શિક્ષણ સાથે જોડાણ ધરાવે છે",
        "highlighting its career themes": "કારકિર્દીના સંબંધિત વિષયો દર્શાવે છે",
        "D9 provides secondary support for planetary maturity": "D9 નવાંશ ગ્રહોની પરિપક્વતા માટે વધારાનો સહકાર આપે છે",
        "Venus is in a traditionally supportive relationship house": "શુક્ર પરંપરાગત રીતે સંબંધો માટે સહાયક ભાવમાં છે",
        "Jupiter supports partnership through a favorable house": "ગુરુ અનુકૂળ ભાવ દ્વારા ભાગીદારી અને દાંપત્યને સહકાર આપે છે",
        "Saturn in the 7th can emphasize responsibility or delay": "સપ્તમ ભાવમાં શનિ જવાબદારી અથવા વિલંબ તરફ સંકેત આપી શકે છે",
        "Jupiter in the 7th supports partnership themes": "સપ્તમ ભાવમાં ગુરુ ભાગીદારી અને દાંપત્યને સહકાર આપે છે",
        "Venus in the 7th strongly emphasizes relationship themes": "સપ્તમ ભાવમાં શુક્ર સંબંધોના વિષયને મજબૂત બનાવે છે",
        "D9 contains a supportive relationship significator in the 7th": "D9 માં સપ્તમ ભાવની સંબંધસૂચક સ્થિતિ સહાયક છે",
        "D9 Saturn emphasizes maturity/responsibility in partnership": "D9 નો શનિ દાંપત્યમાં પરિપક્વતા અને જવાબદારી પર ભાર મૂકે છે",
        "9th and 10th lords are connected": "નવમ અને દશમ ભાવેશો વચ્ચે જોડાણ છે",
        "9th and 12th lords are connected": "નવમ અને દ્વાદશ ભાવેશો વચ્ચે જોડાણ છે",
        "4th and 12th lords are connected, suggesting relocation/foreign themes": "ચતુર્થ અને દ્વાદશ ભાવેશોનું જોડાણ સ્થળાંતર અથવા વિદેશી સંકેતો દર્શાવે છે",
        "occupies a foreign/travel-related house": "વિદેશ અથવા પ્રવાસ સંબંધિત ભાવમાં સ્થિત છે",
        "is retrograde": "વક્રી છે",
        "is exalted": "ઉચ્ચસ્થ છે",
        "is debilitated": "નીચસ્થ છે",
        "is in own sign": "સ્વરાશિમાં છે",
        "is in debilitation": "નીચ રાશિમાં છે",
        "conjunction or 7th-house relationship": "યુતિ અથવા સપ્તમ ભાવનું સંબંધિત જોડાણ",
        "The 9th and 10th lords": "નવમ અને દશમ ભાવેશો",
        "Jupiter is in a Kendra from the Moon": "ચંદ્રથી કેન્દ્રમાં ગુરુ સ્થિત છે",
        "Sun and Mercury occupy the same house/sign": "સૂર્ય અને બુધ એક જ ભાવ/રાશિમાં સ્થિત છે",
        "A dusthana lord is placed in another dusthana": "દુષ્ઠાન ભાવેશ અન્ય દુષ્ઠાન ભાવમાં સ્થિત છે",
        "A full Neecha Bhanga analysis is required before judging the result.": "પરિણામનું મૂલ્યાંકન કરતા પહેલાં સંપૂર્ણ નીચભંગ વિશ્લેષણ જરૂરી છે.",
        "No Manglik indication from the Lagna under the commonly used rule.": "પ્રચલિત નિયમ મુજબ લગ્નથી મંગળ દોષનો સંકેત નથી.",
        "Manglik indication is present from the Lagna under the commonly used rule.": "પ્રચલિત નિયમ મુજબ લગ્નથી મંગળ દોષનો સંકેત છે.",
        "is supportive from the Lagna": "લગ્નથી સહાયક છે",
        "is more reflective from the Lagna": "લગ્નથી વધુ વિચારાત્મક પરિણામ દર્શાવે છે",
        "emphasizes effort/results through": "પ્રયત્ન અને પરિણામ પર ભાર મૂકે છે",
        "emphasizes restructuring through": "પુનઃરચના અને જવાબદારી પર ભાર મૂકે છે",
        "Saturn is in Sade Sati": "શનિ સાડેસાતીના તબક્કામાં છે",
        "relative to natal Moon": "જન્મ ચંદ્રની સરખામણીમાં",
        "activates supportive house": "સહાયક ભાવને સક્રિય કરે છે",
        "activates house": "ભાવને સક્રિય કરે છે",
        "Combustion and dignity should also be considered.": "અસ્ત અને ગ્રહબળનું પણ ધ્યાનમાં રાખવું જોઈએ.",
        "Final strength depends on dignity and affliction.": "અંતિમ બળ ગ્રહની સ્થિતિ અને પીડિતતા પર આધારિત છે.",
    }

    for en, guj in replacements.items():
        text = text.replace(en, guj)

    # Planet names.
    for en, guj in PLANET_GUJARATI.items():
        text = text.replace(en, guj)

    # Specific English descriptors still emitted by the engine.
    simple = {
        "supportive": "સહાયક",
        "favorable": "અનુકૂળ",
        "challenging": "પડકારજનક",
        "responsibility": "જવાબદારી",
        "delay": "વિલંબ",
        "maturity": "પરિપક્વતા",
        "partnership": "ભાગીદારી",
        "education": "શિક્ષણ",
        "career": "કારકિર્દી",
        "wealth": "ધન",
        "income": "આવક",
        "relationship": "સંબંધ",
        "relocation": "સ્થળાંતર",
        "foreign": "વિદેશ",
        "travel": "પ્રવાસ",
        "learning": "અભ્યાસ",
        "Ascendant": "લગ્ન",
        "Lagna": "લગ્ન",
        "Moon": "ચંદ્ર",
    }

    for en, guj in simple.items():
        text = text.replace(en, guj)

    # Replace "house N" after the phrase-level translations.
    for h in range(1, 13):
        text = text.replace(f"house {h}", _guj_house(h))

    # Translate common parenthetical phrases.
    text = text.replace("Moderate", "મધ્યમ")
    text = text.replace("Strong", "મજબૂત")
    text = text.replace("Context-dependent", "પરિસ્થિતિ આધારિત")

    return text


def _guj_yoga_name(value):
    mapping = {
        "Raja Yoga connection": "રાજયોગ સંકેત",
        "Dharma-Karmadhipati Yoga": "ધર્મ-કર્માધિપતિ યોગ",
        "Dhana Yoga connection": "ધન યોગ સંકેત",
        "Gaja Kesari Yoga": "ગજકેસરી યોગ",
        "Budha-Aditya Yoga": "બુધાદિત્ય યોગ",
        "Vipareeta Raja Yoga indication": "વિપરીત રાજયોગ સંકેત",
        "Neecha placement": "નીચ ગ્રહસ્થિતિ",
    }
    return mapping.get(str(value), _guj_reason(value))


def _guj_strength(value):
    return {
        "Strong": "મજબૂત",
        "Moderate": "મધ્યમ",
        "Context-dependent": "પરિસ્થિતિ આધારિત",
        "Requires cancellation analysis": "નીચભંગ વિશ્લેષણ જરૂરી",
    }.get(str(value), _guj_reason(value))


def _guj_manglik_status(value):
    return {
        "Manglik indication present": "મંગળ દોષનો સંકેત હાજર છે",
        "No Manglik indication": "મંગળ દોષનો સંકેત નથી",
    }.get(str(value), _guj_reason(value))


def _make_prediction_dataframe(pred):
    """Gujarati summary table used by Streamlit."""
    rows = []

    labels = {
        "personality": "વ્યક્તિત્વ અને સ્વભાવ",
        "intelligence": "બુદ્ધિ અને શીખવાની ક્ષમતા",
        "education": "શિક્ષણ",
        "career": "કારકિર્દી અને વ્યવસાય",
        "wealth": "ધન અને આવક",
        "relationships": "લગ્ન અને સંબંધો",
        "foreign": "વિદેશી જોડાણ અને સ્થળાંતર",
        "vitality": "જીવનશક્તિ અને જીવનશૈલી",
    }

    for key, label in labels.items():
        item = pred["areas"].get(key, {})
        score = float(item.get("score", 0) or 0)

        rows.append({
            "વિષય": label,
            "સ્કોર": round(score, 1),
            "મૂલ્યાંકન": _guj_status(_status(score)),
        })

    return pd.DataFrame(rows)


def _prediction_report(pred, name=""):
    """Complete Gujarati rule-based Vedic interpretation report."""
    areas = pred["areas"]
    lines = []

    lines.append("\n---\n")
    lines.append("# 🔮 નિયમ આધારિત વૈદિક જ્યોતિષ અર્થઘટન")
    lines.append("")

    lines.append(
        "> **નોંધ:** આ અર્થઘટન પરંપરાગત જ્યોતિષીય નિયમો, "
        "ગ્રહોની સ્થિતિ અને પરસ્પર સંબંધોના આધારે તૈયાર કરવામાં આવ્યું છે. "
        "આ વૈજ્ઞાનિક રીતે માન્ય ભવિષ્યવાણી પદ્ધતિ નથી અને "
        "તબીબી, કાનૂની અથવા નાણાકીય વ્યાવસાયિક સલાહનો વિકલ્પ નથી."
    )
    lines.append("")

    if name:
        lines.append(f"**નામ:** {name}")
        lines.append("")

    lines.append("## 🌟 સમગ્ર કુંડળીનું અર્થઘટન")

    overall = float(pred.get("overall_score", 0) or 0)

    lines.append(
        f"**સમગ્ર વલણ સ્કોર:** {overall:.1f}/100 — "
        f"**{_guj_status(_status(overall))}**"
    )
    lines.append("")

    area_labels = [
        ("personality", "વ્યક્તિત્વ અને સ્વભાવ"),
        ("intelligence", "બુદ્ધિ અને શીખવાની ક્ષમતા"),
        ("education", "શિક્ષણ"),
        ("career", "કારકિર્દી અને વ્યવસાય"),
        ("wealth", "ધન અને આવક"),
        ("relationships", "લગ્ન અને સંબંધો"),
        ("foreign", "વિદેશી જોડાણ અને સ્થળાંતર"),
        ("vitality", "જીવનશક્તિ અને જીવનશૈલી"),
    ]

    for key, label in area_labels:
        item = areas.get(key, {})
        score = float(item.get("score", 0) or 0)

        lines.append(
            f"### {label} — {score:.1f}/100 "
            f"({_guj_status(_status(score))})"
        )

        traits = item.get("traits") or []
        if traits:
            lines.append(
                "**મુખ્ય સ્વભાવના લક્ષણો:** "
                + ", ".join(_guj_trait(x) for x in traits)
            )

        domains = item.get("domains") or []
        if domains:
            lines.append(
                "**સંભવિત કારકિર્દી ક્ષેત્રો:** "
                + ", ".join(_guj_domain(x) for x in domains)
            )

        reasons = item.get("reasons") or []
        if reasons:
            lines.append("**આ મૂલ્યાંકનને સમર્થન આપતા નિયમો:**")
            for reason in reasons[:8]:
                raw = reason.get("text", "") if isinstance(reason, dict) else str(reason)
                lines.append(f"- {_guj_reason(raw)}")

        lines.append("")

    # Yogas
    lines.append("## 🧿 મહત્વપૂર્ણ યોગ અને જ્યોતિષીય સ્થિતિઓ")

    yogas = pred.get("yogas") or []
    if yogas:
        for y in yogas:
            lines.append(
                f"- **{_guj_yoga_name(y.get('name', ''))}** — "
                f"{_guj_strength(y.get('strength', ''))}: "
                f"{_guj_reason(y.get('reason', ''))}"
            )
    else:
        lines.append(
            "વર્તમાન નિયમ સમૂહ મુજબ કોઈ મુખ્ય યોગ ઓળખાયો નથી."
        )

    lines.append("")

    # Manglik
    lines.append("## 🔥 મંગળ દોષ વિશ્લેષણ")

    manglik = pred.get("manglik") or {}
    lines.append(
        f"**{_guj_manglik_status(manglik.get('status', ''))}** — "
        f"{_guj_reason(manglik.get('reason', ''))}"
    )

    if manglik.get("mars_house") is not None:
        lines.append(
            f"મંગળનું ભાવ સ્થાન: {_guj_house(manglik['mars_house'])}"
        )

    lines.append("")

    # Dasha
    lines.append("## 🕉️ વર્તમાન વિંશોત્તરી દશા")

    active = pred.get("active_dasha")

    if isinstance(active, dict):
        md = _guj_planet(active.get("Mahadasha", ""))
        ad = _guj_planet(active.get("Antardasha", ""))

        lines.append(f"**મહાદશા:** {md}")
        lines.append(f"**અંતર્દશા:** {ad}")

        start = active.get("Start")
        end = active.get("End")

        if hasattr(start, "strftime") and hasattr(end, "strftime"):
            lines.append(
                f"**સમયગાળો:** {start.strftime('%d-%m-%Y')} "
                f"થી {end.strftime('%d-%m-%Y')}"
            )

        lines.append("")

        for r in (pred.get("dasha_reasons") or [])[:8]:
            lines.append(f"- {_guj_reason(r)}")
    else:
        lines.append(
            "ઉપલબ્ધ દશા કોષ્ટકમાંથી વર્તમાન દશા ઓળખી શકાઈ નથી."
        )

    lines.append("")

    # Annual trends
    lines.append("## 📅 વર્ષવાર નિયમ આધારિત વલણ")

    lines.append(
        "આ વર્ષવાર વલણ વિંશોત્તરી દશા તથા દર વર્ષની 1 જુલાઈ આસપાસ "
        "ગુરુ અને શનિના ગોચર સ્થાનને આધારે તૈયાર કરવામાં આવ્યું છે. "
        "તેને ચોક્કસ ઘટનાની ખાતરી તરીકે ન જોવું."
    )
    lines.append("")

    for yr in pred.get("annual", []) or []:
        s = yr.get("scores", {}) or {}

        lines.append(
            f"### {yr.get('year', '')} — "
            f"કારકિર્દી {float(s.get('career', 0)):.0f} | "
            f"ધન {float(s.get('wealth', 0)):.0f} | "
            f"શિક્ષણ {float(s.get('education', 0)):.0f} | "
            f"સંબંધો {float(s.get('relationships', 0)):.0f}"
        )

        for r in (yr.get("reasons") or [])[:4]:
            lines.append(f"- {_guj_reason(r)}")

        ad = yr.get("active_dasha")
        if isinstance(ad, dict):
            lines.append(
                f"- દશા સંદર્ભ: "
                f"{_guj_planet(ad.get('Mahadasha', ''))}/"
                f"{_guj_planet(ad.get('Antardasha', ''))}"
            )

        lines.append("")

    # Planet strength
    lines.append("## 🪐 ગ્રહબળનું સંક્ષિપ્ત અર્થઘટન")

    for p in pred.get("planet_strengths", []) or []:
        planet = _guj_planet(p.get("Planet", ""))
        strength = float(p.get("Strength", 0) or 0)
        dignity = _guj_reason(p.get("Dignity", ""))
        house = p.get("House")

        functional = {
            "Supportive": "સહાયક",
            "Challenging": "પડકારજનક",
            "Mixed": "મિશ્ર",
        }.get(str(p.get("Functional", "")), str(p.get("Functional", "")))

        combust = "હા" if p.get("Combust") == "Yes" else "ના"

        line = (
            f"- **{planet}:** બળ {strength:.1f}/100; "
            f"સ્થિતિ: {_guj_reason(dignity)}; "
            f"ભાવ: {_guj_house(house) if house is not None else '—'}; "
            f"કાર્યાત્મક સ્વભાવ: {functional}; "
            f"અસ્ત: {combust}"
        )

        if p.get("Notes"):
            line += f" — {_guj_reason(p['Notes'])}"

        lines.append(line)

    lines.append("")

    # House lord summary
    lines.append("## 🏠 ભાવેશોની સંક્ષિપ્ત સ્થિતિ")

    house_lords = pred.get("house_lords") or {}
    if house_lords:
        for h in range(1, 13):
            lord = house_lords.get(h)
            if lord:
                lines.append(
                    f"- **{_guj_house(h)}:** {_guj_planet(lord)} ભાવેશ"
                )

    lines.append("")

    # Interpretation guide
    lines.append("## 🧭 સ્કોર કેવી રીતે સમજવો")

    lines.append(
        "- **80થી વધુ:** પરંપરાગત નિયમો મુજબ અતિશય સહાયક સંયોજન."
    )
    lines.append(
        "- **65–79:** સામાન્ય રીતે અનુકૂળ સંયોજન."
    )
    lines.append(
        "- **50–64:** મિશ્ર પરિબળો; સમગ્ર કુંડળીના સંદર્ભમાં અર્થઘટન જરૂરી."
    )
    lines.append(
        "- **35–49:** સાવચેતી અને વધુ પ્રયત્નની જરૂરિયાત દર્શાવતું સંયોજન."
    )
    lines.append(
        "- **35થી ઓછું:** વધુ પડકારજનક પરંપરાગત સંકેત."
    )
    lines.append(
        "- ઊંચો સ્કોર ચોક્કસ ઘટના બનવાની ખાતરી આપતો નથી; "
        "તે માત્ર આ નિયમ આધારિત મોડેલમાં વધુ મજબૂત પરંપરાગત સંકેત દર્શાવે છે."
    )

    return "\n".join(lines)


def generate_rule_based_predictions(rows, asc, dasha_df, birth_dt=None):
    """Main public API for the prediction engine."""
    planet_map = _planet_map(rows)
    asc_index = int(asc["Rashi_Index"])
    house_lords = _house_lords(asc_index)

    # Mark combustion dynamically; do not mutate the source rows.
    for p, row in planet_map.items():
        row["Combust"] = _combust_status(planet_map, p)

    personality = _trait_analysis(planet_map, asc, house_lords)
    intelligence_score, intelligence_reasons = _intelligence_analysis(planet_map, house_lords)
    education_score, education_reasons = _education_analysis(planet_map, house_lords)
    career_score, career_reasons, career_domains = _career_analysis(planet_map, house_lords, rows)
    wealth_score, wealth_reasons = _wealth_analysis(planet_map, house_lords)
    marriage_score, marriage_reasons = _marriage_analysis(planet_map, house_lords, rows)
    foreign_score, foreign_reasons = _foreign_analysis(planet_map, house_lords)
    vitality_score, vitality_reasons = _health_routine_analysis(planet_map, house_lords)

    areas = {
        "personality": {"score": personality["score"], "traits": personality["traits"], "reasons": personality["reasons"]},
        "intelligence": {"score": intelligence_score, "reasons": intelligence_reasons},
        "education": {"score": education_score, "reasons": education_reasons},
        "career": {"score": career_score, "reasons": career_reasons, "domains": career_domains},
        "wealth": {"score": wealth_score, "reasons": wealth_reasons},
        "relationships": {"score": marriage_score, "reasons": marriage_reasons},
        "foreign": {"score": foreign_score, "reasons": foreign_reasons},
        "vitality": {"score": vitality_score, "reasons": vitality_reasons}
    }

    # Yoga and condition detection.
    yogas = _yoga_detection(planet_map, house_lords)
    manglik, mars_house, manglik_reason = _manglik_analysis(planet_map)

    # Current Dasha.
    now = birth_dt if birth_dt is not None else datetime.now()
    active = _active_dasha(dasha_df, now)
    dasha_reasons = []
    if active is not None:
        md = active["Mahadasha"]
        ad = active["Antardasha"]
        mod, rs = _dasha_area_modifier(md, ad, planet_map, house_lords)
        dasha_reasons.extend(rs)
        # Dasha is a timing modifier, not the whole chart.
        for key in ["career", "wealth", "education", "relationships"]:
            areas[key]["score"] = _clamp(areas[key]["score"] + mod * 0.35)

    # Overall score is an average of life areas; personality is weighted slightly higher.
    weights = {
        "personality": 1.2, "intelligence": 0.8, "education": 0.8,
        "career": 1.2, "wealth": 1.0, "relationships": 1.0,
        "foreign": 0.7, "vitality": 0.8
    }
    total = sum(areas[k]["score"] * weights[k] for k in areas)
    overall = total / sum(weights.values())

    # Annual trend: current year + next 10 years.
    annual = []
    natal_moon_index = int(planet_map["Moon"]["Rashi_Index"])
    start_year = datetime.now().year
    base_scores = {
        "career": career_score,
        "wealth": wealth_score,
        "education": education_score,
        "relationships": marriage_score,
        "discipline": 60.0
    }
    for year in range(start_year, start_year + 11):
        tp = _annual_transit_profile(asc_index, natal_moon_index, year)
        scores, reasons, ad = _annual_prediction(
            year, base_scores, tp, dasha_df, planet_map, house_lords
        )
        annual.append({
            "year": year,
            "scores": scores,
            "reasons": reasons,
            "active_dasha": ad,
            "transits": tp
        })

    # Planet strength summary.
    strength_rows = []
    for p, row in planet_map.items():
        fb = _functional_nature(p, house_lords)
        score, rs = _planet_strength(p, row, fb)
        strength_rows.append({
            "Planet": p,
            "Strength": round(score, 1),
            "Dignity": _dignity(p, row.get("Rashi"))[0],
            "House": row.get("House"),
            "Functional": "Supportive" if fb is True else ("Challenging" if fb is False else "Mixed"),
            "Combust": "Yes" if row.get("Combust") else "No",
            "Notes": "; ".join(rs[:2])
        })

    return {
        "overall_score": _clamp(overall),
        "areas": areas,
        "yogas": yogas,
        "manglik": {
            "present": manglik,
            "mars_house": mars_house,
            "status": "Manglik indication present" if manglik else "No Manglik indication",
            "reason": manglik_reason
        },
        "active_dasha": active,
        "dasha_reasons": dasha_reasons,
        "annual": annual,
        "planet_strengths": strength_rows,
        "house_lords": house_lords
    }


print("✅ Complete rule-based Vedic prediction engine loaded.")