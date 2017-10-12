from flask import render_template
from . import main


@api.app_errorhandler(403)
def forbidden(message):
    response = jsonify({'error':'forbidden', 'message':message})
    response.status_code = 403
    return response

