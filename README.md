# 🔋 FEMS Integration for Home Assistant

Custom Home Assistant integration for **FENECON FEMS** systems.  
Provides detailed battery, inverter, and diagnostic data via **Modbus** and **REST API**.

---

## ✨ Features

- 🔌 Modbus + REST integration
- 🔄 Central DataUpdateCoordinator architecture
- 🔋 Battery monitoring
  - State of charge (SoC)
  - Voltage, current, power
  - Cycle count and health (SoH)
- ⚡ Inverter / charger data
- 🧠 System status (OK / Warning / Error)
- 📊 Diagnostic sensors
- 🔍 Cell-level monitoring
  - Per-cell voltage (up to 14 cells per module)
- 📈 Battery module monitoring (configurable)
  - Per-module voltage spread (ΔV)

---

## ⚙️ Configuration

During setup, the following parameters are required:

- **REST Host / Port**
- **Modbus Host / Port**
- **Modbus Slave ID**
- **Battery module count**
  - Range: **1–10 modules**
  - Default: **7 modules**

---

## 🔋 Battery Module Configuration

The integration dynamically adapts to your system based on the configured module count.

This setting controls:

- Number of **module spread sensors (ΔV)**
- Number of **cell voltage sensors**

Example:

| Modules | Sensors (approx.) |
|--------|------------------|
| 1      | ~20              |
| 5      | ~80              |
| 7      | ~110             |
| 10     | ~150+            |

⚠️ **Important:**  
Make sure the configured module count matches your actual system.

---

## 🧠 Architecture

- `coordinator.py` → Central data aggregation
- `fems_modbus.py` → Modbus communication
- `fems_rest.py` → REST communication
- `sensor.py` → Sensor entities (dynamic)
- `binary_sensor.py` → Status sensors

---

## 📊 Provided Sensors

### 🔋 Battery
- Voltage
- Current
- Power
- SoC
- SoH
- Cycle count

### ⚡ Charger / Inverter
- Power
- Voltage
- Current
- Energy

### 🧠 System
- Status (OK / Warning / Error)
- Fault
- Communication status

### 📈 Module Diagnostics
- Voltage spread (ΔV) per module

### 🔬 Cell Diagnostics
- Voltage per cell (Module × 14 cells)

---

## ⚡ Performance Notes

The number of entities scales with the number of battery modules.

- More modules → more sensors → higher system load
- Cell voltage sensors are the largest contributor

💡 Recommendation:
- Use only the required module count
- Disable diagnostic sensors if not needed

---

## 🔄 Migration Notes (0.2.3)

- Existing installations are automatically migrated
- Missing `battery_module_count` is set to default (**7 modules**)
- No manual action required

---

## 📦 Installation

### HACS (recommended)
1. Add custom repository
2. Search for **FEMS**
3. Install
4. Restart Home Assistant

### Manual
1. Copy `custom_components/fems` to your HA config directory
2. Restart Home Assistant

---

## 🚀 Roadmap

- [ ] Options Flow (change module count after setup)
- [ ] Energy dashboard integration
- [ ] Optimized default dashboards
- [ ] Sensor grouping / categories
- [ ] Performance optimization for large systems

---

## ⚠️ Disclaimer

This is an unofficial integration.  
Use at your own risk.

---

## 👨‍💻 Author

Developed by **alpenfun**
