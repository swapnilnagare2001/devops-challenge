from flask import Flask, jsonify
import redis, os, time

app = Flask(__name__)
r = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis-service'),
    port=6379, decode_responses=True
)

@app.route('/')
def index():
    r.incr('hits')
    hits = r.get('hits')
    return jsonify({
        "message": "Hello I'm Swapnil, An aspiring DevOps Engineer!",
        "hits": hits,
        "hostname": os.getenv('HOSTNAME', 'unknown')
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/ready')
def ready():
    try:
        r.ping()
        return jsonify({"status": "ready"}), 200
    except:
        return jsonify({"status": "not ready"}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
