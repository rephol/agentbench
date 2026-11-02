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


def next_fire(expr, after):
    raise NotImplementedError
