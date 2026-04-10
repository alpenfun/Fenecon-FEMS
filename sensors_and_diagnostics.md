# Sensors and Diagnostics Guide

This document explains the most important sensors and diagnostic values provided by the FEMS Diagnostics integration.

It is intended to help users understand system behavior, interpret values correctly, and identify potential issues early.

> ⚠️ Note  
> All values should be interpreted in context. Individual readings can vary depending on load, temperature, system configuration, and operating state.

For installation, setup, and general usage, see the main project documentation:
👉 [README](../README.md)

---

# Battery Chemistry (LFP)

The FEMS system uses a **Lithium Iron Phosphate (LiFePO₄ / LFP)** battery.

Compared to other lithium battery types, LFP offers:

- high cycle life  
- high safety  
- stable behavior at high state of charge  

## Practical handling recommendations

- Regular full charge (near 100%) is beneficial for **cell balancing**
- Avoid leaving the battery at **very low SOC** for extended periods
- Typical optimal operating range: **20–80%**
- Full range (0–100%) is safe, but should not be used permanently

> ℹ️ Note  
> The displayed SOC is managed by the system's **Battery Management System (BMS)** and includes internal safety buffers.  
> 0% and 100% are not absolute physical limits.

---

# 1. State of Charge (SOC)

**State of Charge (SOC)** represents the current charge level of the battery in percent.

- **100%** → battery is fully charged  
- **0%** → battery is at its usable lower limit  

## Interpretation

SOC is the most important value for daily operation.

- High SOC → high energy reserve  
- Low SOC → limited remaining energy  

## Typical behavior

- SOC increases during PV production
- SOC decreases when the house consumes energy without PV input
- SOC should change gradually

## Examples

| Situation | Interpretation |
|----------|---------------|
| SOC = 85% (afternoon) | Normal, battery charged by PV |
| SOC = 25% (late evening) | Normal discharge after sunset |
| SOC = 5% (morning) | Low reserve, but still valid |

## When to investigate

- SOC jumps unexpectedly  
- SOC remains constant despite charging/discharging  
- SOC drops very fast under low load  

---

# 2. State of Health (SOH)

**State of Health (SOH)** indicates the long-term condition of the battery.

- **100%** → condition comparable to new  
- Lower values → aging and reduced capacity  

## Interpretation

SOH changes **very slowly** over time.

## Examples

| SOH | Interpretation |
|-----|--------------|
| 98% | Excellent condition |
| 93% | Normal aging |
| 85% | Noticeable aging |

## When to investigate

- Sudden drop in SOH  
- Unrealistic changes in short time  

---

# 3. Cell Voltage Spread (ΔV)

**Cell voltage spread (ΔV)** is the difference between the highest and lowest cell voltage.

Formula:
ΔV = max cell voltage - min cell voltage


## Why it matters

It indicates how well the battery cells are balanced.

- Small ΔV → well balanced battery  
- Large ΔV → imbalance or stress  

## Typical ranges (rule of thumb)

| ΔV | Interpretation |
|----|--------------|
| < 0.010 V | Very good |
| 0.010 – 0.020 V | Normal |
| 0.020 – 0.040 V | Observe |
| > 0.040 V | Potential imbalance |

## Important context

ΔV depends on:

- SOC  
- charging/discharging  
- current load  

Temporary increases under load are normal.

## When to investigate

- ΔV remains high over time  
- ΔV increases across multiple cycles  
- No improvement after full charge cycles  

---

# 4. Minimum and Maximum Cell Voltage

These values show the weakest and strongest individual cell.

- **Min cell voltage** → weakest cell  
- **Max cell voltage** → strongest cell  

## Interpretation

They must always be interpreted together with ΔV.

## Examples

| Min / Max | Interpretation |
|----------|--------------|
| 3.28 / 3.29 V | Excellent balance |
| 3.20 / 3.24 V | Acceptable |
| Strong deviation | Possible imbalance |

## When to investigate

- One cell repeatedly deviates  
- Min voltage drops unusually early  
- Gap between min and max increases over time  

---

