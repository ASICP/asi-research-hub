from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
jwt = JWTManager(app)

with app.app_context():
    token = create_access_token(identity='1') # User ID 1
    print(token)
