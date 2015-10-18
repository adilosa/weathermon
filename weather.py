from pytz import timezone
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

    def latest(self):
        now = datetime.utcnow()
        query = db.session.query(
                    Reading.temperature, 
                    Reading.humidity, 
                    Reading.timestamp
                )\
                .filter_by(channel=self.channel)\
                .filter(Reading.timestamp > now - timedelta(minutes=15))\
                .order_by(Reading.timestamp.desc())
        results = query.all()
        self.latest_data = {
            "temperature": self._median([r[0] for r in results]),
            "humidity": self._median([r[1] for r in results]),
            "timestamp": results[0][2] if len(results) > 0 and len(results[0]) >=2 else now
        }
        return self.latest_data

    def last_day(self):
        utc = timezone("UTC")
        eastern = timezone('US/Eastern')
        hours = 30
        now = datetime.utcnow()
        query = db.session.query(
                func.round(func.avg(Reading.temperature)),
                func.round(func.avg(Reading.humidity)),
                Reading.timestamp
            )\
            .filter_by(channel=self.channel)\
            .filter(Reading.timestamp > func.datetime('now', '-30 hours'))\
            .group_by(func.strftime('%d %H', Reading.timestamp))\
            .order_by(Reading.timestamp.desc())\
            .limit(hours)
        readings = query.all()
        times = ["" for i in range(hours)]
        est = utc.localize(datetime.utcnow()).astimezone(eastern)
        for i in range(0, hours):
             times[i] = "\"" + (est - timedelta(hours=i)).strftime("%I%p").lstrip('0') + "\""
        times.reverse()
        temps = [0 for i in range(hours)]
        hums = [0 for i in range(hours)]
        for r in readings: 
            idx = hours - self._hours(now - r[2]) - 1
            temps[idx] = r[0] / 10
            hums[idx] = r[1]
        self.last_day_data = {
            "temperatures": temps,
            "humidities": hums,
            "timestamps": times
        }
        return self.last_day_data

    @staticmethod
    def _hours(td):
        return (td.days * 24) + int(td.seconds // (60 * 60))

    @staticmethod
    def _median(l):
        s = sorted(l)
        length = len(l)
        if length == 0:
            return 0
        if not length % 2:
            return (s[length / 2] + s[length / 2] - 1) / 2
        return s[length / 2]

    @staticmethod
    def _round_to_hour(dt):
        seconds = (dt - dt.min).seconds
        rounding = (seconds + 3600 / 2) // 3600 * 3600
        return dt + timedelta(0, rounding - seconds, -dt.microsecond)

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

