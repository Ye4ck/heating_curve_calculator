const HC_STRINGS = {
  en: {
    entityRequired: "Please define an entity (the heating curve sensor).",
    entityNotFound: (entity) => `Entity not found: ${entity}`,
    defaultTitle: "Heating Curve",
    outdoor: "Outdoor",
    flow: "Flow",
    slope: "Slope",
    level: "Level",
    hysteresis: "Hysteresis",
    mode: "Mode",
    modeClassic: "Classic",
    modeRoomTemp: "Room temp.",
    pickerDescription:
      "Displays the Heating Curve Calculator's curve as a graph, including the current operating point and hysteresis band.",
    editorEntity: "Flow temperature sensor",
    editorTitle: "Card title",
    editorMinOutdoor: "Outdoor axis minimum (°C)",
    editorMaxOutdoor: "Outdoor axis maximum (°C)",
    editorStyleSection: "Style",
    editorCurveColor: "Curve color",
    editorPointColor: "Current point color",
    editorShowGrid: "Show grid lines",
  },
  de: {
    entityRequired: "Bitte eine Entität angeben (den Heizkurven-Sensor).",
    entityNotFound: (entity) => `Entität nicht gefunden: ${entity}`,
    defaultTitle: "Heizkurve",
    outdoor: "Außen",
    flow: "Vorlauf",
    slope: "Steilheit",
    level: "Niveau",
    hysteresis: "Hysterese",
    mode: "Modus",
    modeClassic: "Klassisch",
    modeRoomTemp: "Raumtemp.",
    pickerDescription:
      "Zeigt die Heizkurve des Heating Curve Calculator als Graph inkl. aktuellem Betriebspunkt und Hysterese-Band.",
    editorEntity: "Vorlauftemperatur-Sensor",
    editorTitle: "Titel der Card",
    editorMinOutdoor: "Außentemp.-Achse Minimum (°C)",
    editorMaxOutdoor: "Außentemp.-Achse Maximum (°C)",
    editorStyleSection: "Stil",
    editorCurveColor: "Kurvenfarbe",
    editorPointColor: "Farbe aktueller Punkt",
    editorShowGrid: "Gitterlinien anzeigen",
  },
};

// Determine the active language from Home Assistant's own configured
// language, not the browser/OS locale (navigator.language) - a user can
// easily have HA set to English while their device is set to German, or
// vice versa, and the card should follow HA's setting.
function hcGetLang(hass) {
  const lang =
    (hass && (hass.language || (hass.locale && hass.locale.language))) ||
    (typeof document !== "undefined" && document.documentElement && document.documentElement.lang) ||
    (typeof navigator !== "undefined" && navigator.language) ||
    "en";
  return String(lang).toLowerCase().startsWith("de") ? "de" : "en";
}

function hcT(hass) {
  return HC_STRINGS[hcGetLang(hass)];
}

// Absolute temperature: full °C -> °F formula (with offset)
function hcToDisplayAbs(value, unit) {
  if (value == null) return null;
  return unit === "°F" ? (value * 9) / 5 + 32 : value;
}

// Inverse of hcToDisplayAbs: HA already converts the primary sensor state
// to the display unit automatically (device_class temperature); we need it
// back in °C to keep it consistent with the attrs (which stay raw °C).
function hcFromDisplayAbs(value, unit) {
  if (value == null) return null;
  return unit === "°F" ? ((value - 32) * 5) / 9 : value;
}

