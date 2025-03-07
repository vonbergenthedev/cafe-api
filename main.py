import random

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import StatementError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass


# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        dictionary = {}

        for column in self.__table__.columns:
            dictionary[column.name] = getattr(self, column.name)

        return dictionary


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


# HTTP GET - Read Record
@app.route('/random')
def get_random_cafe():
    with app.app_context():
        all_cafes = db.session.execute(db.select(Cafe)).scalars().all()
        random_cafe = random.choice(all_cafes)

        return jsonify(cafe=random_cafe.to_dict())


@app.route('/all', )
def get_all_cafes():
    with app.app_context():
        all_cafes = db.session.execute(db.select(Cafe)).scalars().all()

        return jsonify(cafes=[cafe.to_dict() for cafe in all_cafes])


@app.route('/search')
def find_cafe():
    with app.app_context():
        location_selection_cafes = db.session.execute(
            db.select(Cafe).where(Cafe.location == request.args.get('loc')).order_by(Cafe.id)).scalars().all()

        if location_selection_cafes:
            return jsonify(cafes=[cafe.to_dict() for cafe in location_selection_cafes])

    return jsonify(error={'Not Found': 'Sorry, we don\'t have a cafe at that location.'})


# HTTP POST - Create Record
@app.route('/add', methods=['POST'])
def add_cafe():
    with app.app_context():
        new_cafe = Cafe(
            name=request.args.get('name'),
            map_url=request.args.get('map_url'),
            img_url=request.args.get('img_url'),
            location=request.args.get('location'),
            seats=request.args.get('seats'),
            has_toilet=bool(request.args.get('has_toilet')),
            has_wifi=bool(request.args.get('has_wifi')),
            has_sockets=bool(request.args.get('has_sockets')),
            can_take_calls=bool(request.args.get('can_take_calls')),
            coffee_price=request.args.get('coffee_price'),

        )

        db.session.add(new_cafe)

        try:
            db.session.commit()
        except StatementError as e:
            return jsonify(response={'error': f'Entry not structured correctly: {e}'})

        return jsonify(response={'success': 'Successfully added the new cafe.'})


# HTTP PUT/PATCH - Update Record
@app.route('/update-price/<cafe_id>', methods=['PATCH'])
def update_cafe_price(cafe_id):
    cafe_to_update = db.session.get(Cafe, cafe_id)

    if cafe_to_update:
        cafe_to_update.coffee_price = f'£{request.args.get('coffee_price')}'
        db.session.commit()

        return jsonify(response='Successfully updated the price.')

    else:
        return jsonify(error={'Not Found': 'Sorry a cafe with that id was not found in the database.'}), 404


# HTTP DELETE - Delete Record
@app.route('/report-closed/<cafe_id>', methods=['DELETE'])
def cafe_closed(cafe_id):
    api_key = request.args.get('api_key')

    if api_key == 'TopSecretAPIKey':
        cafe_to_delete = db.session.get(Cafe, cafe_id)

        if cafe_to_delete:
            db.session.delete(cafe_to_delete)
            db.session.commit()
            return jsonify(response={'success': 'Cafe removed from the database.'})

        else:
            return jsonify(error='Sorry, a cafe with that ID was not found in the database.'), 404

    else:
        return jsonify(error='Sorry, that\'s not allowed. Make sure you have the correct api_key.'), 403


if __name__ == '__main__':
    app.run(debug=True)
