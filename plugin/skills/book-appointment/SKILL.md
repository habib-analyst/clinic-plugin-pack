---
name: book-appointment
description: "Book an appointment with a named doctor. This skill should be used when the user asks to \"book an appointment\", \"see dr ahmed tomorrow\"."
version: 0.1.0
---

# book-appointment

Book an appointment with a named doctor.

Part of the **clinic** pack (v0.1.0) by Habib Ur Rehman — a clinic front-desk skill pack compiled with [packc](https://github.com/habib-analyst/packc) from the typed source `src/clinic.pack` shipped in this plugin.

## When this skill applies

- The user asks to "book an appointment".
- The user asks to "see dr ahmed tomorrow".

## Tool

Backed by the MCP tool `appointment_book` in this plugin's bundled server (`mcp/clinic_mcp_server.py`, registered in `.mcp.json`). The server validates every call against the typed input schema before dispatch.

## Input — `AppointmentRequest`

| Field | Type | Required | Default |
|---|---|---|---|
| `doctor` | `string` | yes |  |
| `day` | `string` | yes |  |
| `time` | `string` | yes |  |
| `patient_name` | `string` | yes |  |
| `phone` | `string` | yes |  |

## Output — `Appointment`

| Field | Type | Required | Default |
|---|---|---|---|
| `appointment_id` | `string` | yes |  |
| `doctor` | `string` | yes |  |
| `day` | `string` | yes |  |
| `time` | `string` | yes |  |
| `status` | `enum { confirmed, waitlisted }` | yes |  |

## Steps

1. Verify the doctor has a free slot at the requested time.
2. Create the appointment and journal it.
3. Reply with the appointment ID and arrival instructions.

## Flow

In flow `care` (starts at `find-doctor`):
- on `found` → `book-appointment`
- on `none` → `find-doctor`

## Safety and escalation

The pack source declares this escalation policy (context schema `ClinicContext`):

Default tiers by action:
- `message.send` → **auto**
- `appointment.book` → **confirm**
- `appointment.cancel` → **confirm**

- Rule `emergency`: when `is_emergency == true` → tier **human_only**.
- Rule `fallback` (fallback): everything else → **confirm**.

Mutating actions (booking, cancellation) require confirmation by default, and the emergency rule escalates to a human. This pack handles front-desk logistics only; it does not give medical advice.
