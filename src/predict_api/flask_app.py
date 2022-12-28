import json

import requests
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
from dotenv import load_dotenv
from flask import Flask, g, redirect, request, url_for, jsonify
from flask_cors import CORS
from config import Config, logging
from flask import jsonify
from flask_login import login_required

load_dotenv()

spec = APISpec(
    title="Prediction API",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

app = Flask(__name__)
cors = CORS(app)
app.secret_key = Config.SECRET_KEY

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        "errors": [
            {
                "status": "400",
                "detail": str(e)
            },
        ]
    }), 400

@app.errorhandler(404)
def resource_not_found(e):
    return jsonify({
        "errors": [
            {
                "status": "404",
                "detail": str(e)
            },
        ]
    }), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify({
        "errors": [
            {
                "status": "500",
                "detail": str(e)
            },
        ]
    }), 500

@app.route('/')
def home():
    
    from flask import url_for
    def has_no_empty_params(rule):
        defaults = rule.defaults if rule.defaults is not None else ()
        arguments = rule.arguments if rule.arguments is not None else ()
        return len(defaults) >= len(arguments)

    
    
    for rule in app.url_map.iter_rules():
        if has_no_empty_params(rule):
            logging.info(f'{rule.methods}, {rule.endpoint}, {rule.rule}')

    return "hello world"


import views.api
