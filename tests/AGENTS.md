# Test suite

## Composition

- Build test data with the builders in `tests/builders/` (`MerakiDeviceBuilder`,
  `SensorDataBuilder`, `DeviceStatusBuilder`, `HubBuilder`, `IntegrationTestHelper`) instead of
  hand-written dicts, so entity expectations stay in step with production code.
- Presets in `tests/builders/presets.py` are static methods, not constants:
  `DevicePresets.mt_sensor_basic()`, `ScenarioPresets.office_environment()`,
  `ErrorScenarioPresets.offline_devices()`.
- `tests/fixtures/meraki_api.py` holds the baseline organization, network and device payloads.
- Never construct `meraki.aio.AsyncDashboardAPI` in a test.
  `IntegrationTestHelper.setup_meraki_integration` patches it and registers the sensor, binary
  sensor and button platforms.

## Traps

- Mutating a mock response does not reach entities on its own. Call
  `await helper.trigger_coordinator_update()` afterwards. `helper.add_sensor_data` writes to the
  mock's `sensor.getOrganizationSensorReadingsLatest` return value.
- A test that starts timers must `await helper.unload_integration()` in teardown, or the callbacks
  outlive it.
- `asyncio_mode = "auto"`, so async tests need no `@pytest.mark.asyncio`.
- `--strict-markers` is on and only `unit`, `integration` and `slow` are registered in
  `pyproject.toml`. Any other marker is a collection error, not a skip.
- Assert against the constants and enums in `custom_components/meraki_dashboard/const.py`, never
  string literals.

## Running

```bash
just test                                                            # whole suite
just test filter="-k meraki"
just test filter="tests/test_hubs_network.py --log-cli-level=DEBUG"
```

Coverage is always on: `--cov` lives in the pytest `addopts`, so there is no separate coverage run
to remember. Local fixtures are disposable; run and rerun the suite freely.
