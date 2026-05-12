# Victron MQTT Topic Reference

This document summarises the MQTT topic structure exposed by a Victron Cerbo GX (Venus OS).

**Authoritative source:** [victronenergy/venus wiki – dbus](https://github.com/victronenergy/venus/wiki/dbus) (last updated May 2026).  
All path definitions below are derived from that document.

---

## Topic format

```
N/<serial>/<service>/<instance>/<dbus-path>
```

| Segment | Example | Notes |
|---|---|---|
| `N` | `N` | Prefix for normal (retained) messages |
| `<serial>` | `a1b2c3d4e5f6` | VRM Portal ID / device serial |
| `<service>` | `system`, `battery`, `solarcharger` | D-Bus service type |
| `<instance>` | `0` | Device instance (usually `0` for system, varies for multi-device setups) |
| `<dbus-path>` | `Dc/Battery/Soc` | Path within the service |

### Keep-alive

The broker requires a periodic keep-alive or it stops streaming after ~60 s:

```
R/<serial>/keepalive   (publish empty payload)
```

### Units

SI units throughout, with two exceptions:
- **Energy** — kWh
- **Temperature** — °C

---

## `system/0` — Aggregated system view

The `system` service (published by `dbus-systemcalc-py`) aggregates readings from all connected devices into one place. This is the most useful service for dashboards and home-automation.

### DC / battery

```
system/0/Dc/Battery/Soc               State of charge (0–100 %)
system/0/Dc/Battery/Voltage           V DC
system/0/Dc/Battery/Current           A DC (positive = charging)
system/0/Dc/Battery/Power             W (positive = charging)
system/0/Dc/Battery/Temperature       °C
system/0/Dc/Battery/State             0=Idle, 1=Charging, 2=Discharging
system/0/Dc/Battery/TimeToGo          Seconds until SOC floor; capped at 864000 (10 days)
system/0/Dc/Battery/ConsumedAmphours  Ah drawn since last full charge
system/0/Dc/Battery/Capacity          Total capacity in Ah (from selected battery monitor)
```

### DC — solar & other sources

```
system/0/Dc/Pv/Power               W — total output of all solar chargers
system/0/Dc/Pv/Current             A — total output current of all solar chargers
system/0/Dc/Charger/Power          W — DC charger power
system/0/Dc/System/Power           W — DC system (loads not monitored individually)
system/0/Dc/Vebus/Power            W — VE.Bus charge/discharge power
system/0/Dc/Vebus/Current          A
system/0/Dc/InverterCharger/Power  W — preferred alternative to Dc/Vebus for overviews
system/0/Dc/InverterCharger/Current A
```

### AC — grid

```
system/0/Ac/Grid/L1/Power          W
system/0/Ac/Grid/L2/Power          W
system/0/Ac/Grid/L3/Power          W
system/0/Ac/Grid/NumberOfPhases    1 / 2 / 3
system/0/Ac/Grid/ProductId
system/0/Ac/Grid/DeviceType
```

### AC — consumption

```
system/0/Ac/Consumption/L1/Power         W  (DEPRECATED — see ConsumptionOnInput/Output)
system/0/Ac/ConsumptionOnInput/L1/Power  W  — load on AC input side
system/0/Ac/ConsumptionOnOutput/L1/Power W  — load on AC output side
system/0/Ac/Consumption/NumberOfPhases   1 / 2 / 3
```

(L2/L3 paths follow the same pattern)

### AC — PV inverters

```
system/0/Ac/PvOnOutput/L1/Power    W — PV inverter on AC output
system/0/Ac/PvOnGrid/L1/Power      W — PV inverter on grid input
system/0/Ac/PvOnGenset/L1/Power    W
```

### AC — source / state

```
system/0/Ac/ActiveIn/Source        0=unavailable, 1=grid, 2=genset, 3=shore, 240=inverting
system/0/Ac/HasAcLoads             0=DC-only system, 1=AC loads present
```

### System state

```
system/0/SystemState/State         See values below
system/0/SystemState/BatteryLife   1=BatteryLife active
system/0/SystemState/LowSoc        1=at minimum SOC
system/0/SystemState/ChargeDisabled   1=BMS has disabled charging
system/0/SystemState/DischargeDisabled 1=BMS has disabled discharge
```

`/SystemState/State` values:

| Value | Meaning |
|---|---|
| 0 | Off |
| 1 | Low power |
| 2 | VE.Bus fault |
| 3 | Bulk charging |
| 4 | Absorption charging |
| 5 | Float charging |
| 6 | Storage mode |
| 7 | Equalisation |
| 8 | Passthru |
| 9 | Inverting |
| 10 | Assisting |
| 244 | Battery Sustain |
| 252 | External control |
| 256 | Discharging |
| 257 | Sustain |
| 258 | Recharge |
| 259 | Scheduled recharge |

### Timers

```
system/0/Timers/TimeOnGrid       Seconds on grid since last reboot
system/0/Timers/TimeOnGenerator  Seconds on generator since last reboot
system/0/Timers/TimeOnInverter   Seconds inverting since last reboot
system/0/Timers/TimeOff          Seconds off since last reboot
```

### Relay / buzzer

```
system/0/Relay/0/State
system/0/Relay/1/State
system/0/Buzzer/State
```

### Multi-battery

```
system/0/Batteries              JSON array — all batteries (used by gui-v2 / VRM)
system/0/AvailableBatteries     List of all battery measurements
```

---

## `battery/<instance>` — Battery monitor (BMV, Lynx BMS, …)

```
battery/0/Dc/0/Voltage           V DC
battery/0/Dc/0/Current           A (positive = charging)
battery/0/Dc/0/Power             W (positive = charging)
battery/0/Dc/0/Temperature       °C
battery/0/Dc/0/MidVoltage        V (BMV-702 midpoint)
battery/0/Dc/0/MidVoltageDeviation  %
battery/0/Dc/1/Voltage           V — starter battery (BMV-702)

battery/0/Soc                    0–100 %
battery/0/ConsumedAmphours        Ah
battery/0/TimeToGo               Seconds; max 864000

battery/0/Info/MaxChargeCurrent    A — CCL (BYD, Lynx, FreedomWon)
battery/0/Info/MaxDischargeCurrent A — DCL
battery/0/Info/MaxChargeVoltage    V
battery/0/Info/BatteryLowVoltage   V
battery/0/Info/ChargeRequest       1=battery critically low, needs charge
```

**Alarms** (0=OK, 1=Warning, 2=Alarm):

```
battery/0/Alarms/LowVoltage
battery/0/Alarms/HighVoltage
battery/0/Alarms/LowSoc
battery/0/Alarms/LowTemperature
battery/0/Alarms/HighTemperature
battery/0/Alarms/CellImbalance
battery/0/Alarms/HighChargeCurrent
battery/0/Alarms/HighDischargeCurrent
```

**History**:

```
battery/0/History/MinimumVoltage
battery/0/History/MaximumVoltage
battery/0/History/TotalAhDrawn
battery/0/History/ChargeCycles
battery/0/History/DischargedEnergy   kWh
battery/0/History/ChargedEnergy      kWh
```

---

## `solarcharger/<instance>` — MPPT solar charger

```
solarcharger/0/Dc/0/Voltage      V — battery voltage
solarcharger/0/Dc/0/Current      A — charge current
solarcharger/0/Pv/V              V — PV array voltage (single-tracker products)
solarcharger/0/Pv/0/V            V — tracker 0 voltage (multi-tracker)
solarcharger/0/Pv/0/P            W — tracker 0 power
solarcharger/0/Yield/Power       W — total PV power
solarcharger/0/Yield/User        kWh — user-resettable total
solarcharger/0/Yield/System      kWh — lifetime total (not resettable)
solarcharger/0/Load/State        0=off, 1=on
solarcharger/0/Load/I            A — load output current

solarcharger/0/State             See values below
solarcharger/0/ErrorCode         0=no error (see victronenergy.com/live/mppt-error-codes)
solarcharger/0/Mode              1=On, 4=Off
solarcharger/0/MppOperationMode  0=Off, 1=V/I limited, 2=MPPT active
```

`/State` values: 0=Off, 2=Fault, 3=Bulk, 4=Absorption, 5=Float, 6=Storage, 7=Equalize, 252=External control

---

## `vebus/<instance>` — VE.Bus inverter/charger (Multi, Quattro)

### AC input

```
vebus/276/Ac/ActiveIn/L1/F   Hz
vebus/276/Ac/ActiveIn/L1/I   A
vebus/276/Ac/ActiveIn/L1/P   W
vebus/276/Ac/ActiveIn/L1/V   V
vebus/276/Ac/ActiveIn/P      W — total
```

### AC output

```
vebus/276/Ac/Out/L1/F        Hz
vebus/276/Ac/Out/L1/I        A
vebus/276/Ac/Out/L1/P        W
vebus/276/Ac/Out/L1/V        V
```

### DC / battery

```
vebus/276/Dc/0/Voltage       V
vebus/276/Dc/0/Current       A
vebus/276/Dc/0/Power         W
vebus/276/Dc/0/Temperature   °C
```

### State & control

```
vebus/276/State              0=Off, 1=Low power, 2=Fault, 3=Bulk, 4=Absorption,
                             5=Float, 6=Storage, 7=Equalize, 8=Passthru,
                             9=Inverting, 10=Power assist, 252=External control
vebus/276/Mode               1=Charger only, 2=Inverter only, 3=On, 4=Off
vebus/276/ModeIsAdjustable   0=locked, 1=remote control allowed
vebus/276/Ac/ActiveIn/ActiveInput  0=ACin-1, 1=ACin-2, 240=inverting
```

**Alarms** (0=OK, 1=Warning, 2=Alarm):

```
vebus/276/Alarms/HighDcCurrent
vebus/276/Alarms/HighDcVoltage
vebus/276/Alarms/LowBattery
vebus/276/Alarms/Overload      (per-phase: /Alarms/L1/Overload etc.)
vebus/276/Alarms/HighTemperature
vebus/276/Alarms/Ripple
```

---

## `grid/<instance>` — Grid / energy meter

```
grid/30/Ac/Power              W — total all phases
grid/30/Ac/Energy/Forward     kWh — bought (import)
grid/30/Ac/Energy/Reverse     kWh — sold (export)
grid/30/Ac/L1/Current         A
grid/30/Ac/L1/Power           W
grid/30/Ac/L1/Voltage         V
grid/30/Ac/L1/Energy/Forward  kWh
grid/30/Ac/L1/Energy/Reverse  kWh
grid/30/Ac/L1/PowerFactor
```

(L2/L3 paths follow the same pattern)

---

## `pvinverter/<instance>` — AC-coupled PV inverter (e.g. Fronius)

```
pvinverter/20/Ac/Power          W — total
pvinverter/20/Ac/L1/Power       W
pvinverter/20/Ac/L1/Voltage     V
pvinverter/20/Ac/L1/Current     A
pvinverter/20/Ac/L1/Energy/Forward  kWh
pvinverter/20/Ac/Energy/Forward  kWh — total
pvinverter/20/Position           0=AC input 1, 1=AC output, 2=AC input 2
pvinverter/20/StatusCode         0–6=startup, 7=running, 8=standby, 10=error
```

---

## `temperature/<instance>` — Temperature sensors

Includes wired inputs on Cerbo GX/Venus GX and Ruuvi wireless sensors.

```
temperature/0/Temperature       °C
temperature/0/TemperatureType   0=battery, 1=fridge, 2=generic, 3=room,
                                4=outdoor, 5=water heater, 6=freezer
temperature/0/CustomName
temperature/0/Status            0=OK, 1=disconnected, 2=short circuit,
                                3=reverse polarity, 4=unknown

# Ruuvi only:
temperature/0/Humidity          %
temperature/0/Pressure          hPa
temperature/0/BatteryVoltage    V
# Ruuvi Air only:
temperature/0/CO2               ppm
temperature/0/PM25              µg/m³
temperature/0/VOC               index (100 = average)
temperature/0/NOX               index (1 = baseline)
```

---

## `tank/<instance>` — Tank level sensors

```
tank/0/Level        0–100 %
tank/0/Remaining    m³
tank/0/Capacity     m³
tank/0/Status       0=OK, 1=disconnected, 2=short circuit, 3=unknown, 4=config error
tank/0/FluidType    0=fuel, 1=fresh water, 2=waste water, 3=live well, 4=oil,
                    5=black water, 6=gasoline, 7=diesel, 8=LPG, 9=LNG,
                    10=hydraulic oil, 11=raw water
tank/0/Temperature  °C (Mopeka sensors only)
```

---

## Common bridge mapping examples

```sh
# System-level overview (branch mapping — subscribes to whole subtree)
TOPIC_MAPPING='{
  "system/0/Dc/Battery/":        "victron/battery/",
  "system/0/Dc/Pv/":             "victron/solar/",
  "system/0/Ac/Grid/":           "victron/grid/",
  "system/0/Ac/Consumption/":    "victron/consumption/",
  "system/0/SystemState/State":  "victron/system/state"
}'

# Specific leaf values only
TOPIC_MAPPING='{
  "system/0/Dc/Battery/Soc":          "victron/battery/soc",
  "system/0/Dc/Battery/Voltage":      "victron/battery/voltage",
  "system/0/Dc/Battery/Power":        "victron/battery/power",
  "system/0/Dc/Pv/Power":             "victron/solar/power",
  "system/0/Ac/Grid/L1/Power":        "victron/grid/l1/power",
  "system/0/Ac/Grid/L2/Power":        "victron/grid/l2/power",
  "system/0/Ac/Grid/L3/Power":        "victron/grid/l3/power"
}'
```

---

## Discovering paths on your own device

```sh
# 1. Trigger the data stream
mosquitto_pub -h <cerbo-ip> -t "R/<serial>/keepalive" -m ""

# 2. Subscribe to everything and inspect
mosquitto_sub -h <cerbo-ip> -t "N/#" -v

# 3. Or subscribe to one service only
mosquitto_sub -h <cerbo-ip> -t "N/<serial>/system/#" -v
```

The bridge itself logs the full topic tree for your device on startup — look for the `Available Victron topics under N/<serial>/` log block.
