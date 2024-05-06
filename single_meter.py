import flask

app = Flask(__name__)
cors = CORS(app, resources={r"/*/*": {"origins": "*"}})
