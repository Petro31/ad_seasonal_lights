import appdaemon.plugins.hass.hassapi as hass
import voluptuous as vol
from datetime import timedelta, datetime, time, date

MODULE = 'seasonal_lights'
CLASS = 'SeasonalLights'
BINARY_SENSOR = 'binary_sensor'

# General

CONF_AT = 'at'
CONF_CLASS = 'class'
CONF_DATE = 'date'
CONF_DAY = 'day'
CONF_END_DATE = 'end_date'
CONF_ENTITIES = 'entities'
CONF_ENTITIES = 'entities'
CONF_ENTITY = 'entity'
CONF_HOUR = 'hour'
CONF_LOG_LEVEL = 'log_level'
CONF_MINUTE = 'minute'
CONF_MODULE = 'module'
CONF_MONTH = 'month'
CONF_NAME = 'name'
CONF_PLATFORM = 'platform'
CONF_SECOND = 'second'
CONF_SERVICE_DATA = 'service_data'
CONF_START_DATE = 'start_date'
CONF_TIME = 'time'
CONF_TURN_OFF_TIME = 'turn_off_time'
CONF_TURN_ON_TIME = 'turn_on_time'
CONF_WEEK = 'week'

# States

STATE_ON = 'on'
STATE_OFF = 'off'

# logs

LOG_ERROR = 'ERROR'
LOG_DEBUG = 'DEBUG'
LOG_INFO = 'INFO'

ICON_ON = 'mdi:leaf'
ICON_OFF = 'mdi:leaf-off'

# attributes
ATTRIBUTE_IN_SEASON = 'in_season'
ATTRIBUTE_START = 'start'
ATTRIBUTE_END = 'end'
ATTRIBUTE_ON_AT = 'on_at'
ATTRIBUTE_OFF_AT = 'off_at'
ATTRIBUTE_FRIENDLY_NAME = 'friendly_name'
ATTRIBUTE_ICON = 'icon'

# formats

TIME_FORMAT = "%H:%M:%S"
DATE_FORMAT = r"%m/%d"
ATTRIBUTE_FORMAT = "%Y-%m-%dT%H:%M:%S"

# schemas

MONTH_WEEK_DAY_SCHEMA = {
    vol.Required(CONF_MONTH): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
    vol.Required(CONF_WEEK): vol.All(vol.Coerce(int), vol.Range(min=0, max=5)),
    vol.Required(CONF_DAY): vol.All(vol.Coerce(int), vol.Range(min=0, max=6)),
}

MONTH_DAY_SCHEMA = {
    vol.Required(CONF_MONTH): vol.All(vol.Coerce(int), vol.Range(min=1, max=12)),
    vol.Required(CONF_DAY): vol.All(vol.Coerce(int), vol.Range(min=1, max=31)),
}

ENTITIES_SCHEMA = [
    vol.Any(
        str,
        { 
            vol.Required(CONF_ENTITY): str,
            vol.Optional(CONF_SERVICE_DATA): {str: vol.Any(int, str, bool, list, dict)},
        })]

def ConfTime(value):
    return datetime.strptime(value, TIME_FORMAT)

def ConfDate(value):
    return datetime.strptime(value, DATE_FORMAT)

APP_SCHEMA = vol.Schema({
    vol.Required(CONF_MODULE): MODULE,
    vol.Required(CONF_CLASS): CLASS,
    vol.Required(CONF_START_DATE): vol.Any(
        MONTH_WEEK_DAY_SCHEMA,
        MONTH_DAY_SCHEMA,
        ConfDate,
    ),
    vol.Required(CONF_END_DATE): vol.Any(
        MONTH_WEEK_DAY_SCHEMA,
        MONTH_DAY_SCHEMA,
        ConfDate,
    ),
    vol.Optional(CONF_TURN_ON_TIME, default="00:00:00"): ConfTime,
    vol.Optional(CONF_TURN_OFF_TIME, default="23:59:59"): ConfTime,
    vol.Optional(CONF_ENTITIES, default=[]): ENTITIES_SCHEMA,
    vol.Optional(CONF_NAME): str,
    vol.Optional(CONF_LOG_LEVEL, default=LOG_DEBUG): vol.Any(LOG_INFO, LOG_DEBUG),
})

