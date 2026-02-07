# Heating Curve Calculator for Home Assistant

## Setup

1. Go to **Settings** → **Devices & Services**
2. Click on **+ Add Integration**
3. Search for **"Heating Curve Calculator"**
4. Follow the configuration wizard:
   - **Name**: Give your heating curve a name (e.g., "Living Room Heating")
   - **Outdoor Temperature Sensor**: Choose your outdoor temperature sensor
   - **Room Temperature Sensor** (optional): Only for the "With Room Temperature" mode
   - **Calculation Mode**: Choose between classic or with room temperature
   - **Heating Curve Slope**: Typically 0.4 - 2.0 (Default: 1.4)
   - **Heating Curve Level**: Parallel shift from -20 to +20°C (Default: 0)
   - **Room Desired Temperature**: Desired room temperature (Default: 20°C)
   - **Min/Max Flow Temperature**: Safety boundaries for the calculation

## Parameter Explanation

### Heating Curve Slope
- **Low Value (0.4-0.8)**: Flat curve, less change in flow temperature with outdoor temperature fluctuations
  - Good for well-insulated buildings or underfloor heating
- **Medium Value (1.0-1.5)**: Standard for typical radiators
- **High Value (1.6-2.5)**: Steep curve, strong response to outdoor temperature
  - For poorly insulated buildings or rapid heating

### Heating Curve Level (Parallel Shift)
- **Positive Value (+5°C)**: Shifts the entire curve upwards → higher flow temperatures
- **Negative Value (-5°C)**: Shifts the entire curve downwards → lower flow temperatures
- Useful for fine-tuning without changing the slope

### Example Calculations

With default settings (Slope: 1.4, Level: 0, Desired Temperature: 20°C):

| Outdoor Temperature | Calculation | Flow Temperature |
|---------------------|-------------|------------------|
| -10°C | 20 + 1.4 × (20 - (-10)) + 0 | **62°C** |
| 0°C   | 20 + 1.4 × (20 - 0) + 0     | **48°C** |
| 10°C  | 20 + 1.4 × (20 - 10) + 0    | **34°C** |
| 15°C  | 20 + 1.4 × (20 - 15) + 0    | **27°C** |




## Einrichtung

1. Gehe zu **Einstellungen** → **Geräte & Dienste**
2. Klicke auf **+ Integration hinzufügen**
3. Suche nach **"Heating Curve Calculator"**
4. Folge dem Konfigurationsassistenten:
   - **Name**: Gib deiner Heizkurve einen Namen (z.B. "Wohnzimmer Heizung")
   - **Außentemperatur Sensor**: Wähle deinen Außentemperatur-Sensor
   - **Raumtemperatur Sensor** (optional): Nur für Modus "Mit Raumtemperatur"
   - **Berechnungsmodus**: Wähle zwischen klassisch oder mit Raumtemperatur
   - **Heizkurven-Steilheit**: Typisch 0.4 - 2.0 (Standard: 1.4)
   - **Heizkurven-Niveau**: Parallelverschiebung -20 bis +20°C (Standard: 0)
   - **Raum-Solltemperatur**: Gewünschte Raumtemperatur (Standard: 20°C)
   - **Min/Max Vorlauftemperatur**: Sicherheitsgrenzen für die Berechnung

## Berechnungsmodi

### Modus 1: Klassisch (ohne Raumtemperatur)
```
T_Vorlauf = T_Raum-Soll + Steilheit × (T_Raum-Soll - T_Außen) + Niveau
```
Verwendet die Soll-Raumtemperatur für die Berechnung. Ideal für einfache Systeme ohne Raumtemperatur-Feedback.

### Modus 2: Mit Raumtemperatur-Rückkopplung
```
T_Vorlauf = T_Raum-Soll + Steilheit × (T_Raum-Ist - T_Außen) + Niveau
```
Verwendet die tatsächliche Raumtemperatur für die Berechnung. Passt sich dynamisch an tatsächliche Bedingungen an. **Benötigt einen Raumtemperatur-Sensor!**

## Parameter-Erklärung

### Heizkurven-Steilheit
- **Niedriger Wert (0.4-0.8)**: Flache Kurve, weniger Vorlauftemperatur-Änderung bei Außentemperatur-Schwankungen
  - Gut für gut isolierte Gebäude oder Fußbodenheizung
- **Mittlerer Wert (1.0-1.5)**: Standard für normale Heizkörper
- **Hoher Wert (1.6-2.5)**: Steile Kurve, starke Reaktion auf Außentemperatur
  - Für schlecht isolierte Gebäude oder schnelle Aufheizung

### Heizkurven-Niveau (Parallelverschiebung)
- **Positiver Wert (+5°C)**: Verschiebt die gesamte Kurve nach oben → höhere Vorlauftemperaturen
- **Negativer Wert (-5°C)**: Verschiebt die gesamte Kurve nach unten → niedrigere Vorlauftemperaturen
- Nützlich für Feinabstimmung ohne die Steilheit zu ändern

### Beispiel-Berechnungen

Mit Standard-Einstellungen (Steilheit: 1.4, Niveau: 0, Solltemperatur: 20°C):

| Außentemperatur | Berechnung | Vorlauftemperatur |
|-----------------|------------|-------------------|
| -10°C | 20 + 1.4 × (20 - (-10)) + 0 | **62°C** |
| 0°C | 20 + 1.4 × (20 - 0) + 0 | **48°C** |
| 10°C | 20 + 1.4 × (20 - 10) + 0 | **34°C** |
| 15°C | 20 + 1.4 × (20 - 15) + 0 | **27°C** |
