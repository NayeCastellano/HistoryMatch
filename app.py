from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import model
from io import StringIO

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/procesar', methods=['POST'])
def procesar():
    print("Headers ===> ", request.headers)
    print("Files keys ===> ", request.files.keys())
    print("Form keys ===> ", request.form.keys())
    
    if 'archivo' not in request.files:
        return jsonify({"error": "Archivo no encontrado"}), 400

    file = request.files['archivo']

    if file.filename == '':
        return jsonify({"error": "Archivo sin nombre"}), 400

    try:
        resultado = model.procesar_archivo_para_api(file)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
