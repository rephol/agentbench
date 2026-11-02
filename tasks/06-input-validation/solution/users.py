def create_user(name, email, age):
    """Build a user record."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("name must be a non-empty string")
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    email = email.strip().lower()
    local, sep, domain = email.partition("@")
    if not sep or "@" in domain or not local or not domain:
        raise ValueError("invalid email")
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("invalid email domain")
    if not isinstance(age, int) or isinstance(age, bool) or not 0 <= age <= 150:
        raise ValueError("age must be an int between 0 and 150")
    return {"name": name.strip(), "email": email, "age": age}
