# -*- coding: utf-8 -*-
"""Gujarati interpretation layer for the rule-based Vedic astrology engine.

The calculation/rule engine remains unchanged. This module converts the
structured prediction output into a complete Gujarati interpretation.
"""
import re

PLANET_GU = {
    "Sun":"સૂર્ય", "Moon":"ચંદ્ર", "Mars":"મંગળ", "Mercury":"બુધ",
    "Jupiter":"ગુરુ", "Venus":"શુક્ર", "Saturn":"શનિ", "Rahu":"રાહુ", "Ketu":"કેતુ"
}
SIGN_GU = {
    "Mesha":"મેષ", "Vrishabha":"વૃષભ", "Mithuna":"મિથુન", "Karka":"કર્ક",
    "Simha":"સિંહ", "Kanya":"કન્યા", "Tula":"તુલા", "Vrishchika":"વૃશ્ચિક",
    "Dhanu":"ધનુ", "Makara":"મકર", "Kumbha":"કુંભ", "Meena":"મીન"
}
HOUSE_GU = {
    1:"લગ્ન/પ્રથમ ભાવ", 2:"દ્વિતીય ભાવ", 3:"તૃતીય ભાવ", 4:"ચતુર્થ ભાવ",
    5:"પંચમ ભાવ", 6:"ષષ્ઠ ભાવ", 7:"સપ્તમ ભાવ", 8:"અષ્ટમ ભાવ",
    9:"નવમ ભાવ", 10:"દશમ ભાવ", 11:"એકાદશ ભાવ", 12:"દ્વાદશ ભાવ"
}
TRAIT_GU = {
    "leadership":"નેતૃત્વ ક્ષમતા", "authority":"અધિકારભાવ", "confidence":"આત્મવિશ્વાસ", "administration":"વહીવટી કુશળતા",
    "emotional intelligence":"ભાવનાત્મક સમજ", "adaptability":"પરિસ્થિતિ પ્રમાણે અનુકૂલન", "public connection":"લોકો સાથે જોડાવાની ક્ષમતા", "intuition":"અંતઃપ્રેરણા",
    "initiative":"પહેલ કરવાની ક્ષમતા", "courage":"સાહસ", "technical drive":"તકનીકી વલણ", "competition":"સ્પર્ધાત્મક વલણ",
    "analysis":"વિશ્લેષણાત્મક વિચારશક્તિ", "communication":"સંચાર કુશળતા", "technology":"ટેકનોલોજી પ્રત્યે રસ", "commerce":"વાણિજ્યિક સમજ",
    "wisdom":"જ્ઞાન અને પરિપક્વતા", "teaching":"શિક્ષણ આપવાની ક્ષમતા", "research":"સંશોધન વલણ", "guidance":"માર્ગદર્શન આપવાની ક્ષમતા",
    "creativity":"સર્જનાત્મકતા", "relationships":"સંબંધો પ્રત્યે સંવેદનશીલતા", "design":"ડિઝાઇન પ્રત્યે રસ", "diplomacy":"કૂટનીતિક સમજ",
    "discipline":"શિસ્ત", "persistence":"સતત પ્રયત્ન", "structure":"વ્યવસ્થિત અભિગમ", "long-term work":"દીર્ઘકાલીન કાર્યક્ષમતા",
    "ambition":"મહત્વાકાંક્ષા", "innovation":"નવીનતા", "unconventional thinking":"પરંપરાગતથી અલગ વિચારવાની ક્ષમતા", "foreign links":"વિદેશી જોડાણ",
    "specialization":"વિશિષ્ટ ક્ષેત્રમાં નિષ્ણાત બનવાની વૃત્તિ", "detachment":"અલિપ્તતા", "introspection":"આત્મચિંતન"
}
DOMAIN_GU = {
    "administration":"વહીવટ", "government/public institutions":"સરકારી/જાહેર સંસ્થાઓ", "leadership":"નેતૃત્વ", "management":"વ્યવસ્થાપન",
    "public relations":"જનસંપર્ક", "hospitality":"હોસ્પિટાલિટી", "healthcare support":"હેલ્થકેર સહાયક ક્ષેત્ર", "travel/service":"પ્રવાસ/સેવા ક્ષેત્ર",
    "engineering":"ઇજનેરી", "technology":"ટેકનોલોજી", "defence":"રક્ષા ક્ષેત્ર", "operations":"ઓપરેશન્સ", "sports":"રમતગમત",
    "IT/software":"આઈટી/સોફ્ટવેર", "data analysis":"ડેટા વિશ્લેષણ", "communication":"સંચાર", "commerce":"વાણિજ્ય", "business":"વ્યવસાય",
    "teaching":"શિક્ષણ", "research":"સંશોધન", "law":"કાયદો", "finance":"નાણાકીય ક્ષેત્ર", "consulting":"કન્સલ્ટિંગ",
    "design":"ડિઝાઇન", "media":"મીડિયા", "arts":"કલા", "fashion":"ફેશન", "public-facing creative work":"લોકસંપર્ક આધારિત સર્જનાત્મક ક્ષેત્ર",
    "infrastructure":"ઇન્ફ્રાસ્ટ્રક્ચર", "manufacturing":"મેન્યુફેક્ચરિંગ", "large organizations":"મોટી સંસ્થાઓ",
    "digital media":"ડિજિટલ મીડિયા", "foreign organizations":"વિદેશી સંસ્થાઓ", "emerging industries":"ઉભરતા ઉદ્યોગો",
    "analytics":"એનાલિટિક્સ", "specialized technical work":"વિશિષ્ટ તકનીકી કાર્ય", "spiritual/academic study":"આધ્યાત્મિક/શૈક્ષણિક અભ્યાસ"
}
STATUS_GU = {
    "Highly supportive":"ખૂબ અનુકૂળ", "Favorable":"અનુકૂળ", "Mixed / manageable":"મિશ્ર પરંતુ સંભાળી શકાય તેવું",
    "Needs caution":"સાવચેતી અને વધુ પ્રયત્ન જરૂરી", "Challenging":"પડકારજનક"
}
STRENGTH_GU = {"Strong":"મજબૂત", "Moderate":"મધ્યમ", "Context-dependent":"પરિસ્થિતિ આધારિત", "Requires cancellation analysis":"રદયોગ વિશ્લેષણ જરૂરી"}

