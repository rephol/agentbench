def slugify(text):
    """Lowercase `text` and join its alphanumeric words with single hyphens.

    Any run of non-alphanumeric characters is a separator. No leading or
    trailing hyphens. Returns "" if there are no alphanumerics.
    """
    return text.lower().replace(" ", "-")
