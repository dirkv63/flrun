from flask import Blueprint
print("Line 1")
main = Blueprint('main', __name__)
print("Line 2")

from . import routes
print("Line 3")
