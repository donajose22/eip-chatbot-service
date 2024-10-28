from flask import Flask
from flask_cors import CORS
from flask_talisman import Talisman

app = Flask(__name__)
CORS(app)
Talisman(app,force_https=False)

@app.route('/')
def hello_world():
    return "hello world"

#--------------------------
from routes.inference import inference
#from embedding import embedding
#--------------------------
app.register_blueprint(inference, url_prefix='/')
#app.register_blueprint(embedding, url_prefix='/')
#--------------------------

if __name__ == '__main__':
    app.run(debug=True)