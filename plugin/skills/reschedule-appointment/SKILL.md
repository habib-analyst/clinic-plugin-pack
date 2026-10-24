---
name: reschedule-appointment
description: "Move an appointment to a new day and time. This skill should be used when the user asks to \"move my appointment\", \"reschedule visit\"."
version: 0.1.0
---

# reschedule-appointment

Move an appointment to a new day and time.

Part of the **clinic** pack (v0.1.0) by Habib Ur Rehman — a clinic front-desk skill pack compiled with [packc](https://github.com/habib-analyst/packc) from the typed source `src/clinic.pack` shipped in this plugin.

## When this skill applies

- The user asks to "move my appointment".
- The user asks to "reschedule visit".

## Tool

Backed by the MCP tool `appointment_reschedule` in this plugin's bundled server (`mcp/clinic_mcp_server.py`, registered in `.mcp.json`). The server validates every call against the typed input schema before dispatch.

## Input — `RescheduleRequest`

| Field | Type | Required | Default |
|---|---|---|---|
| `appointment_id` | `string?` | no |  |
| `new_day` | `string` | yes |  |
| `new_time` | `string` | yes |  |

## Output — `RescheduleResult`

| Field | Type | Required | Default |
|---|---|---|---|
| `appointment_id` | `string` | yes |  |
| `new_day` | `string` | yes |  |
| `new_time` | `string` | yes |  |

## Steps

1. Look up the appointment by ID or phone number.
2. Verify the new slot is free with the same doctor.
3. Update the appointment and confirm the new slot.

## Safety and escalation

The pack source declares this escalation policy (context schema `ClinicContext`):

Default tiers by action:
- `message.send` → **auto**
- `appointment.book` → **confirm**
- `appointment.cancel` → **confirm**

- Rule `emergency`: when `is_emergency == true` → tier **human_only**.
- Rule `fallback` (fallback): everything else → **confirm**.

Mutating actions (booking, cancellation) require confirmation by default, and the emergency rule escalates to a human. This pack handles front-desk logistics only; it does not give medical advice.