# 5. Minimum and Maximum Cell Temperature

These values describe thermal behavior inside the battery.

- **Min temperature** → coldest cell  
- **Max temperature** → warmest cell  

## Why it matters

Temperature affects:

- efficiency  
- lifetime  
- safety  

## Typical behavior

| Temperature | Interpretation |
|------------|---------------|
| 15–30°C | Optimal range |
| < 10°C | Reduced performance |
| > 40°C | Increased stress |

## When to investigate

- Large temperature differences between cells  
- Persistent high temperatures  
- One module significantly hotter than others  

---

# 6. Power Sensors (W)

Power sensors describe **instantaneous energy flow**.

## 6.1 Grid Power

Indicates energy exchange with the public grid.

| Value | Meaning |
|------|--------|
| Positive | Import from grid |
| Negative | Export to grid |

---

## 6.2 PV Power

Current photovoltaic production.

| Situation | Interpretation |
|----------|---------------|
| 0 W at night | Normal |
| High value at noon | Expected |
| Low value in sun | Check system |

---

## 6.3 Battery Power

Shows whether the battery is charging or discharging.

> ⚠️ Sign convention may vary depending on system setup.

## Recommendation

Verify once:

- During charging → observe sign  
- During discharging → observe sign  

---

## 6.4 House Power (Load)

Current total consumption of the house.

| Value | Interpretation |
|------|---------------|
| 200–500 W | Base load |
| 2000–4000 W | Active appliances |
| Peaks >5000 W | Short-term loads |

---

# 7. Energy Sensors (Wh / kWh)

Energy sensors represent **accumulated values over time**.

## Examples

- PV energy produced  
- Battery charge/discharge energy  
- Grid import/export  
- House consumption  

## Power vs Energy

| Type | Meaning |
|------|--------|
| Power (W) | Current value |
| Energy (kWh) | Accumulated over time |

Example:
1000 W for 1 hour = 1 kWh


---

# 8. Normal vs Critical Behavior

| Category | Normal | Observe | Critical |
|----------|--------|--------|---------|
| SOC | gradual change | fast drop | stuck / erratic |
| SOH | slow decline | faster aging | sudden drop |
| ΔV | small | elevated | persistently high |
| Cell voltage | close values | increasing gap | strong deviation |
| Temperature | moderate | uneven | hotspots / high |
| Power | plausible | unusual peaks | inconsistent |

---

# 9. Practical Scenarios

## A. Normal daytime charging

- PV high  
- Battery charging  
- SOC increasing  
- ΔV small  

→ System operating normally

---

## B. Evening discharge

- PV low  
- Battery supplying house  
- SOC decreasing  

→ Expected behavior

---

## C. Cell imbalance

- ΔV elevated over time  
- Min/max drifting apart  

→ Monitor across cycles

---

## D. Temperature anomaly

- One module hotter  
- Increasing temperature spread  

→ Check thermal conditions

---

# 10. How to Read the System Correctly

Always interpret values **in combination**, not individually.

Best combinations:

- SOC + battery power  
- ΔV + min/max voltage  
- temperature + load  
- PV + grid + house  

---

# 11. Key Takeaways

The most relevant values for daily use:

- **SOC** → available energy  
- **SOH** → battery condition  
- **ΔV** → cell balance  
- **Cell voltages** → weakest/strongest cell  
- **Temperature** → thermal condition  
- **Power sensors** → live energy flow  
- **Energy sensors** → long-term usage  

---

# 12. Final Note

Short-term anomalies are usually not critical.

Focus on:

- trends  
- repeated patterns  
- long-term deviations  

These provide the most reliable indication of system health.


# 13. Manufacturer vs. Practical Experience

These recommendations reflect practical observations from real installations and are intended to support interpretation of system data in everyday use.

> ⚠️ Important  
> Always follow the official documentation and specifications provided by the system manufacturer.  
> These take precedence over general recommendations.

Battery management behavior (e.g. SOC limits, balancing strategy, protection mechanisms) is controlled by the system's internal BMS and may differ between manufacturers, system configurations, and firmware versions.

