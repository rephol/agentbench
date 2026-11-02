class PatchError(Exception):
    """Raised when a patch is malformed or does not apply."""


def apply_patch(original, patch):
    """Apply a single-file unified diff to `original` (a str) and return the new text.

    - Lines before the first "@@" (such as "--- a/x", "+++ b/x", "diff ..." headers) are ignored.
    - Hunk headers look like "@@ -a,b +c,d @@ optional text". A missing ",b" or ",d"
      means a count of 1. For a hunk whose old count is 0, `a` is the line AFTER WHICH the
      new lines go (so "-0,0" inserts at the very start); otherwise `a` is the 1-based
      first line of the hunk in the original.
    - Hunk body lines start with " " (context), "-" (removed) or "+" (added). A completely
      empty line inside a hunk counts as an empty context line. A line starting with
      "\\" ("\\ No newline at end of file") says the line directly above it has no
      trailing newline, in the old text (if it is a context or "-" line) or the new text
      (if it is a context or "+" line).
    - Context and "-" lines must match the original exactly, including whether the line
      ends with a newline; otherwise raise PatchError. Hunks must appear in order and
      must not overlap; a hunk whose body is shorter than its header counts raise PatchError.
    - Only "\n" separates lines. An empty patch (no hunks) returns `original` unchanged.
    """
    raise NotImplementedError
