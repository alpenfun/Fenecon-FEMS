# 🔋 FEMS Diagnostics for Home Assistant

**FEMS Diagnostics** is an unofficial Home Assistant integration focused on **diagnostics, health monitoring, and technical visibility** for FEMS-based energy systems.

It combines:
- 🌐 REST API data for status and diagnostics
- 🔌 Modbus data for technical real-time values
- 📊 a dedicated diagnostic dashboard for fast anomaly detection

> ⚠️ **Unofficial project**  
> This project is not affiliated with, endorsed by, or supported by FENECON GmbH.  
> All product names, trademarks, and brand names belong to their respective owners.

---

## ✨ Features

- 📡 Parallel REST + Modbus integration
- 🔋 Battery health and operating data
- ⚡ Charger / inverter values
- 🚨 Error, warning, and alarm diagnostics
- 📈 Energy counters and phase values
- 🧠 Derived system state: **OK / Warning / Error**
- 🔧 Configurable battery module count
- 🧩 Dashboard optimized for **diagnosis**, not just monitoring

---

## 🧪 Project focus

This integration is intentionally positioned as a **diagnostic and health tool**.

Focus areas:
- Zellgesundheit / cell health
- Spannungsabweichungen / voltage spread (ΔU / ΔV)
- Fehler- und Warnbilder / error and warning patterns
- Kommunikationsstatus / communication state

The goal is to help detect battery issues early instead of only showing general energy flows.

---

## 🖼️ Example dashboard

![FEMS Diagnostics Dashboard](docs/images/dashboard.jpg)

A ready-to-use example dashboard YAML is included here:

```text
docs/dashboard/dashboard.yaml
```

It is based on your current diagnostic layout and uses the provided entity names. The example dashboard file included in the repository reflects the current proposed standard dashboard. fileciteturn5file6

---

## 🎯 Dashboard design decision

**Per-cell voltages are intentionally not shown in the example dashboard.**

Why:
- too many entities for a compact diagnosis view
- slower visual interpretation
- module voltage spread plus min/max values are usually the better first indicator

The cell entities are still created by the integration and remain available for advanced users.

---

## 🟢 Status logic

| Status | Meaning |
|---|---|
| 🟢 Green | System OK |
| 🟡 Yellow | Warning condition detected |
| 🔴 Red | Critical fault or alarm |

### Moduldiagnose (ΔU / ΔV)

| Spread | Interpretation |
|---|---|
| < 0.02 V | 🟢 uncritical |
| 0.02 – 0.05 V | 🟡 observe |
| > 0.05 V | 🔴 critical |

These thresholds are also used visually in the example dashboard for the per-module spread cards. fileciteturn5file6

---

## 📦 Prerequisites

For the dashboard example you need:
- **HACS**
- **Mushroom** dashboard cards
- **button-card** by **@RomRider**

The integration itself can run without the dashboard, but the provided example dashboard depends on those custom dashboard cards.

---

## 📥 Installation

### 1. Install HACS (if not already installed)

See the official HACS documentation.

### 2. Add this repository as a custom repository in HACS

![Installation über HACS](docs/images/hacs_installation.jpg)

Use this repository URL:

```text
https://github.com/alpenfun/fems-diagnostics
```

Type:

```text
Integration
```

### 3. Search for the integration in HACS and install it

![FEMS Integration in HACS suchen](docs/images/hacs_search.jpg)

### 4. Restart Home Assistant

### 5. Add the integration in Home Assistant

![FEMS einrichten](docs/images/config_flow.jpg)

Required setup values:
- REST host
- REST port
- Modbus host
- Modbus port
- Modbus slave
- Battery module count
- Username
- Password

The configuration flow currently exposes these setup parameters directly in Home Assistant, including separate REST and Modbus endpoints and the configurable battery module count. fileciteturn5file8turn5file11

---

## 🧩 Created devices

The integration creates six logical devices:
- 🔋 Battery
- ⚡ Charger 0
- ⚡ Charger 1
- 🧠 Diagnostics
- 📊 Energy management
- 🔬 Cells

---

## ⚙️ Configuration notes

During setup, the battery module count can be configured from **1 to 10**, with **7 modules** as the default. This controls how many module spread and cell sensors are created. The integration constants define that range and default explicitly. fileciteturn5file9

