# Architecture

ARACHNID: Mobility + spatial subsystem.
AESAR: Agricultural/ecological intelligence subsystem.

## System Architecture

Sensors
   ↓
Brain ESP32
   ↓
Wi-Fi/TCP
   ↓
Hardware Gateway
   ↓
Normalized Telemetry
   ↓
┌───────────────┬────────────────┬─────────────────┐
│ Localization  │ Vision         │ Environment     │
└───────────────┴────────────────┴─────────────────┘
                    ↓
             Station Analysis
                    ↓
              PDR + AMRI
                    ↓
             AESA Decision
                    ↓
            Field Card / Action
                    ↓
             Mission Controller
                    ↓
          Existing ARACHNID Navigation
                    ↓
               Drive ESP32
                    ↓
                  Motors

## Important Restrictions
- Mission/AI modules must NOT directly control motor GPIOs.
- The existing Drive ESP32 remains the motor authority.
- AESAR should issue high-level navigation requests through the integration layer.
