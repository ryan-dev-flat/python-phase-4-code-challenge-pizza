#!/usr/bin/env python3
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os
from models import db, Restaurant, RestaurantPizza, Pizza
from flask import jsonify

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)
api = Api(app)

db.init_app(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"



class RestaurantResource(Resource):
    def get(self, id=None):
        if id is None:
            restaurants = Restaurant.query.all()
            return [restaurant.to_dict(only=("id", "name", "address")) for restaurant in restaurants], 200
        else:
            restaurant = Restaurant.query.get(id)
            if restaurant:
                return restaurant.to_dict(), 200
            else:
                return {"error": "Restaurant not found"}, 404

    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return {"error": "Restaurant not found"}, 404
        db.session.delete(restaurant)
        db.session.commit()
        return "", 204

api.add_resource(RestaurantResource, '/restaurants', '/restaurants/<int:id>')

class PizzaResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        for pizza in pizzas:
            print(pizza)
        return [pizza.to_dict(only=("id", "name", "ingredients")) for pizza in pizzas]
api.add_resource(PizzaResource, '/pizzas')

from sqlalchemy.exc import IntegrityError

class RestaurantPizzaResource(Resource):
    def post(self):
        data = request.json
        if not all(key in data for key in ('price', 'pizza_id', 'restaurant_id')):
            return {"errors": ["validation errors"]}, 400

        restaurant = Restaurant.query.get(data['restaurant_id'])
        pizza = Pizza.query.get(data['pizza_id'])
        if not restaurant or not pizza:
            return {"errors": ["validation errors"]}, 400

        try:
            restaurant_pizza = RestaurantPizza(
                price=data['price'],
                pizza_id=data['pizza_id'],
                restaurant_id=data['restaurant_id']
            )
            db.session.add(restaurant_pizza)
            db.session.commit()

            return {
                "id": restaurant_pizza.id,
                "price": restaurant_pizza.price,
                "pizza_id": restaurant_pizza.pizza_id,
                "restaurant_id": restaurant_pizza.restaurant_id,
                "pizza": {
                    "id": pizza.id,
                    "name": pizza.name,
                    "ingredients": pizza.ingredients
                },
                "restaurant": {
                    "id": restaurant.id,
                    "name": restaurant.name,
                    "address": restaurant.address
                }
            }, 201
        except ValueError as e:
            return {"errors": ["validation errors"]}, 400
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400

api.add_resource(RestaurantPizzaResource, '/restaurant_pizzas')

if __name__ == "__main__":
    app.run(port=5555, debug=True)
