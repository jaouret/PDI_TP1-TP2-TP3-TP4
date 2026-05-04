%%writefile sensor_editar_tabla_r1A.py

from flask import Flask, render_template, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from decimal import Decimal

app = Flask(__name__)


# CONFIGURACION SQLITE

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///datos_sensores.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# MODELO DE TABLA SQL


class LecturaSensores(db.Model):
    __tablename__ = "lectura_sensores"

    id = db.Column(db.Integer, primary_key=True)
    co2 = db.Column(db.Float)
    co2_corregido = db.Column(db.Numeric(precision=10, scale=2))
    temp = db.Column(db.Numeric(precision=10, scale=2))
    hum = db.Column(db.Numeric(precision=10, scale=2))
    fecha = db.Column(db.Text)
    lugar = db.Column(db.Text)
    altura = db.Column(db.Numeric(precision=8, scale=0))
    presion = db.Column(db.Numeric(precision=8, scale=2))
    presion_nm = db.Column(db.Numeric(precision=8, scale=2))
    temp_ext = db.Column(db.Numeric(precision=8, scale=2))
    temp_ref = db.Column(db.Numeric(precision=8, scale=2))

    def __repr__(self):
        return f"<Id {self.id}>"

    def to_dict(self):
        def convertir(valor):
            if isinstance(valor, Decimal):
                return float(valor)
            return valor

        return {
            "id": self.id,
            "co2": convertir(self.co2),
            "co2_corregido": convertir(self.co2_corregido),
            "temp": convertir(self.temp),
            "hum": convertir(self.hum),
            "fecha": self.fecha,
            "lugar": self.lugar,
            "altura": convertir(self.altura),
            "presion": convertir(self.presion),
            "presion_nm": convertir(self.presion_nm),
            "temp_ext": convertir(self.temp_ext),
            "temp_ref": convertir(self.temp_ref),
        }


# CREAR TABLAS SI NO EXISTEN


with app.app_context():
    db.create_all()


# PAGINA PRINCIPAL


@app.route("/")
def index():
    return render_template("tabla_sensores_para_editar.html")


# CONSULTAR DATOS CON FILTRO + PAGINACION + ORDEN


@app.route("/api/datos")
def datos():

    query = LecturaSensores.query

    search = request.args.get("search")
    if search:
        query = query.filter(LecturaSensores.lugar.like(f"%{search}%"))

    total = query.count()

    sort = request.args.get("sort", "id")

    allowed_columns = {
        "id": LecturaSensores.id,
        "lugar": LecturaSensores.lugar,
        "fecha": LecturaSensores.fecha,
        "co2": LecturaSensores.co2,
        "temp": LecturaSensores.temp,
        "hum": LecturaSensores.hum
    }

    if sort:
        descending = False

        if sort.startswith("-"):
            descending = True
            sort = sort[1:]

        column = allowed_columns.get(sort, LecturaSensores.id)

        if descending:
            column = column.desc()

        query = query.order_by(column)

    start = request.args.get("start", type=int, default=0)
    length = request.args.get("length", type=int, default=50)

    query = query.offset(start).limit(length)

    registros = query.all()

    return jsonify({
        "data": [r.to_dict() for r in registros],
        "total": total
    })


# CREAR NUEVO REGISTRO


@app.route("/api/data", methods=["POST"])
def create():

    data = request.get_json()

    if not data:
        abort(400)

    nuevo = LecturaSensores(
        co2=data.get("co2"),
        co2_corregido=data.get("co2_corregido"),
        temp=data.get("temp"),
        hum=data.get("hum"),
        fecha=data.get("fecha"),
        lugar=data.get("lugar"),
        altura=data.get("altura"),
        presion=data.get("presion"),
        presion_nm=data.get("presion_nm"),
        temp_ext=data.get("temp_ext"),
        temp_ref=data.get("temp_ref")
    )

    db.session.add(nuevo)
    db.session.commit()

    return jsonify({
        "mensaje": "Registro creado correctamente",
        "registro": nuevo.to_dict()
    }), 201


# ACTUALIZAR REGISTRO EXISTENTE


@app.route("/api/data/<int:id>", methods=["PUT"])
def update(id):

    data = request.get_json()

    if not data:
        abort(400)

    registro = LecturaSensores.query.get(id)

    if not registro:
        abort(404)

    campos_editables = [
        "co2",
        "co2_corregido",
        "temp",
        "hum",
        "fecha",
        "lugar",
        "altura",
        "presion",
        "presion_nm",
        "temp_ext",
        "temp_ref"
    ]

    for campo in campos_editables:
        if campo in data:
            setattr(registro, campo, data[campo])

    db.session.commit()

    return jsonify({
        "mensaje": "Registro actualizado correctamente",
        "registro": registro.to_dict()
    })


# BORRAR REGISTRO


@app.route("/api/data/<int:id>", methods=["DELETE"])
def delete(id):

    registro = LecturaSensores.query.get(id)

    if not registro:
        abort(404)

    db.session.delete(registro)
    db.session.commit()

    return jsonify({
        "mensaje": "Registro eliminado correctamente",
        "id": id
    })


# INSERCION AUTOMATICA DE DATOS DE PRUEBA (sólo primera vez)


@app.route("/cargar_demo")
def cargar_demo():

    if LecturaSensores.query.count() == 0:

        demo1 = LecturaSensores(
            co2=800,
            co2_corregido=798.25,
            temp=23.10,
            hum=77.10,
            fecha="22/03/2021",
            lugar="Laboratorio UCA",
            altura=15,
            presion=1009.55,
            presion_nm=1013.25,
            temp_ext=18.40,
            temp_ref=25.00
        )

        demo2 = LecturaSensores(
            co2=810,
            co2_corregido=807.80,
            temp=24.20,
            hum=75.00,
            fecha="23/03/2021",
            lugar="Aula 3",
            altura=12,
            presion=1008.20,
            presion_nm=1012.10,
            temp_ext=19.10,
            temp_ref=25.00
        )

        db.session.add(demo1)
        db.session.add(demo2)
        db.session.commit()

        return "Datos demo cargados"

    return "La base ya contiene datos"


# MAIN


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
