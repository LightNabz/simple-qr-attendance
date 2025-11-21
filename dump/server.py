from flask import Flask

app = Flask(__name__)

@app.route('/user<int:user_id>/timeout', methods=['GET'])
def timeout(user_id):
    print(f"Timeout received for user {user_id}")
    return f"Timeout handled for user {user_id}", 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
