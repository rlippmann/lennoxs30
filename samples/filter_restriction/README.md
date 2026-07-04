# Lennox Filter Restriction Monitor Sample

## Purpose

This directory contains an advanced Home Assistant package sample for monitoring possible filter restriction using Lennox runtime diagnostics and blower-effort proxy metrics.

This sample is intended for experienced users who are comfortable validating entity mappings, reviewing package YAML, and dogfooding before relying on alerts.

## Components

Contents:

- `lennox_filter_restriction_monitor_package_sample.yaml`

The package includes:

- helper entities
- statistics sensors
- template sensors
- one binary sensor for possible filter restriction
- one user-facing filter replacement event marker script
- one snapshot collector automation
- one watchdog automation

## Important Safety Notes

- This is an advanced sample and should be used with caution.
- The package may temporarily raise Lennox diagnostic level to `1` during sampling if the system is not already at that level.
- The watchdog automation should always be enabled whenever the snapshot collector automation is enabled.
- The package is not installed automatically and is not part of the active integration runtime.
- This sample should be validated and dogfooded before it is used for operational alerts.

## Dehumidification and Drying Caveat

- Some systems may spend long periods in `hvac_action = drying` rather than `cooling`.
- This sample only captures samples during `cooling` or `heating`.
- Drying or dehumidification-heavy runtime may therefore prevent sample collection.
- Drying-state samples should not be mixed into cooling baselines unless separately validated for the specific system.

## Variable-Speed Airflow Caveat

- Variable-capacity Lennox systems may legitimately report blower airflow below the exposed "normal cooling airflow" parameter values.
- v3 no longer requires CFM to remain above the exposed low "normal cooling airflow" parameter.
- Low airflow can be valid during variable-speed operation, so the package records climate demand for context instead of using low airflow as a hard rejection rule.
- A high-airflow sanity bound is still applied to reject implausible values, and those bounds may still require local tuning.
- Do not treat this sample as universally valid for all Lennox systems, zoning configurations, or dehumidification setups.
- This sample does not claim to detect all filter restrictions and should be treated as a diagnostic aid rather than a universal fault detector.

## Customization Checklist

Before enabling the sample:

- verify entity mappings for the target system
- validate Home Assistant configuration
- enable the watchdog together with the collector
- verify diagnostic level restores correctly after a sample attempt
- review airflow bounds against local equipment behavior
- dogfood the package before relying on alerts or automations built on top of it

## Trend And Step-Change Direction

The package is moving toward trend and step-change monitoring rather than requiring a manual clean-filter baseline workflow before the monitor is useful.

The collector can gather accepted samples without any user-marked replacement event. This means you can install the package, validate it, enable the collector and watchdog, and begin building history immediately.

## Mark Filter Replaced

The package includes a user-facing `Mark Filter Replaced` script.

This script is an event marker, not a required baseline-generation step.

When run, it:

- records the replacement timestamp
- records a `filter_replaced` event marker
- optionally snapshots the current rolling means into existing baseline/reference helpers when enough valid data already exists

The script does not force a new sample capture. It uses whatever accepted rolling-average data already exists at the time you mark the event.

Marking a replacement is still useful because it gives later analysis an explicit point for comparing pre/post filter behavior, even if the monitor had already been collecting data before the replacement.

The older `Set Clean Filter Baseline` script name is retained only as a deprecated compatibility wrapper around `Mark Filter Replaced`.

## Build / Usage Notes

- This is a generic sample package that uses explicit `SYSTEM_PREFIX` and `SYSTEM_LABEL` placeholders.
- Generated installation-specific package variants are intentionally not included in this repository.
- No unsupported airflow formulas are assumed in this sample package. Local tuning and validation are expected.
- Helper ranges and example tuning values in the sample are defaults for initial setup, not intended restart-reset values.
- For the tuning helpers and `last_sample_mode`, Home Assistant should restore user-changed values across restart rather than resetting them from YAML.
- The generator derives the display label automatically from the system prefix.
  Example: `upstairs` -> `Upstairs`, `main_house` -> `Main House`.
- Home Assistant should restore each automation's prior enabled/disabled state across restart rather than resetting it from YAML.
- The snapshot collector automation polls every 10 minutes.
- The snapshot cooldown helper controls eligibility; it does not control the trigger cadence.
- When a polling check finds the system eligible, the automation waits 60 seconds before raising diagnostics.
- After the required diagnostic entities populate, the automation waits an additional 15 seconds before beginning the bounded capture/retry loop.
- Diagnostics are kept on only for the capture attempt and capture window, then restored as part of cleanup.
- Accepted samples still require these core entities to be available and valid:
  `sensor.<prefix>_iu_blower_cfm_demand`, `sensor.<prefix>_iu_indoor_blower_rpm`,
  `sensor.<prefix>_iu_indoor_blower_power`, `sensor.<prefix>_iu_defrost_status`,
  `sensor.<prefix>_iu_dehumidification_relay_status`,
  `sensor.<prefix>_iu_humidification_relay_status`,
  `number.<prefix>_diagnostic_level`, and `climate.<prefix>_zone_1`.
- Optional debug/context entities do not gate acceptance. If they are missing or unavailable, the sample records `0` or `unknown` and continues cleanup normally.
- The current optional debug/context reads include `sensor.<prefix>_ou_compressor_hz`,
  `sensor.<prefix>_ou_cooling_rate`, `sensor.<prefix>_ou_heating_rate`, and the
  accepted-sample debug helpers populated from them.
- Static pressure remains a manual, on-demand diagnostic exercise and is not currently part of this sample package.
- RPM/CFM remains the primary experimental detection metric in this sample.
- Power/CFM remains secondary and observational rather than the primary detection signal.
- Accepted-sample debug helpers record the last observed HVAC action, compressor Hz, cooling rate, heating rate, and live diagnostic level to make accepted captures easier to interpret during dogfooding.
- The replacement marker can optionally refresh existing baseline/reference helpers, but normal monitoring does not depend on that step.

Use the helper script to generate an installation-specific package:

```bash
./generate_sample_package.sh OUTPUT_FILE SYSTEM_PREFIX
```

Example:

```bash
./generate_sample_package.sh /tmp/upstairs_filter_package.yaml upstairs
```

Arguments:

- `OUTPUT_FILE`: path to the generated Home Assistant package YAML.
- `SYSTEM_PREFIX`: replacement for entity IDs and references, such as `upstairs` or `downstairs`.
