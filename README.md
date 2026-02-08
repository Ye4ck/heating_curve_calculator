# Heating Curve Calculator for Home Assistant

[English](#english) | [Deutsch](#deutsch)

---

## English

A Home Assistant custom integration for calculating optimal flow temperature based on outdoor temperature using a heating curve with hysteresis.

### Features

- 🌡️ **Dynamic Flow Temperature Calculation** - Automatically calculates optimal flow temperature based on outdoor conditions
- 📊 **Two Calculation Modes**:
  - Classic mode (based on target room temperature)
  - Room temperature feedback mode (uses actual room temperature)
- 🎚️ **Fully Adjustable Parameters** - All parameters can be adjusted via Number and Select entities
- 🔄 **Hysteresis Support** - Prevents frequent temperature changes and reduces wear on heating system
- 🎛️ **Real-time Updates** - Changes take effect immediately without restarting
- 🌐 **Multi-language Support** - English and German translations included

### Installation

#### Manual Installation

1. Copy the `custom_components/heating_curve` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services → Add Integration → "Heating Curve Calculator"

### Configuration

#### Initial Setup

During setup, you only need to configure:

- **Name** - A friendly name for your heating curve
- **Outdoor Temperature Sensor** - Your outdoor temperature sensor (required)
- **Room Temperature Sensor** - Optional sensor for room temperature feedback

#### Adjustable Parameters (Number Entities)

All heating parameters can be adjusted anytime via the created Number entities:

| Entity | Description | Range | Default | Unit |
|--------|-------------|-------|---------|------|
| Curve Slope | Steepness of the heating curve | 0.1 - 5.0 | 1.4 | - |
| Curve Level | Parallel shift of the heating curve | -20.0 - 20.0 | 0.0 | °C |
| Target Room Temperature | Desired room temperature | 15.0 - 25.0 | 20.0 | °C |
| Min Flow Temperature | Minimum flow temperature | 15.0 - 50.0 | 20.0 | °C |
| Max Flow Temperature | Maximum flow temperature | 40.0 - 90.0 | 75.0 | °C |
| Hysteresis | Temperature change threshold | 0.0 - 5.0 | 1.0 | °C |

#### Calculation Mode (Select Entity)

- **Classic** - Uses target room temperature for calculation
- **With Room Temperature** - Uses actual room temperature (requires room sensor)

### How It Works

#### Heating Curve Formula

**Classic Mode:**
```
T_flow = T_room_target + slope × (T_room_target - T_outdoor) + level
```

**With Room Temperature Mode:**
```
T_flow = T_room_target + slope × (T_room_actual - T_outdoor) + level
```

The result is clamped between min and max flow temperature.

#### Hysteresis

Hysteresis prevents the flow temperature from changing too frequently:

- The calculated flow temperature only changes when the difference exceeds the hysteresis value
- Example with 1.0°C hysteresis:
  - Current: 45.0°C, Calculated: 45.5°C → **No change** (< 1.0°C difference)
  - Current: 45.0°C, Calculated: 46.2°C → **Change to 46.2°C** (≥ 1.0°C difference)

**Benefits:**
- Reduces heating system on/off cycles
- Extends equipment lifetime
- More stable heating behavior
- Lower energy consumption

**Recommended Settings:**
- Underfloor heating: 0.5-1.0°C (slow response system)
- Radiators: 1.0-1.5°C (faster response system)
- Unstable sensors: 1.5-2.0°C

### Entities

The integration creates the following entities:

#### Sensor
- `sensor.[name]_vorlauftemperatur` - Calculated flow temperature

#### Number Entities
- `number.[name]_heizkurven_steilheit` - Curve Slope
- `number.[name]_heizkurven_niveau` - Curve Level
- `number.[name]_raum_solltemperatur` - Target Room Temperature
- `number.[name]_min_vorlauftemperatur` - Min Flow Temperature
- `number.[name]_max_vorlauftemperatur` - Max Flow Temperature
- `number.[name]_hysterese` - Hysteresis

#### Select Entity
- `select.[name]_berechnungsmodus` - Calculation Mode

### Sensor Attributes

The flow temperature sensor provides additional attributes:

```yaml
outdoor_temperature: 5.2
room_temperature_actual: 21.3  # if room sensor configured
curve_slope: 1.4
curve_level: 0.0
room_temperature_target: 20.0
min_flow_temperature: 20.0
max_flow_temperature: 75.0
calculation_mode: classic
hysteresis: 1.0
outdoor_sensor: sensor.outdoor_temp
room_sensor: sensor.living_room_temp  # if configured
```

### Example Automation

```yaml
automation:
  - alias: "Adjust heating curve in winter"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temp
        below: 0
    action:
      - service: number.set_value
        target:
          entity_id: number.heating_curve_curve_slope
        data:
          value: 1.6
```

### Support

- 🐛 [Report Issues](https://github.com/Ye4ck/heating_curve_calculator/issues)

---

## Deutsch

Eine Home Assistant Custom Integration zur Berechnung der optimalen Vorlauftemperatur basierend auf der Außentemperatur mittels einer Heizkurve mit Hysterese.

### Funktionen

- 🌡️ **Dynamische Vorlauftemperatur-Berechnung** - Berechnet automatisch die optimale Vorlauftemperatur basierend auf den Außenbedingungen
- 📊 **Zwei Berechnungsmodi**:
  - Klassischer Modus (basierend auf Raum-Solltemperatur)
  - Raumtemperatur-Rückkopplungs-Modus (verwendet tatsächliche Raumtemperatur)
- 🎚️ **Vollständig anpassbare Parameter** - Alle Parameter können über Number- und Select-Entitäten angepasst werden
- 🔄 **Hysterese-Unterstützung** - Verhindert häufige Temperaturänderungen und reduziert Verschleiß der Heizungsanlage
- 🎛️ **Echtzeit-Updates** - Änderungen wirken sofort ohne Neustart
- 🌐 **Mehrsprachige Unterstützung** - Englische und deutsche Übersetzungen enthalten

### Installation

#### Manuelle Installation

1. Kopiere den Ordner `custom_components/heating_curve` in dein Home Assistant `custom_components` Verzeichnis
2. Starte Home Assistant neu
3. Füge die Integration über Einstellungen → Geräte & Dienste → Integration hinzufügen → "Heating Curve Calculator" hinzu

### Konfiguration

#### Ersteinrichtung

Bei der Einrichtung musst du nur konfigurieren:

- **Name** - Ein freundlicher Name für deine Heizkurve
- **Außentemperatur-Sensor** - Dein Außentemperatursensor (erforderlich)
- **Raumtemperatur-Sensor** - Optionaler Sensor für Raumtemperatur-Rückkopplung

#### Anpassbare Parameter (Number-Entitäten)

Alle Heizparameter können jederzeit über die erstellten Number-Entitäten angepasst werden:

| Entität | Beschreibung | Bereich | Standard | Einheit |
|---------|--------------|---------|----------|---------|
| Heizkurven-Steilheit | Steilheit der Heizkurve | 0.1 - 5.0 | 1.4 | - |
| Heizkurven-Niveau | Parallelverschiebung der Heizkurve | -20.0 - 20.0 | 0.0 | °C |
| Raum-Solltemperatur | Gewünschte Raumtemperatur | 15.0 - 25.0 | 20.0 | °C |
| Min. Vorlauftemperatur | Minimale Vorlauftemperatur | 15.0 - 50.0 | 20.0 | °C |
| Max. Vorlauftemperatur | Maximale Vorlauftemperatur | 40.0 - 90.0 | 75.0 | °C |
| Hysterese | Schwellwert für Temperaturänderung | 0.0 - 5.0 | 1.0 | °C |

#### Berechnungsmodus (Select-Entität)

- **Klassisch** - Verwendet Raum-Solltemperatur für Berechnung
- **Mit Raumtemperatur** - Verwendet tatsächliche Raumtemperatur (benötigt Raumsensor)

### Funktionsweise

#### Heizkurven-Formel

**Klassischer Modus:**
```
T_vorlauf = T_raum_soll + Steilheit × (T_raum_soll - T_außen) + Niveau
```

**Mit Raumtemperatur-Modus:**
```
T_vorlauf = T_raum_soll + Steilheit × (T_raum_ist - T_außen) + Niveau
```

Das Ergebnis wird zwischen minimaler und maximaler Vorlauftemperatur begrenzt.

#### Hysterese

Die Hysterese verhindert zu häufige Änderungen der Vorlauftemperatur:

- Die berechnete Vorlauftemperatur ändert sich nur, wenn die Differenz den Hysterese-Wert überschreitet
- Beispiel mit 1.0°C Hysterese:
  - Aktuell: 45.0°C, Berechnet: 45.5°C → **Keine Änderung** (< 1.0°C Differenz)
  - Aktuell: 45.0°C, Berechnet: 46.2°C → **Änderung auf 46.2°C** (≥ 1.0°C Differenz)

**Vorteile:**
- Reduziert Ein/Aus-Zyklen der Heizung
- Verlängert Lebensdauer der Komponenten
- Stabileres Heizverhalten
- Geringerer Energieverbrauch

**Empfohlene Einstellungen:**
- Fußbodenheizung: 0.5-1.0°C (träges System)
- Radiatoren: 1.0-1.5°C (schnelleres System)
- Instabile Sensoren: 1.5-2.0°C

### Entitäten

Die Integration erstellt folgende Entitäten:

#### Sensor
- `sensor.[name]_vorlauftemperatur` - Berechnete Vorlauftemperatur

#### Number-Entitäten
- `number.[name]_heizkurven_steilheit` - Heizkurven-Steilheit
- `number.[name]_heizkurven_niveau` - Heizkurven-Niveau
- `number.[name]_raum_solltemperatur` - Raum-Solltemperatur
- `number.[name]_min_vorlauftemperatur` - Min. Vorlauftemperatur
- `number.[name]_max_vorlauftemperatur` - Max. Vorlauftemperatur
- `number.[name]_hysterese` - Hysterese

#### Select-Entität
- `select.[name]_berechnungsmodus` - Berechnungsmodus

### Sensor-Attribute

Der Vorlauftemperatur-Sensor bietet zusätzliche Attribute:

```yaml
outdoor_temperature: 5.2
room_temperature_actual: 21.3  # falls Raumsensor konfiguriert
curve_slope: 1.4
curve_level: 0.0
room_temperature_target: 20.0
min_flow_temperature: 20.0
max_flow_temperature: 75.0
calculation_mode: classic
hysteresis: 1.0
outdoor_sensor: sensor.outdoor_temp
room_sensor: sensor.living_room_temp  # falls konfiguriert
```

### Beispiel-Automatisierung

```yaml
automation:
  - alias: "Heizkurve im Winter anpassen"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temp
        below: 0
    action:
      - service: number.set_value
        target:
          entity_id: number.heating_curve_heizkurven_steilheit
        data:
          value: 1.6
```

### Support

- 🐛 [Probleme melden](https://github.com/Ye4ck/heating_curve_calculator/issues)

