from py2neo import Graph
import spacy

from flask import Flask, render_template
from flask_socketio import SocketIO

from KGB import KGB

nlp = spacy.load('en_core_web_lg')
print("NLP Model Loaded")
# self.nlp = spacy.load('en')
graph = Graph(password="admin")
engine = KGB(nlp, graph, True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
socketio = SocketIO(app)


@app.route('/')
def sessions():
    return render_template('chat.html')

@socketio.on('connected')
def handle_connected(message, methods=['GET']):
    print('User connected')


@socketio.on('message')
def handle_incoming_event(json, methods=['GET', 'POST']):
    print('received event: ' + str(json))
    json = engine.parse(nlp(json['message']))
    print(json)
    socketio.emit('response', json)


if __name__ == '__main__':
    print("System ready")
    socketio.run(app)