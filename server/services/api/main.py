import datetime
import random
import sys
import uuid
import jwt
from functools import wraps
from flask import Flask, jsonify, request, Response, make_response
from flask.cli import FlaskGroup
from marshmallow import Schema, fields, pre_load, validate, ValidationError
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc, UniqueConstraint
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object("config.Config")
db = SQLAlchemy(app)
ma = Marshmallow()
NR_WORKERS = 5


##### Tables #####


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.Integer)
    username = db.Column(db.String(50), index = True, unique=True)
    password = db.Column(db.String(128))

def token_required(f):  
    @wraps(f)  
    def decorator(*args, **kwargs):
        token = None 
        if 'x-access-tokens' in request.headers:  
            token = request.headers['x-access-tokens']

        if not token:  
            return jsonify({'message': 'a valid token is missing'}), 400  

        try:
            data = jwt.decode(token, 'Th1s1ss3cr3t')
            current_user = User.query.filter_by(public_id=data['public_id']).first()  
        except:  
            return jsonify({'message': 'token is invalid'}), 400
        return f(current_user, *args,  **kwargs)  
            
    return decorator 

class Boss(db.Model):
    __tablename__ = 'bosses'
    __table_args__ = (
        db.UniqueConstraint('username', 'ip_address', 'port'),
    )
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    ip_address = db.Column(db.String(128))
    port = db.Column(db.Integer)
    idle = db.Column(db.Boolean)

class Worker(db.Model):
    __tablename__ = 'workers'
    __table_args__ = (
        db.UniqueConstraint('username', 'ip_address', 'port'),
    )
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    ip_address = db.Column(db.String(128))
    port = db.Column(db.Integer)
    idle = db.Column(db.Boolean)
    boss_id = db.Column(db.Integer)


##### SCHEMAS #####

class UserSchema(ma.Schema):
    id = fields.Integer(required=True)
    public_id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(1))
    password = fields.String(required=True, validate=validate.Length(1))

class BossSchema(ma.Schema):
    id = fields.Integer( primary_key=True)
    username = fields.String(required=True, validate=validate.Length(1))
    ip_address = fields.String(required=True)
    port = fields.Integer(required=True)
    idle = fields.Boolean(required=True)
    
class WorkerSchema(ma.Schema):
    id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(1))
    ip_address = fields.String(required=True)
    port = fields.Integer(required=True)
    idle = fields.Boolean(required=True)
    boss_id = fields.Integer(required=True)


user_schema = UserSchema()
users_schema = UserSchema(many=True)
worker_schema = WorkerSchema()
workers_schema = WorkerSchema(many=True)
boss_schema = BossSchema()
bosses_schema = BossSchema(many=True) 


##### API routes #####

@app.route("/")
def hello_world():
    return jsonify(hello="VideoProcessing API up and running"), 200


##### Session routes #####

@app.route('/register', methods=['GET', 'POST'])
def signup_user():  
    # Function that adds an user to db with username, password
    data = request.get_json(silent=True)
    if not data:
        # Error handling
        return jsonify("Invalid request."), 400

    hashed_password = generate_password_hash(data['password'], method='sha256')
    id_public = random.randint(1, 5050)
    
    new_user = User(public_id=id_public, username=data['username'], password=hashed_password) 
    
    try:
        db.session.add(new_user)  
        db.session.commit()    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("User already in dabase"), 409

    return jsonify("User registered successfully: " + data['username']), 201   