AREA_META = {
    "personality": ("🧠 સ્વભાવ અને વ્યક્તિત્વ", "વ્યક્તિત્વ, આત્મવિશ્વાસ, વર્તન અને જીવન પ્રત્યેના અભિગમ અંગેનું નિયમ આધારિત વિશ્લેષણ."),
    "intelligence": ("🧠 બુદ્ધિ અને શીખવાની ક્ષમતા", "વિચારશક્તિ, વિશ્લેષણ, સંચાર અને જ્ઞાન ગ્રહણ કરવાની વૃત્તિનું વિશ્લેષણ."),
    "education": ("🎓 શિક્ષણ", "અભ્યાસ, ઉચ્ચ શિક્ષણ, સંશોધન અને શૈક્ષણિક સ્થિરતાના સંકેતો."),
    "career": ("💼 કારકિર્દી અને વ્યવસાય", "દશમ ભાવ, તેના સ્વામી અને સંબંધિત ગ્રહોના આધારે વ્યવસાયિક દિશાનું વિશ્લેષણ."),
    "wealth": ("💰 ધન અને આવક", "દ્વિતીય, પંચમ, નવમ અને એકાદશ ભાવના નિયમો પરથી ધન અને આવકના સંકેતો."),
    "relationships": ("❤️ લગ્ન અને સંબંધો", "સપ્તમ ભાવ, શુક્ર, ગુરુ અને D9ના સહાયક સંકેતો પરથી સંબંધોનું વિશ્લેષણ."),
    "foreign": ("✈️ વિદેશ અને સ્થળાંતર", "તૃતીય, નવમ અને દ્વાદશ ભાવ તથા સંબંધિત સ્વામીઓ પરથી વિદેશ/સ્થળાંતરના સંકેતો."),
    "vitality": ("🧘 જીવનશક્તિ અને દૈનિક રૂટિન", "પ્રથમ અને ષષ્ઠ ભાવના નિયમો પરથી સામાન્ય vitality અને routine themes; આ તબીબી નિદાન નથી."),
}

def _p(p): return PLANET_GU.get(str(p), str(p))
def _h(h):
    try: return HOUSE_GU.get(int(h), f"{h}મો ભાવ")
    except Exception: return str(h)
