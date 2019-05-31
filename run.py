from lazystatus.lazystatus import LazyStatus
from flask import Flask                                                         
import threading

app = Flask(__name__)

@app.route("/connect/github", methods=["POST"])
def process_github():
    
    return "Hello"

if __name__ == "__main__":
    flask_app = threading.Thread(target=app.run)
    flask_app.daemon = True
    flask_app.start()
    bot = LazyStatus()
    bot.connect()