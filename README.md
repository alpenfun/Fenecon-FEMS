
<p align="center">
  <img src="https://raw.githubusercontent.com/alpenfun/fems-diagnostics/main/docs/images/logo.png" width="300">
</p>

<h1 align="center">FEMS Diagnostics</h1>
<p align="center">
  Advanced battery and system diagnostics for Home Assistant
</p>


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

![FEMS Diagnostics Dashboard](https://raw.githubusercontent.com/alpenfun/fems-diagnostics/main/docs/images/dashboard.png)

A ready-to-use example dashboard YAML is included here:

```text
docs/dashboard/dashboard.yaml
```

It is based on your current diagnostic layout and uses the provided entity names. The example dashboard file included in the repository reflects the current proposed standard dashboard.

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

⚠️ Cell voltage spread (ΔU / ΔV) interpretation

The cell voltage spread (ΔU / ΔV) is one of the key indicators used by this integration to assess battery health.

However, it is important to understand the following:

❗ Not an official manufacturer metric

The thresholds used in this integration:

Spread	Interpretation
< 0.02 V	uncritical
0.02 – 0.05 V	observe
> 0.05 V	critical

are engineering heuristics based on general lithium-ion battery behavior.

👉 They are NOT official thresholds from FENECON or any other manufacturer.

⚡ Strongly dependent on operating conditions

The spread between cell voltages is not constant and varies depending on system conditions.

Higher spread values can be completely normal during:

low state of charge (SOC)
charging phases
high load / discharge currents
transient system behavior

In particular:

A higher ΔU at low SOC does not necessarily indicate a battery defect.

🧠 Context-aware evaluation in this integration

To avoid false interpretations, this integration evaluates ΔU with context:

low SOC → separate status (low_soc)
high current → separate status (under_load)
missing context → not_evaluable

This helps prevent false "critical" indications under normal operating conditions.

📊 Recommendation for users
Do not evaluate ΔU based on a single measurement
Observe trends over time
Compare behavior at similar SOC levels
Use manufacturer tools for final diagnosis if needed
🚫 Important disclaimer

This integration is intended as a diagnostic aid.

It does not replace manufacturer diagnostics or official support.

If you suspect a real issue with your system, always consult the official FENECON service.

---

## 📦 Prerequisites

### 🧩 HACS (Home Assistant Community Store)

This integration and the example dashboard rely on HACS.

👉 HACS is required to install:
- this integration
- custom dashboard cards

Install HACS here:
👉 https://hacs.xyz/

👉 Without HACS, the integration and dashboard cannot be installed.

---

### 🎨 Dashboard dependencies

For the provided example dashboard you also need:

- 🍄 [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- 🔘 [button-card](https://github.com/custom-cards/button-card) by @RomRider

These can be installed directly via HACS.

The integration itself can run without the dashboard, but the provided example dashboard depends on those custom dashboard cards.

---

## 📥 Installation

### 1. Install HACS (if not already installed)

See the official HACS documentation.

### 2. Add this repository as a custom repository in HACS

![Installation über HACS](https://raw.githubusercontent.com/alpenfun/fems-diagnostics/main/docs/images/hacs_installation.png)

Use this repository URL:

```text
https://github.com/alpenfun/fems-diagnostics
```

Type:

```text
Integration
```

### 3. Search for the integration in HACS and install it

![FEMS Integration in HACS suchen](https://raw.githubusercontent.com/alpenfun/fems-diagnostics/main/docs/images/hacs_search.png)

### 4. Restart Home Assistant

### 5. Add the integration in Home Assistant

![FEMS einrichten](https://raw.githubusercontent.com/alpenfun/fems-diagnostics/main/docs/images/config_flow.png)

Required setup values:
- REST host
- REST port
- Modbus host
- Modbus port
- Modbus slave
- Battery module count
- Username
- Password

The configuration flow currently exposes these setup parameters directly in Home Assistant, including separate REST and Modbus endpoints and the configurable battery module count.

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

During setup, the battery module count can be configured from **1 to 10**, with **7 modules** as the default. This controls how many module spread and cell sensors are created. The integration constants define that range and default explicitly.

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

The provided dashboard view is currently named **FEMS Diagnostics** and includes status badges, KPI cards, module spread cards, compact health information, critical diagnostics, warnings, phase values, and energy counters.

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

Your current binary sensor implementation derives these overall health states from REST and Modbus availability plus fault, warning, and alarm signals.

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