class HeatingCurveCard extends HTMLElement {
  setConfig(config) {
    const t = hcT(this._hass);
    if (!config.entity) {
      throw new Error(t.entityRequired);
    }
    this._config = {
      title: t.defaultTitle,
      min_outdoor: -20,
      max_outdoor: 20,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    const t = hcT(hass);
    const stateObj = hass.states[this._config.entity];

    if (!stateObj) {
      this._renderError(t.entityNotFound(this._config.entity));
      return;
    }

    if (!this._content) {
      this._buildCard();
    }

    this._updateCard(stateObj);
  }

  _renderError(message) {
    this.innerHTML = `
      <ha-card>
        <div style="padding:16px;color:var(--error-color, red);">${message}</div>
      </ha-card>
    `;
  }

  _buildCard() {
    this.innerHTML = `
      <ha-card>
        <div class="card-header" style="font-size:1.1em;font-weight:500;padding:12px 16px 0 16px;">
          ${this._config.title}
        </div>
        <div class="card-content" style="padding:8px 16px 16px 16px;">
          <svg id="hc-svg" viewBox="0 0 400 240" style="width:100%;height:auto;overflow:visible;font-family:var(--paper-font-body1_-_font-family, sans-serif);">
          </svg>
          <div id="hc-legend" style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-top:8px;font-size:0.85em;color:var(--secondary-text-color);"></div>
        </div>
      </ha-card>
    `;
    this._svg = this.querySelector("#hc-svg");
    this._legend = this.querySelector("#hc-legend");
    this._content = true;
  }

  _calcFlow(outdoor, target, slope, level, minFlow, maxFlow, refTemp) {
    const diff = refTemp - outdoor;
    let flow = target + slope * diff + level;
    flow = Math.max(minFlow, Math.min(maxFlow, flow));
    return flow;
  }

  _updateCard(stateObj) {
    const t = hcT(this._hass);
    const attrs = stateObj.attributes || {};
    const displayUnit = attrs.display_unit || "°C";
    const slope = Number(attrs.curve_slope ?? 1.4);
    const level = Number(attrs.curve_level ?? 0.0);
    const target = Number(attrs.room_temperature_target ?? 20.0);
    const minFlow = Number(attrs.min_flow_temperature ?? 20.0);
    const maxFlow = Number(attrs.max_flow_temperature ?? 75.0);
    const hysteresis = Number(attrs.hysteresis ?? 1.0);
    const mode = attrs.calculation_mode ?? "classic";
    const outdoorNow = attrs.outdoor_temperature;
    const roomActual = attrs.room_temperature_actual;
    // stateObj.state is already converted to displayUnit by HA (device_class
    // temperature) - normalize back to °C so it's consistent with the attrs,
    // which always stay in raw °C internally.
    const flowNowRaw =
      stateObj.state !== "unknown" && stateObj.state !== "unavailable"
        ? Number(stateObj.state)
        : null;
    const flowNow = hcFromDisplayAbs(flowNowRaw, displayUnit);

    const refTemp =
      mode === "with_room_temp" && roomActual != null ? Number(roomActual) : target;

    const minX = this._config.min_outdoor;
    const maxX = this._config.max_outdoor;
    const minY = Math.min(minFlow, 15);
    const maxY = Math.max(maxFlow, 45);

    const padL = 34;
    const padB = 22;
    const padT = 10;
    const padR = 10;
    const w = 400 - padL - padR;
    const h = 240 - padT - padB;

    const xToPx = (x) => padL + ((x - minX) / (maxX - minX)) * w;
    const yToPx = (y) => padT + h - ((y - minY) / (maxY - minY)) * h;

    const steps = 40;
    let d = "";
    for (let i = 0; i <= steps; i++) {
      const outdoor = minX + ((maxX - minX) * i) / steps;
      const flow = this._calcFlow(outdoor, target, slope, level, minFlow, maxFlow, refTemp);
      const px = xToPx(outdoor);
      const py = yToPx(flow);
      d += i === 0 ? `M ${px} ${py}` : ` L ${px} ${py}`;
    }

    const gridColor = "var(--divider-color, #ccc)";
    const axisColor = "var(--secondary-text-color, #888)";
    const curveColor = this._config.curve_color
      ? `rgb(${this._config.curve_color.join(",")})`
      : "var(--primary-color, #03a9f4)";
    const pointColor = this._config.point_color
      ? `rgb(${this._config.point_color.join(",")})`
      : "var(--state-active-color, var(--primary-color, #ff9800))";
    const showGrid = this._config.show_grid !== false;

    let svg = "";

    if (showGrid) {
      for (let gx = Math.ceil(minX / 5) * 5; gx <= maxX; gx += 5) {
        const px = xToPx(gx);
        const label = Math.round(hcToDisplayAbs(gx, displayUnit));
        svg += `<line x1="${px}" y1="${padT}" x2="${px}" y2="${padT + h}" stroke="${gridColor}" stroke-width="0.5" />`;
        svg += `<text x="${px}" y="${padT + h + 14}" font-size="9" fill="${axisColor}" text-anchor="middle">${label}°</text>`;
      }
      const yTicks = 4;
      for (let i = 0; i <= yTicks; i++) {
        const gy = minY + ((maxY - minY) * i) / yTicks;
        const py = yToPx(gy);
        const label = Math.round(hcToDisplayAbs(gy, displayUnit));
        svg += `<line x1="${padL}" y1="${py}" x2="${padL + w}" y2="${py}" stroke="${gridColor}" stroke-width="0.5" />`;
        svg += `<text x="${padL - 6}" y="${py + 3}" font-size="9" fill="${axisColor}" text-anchor="end">${label}°</text>`;
      }
    }

    svg += `<line x1="${padL}" y1="${yToPx(minFlow)}" x2="${padL + w}" y2="${yToPx(minFlow)}" stroke="${axisColor}" stroke-dasharray="3,3" stroke-width="0.75" />`;
    svg += `<line x1="${padL}" y1="${yToPx(maxFlow)}" x2="${padL + w}" y2="${yToPx(maxFlow)}" stroke="${axisColor}" stroke-dasharray="3,3" stroke-width="0.75" />`;

    svg += `<path d="${d}" fill="none" stroke="${curveColor}" stroke-width="2.5" stroke-linecap="round" />`;

    if (outdoorNow != null && flowNow != null) {
      const outdoorClamped = Math.max(minX, Math.min(maxX, Number(outdoorNow)));
      const cx = xToPx(outdoorClamped);
      const cy = yToPx(flowNow);
      const bandTop = yToPx(Math.min(maxFlow, flowNow + hysteresis));
      const bandBottom = yToPx(Math.max(minFlow, flowNow - hysteresis));
      const flowNowDisplay = hcToDisplayAbs(flowNow, displayUnit);
      svg += `<rect x="${cx - 5}" y="${bandTop}" width="10" height="${bandBottom - bandTop}" fill="${pointColor}" opacity="0.15" />`;
      svg += `<circle cx="${cx}" cy="${cy}" r="5" fill="${pointColor}" stroke="var(--card-background-color, white)" stroke-width="1.5" />`;
      svg += `<text x="${cx}" y="${cy - 10}" font-size="10" fill="${pointColor}" text-anchor="middle" font-weight="600">${flowNowDisplay.toFixed(1)}${displayUnit}</text>`;
    }

    svg += `<line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + h}" stroke="${axisColor}" stroke-width="1" />`;
    svg += `<line x1="${padL}" y1="${padT + h}" x2="${padL + w}" y2="${padT + h}" stroke="${axisColor}" stroke-width="1" />`;

    this._svg.innerHTML = svg;

    this._legend.innerHTML = `
      <span>${t.outdoor}: <b>${outdoorNow != null ? hcToDisplayAbs(Number(outdoorNow), displayUnit).toFixed(1) + displayUnit : "–"}</b></span>
      <span>${t.flow}: <b>${flowNow != null ? hcToDisplayAbs(flowNow, displayUnit).toFixed(1) + displayUnit : "–"}</b></span>
      <span>${t.slope}: <b>${slope}</b></span>
      <span>${t.level}: <b>${level.toFixed(1)} K</b></span>
      <span>${t.hysteresis}: <b>${hysteresis.toFixed(1)} K</b></span>
      <span>${t.mode}: <b>${mode === "with_room_temp" ? t.modeRoomTemp : t.modeClassic}</b></span>
    `;
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("heating-curve-card-editor");
  }

  static getStubConfig(hass) {
    const t = hcT(hass);
    const entities = Object.keys(hass.states).filter((e) =>
      e.startsWith("sensor.") && e.includes("vorlauftemperatur")
    );
    return { entity: entities[0] || "", title: t.defaultTitle };
  }
}

class HeatingCurveCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  get _schema() {
    const t = hcT(this._hass);
    return [
      { name: "entity", selector: { entity: { domain: "sensor" } } },
      { name: "title", selector: { text: {} } },
      { name: "min_outdoor", selector: { number: { mode: "box", step: 1 } } },
      { name: "max_outdoor", selector: { number: { mode: "box", step: 1 } } },
      {
        type: "expandable",
        name: "style_section",
        title: t.editorStyleSection,
        iconPath:
          "M20.71,5.63L19.37,4.29C19,3.9 18.35,3.9 17.96,4.29L9,13.25L10.75,15L19.71,6.04C20.1,5.65 20.1,5 20.71,5.63M7,14A3,3 0 0,0 4,17C4,18.31 2.84,19 2,19C2.92,20.22 4.5,21 6,21A4,4 0 0,0 10,17A3,3 0 0,0 7,14Z",
        flatten: true,
        schema: [
          { name: "curve_color", selector: { color_rgb: {} } },
          { name: "point_color", selector: { color_rgb: {} } },
          { name: "show_grid", selector: { boolean: {} } },
        ],
      },
    ];
  }

  _computeLabel = (schema) => {
    const t = hcT(this._hass);
    const labels = {
      entity: t.editorEntity,
      title: t.editorTitle,
      min_outdoor: t.editorMinOutdoor,
      max_outdoor: t.editorMaxOutdoor,
      curve_color: t.editorCurveColor,
      point_color: t.editorPointColor,
      show_grid: t.editorShowGrid,
    };
    return labels[schema.name] || schema.name;
  };

  _render() {
    if (!this._hass || !this._config) {
      return;
    }

    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        ev.stopPropagation();
        const newConfig = ev.detail.value;
        this._config = newConfig;
        this.dispatchEvent(
          new CustomEvent("config-changed", {
            detail: { config: newConfig },
            bubbles: true,
            composed: true,
          })
        );
      });
      this.appendChild(this._form);
    }

    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = this._schema;
    this._form.computeLabel = this._computeLabel;
  }
}

customElements.define("heating-curve-card-editor", HeatingCurveCardEditor);

customElements.define("heating-curve-card", HeatingCurveCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "heating-curve-card",
  name: "Heating Curve Card",
  description: hcT().pickerDescription,
});