class SeasonalLights(hass.Hass):
    def initialize(self):
        args = APP_SCHEMA(self.args)

        # Set Lazy Logging (to not have to restart appdaemon)
        self._level = args.get(CONF_LOG_LEVEL)
        self.log(args, level=self._level)

        # Required
        self._startdate = self._get_app_date(args.get(CONF_START_DATE))
        self._enddate = self._get_app_date(args.get(CONF_END_DATE))

        # Evaluate the dates
        if self._enddate < self._startdate:
            # Add a year if the date is before the start.
            self.log("End date is before start date, adding a year.", level=self._level)
            self._enddate = self._enddate.replace(year=datetime.now().year+1)

        name = self.name.replace('_',' ').title()
        self._friendly_name = args.get(CONF_NAME, name)
        self._sensor = f"{BINARY_SENSOR}.{self._friendly_name.lower().replace(' ','_')}"

        self.log(f"Start Date: {self._startdate}", level=self._level)
        self.log(f"End Date: {self._enddate}", level=self._level)

        self._entities = [ AppEntity(e) for e in args.get(CONF_ENTITIES) ]
        self._starttime = args.get(CONF_TURN_ON_TIME).time()
        self._endtime = args.get(CONF_TURN_OFF_TIME).time()

        midnight = time(0,0,0)
        self.log(f"Running daily at {midnight.strftime(TIME_FORMAT)}", level=self._level)
        self.run_daily(self.run_season, midnight)

        if self._entities:
            self.log(f"Running daily '{self._sensor}' '{STATE_ON}' at '{self._starttime.strftime(TIME_FORMAT)}'", level=self._level)
            self.run_daily(self.run_turn_on, self._starttime)

            self.log(f"Running daily '{self._sensor}' '{STATE_OFF}' at '{self._endtime.strftime(TIME_FORMAT)}'", level=self._level)
            self.run_daily(self.run_turn_on, self._endtime)

        #Update Sensor on Startup
        self.run_season(None)

    def update_year(self):
        """ updates the current year incase we cross the mark """
        year = datetime.now().year
        self._startdate.replace(year = year)
        self._enddate.replace(year = year)
        if self._enddate < self._startdate:
            # Add a year if the date is before the start.
            self._enddate.replace(year=year+1)

    @property
    def in_season(self):
        t = datetime.now().date()
        if t > self._enddate:
            # this should only be hit after an exented period of app on time.
            self.update_year()
        ret = self._startdate <= t <= self._enddate
        #self.log(f"'in_season' {ret}: {self._startdate} <= {t} <= {self._enddate}", level=self._level)
        return ret

    def date_or_time_to_attribute(self, value):
        if isinstance(value, date):
            ret = datetime(value.year, value.month, value.day, 0, 0, 0, 0)
        elif isinstance(value, time):
            ret = datetime.now().replace(
                hour=value.hour, 
                minute=value.minute, 
                second=value.second, 
                microsecond=0)
        else:
            ret = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        return ret.strftime(ATTRIBUTE_FORMAT)

    def run_season(self, kwargs):
        self.log(f"'run_season' executed at '{datetime.now().strftime(TIME_FORMAT)}'", level=self._level)
        state = STATE_ON if self.entities_on() else STATE_OFF
        self._update_sensor(state)

    def entities_on(self):
        if self.in_season:
            if self._entities:
                t = datetime.now().time()
                if self._starttime < self._endtime:
                    return self._starttime <= t <= self._endtime
                else:
                    day_start = time(0,0,0)
                    day_end = time(23,59,59,999999)
                    return day_start <= t <= self._endtime or self._starttime <= t <= day_end
            else:
                # we just want a season thats on/off
                return True
        else:
            return False

    def _turn_state_entities(self, state):
        self.log(f"'run_turn_{state}' executed at '{datetime.now().strftime(TIME_FORMAT)}'", level=self._level)
        if self.in_season and self._entities:
            self._update_sensor(state)
            for ae in self._entities:
                entity_id, attributes = ae.entity_id, ae.attributes
    
                if state == STATE_ON:
                    if attributes:
                        self.turn_on(entity_id, **attributes)
                    else:
                        self.turn_on(entity_id)
                else:
                    self.turn_off(entity_id)

    def _update_sensor(self, state):
        icon = ICON_ON if self.in_season else ICON_OFF
        attributes = {
            ATTRIBUTE_FRIENDLY_NAME: self._friendly_name,
            ATTRIBUTE_ICON: icon,
            ATTRIBUTE_IN_SEASON: self.in_season,
            ATTRIBUTE_START: self.date_or_time_to_attribute(self._startdate),
            ATTRIBUTE_END: self.date_or_time_to_attribute(self._enddate),
        }
        if self._entities:
            on_at = self.date_or_time_to_attribute(self._starttime) if self.in_season else None
            off_at = self.date_or_time_to_attribute(self._endtime) if self.in_season else None
            attributes[ATTRIBUTE_ON_AT] = on_at
            attributes[ATTRIBUTE_OFF_AT] = off_at

        self.log(f"'{self._sensor}' -> {state}: {attributes}", level = self._level)
        self.set_state(self._sensor, state=state, attributes=attributes)

    def run_turn_on(self, kwargs):
        self._turn_state_entities(STATE_ON)

    def run_turn_off(self, kwargs):
        self._turn_state_entities(STATE_OFF)

    def nth_weekday(self, the_date, nth_week, week_day):
        temp = the_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        adjust = (week_day - temp.weekday()) % 7
        temp += timedelta(days=adjust)
        temp += timedelta(weeks=nth_week-1)
        return temp.date()

    def _get_app_date(self, conf):
        """ gets datetime.date() from conf """
        ret = None
        if isinstance(conf, dict):
            # init
            year = datetime.now().year
            month = conf.get(CONF_MONTH)
            week = conf.get(CONF_WEEK)
            day = conf.get(CONF_DAY)

            if month is not None and week is not None and day is not None:
                # ret = datetime.date() object
                ret = self.nth_weekday(
                    datetime(year, month, 1),
                    week, 
                    day)

            elif month is not None and day is not None:
                # ret = datetime.date() object
                ret = datetime(year, month, day).date()

        elif isinstance(conf, datetime):
            ret = conf
            ret.replace(year=datetime.now().year)
            # ret = datetime.date() object
            ret = ret.date()

        if ret is None:
            # Return todays date, this will result in an error later.
            ret = datetime.now().date()

        return ret

class AppEntity(object):
    def __init__(self, conf):
        self.attributes = {}
        if isinstance(conf, dict):
            self.entity_id = conf.get(CONF_ENTITY)
            self.attributes = conf.get(CONF_SERVICE_DATA, {})            
        elif isinstance(conf, str):
            self.entity_id = conf
 
