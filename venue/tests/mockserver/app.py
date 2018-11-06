from flask import Flask
from flask import Response
import json


app = Flask(__name__)


@app.route('/bitcointalk/<params>')
def bitcointalk(params):
    response = {}
    return Response(
        json.dumps(response),
        status=500,
        mimetype='application/json'
    )


app.run(host='0.0.0.0', port=5000)
