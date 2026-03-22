# 🔋 Fenecon FEMS Integration for Home Assistant

A custom Home Assistant integration for **Fenecon FEMS (Energy Management System)**
providing **real-time data**, **battery diagnostics**, and **energy flow insights** via REST and Modbus.

---

## ✨ Features

* 🔌 REST + Modbus integration
* 🔋 Full battery monitoring (SOC, SOH, voltage, current, cycles)
* ⚡ Real-time power data (PV, grid, house, battery)
* 📊 Energy counters (charge, discharge, consumption, feed-in)
* 🧠 Advanced diagnostics (cell voltage spread, fault states)
* 🧱 Clean architecture using `DataUpdateCoordinator`
* 🌍 Full localization support (`en` / `de`)
* 🧩 HACS compatible

---

## 📦 Installation

### HACS (recommended)

1. Open HACS
2. Go to **Integrations**
3. Click **⋮ → Custom repositories**
4. Add your repository URL
5. Select category: **Integration**
6. Install **FEMS**
7. Restart Home Assistant

---

## ⚙️ Configuration

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Add Integration**
3. Search for **FEMS**
4. Enter:

   * REST host / port
   * Modbus host / port / slave
   * Credentials (if required)

---

## 🧠 Dashboard Recommendation

This integration is designed with a **clean, user-focused dashboard structure**.

👉 Important:

* Entity IDs may vary depending on language and system setup
* Use **names (not IDs)** when building your dashboard

---

### 🟢 1. System Status

**Goal:** Instant system health overview

**Entities:**

* System OK
* System Warning
* System Error
* REST Connected
* Modbus Connected
* Fault Active

**Recommended card:**

* Tile cards (color-coded)

---

### ⚡ 2. Live Power

**Goal:** Understand current energy flow

**Entities:**

* PV Power
* House Load
* Grid Power
* Battery Power

**Recommended card:**

* Gauge or Tile

---

### 🔋 3. Battery Overview

**Goal:** Monitor battery condition

**Entities:**

* State of Charge (SOC)
* State of Health (SOH)
* Battery Current
* Battery Voltage (DC)
* Battery Pack Voltage
* Charge Cycles
* Battery State
* Battery State Machine

---

### 🔌 4. Energy Counters

**Goal:** Long-term energy tracking

**Entities:**

* PV Yield
* House Consumption
* Grid Import
* Grid Export
* Battery Charge Energy
* Battery Discharge Energy
* AC Charge Energy
* AC Discharge Energy

---

### 🔁 5. Phase Values (optional)

**Goal:** Analyze load distribution

**Entities:**

* Battery L1 / L2 / L3
* Grid L1 / L2 / L3
* House L1 / L2 / L3

---

### 🧪 6. Cell Health (Recommended)

**Goal:** Detect battery issues early

**Entities:**

* Cell Voltage Spread (overall)
* Module 0–6 ΔV

👉 This replaces the need to display all individual cell voltages.

---

### 🔧 7. Diagnostics (optional)

**Goal:** Debugging and deep analysis

**Includes:**

* Tower temperatures
* Cell voltage min/max
* Undervoltage levels
* Internal fault flags

👉 These entities are:

* marked as **diagnostic**
* **disabled by default**

---

## 🎯 Design Philosophy

* Clean default dashboard (no sensor overload)
* Diagnostics separated from daily use
* Focus on meaningful indicators (e.g. Δ cell voltage)
* Scalable for large battery systems

---

## ⚠️ Notes

* Cell voltages are available but **disabled by default**
* Diagnostic sensors return **0/1 values** for stability
* Entity IDs may differ depending on language settings

---

## 🚀 Roadmap

* [ ] Stable entity IDs for universal dashboards
* [ ] Energy Flow Card example
* [ ] Advanced statistics dashboard
* [ ] Alarm aggregation sensor
* [ ] HACS default dashboard blueprint

---

## 🤝 Contributing

Contributions, ideas and feedback are welcome!

---

## 📄 License

MIT License

---

## 🙌 Acknowledgements

* Home Assistant Community
* Fenecon ecosystem
