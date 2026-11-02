"""Cron schedule evaluation.

next_fire(expr, after) -> datetime

`expr` is a standard 5-field cron expression: minute hour day-of-month month day-of-week.
`after` is a naive `datetime`. Return the earliest datetime STRICTLY later than `after`
(seconds and microseconds of `after` are ignored: 12:00:30 counts as 12:00, so the
answer is 12:01 at the earliest) at which the schedule fires. The result has seconds == 0.

Field syntax (fields are separated by one or more spaces/tabs):
* `*` every value; `*/n` every n-th value starting at the field minimum;
* `a` a single value; `a-b` an inclusive range; `a-b/n` a range with step n;
  `a/n` means `a-<max>/n`; a comma-separated list of any of those items.
* Ranges: minute 0-59, hour 0-23, day-of-month 1-31, month 1-12, day-of-week 0-7
  (both 0 and 7 mean Sunday).
* Month names JAN..DEC and weekday names SUN..SAT (any case) work in single values
  and ranges (`mon-fri`, `jan,jul`, `mon-sun/2`). As the END of a range, `sun` means 7
  (so `mon-sun` is Monday through Sunday).
* A range whose start is greater than its end (wrapping, e.g. `fri-mon`, `22-3`) is an
  error. Step must be >= 1. Values out of range, unknown names, wrong field count, or empty
  items raise ValueError.

Day matching: if BOTH day-of-month and day-of-week are restricted (neither field text
starts with `*`), a day matches when EITHER field matches. If only one is restricted
(the other starts with `*`), only the restricted one is used. If neither is restricted
every day matches. Note `*/2` starts with `*`, so it counts as unrestricted for this rule.

A day-of-month that does not exist in a month (the 31st of April, Feb 30) never matches
in that month. `0 0 29 2 *` fires only on leap days. If the schedule can never fire
(e.g. `0 0 30 2 *`) raise ValueError (search at most 9 years ahead, which covers every
satisfiable expression including leap-day-only ones across the 2100 non-leap year).
"""
from datetime import datetime


from datetime import timedelta
import calendar

_MONTHS = {n: i for i, n in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DAYS = {n: i for i, n in enumerate(["sun", "mon", "tue", "wed", "thu", "fri", "sat"])}


def _val(tok, lo, hi, names, end=False):
    t = tok.lower()
    if end and t == "sun" and names is _DAYS:
        return 7
    if t in names:
        return names[t]
    if not tok.isdigit() or not tok.isascii():
        raise ValueError("bad value %r" % (tok,))
    v = int(tok)
    if not lo <= v <= hi:
        raise ValueError("value out of range %r" % (tok,))
    return v


def _field(text, lo, hi, names):
    out = set()
    for item in text.split(","):
        if not item:
            raise ValueError("empty item")
        base, sep, step = item.partition("/")
        if sep:
            if not step.isdigit() or int(step) < 1:
                raise ValueError("bad step")
            step = int(step)
        else:
            step = 1
        if base == "*":
            a, b = lo, hi
        elif "-" in base:
            x, y = base.split("-", 1)
            a, b = _val(x, lo, hi, names), _val(y, lo, hi, names, end=True)
            if a > b:
                raise ValueError("wrapping range")
        else:
            a = _val(base, lo, hi, names)
            b = hi if sep else a
        out.update(range(a, b + 1, step))
    return out


def next_fire(expr, after):
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError("need 5 fields")
    mins = _field(parts[0], 0, 59, {})
    hours = _field(parts[1], 0, 23, {})
    doms = _field(parts[2], 1, 31, {})
    months = _field(parts[3], 1, 12, _MONTHS)
    dows = {d % 7 for d in _field(parts[4], 0, 7, _DAYS)}
    dom_r, dow_r = not parts[2].startswith("*"), not parts[4].startswith("*")

    def day_ok(d):
        if d.month not in months:
            return False
        dm = d.day in doms
        dw = (d.isoweekday() % 7) in dows
        if dom_r and dow_r:
            return dm or dw
        if dom_r:
            return dm
        if dow_r:
            return dw
        return True

    start = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
    day = start.replace(hour=0, minute=0)
    limit = start.replace(year=start.year + 9)
    first = True
    while day <= limit:
        if day_ok(day):
            for h in sorted(hours):
                for m in sorted(mins):
                    cand = day.replace(hour=h, minute=m)
                    if cand >= start:
                        return cand
        day += timedelta(days=1)
    raise ValueError("schedule never fires")
