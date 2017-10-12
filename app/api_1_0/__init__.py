from flask import Blueprint
from ..models import Permission

api = Blueprint('api', __name__)

from . import views, errors
