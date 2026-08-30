const HC_LANG = (navigator.language || "en").toLowerCase().startsWith("de") ? "de" : "en";

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
  },
};

const t = HC_STRINGS[HC_LANG];

class HeatingCurveCard extends HTMLElement {
  setConfig(config) {
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
    const attrs = stateObj.attributes || {};
    const slope = Number(attrs.curve_slope ?? 1.4);
    const level = Number(attrs.curve_level ?? 0.0);
    const target = Number(attrs.room_temperature_target ?? 20.0);
    const minFlow = Number(attrs.min_flow_temperature ?? 20.0);
    const maxFlow = Number(attrs.max_flow_temperature ?? 75.0);
    const hysteresis = Number(attrs.hysteresis ?? 1.0);
    const mode = attrs.calculation_mode ?? "classic";
    const outdoorNow = attrs.outdoor_temperature;
    const roomActual = attrs.room_temperature_actual;
    const flowNow =
      stateObj.state !== "unknown" && stateObj.state !== "unavailable"
        ? Number(stateObj.state)
        : null;

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
    const curveColor = "var(--primary-color, #03a9f4)";
    const pointColor = "var(--state-active-color, var(--primary-color, #ff9800))";

    let svg = "";

    for (let gx = Math.ceil(minX / 5) * 5; gx <= maxX; gx += 5) {
      const px = xToPx(gx);
      svg += `<line x1="${px}" y1="${padT}" x2="${px}" y2="${padT + h}" stroke="${gridColor}" stroke-width="0.5" />`;
      svg += `<text x="${px}" y="${padT + h + 14}" font-size="9" fill="${axisColor}" text-anchor="middle">${gx}°</text>`;
    }
    const yTicks = 4;
    for (let i = 0; i <= yTicks; i++) {
      const gy = minY + ((maxY - minY) * i) / yTicks;
      const py = yToPx(gy);
      svg += `<line x1="${padL}" y1="${py}" x2="${padL + w}" y2="${py}" stroke="${gridColor}" stroke-width="0.5" />`;
      svg += `<text x="${padL - 6}" y="${py + 3}" font-size="9" fill="${axisColor}" text-anchor="end">${Math.round(gy)}°</text>`;
    }

    svg += `<line x1="${padL}" y1="${yToPx(minFlow)}" x2="${padL + w}" y2="${yToPx(minFlow)}" stroke="${axisColor}" stroke-dasharray="3,3" stroke-width="0.75" />`;
    svg += `<line x1="${padL}" y1="${yToPx(maxFlow)}" x2="${padL + w}" y2="${yToPx(maxFlow)}" stroke="${axisColor}" stroke-dasharray="3,3" stroke-width="0.75" />`;

    svg += `<path d="${d}" fill="none" stroke="${curveColor}" stroke-width="2.5" stroke-linecap="round" />`;

    if (outdoorNow != null && flowNow != null) {
      const cx = xToPx(Number(outdoorNow));
      const cy = yToPx(flowNow);
      const bandTop = yToPx(Math.min(maxFlow, flowNow + hysteresis));
      const bandBottom = yToPx(Math.max(minFlow, flowNow - hysteresis));
      svg += `<rect x="${cx - 5}" y="${bandTop}" width="10" height="${bandBottom - bandTop}" fill="${pointColor}" opacity="0.15" />`;
      svg += `<circle cx="${cx}" cy="${cy}" r="5" fill="${pointColor}" stroke="var(--card-background-color, white)" stroke-width="1.5" />`;
      svg += `<text x="${cx}" y="${cy - 10}" font-size="10" fill="${pointColor}" text-anchor="middle" font-weight="600">${flowNow.toFixed(1)}°C</text>`;
    }

    svg += `<line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT + h}" stroke="${axisColor}" stroke-width="1" />`;
    svg += `<line x1="${padL}" y1="${padT + h}" x2="${padL + w}" y2="${padT + h}" stroke="${axisColor}" stroke-width="1" />`;

    this._svg.innerHTML = svg;

    this._legend.innerHTML = `
      <span>${t.outdoor}: <b>${outdoorNow != null ? Number(outdoorNow).toFixed(1) + "°C" : "–"}</b></span>
      <span>${t.flow}: <b>${flowNow != null ? flowNow.toFixed(1) + "°C" : "–"}</b></span>
      <span>${t.slope}: <b>${slope}</b></span>
      <span>${t.level}: <b>${level}°C</b></span>
      <span>${t.hysteresis}: <b>${hysteresis}°C</b></span>
      <span>${t.mode}: <b>${mode === "with_room_temp" ? t.modeRoomTemp : t.modeClassic}</b></span>
    `;
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement("hui-generic-entity-row");
  }

  static getStubConfig(hass) {
    const entities = Object.keys(hass.states).filter((e) =>
      e.startsWith("sensor.") && e.includes("vorlauftemperatur")
    );
    return { entity: entities[0] || "", title: t.defaultTitle };
  }
}

customElements.define("heating-curve-card", HeatingCurveCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "heating-curve-card",
  name: "Heating Curve Card",
  description: t.pickerDescription,
});
