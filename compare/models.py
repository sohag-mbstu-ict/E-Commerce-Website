# Compare is intentionally stateless on the server side - it's tracked via
# the visitor's session (see compare/utils.py) so guests can use it too,
# the same way the cart works before login.