@app.route('/login', methods=['GET', 'POST'])  
def login_user(): 
    # Function that returns the session token for an user provided username, password
    auth = request.authorization   
    
    if not auth or not auth.username or not auth.password:  
        return make_response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})    

    user = User.query.filter_by(username=auth.username).first()   

    if check_password_hash(user.password, auth.password):  
        token = jwt.encode({'public_id': user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, 'Th1s1ss3cr3t')  
        return jsonify({'token' : token.decode('UTF-8')})

    return make_response('could not verify',  401, {'WWW.Authentication': 'Basic realm: "login required"'})


@app.route("/unregister", methods=["DELETE"])
@token_required
def unregister_user(current_user):
    # Function that unregisteres user - deletes user from db
    user = user_schema.dump(current_user)
    username = user['username']

    try:
        db.session.query(User).filter(User.username == username).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Error while deleting User from database."), 404

    # Return success message
    return jsonify("User deleted succesfully from database."), 200

@app.route("/unregister/boss", methods=["DELETE"])
@token_required
def unregister_boss(current_user):
    # Function that deletes a boss session from db
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    id = data['id']

    user = user_schema.dump(current_user)
    username = user['username']

    try:
        db.session.query(Boss).filter(Boss.id == id).filter(Boss.username == username).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Error while deleting Boss from database."), 404

    # Return success message
    return jsonify("Boss deleted succesfully from database."), 200

@app.route("/unregister/worker", methods=["DELETE"])
@token_required
def unregister_worker(current_user):
    # Function that deletes a worker session from db
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    id = data['id']

    user = user_schema.dump(current_user)
    username = user['username']

    try:
        db.session.query(Worker).filter(Worker.id == id).filter(Worker.username == username).delete()
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Error while deleting User from database."), 404

    # Return success message
    return jsonify("Worker deleted succesfully from database."), 200

@app.route("/register/boss", methods=["POST"])
@token_required
def register_as_boss(current_user):
    # Functon that registeres user session as boss
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port = data['port']

    new_boss = Boss(username=username, ip_address=ip_address, port=port, idle=True)
    try:
        db.session.add(new_boss)  
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Boss already in dabase"), 409
    
    query = db.session.query(Boss).filter(Boss.username == username)\
                                .filter(Boss.ip_address == ip_address)\
                                .filter(Boss.port == port).first()
    boss = boss_schema.dump(query)

    # Return success message
    return jsonify({'message': "User session registered as boss succesfully.", "id": boss['id']}), 200

@app.route("/register/worker", methods=["POST"])
@token_required
def register_as_worker(current_user):
    # Functon that registeres user session as worker
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port = data['port']

    new_worker = Worker(username=username, ip_address=ip_address, port=port, idle=True, boss_id=-2147483647) 
    try:
        db.session.add(new_worker)  
        db.session.commit()    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Worker already in dabase"), 409

    query = db.session.query(Worker).filter(Worker.username == username)\
                                    .filter(Worker.ip_address == ip_address)\
                                    .filter(Worker.port == port).first()
    worker = worker_schema.dump(query)

    # Return success message
    return jsonify({'message': "User session registered as worker succesfully.", "id": worker['id']}), 200

@app.route("/recover/worker", methods=["GET"])
@token_required
def recover_worker_session(current_user):
    # Function that returns the id of a corrupted worker sesssion 
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port']:
        # Error handling
        return jsonify("Invalid request."), 400

    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port = data['port']

    query = db.session.query(Worker).filter(Worker.username == username)\
                                    .filter(Worker.ip_address == ip_address)\
                                    .filter(Worker.port == port).first()
    
    exists = bool(query)
    if exists is False:
        return jsonify("No worker with id exists in database."), 404
    worker = worker_schema.dump(query)

    return jsonify({"id": worker['id']}), 200

@app.route("/recover/boss", methods=["GET"])
@token_required
def recover_boss_session(current_user):
    # Function that returns the id of a corrupted boss sesssion 
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port']:
        # Error handling
        return jsonify("Invalid request."), 400

    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port = data['port']

    query = db.session.query(Boss).filter(Boss.username == username)\
                                .filter(Boss.ip_address == ip_address)\
                                .filter(Boss.port == port).first()
    exists = bool(query)
    if exists is False:
        return jsonify("No boss with id exists in database."), 404

    boss = boss_schema.dump(query)

    return jsonify({"id": boss['id']}), 200


##### Work routes #####
@app.route('/worker', methods=['GET'])
def get_all_workers():  
    query = Worker.query.all() 
    result = workers_schema.dump(query)

    return jsonify(result), 200

@app.route('/boss', methods=['GET'])
def get_all_bosse():  
    query = Boss.query.all() 
    result = bosses_schema.dump(query)

    return jsonify(result), 200

@app.route('/user', methods=['GET'])
def get_all_users():  
    query = User.query.all() 
    result = users_schema.dump(query)

    return jsonify(result), 200

@app.route("/worker/status", methods=["PUT"])
@token_required
def worker_update_status(current_user):
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    worker = db.session.query(Worker).filter(Worker.id == id).first()

    try:
        worker.idle = True
        worker.boss_id = -2147483647
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying worker status in database."), 409

    # Return success message
    return jsonify("Worker updated to IDLE status."), 200

@app.route("/boss/status", methods=["PUT"])
@token_required
def boss_update_status(current_user):
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400

    id = data['id']
    boss = db.session.query(Boss).filter(Boss.id == id).first()

    try:
        boss.idle = True
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying boss status in database."), 409

    # Return success message
    return jsonify("Boss updated to IDLE status."), 200

@app.route("/worker/owner", methods=["GET"])
@token_required
def worker_request_boss(current_user):
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    query = db.session.query(Worker).filter(Worker.id == id).first()
    worker = worker_schema.dump(query)

    if worker['boss_id'] == -2147483647:
        return jsonify("Worker session should be IDLE."), 404

    query_boss = db.session.query(Boss).filter(Boss.id == worker['boss_id']).first()
    exists = bool(query_boss)

    if exists is False:
        return jsonify("Worker session is orfan."), 404
    
    boss = user_schema.dump(query_boss)

    return jsonify({"boss_ip_address": boss['ip_address']}), 200

@app.route("/boss/job", methods=["GET"])
@token_required
def boss_submit_job(current_user):
    # Function that sets first DEFAULT_VALUE workers that are in IDLE into Working
    # and returns them to the boss session thta reuested worker ONLY if the number
    # of worker sessions assigned to user >= number of boss sessions of user

    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    user = user_schema.dump(current_user)
    username = user['username']
    id = data['id']

    # get boss sessions
    nrBossSessions = db.session.query(Boss.username).filter(Boss.username == username).count()
    # get worker sessions
    nrWorkerSessions = db.session.query(Worker.username).filter(Worker.username == username).count()
    if nrBossSessions > nrWorkerSessions:
        return jsonify("Worker sessions less than boss sessions for user "), 401

    #update boss
    try:
        boss = db.session.query(Boss).filter(Boss.id == id).first()

        if boss.idle == False:
            return jsonify("Boss session hasn't finished previous job."), 401

        boss.idle = False
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying boss status in database."), 409

    # Error fetching list of workers
    try:
        list_workers = db.session.query(Worker).filter(Worker.idle == True).limit(NR_WORKERS)
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Server error. Error fetching workers list"), 500

    result = workers_schema.dump(list_workers)

    #update status workers
    for worker in list_workers:
        try:
            worker.idle = False
            worker.boss_id = id
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return jsonify("Error while modifying worker status in database."), 409

    # Return list of countries
    return jsonify(result), 200



#### Create db ####


def create_db():
    db.create_all()
    db.session.commit()

def main():
    create_db()
    app.run(host="0.0.0.0")   

if __name__ == "__main__":
    main()