from flask import Flask, render_template, request, jsonify
from Human import PlayOnline


app = Flask(__name__)
player = PlayOnline()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/player/<string:id>')
def goChess(id):
    point = request.args['point']
    res = player.AI_play_online(int(point), int(id))
    return jsonify(res)


@app.route('/restart')
def restart():
    player.reset()
    return render_template('index.html')


if __name__ == '__main__':
    player.init('../model/best_94_policy_model')
    app.run(host='127.0.0.1', port=8877, debug=True)
