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

## Build / Usage Notes

- This is a generic sample package that uses a `system` prefix and is intended for search/replace into a real installation.
- Local dogfood copies for specific systems are intentionally not included here.
- No unsupported airflow formulas are assumed in this sample package. Local tuning and validation are expected.