If the configured module count does not match the real system, diagnostic values may become misleading.

---

## 📊 Dashboard setup

To use the included example dashboard:

1. Open the dashboard editor in Home Assistant
2. Switch to YAML mode if needed
3. Copy the content of:

```text
docs/dashboard/dashboard.yaml
```

4. Paste it into your dashboard / view configuration

The provided dashboard view is currently named **FEMS Diagnostics** and includes status badges, KPI cards, module spread cards, compact health information, critical diagnostics, warnings, phase values, and energy counters. fileciteturn5file6

---

## 📡 Sensors and diagnostics

The integration provides, among other things:

### Battery
- SoC
- SoH
- current
- DC voltage
- pack voltage
- capacity
- cycle count

### Charger / inverter
- power
- voltage
- current

### Diagnostics
- fault status
- warning status
- alarm status
- communication state
- module spread per battery module
- per-cell voltage entities

### Derived binary states
- system OK
- system warning
- system error
- REST communication
- Modbus communication

Your current binary sensor implementation derives these overall health states from REST and Modbus availability plus fault, warning, and alarm signals. fileciteturn5file16

---

## ⚡ Performance notes

The total entity count grows with the configured number of battery modules.

Important:
- more modules = more entities
- per-cell voltages are the largest contributor
- the first refresh can take noticeably longer than later updates
- REST is usually slower than Modbus

---

## 🛠️ Repository structure

Recommended structure:

```text
custom_components/fems/
docs/images/
docs/dashboard/
README.md
hacs.json
manifest.json
```

This README assumes the following documentation files exist:
- `docs/images/dashboard.jpg`
- `docs/images/hacs_installation.jpg`
- `docs/images/hacs_search.jpg`
- `docs/images/config_flow.jpg`
- `docs/dashboard/dashboard.yaml`

---

## 🤝 Contributing

Feedback, issues, and pull requests are welcome.

---

## 📜 License

MIT License

---

## 🔋 Moduldiagnose (ΔU)

| ΔU            | Bewertung     |
| ------------- | ------------- |
| < 0.02 V      | 🟢 unkritisch |
| 0.02 – 0.05 V | 🟡 beobachten |
| > 0.05 V      | 🔴 kritisch   |

---

# 📦 Installation

## 1. HACS installieren (falls noch nicht vorhanden)

👉 https://hacs.xyz/

---

## 2. Repository hinzufügen

![HACS Installation](docs/images/hacs_installation.jpg)

* HACS öffnen
* „Custom Repositories“
* URL einfügen:

```
https://github.com/alpenfun/Fenecon-FEMS
```

* Typ: **Integration**

---

## 3. Integration suchen & installieren

![HACS Suche](docs/images/hacs_search.jpg)

---

## 4. Integration konfigurieren

![Config](docs/images/config_flow.jpg)

Benötigte Daten:

* REST Host (IP)
* REST Port (Standard: 8084)
* Modbus Host
* Modbus Port (502)
* Modbus Slave (meist 1)
* Anzahl Batteriemodule

---

# ⚙️ Geräte-Struktur

Die Integration legt folgende Geräte an:

* 🔋 Batterie
* ⚡ Charger 0
* ⚡ Charger 1
* 🧠 Diagnose
* 📊 Energiemanagement
* 🔬 Zellen

---

# 📊 Dashboard einrichten

## YAML importieren

Datei:

```
docs/dashboard/dashboard.yaml
```

👉 in Home Assistant:

* Dashboard → bearbeiten
* YAML Modus aktivieren
* Inhalt einfügen

---

## 🔧 Voraussetzungen (WICHTIG)

Dieses Dashboard nutzt Custom Cards:

### Pflicht:

* HACS
* 🍄 Mushroom Cards
* 🔘 Button Card (by RomRider)

Installation über HACS:

* „Mushroom“
* „button-card“

---

# ⚡ Hinweise

* Erststart kann 30–60 Sekunden dauern
* REST ist langsamer als Modbus
* Sensoren werden dynamisch erzeugt

---

# 🛠️ Entwicklung

Status:
👉 aktiv

Geplant:

* automatische Modulerkennung
* erweiterte Diagnose
* Health Score

---

# 🤝 Mitwirken

Feedback & Pull Requests willkommen!

---

# 📜 Lizenz

MIT License
