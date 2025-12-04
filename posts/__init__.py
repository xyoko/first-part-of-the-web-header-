from flask import Blueprint

bp = Blueprint('posts', __name__, url_prefix='/recipes')

from . import routes