def _s(s): return SIGN_GU.get(str(s), str(s))
def _score_sentence(score):
    if score >= 80: return "આ ક્ષેત્રમાં કુંડળીના નિયમો ખૂબ મજબૂત અને સહાયક સંકેત આપે છે."
    if score >= 65: return "આ ક્ષેત્રમાં કુંડળીના નિયમો સામાન્ય રીતે અનુકૂળ સંકેત આપે છે."
    if score >= 50: return "આ ક્ષેત્રમાં અનુકૂળ અને પડકારજનક બંને પરિબળો છે; યોગ્ય પ્રયત્નથી પરિણામ સંભાળી શકાય છે."
    if score >= 35: return "આ ક્ષેત્રમાં કેટલાક પડકારજનક સંકેતો છે; ધીરજ, આયોજન અને સતત પ્રયત્ન મહત્વપૂર્ણ રહેશે."
    return "આ ક્ષેત્રમાં વર્તમાન નિયમ સમૂહ મુજબ વધુ પડકારજનક સંકેતો જોવા મળે છે; નિર્ણયોમાં સાવચેતી જરૂરી છે."

def _translate_reason(text):
    """Translate every known rule-engine reason into natural Gujarati."""
    t = str(text).strip()
    m = re.match(r"Lagna lord (\w+) is in supportive house (\d+)", t)
    if m: return f"લગ્નેશ {_p(m.group(1))} {_h(m.group(2))}માં હોવાથી વ્યક્તિત્વ માટે સહાયક સ્થિતિ દર્શાવે છે."
    m = re.match(r"Lagna lord (\w+) is in house (\d+)", t)
    if m: return f"લગ્નેશ {_p(m.group(1))} {_h(m.group(2))}માં સ્થિત છે; તેથી આ સ્થાનના વિષયો જીવનમાં વધુ અસરકારક બની શકે છે."
    m = re.match(r"(\w+) occupies the Ascendant", t)
    if m: return f"{_p(m.group(1))} લગ્નમાં સ્થિત હોવાથી તેના ગુણો વ્યક્તિત્વમાં વધુ સ્પષ્ટ રીતે દેખાઈ શકે છે."
    m = re.match(r"(\w+) aspects the Ascendant", t)
    if m: return f"{_p(m.group(1))}ની લગ્ન પર દૃષ્ટિ હોવાથી {_p(m.group(1))} સંબંધિત ગુણો વ્યક્તિત્વને પ્રભાવિત કરે છે."
    m = re.match(r"Moon occupies supportive house (\d+)", t)
    if m: return f"ચંદ્ર {_h(m.group(1))}માં હોવાથી મન અને ભાવનાત્મક અભિગમ માટે સહાયક સંકેત મળે છે."
    m = re.match(r"(\w+) supports learning through house (\d+)", t)
    if m: return f"{_p(m.group(1))} {_h(m.group(2))} મારફતે શીખવાની અને જ્ઞાન ગ્રહણ કરવાની ક્ષમતાને સહાય કરે છે."
    m = re.match(r"(\w+) is connected with education", t)
    if m: return f"{_p(m.group(1))} શિક્ષણ સંબંધિત ભાવો સાથે જોડાયેલ હોવાથી અભ્યાસ અને જ્ઞાન ક્ષેત્રે સહાયક સંકેત મળે છે."
    m = re.match(r"Lord of house (\d+) occupies a supportive house \((\d+)\)", t)
    if m: return f"{_h(m.group(1))}ના સ્વામી {_h(m.group(2))}માં હોવાથી તે ભાવના વિષયો માટે સહાયક સ્થિતિ દર્શાવે છે."
    m = re.match(r"Lord of house (\d+) occupies a dusthana \((\d+)\)", t)
    if m: return f"{_h(m.group(1))}ના સ્વામી {_h(m.group(2))}માં હોવાથી આ ક્ષેત્રમાં વધુ મહેનત અથવા અવરોધના સંકેતો મળે છે."
    m = re.match(r"(\w+) occupies house (\d+)", t)
    if m: return f"{_p(m.group(1))} {_h(m.group(2))}માં સ્થિત છે; તેથી તે ભાવના વિષયો સક્રિય બને છે."
    m = re.match(r"(\w+) influences house (\d+)", t)
    if m: return f"{_p(m.group(1))} {_h(m.group(2))}ને પ્રભાવિત કરે છે; તેથી તે ક્ષેત્રમાં જવાબદારી અથવા પડકાર વધારી શકે છે."
    m = re.match(r"(\w+) aspects house (\d+)", t)
    if m: return f"{_p(m.group(1))}ની દૃષ્ટિ {_h(m.group(2))} પર હોવાથી આ ક્ષેત્રમાં તેનો પ્રભાવ રહે છે."
    m = re.match(r"10th lord is (\w+), highlighting its career themes", t)
    if m: return f"દશમેશ {_p(m.group(1))} હોવાથી કારકિર્દીમાં {_p(m.group(1))} સંબંધિત ક્ષેત્રોનું મહત્વ વધે છે."
    m = re.match(r"(\w+) occupies the 10th house", t)
    if m: return f"{_p(m.group(1))} દશમ ભાવમાં હોવાથી કારકિર્દી અને જાહેર પ્રતિષ્ઠા પર તેનો વિશેષ પ્રભાવ રહે છે."
    m = re.match(r"D9 provides secondary support for planetary maturity", t)
    if m: return "D9 નવાંશ કેટલાક ગ્રહોની પરિપક્વતા અને લાંબા ગાળાના પરિણામો માટે વધારાનો સહાયક સંકેત આપે છે."
    m = re.match(r"Connection between lords of houses (\d+) and (\d+)", t)
    if m: return f"{_h(m.group(1))} અને {_h(m.group(2))}ના સ્વામીઓ વચ્ચે સંબંધ હોવાથી આ બંને ક્ષેત્રોમાં પરસ્પર જોડાણ જોવા મળે છે."
    m = re.match(r"Venus is in a traditionally supportive relationship house", t)
    if m: return "શુક્ર પરંપરાગત રીતે સંબંધો માટે અનુકૂળ ભાવમાં હોવાથી પ્રેમ, સુમેળ અને ભાગીદારી માટે સહાયક સંકેત મળે છે."
    m = re.match(r"Jupiter supports partnership through a favorable house", t)
    if m: return "ગુરુ અનુકૂળ ભાવમાં હોવાથી સંબંધોમાં સમજ, માર્ગદર્શન અને સ્થિરતા માટે સહાયક સંકેત મળે છે."
    m = re.match(r"Saturn in the 7th can emphasize responsibility or delay", t)
    if m: return "સપ્તમ ભાવમાં શનિ સંબંધોમાં જવાબદારી, પરિપક્વતા અથવા વિલંબ જેવા વિષયો વધારે સક્રિય કરી શકે છે."
    m = re.match(r"Jupiter in the 7th supports partnership themes", t)
    if m: return "સપ્તમ ભાવમાં ગુરુ ભાગીદારી, સમજણ અને સંબંધોમાં સહકાર માટે અનુકૂળ સંકેત આપે છે."
    m = re.match(r"Venus in the 7th strongly emphasizes relationship themes", t)
    if m: return "સપ્તમ ભાવમાં શુક્ર સંબંધો, આકર્ષણ અને દાંપત્ય જીવનને વિશેષ મહત્વ આપે છે."
    m = re.match(r"D9 contains a supportive relationship significator in the 7th", t)
    if m: return "D9ના સપ્તમ ભાવમાં સંબંધકારક ગ્રહની સહાયક સ્થિતિ દાંપત્ય માટે વધારાનો સકારાત્મક સંકેત આપે છે."
    m = re.match(r"D9 Saturn emphasizes maturity/responsibility in partnership", t)
    if m: return "D9ના સપ્તમ ભાવમાં શનિ સંબંધોમાં પરિપક્વતા, જવાબદારી અને ધીરજનું મહત્વ દર્શાવે છે."
    m = re.match(r"9th and 12th lords are connected", t)
    if m: return "નવમ અને દ્વાદશ ભાવના સ્વામીઓ વચ્ચે સંબંધ હોવાથી વિદેશ, લાંબી મુસાફરી અથવા વિદેશી જોડાણના સંકેતો વધે છે."
    m = re.match(r"4th and 12th lords are connected, suggesting relocation/foreign themes", t)
    if m: return "ચતુર્થ અને દ્વાદશ ભાવના સ્વામીઓનો સંબંધ ઘર/સ્થળ પરિવર્તન અથવા વિદેશી જોડાણની સંભાવના તરફ સંકેત કરે છે."
    m = re.match(r"(\w+) occupies a foreign/travel-related house", t)
    if m: return f"{_p(m.group(1))} વિદેશ/પ્રવાસ સંબંધિત ભાવમાં હોવાથી સ્થળાંતર અથવા વિદેશી જોડાણને પ્રોત્સાહન મળી શકે છે."
    m = re.match(r"Dasha lord (\w+) activates supportive house (\d+)", t)
    if m: return f"દશા સ્વામી {_p(m.group(1))} {_h(m.group(2))}ને સક્રિય કરે છે, તેથી આ સમયગાળામાં સંબંધિત શુભ વિષયો વધુ સક્રિય થઈ શકે છે."
    m = re.match(r"Mahadasha lord (\w+) activates supportive house (\d+)", t)
    if m: return f"મહાદશા સ્વામી {_p(m.group(1))} {_h(m.group(2))}ને સક્રિય કરે છે; આ સમયગાળો સંબંધિત ક્ષેત્રોમાં સહાયક બની શકે છે."
    m = re.match(r"Antardasha lord (\w+) activates supportive house (\d+)", t)
    if m: return f"અંતર્દશા સ્વામી {_p(m.group(1))} {_h(m.group(2))}ને સક્રિય કરે છે; તેથી તે ક્ષેત્રના પરિણામો વધુ સ્પષ્ટ થઈ શકે છે."
    m = re.match(r"(Mahadasha|Antardasha) lord (\w+) activates house (\d+)", t)
    if m:
        label = "મહાદશા" if m.group(1)=="Mahadasha" else "અંતર્દશા"
        return f"{label} સ્વામી {_p(m.group(2))} {_h(m.group(3))}ને સક્રિય કરે છે; આ ભાવના વિષયો સાથે જોડાયેલા અનુભવ વધે શકે છે."
    m = re.match(r"Jupiter transit is supportive from the Lagna \(house (\d+)\)", t)
    if m: return f"વર્ષ દરમિયાન ગુરુનો ગોચર લગ્નથી {_h(m.group(1))}માં હોવાથી કારકિર્દી, શિક્ષણ અને વૃદ્ધિ માટે સહાયક વલણ દર્શાવે છે."
    m = re.match(r"Jupiter transit is more reflective from the Lagna \(house (\d+)\)", t)
    if m: return f"વર્ષ દરમિયાન ગુરુનો ગોચર લગ્નથી {_h(m.group(1))}માં હોવાથી પરિણામો મેળવવા પહેલાં આંતરિક સમીક્ષા અને ધીરજની જરૂર પડી શકે છે."
    m = re.match(r"Saturn transit emphasizes effort/results through house (\d+)", t)
    if m: return f"શનિનો ગોચર {_h(m.group(1))}ને સક્રિય કરે છે; મહેનત, શિસ્ત અને લાંબા ગાળાના પરિણામો પર ભાર રહે છે."
    m = re.match(r"Saturn transit emphasizes restructuring through house (\d+)", t)
    if m: return f"શનિનો ગોચર {_h(m.group(1))}માં હોવાથી પુનર્ગઠન, જવાબદારી અને ધીરજની જરૂરિયાત વધી શકે છે."
    m = re.match(r"Saturn is in Sade Sati (Phase [123]) relative to natal Moon", t)
    if m: return f"જન્મ ચંદ્રની તુલનામાં શનિ સાડેસાતીના {m.group(1).replace('Phase','તબક્કા')}માં છે; તેથી જવાબદારી અને માનસિક દબાણ જેવા વિષયો પર વધુ ધ્યાન આપવું યોગ્ય છે."
    if t == "No Manglik indication from the Lagna under the commonly used rule.":
        return "પ્રચલિત લગ્ન આધારિત નિયમ મુજબ મંગળ દોષનો સંકેત મળતો નથી."
    if t == "Manglik indication is present from the Lagna under the commonly used rule.":
        return "પ્રચલિત લગ્ન આધારિત નિયમ મુજબ મંગળ દોષનો સંકેત હાજર છે; સંપૂર્ણ નિર્ણય માટે અન્ય સમતોલક પરિબળો પણ જોવાના રહે છે."
    m = re.match(r"(\w+) is (exalted|debilitated|own sign) in (\w+)", t)
    if m:
        dignity = {"exalted":"ઉચ્ચ", "debilitated":"નીચ", "own sign":"સ્વરાશિ"}.get(m.group(2),m.group(2))
        return f"{_p(m.group(1))} {_s(m.group(3))}માં {dignity} સ્થિતિમાં છે, જે તેની કાર્યક્ષમતા પર મહત્વપૂર્ણ અસર કરે છે."
    m = re.match(r"(\w+) is retrograde", t)
    if m: return f"{_p(m.group(1))} વક્રી હોવાથી તેના કારકત્વમાં આંતરિકતા, પુનર્વિચાર અથવા અસામાન્ય અભિવ્યક્તિ જોવા મળી શકે છે."
    if t == "Kendra and Trikona lords have a conjunction or 7th-house relationship.": return "કેન્દ્ર અને ત્રિકોણ ભાવોના સ્વામીઓ વચ્ચે યુતિ અથવા પરસ્પર સાતમી દૃષ્ટિનો સંબંધ છે."
    if t == "The 9th and 10th lords are connected.": return "નવમ અને દશમ ભાવના સ્વામીઓ વચ્ચે સંબંધ હોવાથી ધર્મ અને કર્મના ક્ષેત્રો વચ્ચે જોડાણ બને છે."
    if t == "Wealth-related house lords have supportive connections.": return "ધન સંબંધિત ભાવોના સ્વામીઓ વચ્ચે સહાયક સંબંધ હોવાથી આવક અને સંપત્તિ માટે સકારાત્મક સંકેત મળે છે."
    if t.startswith("Jupiter is in a Kendra from the Moon"):
        return "ચંદ્રથી ગુરુ કેન્દ્રમાં હોવાથી ગજકેસરી યોગનો સંકેત મળે છે; તેની વાસ્તવિક શક્તિ ગ્રહબળ અને પીડા પર આધારિત છે."
    if t.startswith("Sun and Mercury occupy the same house/sign"):
        return "સૂર્ય અને બુધ એક જ ભાવ/રાશિમાં હોવાથી બુધાદિત્ય યોગનો સંકેત મળે છે; દહન અને ગ્રહબળ પણ જોવું જરૂરી છે."
    if t == "A dusthana lord is placed in another dusthana.": return "દુષ્ઠાન ભાવના સ્વામીનો અન્ય દુષ્ઠાન ભાવમાં સ્થાન હોવાથી વિપરીત રાજયોગનો સંકેત બને છે."
    if "is in debilitation" in t:
        names = [x.strip() for x in t.split(" is in debilitation")[0].split(",")]
        return "આ ગ્રહ નીચ રાશિમાં છે; સંપૂર્ણ પરિણામ માટે નીચભંગ જેવા પરિબળોનું વિશ્લેષણ જરૂરી છે."
    # Safe fallback: still keep it fully Gujarati rather than leaking English.
    return "આ નિયમ કુંડળીના સંબંધિત ગ્રહ/ભાવની સ્થિતિને ધ્યાનમાં રાખીને આ ક્ષેત્રમાં વધારાનો સંકેત આપે છે."

