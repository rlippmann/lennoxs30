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
- one user-facing baseline reset script
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

## Establishing a Clean Filter Baseline

The monitor does not automatically know what a clean filter looks like.

Recommended process:

1. Install a new filter.
2. Enable the collector and watchdog automations.
3. Allow the system to collect multiple valid samples.
4. Verify that sample counts have accumulated.
5. Run the baseline script.

The baseline script records the current accepted measurements as the clean-filter reference used for future comparisons.

The script does not force a new sample capture. It uses previously collected valid sample data.

## Baseline Script

The package includes a user-facing script that records the current accepted measurements as the clean-filter baseline.

Run this script:

- after installing a new filter
- after collecting sufficient valid samples

Do not run it immediately after package installation before valid samples exist.

## Build / Usage Notes

- This is a generic sample package that uses explicit `SYSTEM_PREFIX` and `SYSTEM_LABEL` placeholders.
- Generated installation-specific package variants are intentionally not included in this repository.
- No unsupported airflow formulas are assumed in this sample package. Local tuning and validation are expected.
- Helper ranges and example tuning values in the sample are defaults for initial setup, not intended restart-reset values.
- For the tuning helpers and `last_sample_mode`, Home Assistant should restore user-changed values across restart rather than resetting them from YAML.
- The generator derives the display label automatically from the system prefix.
  Example: `upstairs` -> `Upstairs`, `main_house` -> `Main House`.
- The snapshot collector automation polls every 10 minutes.
- The snapshot cooldown helper controls eligibility; it does not control the trigger cadence.
- When a polling check finds the system eligible, the automation waits 60 seconds before raising diagnostics.
- After the required diagnostic entities populate, the automation waits an additional 15 seconds before beginning the bounded capture/retry loop.
- Diagnostics are kept on only for the capture attempt and capture window, then restored as part of cleanup.

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
