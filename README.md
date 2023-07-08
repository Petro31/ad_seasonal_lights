# Home Assistant Seasonal Lights Appdeamon App

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
<br><a href="https://www.buymeacoffee.com/Petro31" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-black.png" width="150px" height="35px" alt="Buy Me A Coffee" style="height: 35px !important;width: 150px !important;" ></a>

_Seasonal Lights app for AppDaemon._

Creates a season binary_sensor.  The automation will turn on/off lights at the specified times.

## Installation

1. Add the voluptuous depenedency to AppDaemon.

2. Download the `seasonal_lights` directory from inside the `apps` directory to your local `apps` directory, then add the configuration to enable the `hacs` module.

## Example App configuration

#### Basic (Season only)
```yaml
# basic christmas season.
christmas_season:
  module: seasonal_lights
  class: SeasonalLights
  start_date:
    # Thanksgiving, 4th day in the 5th week.
    month: 11
    week: 4
    day: 3
  end_date:
    # Christmas Day, 25th of December
    month: 12
    day: 25
```

#### Advanced (Season & Lights)
```yaml
# basic christmas season.
christmas_season:
  module: seasonal_lights
  class: SeasonalLights
  start_date:
    # Thanksgiving, 4th day in the 5th week.
    month: 11
    week: 4
    day: 3
  end_date:
    # Christmas Day, 25th of December
    month: 12
    day: 25
  turn_on_time: '17:00:00'
  turn_off_time: '22:00:00'
  entities:
  - switch.holiday
  - entity: light.holiday
    service_data:
      brightness: 100
      kelvin: 2700
  - entity: light.holiday_2
    service_data:
      brightness: 130
      rgb_color: [255,0,0]
```

#### App Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`module` | False | string | `seasonal_lights` | The module name of the app.
`class` | False | string | `SeasonalLights` | The name of the Class.
`start_date` | False | map | | date map, start of the season.
`end_date` | False | map | | date map, end of the season.
`turn_on_time` | False | str | `'00:00:00'` | date map, end of the season.
`turn_off_time` | False | str | `'23:59:59'` | date map, end of the season.
`entities`| True | list | | A list of entity_id's or entity objects.
`log_level` | True | `'INFO'` &#124; `'DEBUG'` | `'INFO'` | Switches log level.

#### Date Map Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`month` | False | int | | The month.  `1` is January. `12` is December.
`day` | False | int | | The day number of the event.  `1` = first day in the month.  You will get errors if you set the day beyond the number of days in the month.

#### Date Map nth Weekday Configuration
key | optional | type | default | description
-- | -- | -- | -- | --
`month` | False | int | | The month the nth weekday occurs.  `1` is January. `12` is December.
`week` | False | int | | The week number of the event, first week being `0`.  The max number of weeks in a month is `5`.  This is a VERY rare occurance.  Most months are `0` to `4` weeks long.
`day` | False | int | | The day number of the event.  `0` = first day in the week, typically a monday. This gets wonky if it's not a complete week.
