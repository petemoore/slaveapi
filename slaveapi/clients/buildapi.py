from calendar import timegm
from datetime import datetime
from furl import furl
from pytz import timezone, utc
import requests

import logging
log = logging.getLogger(__name__)

def fix_pacific_timestamp(ts):
    """BuildAPI gives us unix timestamps that are in Pacific time. This is bad
    because timestamps are expected to be in epoch time. This function fixes
    such a timestamp. This can probably be removed
    when https://bugzilla.mozilla.org/show_bug.cgi?id=931854 is fixed.
    """
    pacific_time = timezone("America/Los_Angeles")
    # First, get the timestamp into a datetime object. At this point it is
    # ahead by however many hours the UTC-Pacific offset is.
    starttime = datetime.utcfromtimestamp(ts)
    # Now we need to pretend that it's actually in UTC time so that we can
    # properly adjust the offset (because it differs depending on the day).
    # The datetime hasn't changed at all yet, we've just added timezone
    # information to it.
    starttime = starttime.replace(tzinfo=utc)
    # astimezone() will fix the offset, accounting for daylight savings time.
    # Because the datettime isn't actually in UTC time this might be incorrect
    # for a small window (7-8h I think) whenever daylight savings time starts
    # or ends. I don't think we can do any better than this. After this, the
    # datetime in correct but astimezone() has set the tzinfo to Pacific.
    starttime = starttime.astimezone(pacific_time)
    # Finally, we re-adjust the timezone to be correct again.
    starttime = starttime.replace(tzinfo=utc)

    # Now that we have a proper datetime the rest is easy! We just convert it
    # to a unix timestamp again.
    return timegm(starttime.utctimetuple())

def get_recent_jobs(slavename, api, n_jobs=None):
    url = furl(api)
    url.path.add("recent/%s" % slavename)
    url.args["format"] = "json"
    if n_jobs:
        url.args["numbuilds"] = n_jobs
    log.debug("%s - Making request to %s", slavename, url)
    r = requests.get(str(url)).json()
    for build in r:
        build["starttime"] = fix_pacific_timestamp(build["starttime"])
        build["endtime"] = fix_pacific_timestamp(build["endtime"])
    return r
