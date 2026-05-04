# sensor_editar_tabla_r1B_geo.py

import os
import random
import sqlite3
import requests
import geocoder

from datetime import datetime
from flask import Flask, render_template, jsonify, request


app = Flask(__name__)

DB_NAME = "db.datos_sensores"

# Mejor usar variable de entorno:
# export OPENWEATHER_API_KEY="TU_API_KEY"
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "COLOCAR_AQUI_TU_API_KEY")


# ============================================================
# BASE DE DATOS
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME)


def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lectura_sensores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            co2 REAL,
            temp REAL,
            hum REAL,
            fecha TEXT,
            lugar TEXT,
            altura REAL,
            presion REAL,
            presion_nm REAL,
            temp_ext REAL,
            humedad_ext REAL,
            descripcion_clima TEXT
        )
    """)

    conn.commit()
    conn.close()


def obtener_registros():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            id,
            co2,
            temp,
            hum,
            fecha,
            lugar,
            altura,
            presion,
            presion_nm,
            temp_ext,
            humedad_ext,
            descripcion_clima
        FROM lectura_sensores
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    datos = []

    for r in rows:
        datos.append({
            "id": r[0],
            "co2": r[1],
            "temp": r[2],
            "hum": r[3],
            "fecha": r[4],
            "lugar": r[5],
            "altura": r[6],
            "presion": r[7],
            "presion_nm": r[8],
            "temp_ext": r[9],
            "humedad_ext": r[10],
            "descripcion_clima": r[11]
        })

    return datos


# ============================================================
# GEOLOCALIZACION + CLIMA
# ============================================================

def geo_latlon():
    g = geocoder.ip("me")

    if not g.latlng:
        raise Exception("No se pudo obtener la ubicación por IP")

    lat, lon = g.latlng

    url = (
        "https://api.openweathermap.org/data/2.5/weather?"
        f"lat={lat}&lon={lon}"
        f"&appid={OPENWEATHER_API_KEY}"
        "&units=metric"
        "&lang=es"
    )

    response = requests.get(url, timeout=10)
    data = response.json()

    if str(data.get("cod")) not in ["200"]:
        raise Exception(f"Error OpenWeatherMap: {data}")

    main = data["main"]
    weather = data["weather"][0]

    temp_ext = main["temp"]
    presion = main["pressure"]
    humedad_ext = main["humidity"]
    descripcion_clima = weather["description"]

    return {
        "lat": lat,
        "lon": lon,
        "temp_ext": temp_ext,
        "presion": presion,
        "humedad_ext": humedad_ext,
        "descripcion_clima": descripcion_clima
    }


def clima_por_ciudad(ciudad):
    url = (
        "https://api.openweathermap.org/data/2.5/weather?"
        f"q={ciudad}"
        f"&appid={OPENWEATHER_API_KEY}"
        "&units=metric"
        "&lang=es"
    )

    response = requests.get(url, timeout=10)
    data = response.json()

    if str(data.get("cod")) not in ["200"]:
        raise Exception(f"Ciudad no encontrada o error OpenWeatherMap: {data}")

    main = data["main"]
    weather = data["weather"][0]

    return {
        "lat": data["coord"]["lat"],
        "lon": data["coord"]["lon"],
        "temp_ext": main["temp"],
        "presion": main["pressure"],
        "humedad_ext": main["humidity"],
        "descripcion_clima": weather["description"]
    }


# ============================================================
# SIMULACION DE SENSOR
# ============================================================

def simular_lectura(lugar, altura, clima):
    temp_ext = float(clima["temp_ext"])
    presion = float(clima["presion"])

    co2_medido = random.uniform(250, 1100)
    temp_sensor = random.uniform(temp_ext, temp_ext + 10)
    humedad_relativa = random.uniform(40, 80)

    fecha = datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")

    lectura = {
        "co2": round(co2_medido, 2),
        "temp": round(temp_sensor, 2),
        "hum": round(humedad_relativa, 2),
        "fecha": fecha,
        "lugar": lugar,
        "altura": altura,
        "presion": presion,
        "presion_nm": presion,
        "temp_ext": clima["temp_ext"],
        "humedad_ext": clima["humedad_ext"],
        "descripcion_clima": clima["descripcion_clima"]
    }

    return lectura


def insertar_lectura(lectura):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO lectura_sensores (
            co2,
            temp,
            hum,
            fecha,
            lugar,
            altura,
            presion,
            presion_nm,
            temp_ext,
            humedad_ext,
            descripcion_clima
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        lectura["co2"],
        lectura["temp"],
        lectura["hum"],
        lectura["fecha"],
        lectura["lugar"],
        lectura["altura"],
        lectura["presion"],
        lectura["presion_nm"],
        lectura["temp_ext"],
        lectura["humedad_ext"],
        lectura["descripcion_clima"]
    ))

    conn.commit()
    lectura["id"] = cursor.lastrowid
    conn.close()

    return lectura


# ============================================================
# RUTAS WEB
# ============================================================

@app.route("/")
def index():
    return render_template("tabla_sensores_geo.html")


@app.route("/api/datos")
def api_datos():
    return jsonify({
        "data": obtener_registros()
    })


@app.route("/api/clima")
def api_clima():
    ciudad = request.args.get("ciudad")

    try:
        if ciudad:
            clima = clima_por_ciudad(ciudad)
        else:
            clima = geo_latlon()

        return jsonify(clima)

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/capturar", methods=["POST"])
def api_capturar():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Debe enviar JSON"}), 400

    lugar = data.get("lugar", "Sin definir")
    altura = float(data.get("altura", 0))
    ciudad = data.get("ciudad", "").strip()

    try:
        if ciudad:
            clima = clima_por_ciudad(ciudad)
        else:
            clima = geo_latlon()

        lectura = simular_lectura(lugar, altura, clima)
        lectura = insertar_lectura(lectura)

        return jsonify({
            "mensaje": "Lectura capturada correctamente",
            "lectura": lectura
        }), 201

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route("/api/data/<int:id>", methods=["DELETE"])
def borrar(id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lectura_sensores WHERE id = ?", (id,))
    conn.commit()

    borrados = cursor.rowcount
    conn.close()

    if borrados == 0:
        return jsonify({"error": "Registro no encontrado"}), 404

    return jsonify({
        "mensaje": "Registro eliminado",
        "id": id
    })


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    create_table()
    app.run(host="0.0.0.0", port=5011, debug=True)