def _gu_reason_list(reasons, limit=8):
    out=[]
    for r in (reasons or [])[:limit]:
        text = r.get("text", r) if isinstance(r, dict) else r
        out.append(_translate_reason(text))
    return out

def _traits_text(traits):
    vals=[TRAIT_GU.get(x, x) for x in (traits or [])]
    return ", ".join(vals) if vals else "વિશેષ લક્ષણો માટે પૂરતો નિયમ આધાર મળ્યો નથી."

def _domains_text(domains):
    vals=[DOMAIN_GU.get(x, x) for x in (domains or [])]
    return ", ".join(vals) if vals else "વિશિષ્ટ કારકિર્દી ક્ષેત્રો માટે પૂરતો સંકેત મળ્યો નથી."

def _yoga_gujarati(y):
    names={
        "Raja Yoga connection":"રાજયોગ સંકેત", "Dharma-Karmadhipati Yoga":"ધર્મ-કર્માધિપતિ યોગ",
        "Dhana Yoga connection":"ધન યોગ સંકેત", "Gaja Kesari Yoga":"ગજકેસરી યોગ",
        "Budha-Aditya Yoga":"બુધાદિત્ય યોગ", "Vipareeta Raja Yoga indication":"વિપરીત રાજયોગ સંકેત",
        "Neecha placement":"નીચ ગ્રહસ્થિતિ"
    }
    return names.get(y.get("name"), y.get("name","યોગ")), STRENGTH_GU.get(y.get("strength"), y.get("strength","")), _translate_reason(y.get("reason",""))

