from datetime import datetime, timedelta
from collections import Counter

from flask import Flask, render_template, jsonify
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_bootstrap import Bootstrap


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///weather.db"
db = SQLAlchemy(app)
bootstrap = Bootstrap(app)


class Reading(db.Model):
    __tablename__ = "reading"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    channel = db.Column(db.Integer)
    temperature = db.Column(db.Integer)
    humidity = db.Column(db.Integer)
    battery = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)

    @property
    def data(self):
        return {
            "id": self.id, 
            "channel": self.channel, 
            "temperature": self.temperature, 
            "humidity": self.humidity,
            "timestamp": self.timestamp
        }

    def __repr__(self):
        return "<Reading {id} - Ch {ch}  {temp}F {hum}% at {time}>".format(
            id=self.id,
            ch=self.channel,
            temp=self.temperature,
            hum=self.humidity, 
            time=self.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        )


class Sensor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    channel = db.Column(db.Integer)
    name = db.Column(db.String(64))

    @property
    def data(self):
        return {
            "id": self.id,
            "channel": self.channel,
            "name": self.name,
            "temperature": self.temperature,
            "humidity": self.humidity
        }

    @property
    def temperature(self):
        return self.latest()["temperature"]

    @property
    def humidity(self):
        return self.latest()["humidity"]

    def latest(self):
        if hasattr(self, 'latest_data'):
            return self.latest_data
        limit = 15
        query = db.session.query(
                    Reading.temperature, 
                    Reading.humidity, 
                    Reading.timestamp
                )\
                .filter_by(channel=self.channel)\
                .order_by(Reading.timestamp.desc())\
                .limit(limit)
        results = query.all()
        self.latest_data = {
            "temperature": sum([r[0] for r in results]) / limit,
            "humidity": sum([r[1] for r in results]) / limit,
            "timestamp": results[0][2]
        }
        return self.latest_data

    def last_day(self):
        query = db.session.query(
                func.round(func.avg(Reading.temperature)), 
                func.round(func.avg(Reading.humidity)),
                Reading.timestamp
            )\
            .filter_by(channel=self.channel)\
            .group_by(func.strftime('%H', Reading.timestamp))\
            .order_by(Reading.timestamp.desc())\
            .limit(30)
        return [
            {
                "temperature": r[0],
                "humidity": r[1],
                "timestamp": r[2]
            } for r in query.all()
        ]

    def __repr__(self):
        return "<Sensor {id}: \"{name}\" on Ch {ch}>".format(
            id=self.id,
            name=self.name,
            ch=self.channel
        )


@app.route("/")
def main_page():
    return render_template(
        "home.jinja2", 
        sensors=Sensor.query.order_by(Sensor.channel.asc()).all()
    )


@app.route("/sensors", defaults={"_id": None})
@app.route("/sensors/<int:_id>")
def sensors(_id):
    return jsonify(_sensors(_id))


def _sensors(_id=None):
    if _id is not None:
        sensor = Sensor.query.filter_by(id=_id).first_or_404()
        data = sensor.data
        data.update({"readings": sensor.last_day()})
        return data
    return {"sensors": [sensor.data for sensor in Sensor.query.all()]}


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)