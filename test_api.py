# test_api.py
from flask import Flask, request, jsonify

app = Flask(__name__)

def compute_expectation(data_list):
    """Простой пример: мат. ожидание для списка чисел."""
    if not data_list:
        return None
    return sum(data_list) / len(data_list)

@app.route('/api/process_mock', methods=['POST'])
def process_mock():
    payload = request.get_json(force=True)
    # ожидаем, что payload = { "values": [числа...] }
    values = payload.get('values', [])
    expectation = compute_expectation(values)
    return jsonify({ "expectation": expectation })

if __name__ == "__main__":
    # отключаем дебаг-режим, если не нужно
    app.run(port=5001)
