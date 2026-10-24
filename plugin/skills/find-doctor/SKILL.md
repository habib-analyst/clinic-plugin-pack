---
name: find-doctor
description: "Find doctors by specialty and day. This skill should be used when the user asks to \"find a doctor\", \"cardiologist available\", \"doctor on monday\"."
version: 0.1.0
---

# find-doctor

Find doctors by specialty and day.

Part of the **clinic** pack (v0.1.0) by Habib Ur Rehman — a clinic front-desk skill pack compiled with [packc](https://github.com/habib-analyst/packc) from the typed source `src/clinic.pack` shipped in this plugin.

## When this skill applies

- The user asks to "find a doctor".
- The user asks to "cardiologist available".
- The user asks to "doctor on monday".

## Tool

Backed by the MCP tool `doctors_search` in this plugin's bundled server (`mcp/clinic_mcp_server.py`, registered in `.mcp.json`). The server validates every call against the typed input schema before dispatch.

## Input — `SpecialtyRequest`

| Field | Type | Required | Default |
|---|---|---|---|
| `specialty` | `string` | yes |  |
| `day` | `string?` | no |  |

## Output — `DoctorList`

| Field | Type | Required | Default |
|---|---|---|---|
| `doctors` | `list[Doctor]` | yes |  |

## Steps

1. Parse the specialty and optional day.
2. Search the roster for matching doctors.
3. Reply with names and their available days.

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
