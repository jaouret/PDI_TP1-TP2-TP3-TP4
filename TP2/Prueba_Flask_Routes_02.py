from flask import Flask, jsonify, request

app = Flask(__name__)

sensors = [
    {
        "id": 0,
        "co2": 800,
        "temp": 23.0,
        "hum": 77.1,
        "fecha": "22/3/2021"
    },
    {
        "id": 1,
        "co2": 801,
        "temp": 24.0,
        "hum": 78.1,
        "fecha": "23/3/2021"
    }
]


@app.route("/")
def index():
    return """
    <!doctype html>
    <html lang="es">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Flask Sensores</title>

        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>

    <body class="bg-light">

    <nav class="navbar navbar-dark bg-dark mb-4">
        <div class="container">
            <span class="navbar-brand mb-0 h1">Servidor Flask - Sensores</span>
        </div>
    </nav>

    <div class="container">

        <div class="alert alert-success">
            Flask está funcionando correctamente en el puerto 5001.
        </div>

        <div class="row g-4">

            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header bg-primary text-white">
                        Login por POST
                    </div>
                    <div class="card-body">
                        <form action="/login" method="post">
                            <div class="mb-3">
                                <label class="form-label">Nombre</label>
                                <input type="text" name="nombre" class="form-control" placeholder="javier">
                            </div>

                            <div class="mb-3">
                                <label class="form-label">Clave</label>
                                <input type="password" name="clave" class="form-control" placeholder="abc">
                            </div>

                            <button type="submit" class="btn btn-primary">
                                Ingresar
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            <div class="col-md-6">
                <div class="card shadow-sm">
                    <div class="card-header bg-success text-white">
                        Accesos rápidos
                    </div>
                    <div class="card-body">
                        <a href="/login_get?nombre=javier&clave=abc" class="btn btn-outline-primary mb-2 w-100">
                            Probar Login GET
                        </a>

                        <a href="/sensors" class="btn btn-outline-success mb-2 w-100">
                            Ver sensores JSON
                        </a>

                        <a href="/sensors/0" class="btn btn-outline-secondary mb-2 w-100">
                            Ver sensor 0
                        </a>

                        <a href="/sensors/1" class="btn btn-outline-secondary w-100">
                            Ver sensor 1
                        </a>
                    </div>
                </div>
            </div>

        </div>

        <div class="card mt-4 shadow-sm">
            <div class="card-header bg-dark text-white">
                Endpoints disponibles
            </div>
            <div class="card-body">
                <table class="table table-striped table-bordered">
                    <thead>
                        <tr>
                            <th>Método</th>
                            <th>Ruta</th>
                            <th>Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><span class="badge bg-success">GET</span></td>
                            <td>/sensors</td>
                            <td>Lista todos los sensores</td>
                        </tr>
                        <tr>
                            <td><span class="badge bg-success">GET</span></td>
                            <td>/sensors/&lt;id&gt;</td>
                            <td>Consulta un sensor por ID</td>
                        </tr>
                        <tr>
                            <td><span class="badge bg-primary">POST</span></td>
                            <td>/sensors</td>
                            <td>Crea un nuevo sensor usando JSON</td>
                        </tr>
                        <tr>
                            <td><span class="badge bg-warning text-dark">PUT</span></td>
                            <td>/sensors/&lt;id&gt;</td>
                            <td>Actualiza un sensor</td>
                        </tr>
                        <tr>
                            <td><span class="badge bg-danger">DELETE</span></td>
                            <td>/sensors/&lt;id&gt;</td>
                            <td>Elimina un sensor</td>
                        </tr>
                        <tr>
                            <td><span class="badge bg-primary">POST</span></td>
                            <td>/post_json</td>
                            <td>Recibe datos JSON genéricos</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </div>

    </body>
    </html>
    """


@app.route("/login", methods=["POST"])
def login_post():
    nombre = request.form.get("nombre")
    clave = request.form.get("clave")

    if nombre == "javier" and clave == "abc":
        return f"Hola {nombre} con POST"

    return "Usuario o clave incorrectos", 401


@app.route("/login_get", methods=["GET"])
def login_get():
    nombre = request.args.get("nombre")
    clave = request.args.get("clave")

    if nombre == "javier" and clave == "abc":
        return f"Hola {nombre} con GET"

    return "Usuario o clave incorrectos", 401


@app.route("/post_json", methods=["POST"])
def process_json():
    if not request.is_json:
        return jsonify({"error": "Content-Type no soportado. Use application/json"}), 415

    data = request.get_json()
    return jsonify({
        "mensaje": "JSON recibido correctamente",
        "datos": data
    })


@app.route("/sensors", methods=["GET"])
def get_sensors():
    return jsonify({"sensors": sensors})


@app.route("/sensors/<int:id>", methods=["GET"])
def get_sensor(id):
    for sensor in sensors:
        if sensor["id"] == id:
            return jsonify({"sensor": sensor})

    return jsonify({"error": "Sensor no encontrado"}), 404


@app.route("/sensors", methods=["POST"])
def create_sensor():
    if not request.is_json:
        return jsonify({"error": "Debe enviar datos en formato JSON"}), 415

    data = request.get_json()

    new_sensor = {
        "id": len(sensors),
        "co2": data.get("co2"),
        "temp": data.get("temp"),
        "hum": data.get("hum"),
        "fecha": data.get("fecha")
    }

    sensors.append(new_sensor)

    return jsonify({
        "mensaje": "Sensor creado correctamente",
        "sensor": new_sensor
    }), 201


@app.route("/sensors/<int:id>", methods=["PUT"])
def update_sensor(id):
    if not request.is_json:
        return jsonify({"error": "Debe enviar datos en formato JSON"}), 415

    data = request.get_json()

    for sensor in sensors:
        if sensor["id"] == id:
            sensor["co2"] = data.get("co2", sensor["co2"])
            sensor["temp"] = data.get("temp", sensor["temp"])
            sensor["hum"] = data.get("hum", sensor["hum"])
            sensor["fecha"] = data.get("fecha", sensor["fecha"])

            return jsonify({
                "mensaje": "Sensor actualizado correctamente",
                "sensor": sensor
            })

    return jsonify({"error": "Sensor no encontrado"}), 404


@app.route("/sensors/<int:id>", methods=["DELETE"])
def delete_sensor(id):
    for sensor in sensors:
        if sensor["id"] == id:
            sensors.remove(sensor)
            return jsonify({
                "mensaje": "Sensor eliminado correctamente",
                "result": True
            })

    return jsonify({"error": "Sensor no encontrado"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