def _prediction_report_gujarati(pred, name=""):
    lines=[]
    overall=float(pred.get("overall_score",0))
    lines += ["\n---\n", "# 🔮 સંપૂર્ણ નિયમ આધારિત વૈદિક જ્યોતિષ વિશ્લેષણ", "",
              "> **મહત્વપૂર્ણ નોંધ:** આ અહેવાલ પરંપરાગત વૈદિક જ્યોતિષના સ્પષ્ટ નિયમો, ગ્રહસ્થિતિ, ભાવસંબંધો, દશા અને ગોચર પરથી બનાવવામાં આવે છે. આ વૈજ્ઞાનિક રીતે માન્ય આગાહી નથી અને તબીબી, કાનૂની અથવા નાણાકીય નિર્ણય માટે તેનો વિકલ્પ તરીકે ઉપયોગ ન કરવો.", "",
              f"## 🌟 સમગ્ર કુંડળીનું મૂલ્યાંકન — {overall:.1f}/100 ({STATUS_GU.get('Highly supportive' if overall>=80 else 'Favorable' if overall>=65 else 'Mixed / manageable' if overall>=50 else 'Needs caution' if overall>=35 else 'Challenging')})",
              _score_sentence(overall), ""]
    for key in ["personality","intelligence","education","career","wealth","relationships","foreign","vitality"]:
        item=pred.get("areas",{}).get(key,{})
        score=float(item.get("score",0))
        title, desc=AREA_META[key]
        status = "ખૂબ અનુકૂળ" if score>=80 else "અનુકૂળ" if score>=65 else "મિશ્ર" if score>=50 else "સાવચેતી જરૂરી" if score>=35 else "પડકારજનક"
        lines += [f"## {title} — {score:.1f}/100 ({status})", desc, _score_sentence(score)]
        if key=="personality": lines.append(f"**મુખ્ય ગુણધર્મો:** {_traits_text(item.get('traits'))}")
        if key=="career": lines.append(f"**સંભવિત કારકિર્દી ક્ષેત્રો:** {_domains_text(item.get('domains'))}")
        rs=_gu_reason_list(item.get("reasons"), 8)
        if rs:
            lines.append("**નિયમ આધારિત કારણો:**")
            lines.extend([f"- {x}" for x in rs])
        lines.append("")

    lines += ["## 🧿 મહત્વપૂર્ણ યોગ અને ગ્રહયોગ", ""]
    if pred.get("yogas"):
        for y in pred["yogas"]:
            n,s,r=_yoga_gujarati(y)
            lines.append(f"### {n} — {s}")
            lines.append(r)
            lines.append("")
    else:
        lines.append("વર્તમાન નિયમ સમૂહ મુજબ કોઈ મુખ્ય યોગ મળ્યો નથી.")
        lines.append("")

    m=pred.get("manglik",{})
    lines += ["## 🔴 મંગળ દોષ વિશ્લેષણ", f"**સ્થિતિ:** {'મંગળ દોષનો સંકેત છે' if m.get('present') else 'મંગળ દોષનો સંકેત નથી'}"]
    if m.get("mars_house"):
        lines.append(f"**મંગળનું ભાવસ્થાન:** {_h(m['mars_house'])}")
    lines.append(_translate_reason(m.get("reason","")))
    lines.append("")

    lines += ["## 🕉️ વર્તમાન વિંશોત્તરી દશા", ""]
    d=pred.get("active_dasha")
    if d:
        lines.append(f"**મહાદશા:** {_p(d.get('Mahadasha'))}")
        lines.append(f"**અંતર્દશા:** {_p(d.get('Antardasha'))}")
        lines.append(f"**સમયગાળો:** {d['Start'].strftime('%d-%m-%Y')} થી {d['End'].strftime('%d-%m-%Y')}")
        rs=_gu_reason_list(pred.get("dasha_reasons"), 8)
        if rs:
            lines.append("**દશા આધારિત સંકેતો:**")
            lines.extend([f"- {x}" for x in rs])
    else:
        lines.append("વર્તમાન દશા ઓળખી શકાઈ નથી.")
    lines.append("")

    lines += ["## 📅 11 વર્ષનું નિયમ આધારિત ટ્રેન્ડ", "", "આ ટ્રેન્ડ વિંશોત્તરી દશા તથા 1 જુલાઈના આસપાસના ગુરુ-શનિ ગોચર પરથી બને છે. તે ચોક્કસ ઘટના બનવાની ખાતરી નથી.", ""]
    for yr in pred.get("annual",[]):
        s=yr.get("scores",{})
        lines.append(f"### {yr.get('year')} — કારકિર્દી {s.get('career',0):.0f} | ધન {s.get('wealth',0):.0f} | શિક્ષણ {s.get('education',0):.0f} | સંબંધો {s.get('relationships',0):.0f}")
        for r in _gu_reason_list(yr.get("reasons"), 4): lines.append(f"- {r}")
        ad=yr.get("active_dasha")
        if ad: lines.append(f"- દશા સંદર્ભ: {_p(ad.get('Mahadasha'))}/{_p(ad.get('Antardasha'))}")
        lines.append("")

    lines += ["## 🪐 ગ્રહબળનું અર્થઘટન", ""]
    for row in pred.get("planet_strengths",[]):
        p=_p(row.get("Planet")); dignity={"exalted":"ઉચ્ચ", "debilitated":"નીચ", "own sign":"સ્વરાશિ", "neutral":"સામાન્ય", "node":"છાયા ગ્રહ"}.get(row.get("Dignity"), row.get("Dignity",""))
        func={"Supportive":"સહાયક", "Challenging":"પડકારજનક", "Mixed":"મિશ્ર"}.get(row.get("Functional"), row.get("Functional",""))
        notes=_translate_reason(row.get("Notes","")) if row.get("Notes") else "વિશેષ નોંધ નથી."
        lines.append(f"- **{p}:** બળ {row.get('Strength',0):.1f}/100 | {dignity} | {_h(row.get('House'))} | કાર્યાત્મક સ્વભાવ: {func}. {notes}")
    lines.append("")

    lines += ["## 🧭 સ્કોર કેવી રીતે વાંચવો", "", "- **80+**: ખૂબ મજબૂત સહાયક સંકેત.", "- **65–79**: અનુકૂળ સંકેત.", "- **50–64**: મિશ્ર પરંતુ સંભાળી શકાય તેવું.", "- **35–49**: વધુ મહેનત અને સાવચેતી જરૂરી.", "- **35થી નીચે**: પડકારજનક સંકેત.", "", "**સ્કોર કોઈ ઘટના બનવાની ખાતરી નથી આપતો; તે માત્ર આ નિયમ આધારિત મોડેલમાં ગ્રહ-ભાવ સંબંધોનું પ્રમાણ દર્શાવે છે.**"]
    return "\n".join(lines)


def make_prediction_dataframe_gujarati(pred):
    labels={
        "personality":"સ્વભાવ અને વ્યક્તિત્વ", "intelligence":"બુદ્ધિ અને શીખવાની ક્ષમતા", "education":"શિક્ષણ",
        "career":"કારકિર્દી", "wealth":"ધન અને આવક", "relationships":"લગ્ન અને સંબંધો",
        "foreign":"વિદેશ / સ્થળાંતર", "vitality":"જીવનશક્તિ / રૂટિન"
    }
    rows=[]
    for key,label in labels.items():
        score=float(pred.get("areas",{}).get(key,{}).get("score",0))
        rows.append({"ક્ષેત્ર":label,"સ્કોર":round(score,1),"મૂલ્યાંકન":"ખૂબ અનુકૂળ" if score>=80 else "અનુકૂળ" if score>=65 else "મિશ્ર" if score>=50 else "સાવચેતી જરૂરી" if score>=35 else "પડકારજનક"})
    return rows
