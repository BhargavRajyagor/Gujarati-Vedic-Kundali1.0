---
title: Gujarati Vedic Kundali — Complete Gujarati Interpretation
emoji: 🪔
colorFrom: purple
colorTo: blue
sdk: streamlit
app_file: streamlit_app.py
python_version: "3.11"
short_description: Gujarati Vedic Kundali with D1, D9, Dasha and predictions
---

# 🪔 Gujarati Vedic Kundali — Streamlit

Complete Streamlit edition of the Gujarati Vedic Kundali application.

## Included

- Interactive Gujarat birth-location map
- Gujarat location search with OpenStreetMap Nominatim
- Automatic timezone detection
- Swiss Ephemeris + Lahiri sidereal calculations
- Mean Rahu and Ketu opposite Rahu
- Whole-sign D1 houses
- North Indian D1 Rashi chart
- North Indian D9 Navamsa chart
- Gujarati planet, rashi and nakshatra labels
- Vimshottari Mahadasha / Antardasha
- Complete rule-based Gujarati interpretation
- Gujarati personality and nature interpretation
- Gujarati education interpretation
- Gujarati career and profession interpretation
- Gujarati wealth and income interpretation
- Gujarati marriage and relationship interpretation
- Gujarati foreign / relocation interpretation
- Gujarati vitality / lifestyle interpretation
- Gujarati Yoga interpretation
- Gujarati Manglik interpretation
- Gujarati Vimshottari Dasha interpretation
- Gujarati year-wise traditional trend analysis
- Gujarati planetary-strength interpretation
- Gujarati house-lord summary
- Gujarati score and assessment labels
- PNG, CSV, Markdown and PDF downloads
- Bundled Noto Sans Gujarati fonts for chart/PDF rendering

## Important fixes

- Offset-naive and offset-aware datetime values are normalized safely.
- Active Dasha always returns a normal Python dictionary, never a pandas Series.
- Annual Dasha checks use explicit `is not None` logic.
- `matplotlib.patches` is imported explicitly for North Indian charts.
- Gujarati fonts are bundled inside the project and used explicitly by Matplotlib and ReportLab.

## Disclaimer

This application provides traditional Jyotish interpretations. It is not a scientifically validated method of predicting future events and should not be used for medical, legal, financial, or other high-stakes decisions.
