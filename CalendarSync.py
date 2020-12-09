import caldav
import datetime
import logging
import re
import vobject

class CalendarSync(object):
    log = logging.getLogger("CalendarSync")

    startTime = "06:00"

    def __init__(self):
        self._calendar = None
        self._client = None

    def connect(self, url, user, passwd):
        self._client = caldav.DAVClient(url=url, username=user, password=passwd)

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def getExistingMuellEvents(self) -> list[caldav.Event]:
        events = self._calendar.events()
        ret = []
        for e in events:
            try:
                uid = e.vobject_instance.vevent.uid.value
                m = re.match(r'(.+)@MyMuell', uid)
                if m is not None:
                    ret.append(e)
            except AttributeError:
                continue
        return ret

    def createEvent(self, uid, summary, date):
        date_start = datetime.datetime.combine(date, datetime.time.fromisoformat(CalendarSync.startTime))
        date_end = date_start + datetime.timedelta(minutes=5)

        cal = vobject.iCalendar()
        ev = cal.add('vevent')
        ev.add("summary").value = summary
        ev.add("dtstart").value = date_start
        ev.add("dtend").value = date_end
        ev.add("uid").value = str(uid) + "@MyMuell"
        ev.add("valarm").add("trigger").value = datetime.timedelta(hours=-12)
        ev.add("valarm").add("trigger").value = datetime.timedelta(hours=0)

        self._calendar.save_event(cal.serialize())

    def syncEvents(self, e):
        self.createEvent(
            e["id"],
            e["title"],
            datetime.datetime.strptime(e["day"], "%Y-%m-%d"))

    def getCalendars(self):
        principal = self._client.principal()
        cals = principal.calendars()
        ret = []
        for c in cals:
            ret.append(c.name)
        return ret

    def createCalendar(self, cal):
        principal = self._client.principal()
        cals = principal.calendars()

        for c in cals:
            if c.name == cal:
                self._calendar = c

        if self._calendar is None:
            CalendarSync.log.info("creating new calendar \"{}\"".format(cal))
            self._calendar = principal.make_calendar(name=cal)