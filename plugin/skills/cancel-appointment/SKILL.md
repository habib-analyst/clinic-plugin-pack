---
name: cancel-appointment
description: "Cancel an appointment. This skill should be used when the user asks to \"cancel my appointment\", \"cannot come tomorrow\"."
version: 0.1.0
---

# cancel-appointment

Cancel an appointment.

Part of the **clinic** pack (v0.1.0) by Habib Ur Rehman — a clinic front-desk skill pack compiled with [packc](https://github.com/habib-analyst/packc) from the typed source `src/clinic.pack` shipped in this plugin.

## When this skill applies

- The user asks to "cancel my appointment".
- The user asks to "cannot come tomorrow".

## Tool

Backed by the MCP tool `appointment_cancel` in this plugin's bundled server (`mcp/clinic_mcp_server.py`, registered in `.mcp.json`). The server validates every call against the typed input schema before dispatch.

## Input — `AppointmentRef`

| Field | Type | Required | Default |
|---|---|---|---|
| `appointment_id` | `string?` | no |  |

## Output — `CancelOutcome`

| Field | Type | Required | Default |
|---|---|---|---|
| `cancelled` | `bool` | yes |  |

## Steps

1. Look up the appointment by ID or phone number.
2. Cancel it and release the slot.
3. Confirm the cancellation.

## Safety and escalation

The pack source declares this escalation policy (context schema `ClinicContext`):

Default tiers by action:
- `message.send` → **auto**
- `appointment.book` → **confirm**
- `appointment.cancel` → **confirm**

- Rule `emergency`: when `is_emergency == true` → tier **human_only**.
- Rule `fallback` (fallback): everything else → **confirm**.

Mutating actions (booking, cancellation) require confirmation by default, and the emergency rule escalates to a human. This pack handles front-desk logistics only; it does not give medical advice.
