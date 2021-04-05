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


##### Formatting #####

# Function used to format string as DateTime
def toDate(dateString): 
    return datetime.datetime.strptime(dateString, "%Y-%m-%d").date()
    

##### Tables #####


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    public_id = db.Column(db.Integer)
    username = db.Column(db.String(50), index = True, unique=True)
    password = db.Column(db.String(128))
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

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
        db.UniqueConstraint('username', 'ip_address', 'port_msg'),
    )
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    ip_address = db.Column(db.String(128))
    port_msg = db.Column(db.Integer)
    port_file = db.Column(db.Integer)
    idle = db.Column(db.Boolean)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class Worker(db.Model):
    __tablename__ = 'workers'
    __table_args__ = (
        db.UniqueConstraint('username', 'ip_address', 'port_msg'),
    )
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), db.ForeignKey('users.username', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    ip_address = db.Column(db.String(128))
    port_msg = db.Column(db.Integer)
    port_file = db.Column(db.Integer)
    idle = db.Column(db.Boolean)
    boss_id = db.Column(db.Integer)
    pp_x265 = db.Column(db.Float)
    pp_vp9 = db.Column(db.Float)
    pp_av1 = db.Column(db.Float)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

class JobEvent(db.Model):
    __tablename__ = 'jobRequests'
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    worker_username = db.Column(db.String(50))
    worker_id = db.Column(db.Integer)
    worker_ip_address = db.Column(db.String(128))
    worker_port_msg = db.Column(db.Integer)
    worker_port_file = db.Column(db.Integer)
    boss_username = db.Column(db.String(50))
    boss_id = db.Column(db.Integer)
    boss_ip_address = db.Column(db.String(128))
    boss_port_msg = db.Column(db.Integer)
    boss_port_file = db.Column(db.Integer)

class JobResult(db.Model):
    __tablename__ = 'jobResults'
    id = db.Column(db.Integer, primary_key = True)
    timestamp = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    codec = db.Column(db.String)
    time_io = db.Column(db.Float)
    time_transcoding = db.Column(db.Float)
    estimated_power = db.Column(db.Float)
    nr_chunks_total = db.Column(db.Integer)
    nr_chunks_proccessed = db.Column(db.Integer)



##### SCHEMAS #####

class UserSchema(ma.Schema):
    id = fields.Integer(required=True)
    public_id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(1))
    password = fields.String(required=True, validate=validate.Length(1))
    timestamp = fields.DateTime(required=False, format='%Y-%m-%d')

class BossSchema(ma.Schema):
    id = fields.Integer( primary_key=True)
    username = fields.String(required=True, validate=validate.Length(1))
    ip_address = fields.String(required=True)
    port_msg = fields.Integer(required=True)
    port_file = fields.Integer(required=True)
    idle = fields.Boolean(required=True)
    timestamp = fields.DateTime(required=False, format='%Y-%m-%d')
    
class WorkerSchema(ma.Schema):
    id = fields.Integer(required=True)
    username = fields.String(required=True, validate=validate.Length(1))
    ip_address = fields.String(required=True)
    port_msg = fields.Integer(required=True)
    port_file = fields.Integer(required=True)
    idle = fields.Boolean(required=True)
    boss_id = fields.Integer(required=True)
    pp_x265 = fields.Float(required=True)
    pp_vp9 = fields.Float(required=True)
    pp_av1 = fields.Float(required=True)
    timestamp = fields.DateTime(required=False, format='%Y-%m-%d')


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

@app.route('/api/register', methods=['GET', 'POST'])
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


@app.route('/api/login', methods=['GET', 'POST'])  
def login_user(): 
    # Function that returns the session token for an user provided username, password
    auth = request.authorization   
    
    if not auth or not auth.username or not auth.password:  
        return make_response('could not verify', 401, {'WWW.Authentication': 'Basic realm: "login required"'})    

    user = User.query.filter_by(username=auth.username).first()   

    if check_password_hash(user.password, auth.password):  
        token = jwt.encode({'public_id': user.public_id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, 'Th1s1ss3cr3t')  
        return jsonify({'token' : token.decode('UTF-8')}), 200

    return make_response('could not verify',  401, {'WWW.Authentication': 'Basic realm: "login required"'})


@app.route("/api/unregister", methods=["DELETE"])
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

@app.route("/api/unregister/boss", methods=["DELETE"])
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

@app.route("/api/unregister/worker", methods=["DELETE"])
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

@app.route("/api/register/boss", methods=["POST"])
@token_required
def register_as_boss(current_user):
    # Functon that registeres user session as boss
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port_msg'] or not data['port_file']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port_msg = data['port_msg']
    port_file = data['port_file']

    new_boss = Boss(username=username, ip_address=ip_address,\
                    port_msg=port_msg, port_file=port_file, idle=True)
    try:
        db.session.add(new_boss)  
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Boss already in dabase"), 409
    
    query = db.session.query(Boss).filter(Boss.username == username)\
                                .filter(Boss.ip_address == ip_address)\
                                .filter(Boss.port_msg == port_msg).first()
    boss = boss_schema.dump(query)

    # Return success message
    return jsonify({'message': "User session registered as boss succesfully.", "id": boss['id']}), 200

@app.route("/api/register/worker", methods=["POST"])
@token_required
def register_as_worker(current_user):
    # Functon that registeres user session as worker
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port_msg'] or not data['port_file']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port_msg = data['port_msg']
    port_file = data['port_file']
    p1 = data['pp_x265']
    p2 = data['pp_vp9']
    p3 = data['pp_av1']

    new_worker = Worker(username=username, ip_address=ip_address,\
                        port_msg=port_msg, port_file=port_file, idle=True,\
                        boss_id=-2147483647, pp_x265=p1, pp_vp9=p2, pp_av1=p3) 

    try:
        db.session.add(new_worker)  
        db.session.commit()    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Worker already in dabase"), 409

    query = db.session.query(Worker).filter(Worker.username == username)\
                                    .filter(Worker.ip_address == ip_address)\
                                    .filter(Worker.port_msg == port_msg).first()
    worker = worker_schema.dump(query)

    # Return success message
    return jsonify({'message': "User session registered as worker succesfully.", "id": worker['id']}), 200

@app.route("/api/recover/worker", methods=["GET"])
@token_required
def recover_worker_session(current_user):
    # Function that returns the id of a corrupted worker sesssion 
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port_msg']:
        # Error handling
        return jsonify("Invalid request."), 400

    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port_msg = data['port_msg']

    query = db.session.query(Worker).filter(Worker.username == username)\
                                    .filter(Worker.ip_address == ip_address)\
                                    .filter(Worker.port_msg == port_msg).first()
    
    exists = bool(query)
    if exists is False:
        return jsonify("No worker with id exists in database."), 404
    
    query.idle = True
    query.boss_id = -214748364
    worker = worker_schema.dump(query)

    return jsonify({"id": worker['id']}), 200

@app.route("/api/recover/boss", methods=["GET"])
@token_required
def recover_boss_session(current_user):
    # Function that returns the id of a corrupted boss sesssion 
    data = request.get_json(silent=True)
    if not data or not data['ip_address'] or not data['port_msg']:
        # Error handling
        return jsonify("Invalid request."), 400

    user = user_schema.dump(current_user)
    username = user['username']
    ip_address = data['ip_address']
    port = data['port_msg']

    query = db.session.query(Boss).filter(Boss.username == username)\
                                .filter(Boss.ip_address == ip_address)\
                                .filter(Boss.port_msg == port).first()
    exists = bool(query)
    if exists is False:
        return jsonify("No boss with id exists in database."), 404

    query.idle = True
    boss = boss_schema.dump(query)

    return jsonify({"id": boss['id']}), 200


##### Work routes #####
@app.route('/api/worker', methods=['GET'])
def get_all_workers():  
    query = Worker.query.all() 
    result = workers_schema.dump(query)

    return jsonify(result), 200

@app.route('/api/boss', methods=['GET'])
def get_all_bosse():  
    query = Boss.query.all() 
    result = bosses_schema.dump(query)

    return jsonify(result), 200

@app.route('/api/user', methods=['GET'])
def get_all_users():  
    query = User.query.all() 
    result = users_schema.dump(query)

    return jsonify(result), 200

@app.route("/api/worker/status", methods=["PUT"])
@token_required
def worker_update_status(current_user):
    #Function that updates worker to IDLE status after finishing job
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

@app.route("/api/worker/ip", methods=["PUT"])
@token_required
def worker_update_ip(current_user):
    #Function that updates worker ip address
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    ip = data['ip']
    worker = db.session.query(Worker).filter(Worker.id == id).first()

    try:
        worker.ip = ip
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying worker ip in database."), 409

    # Return success message
    return jsonify("Worker ip address updated."), 200

@app.route("/api/worker/pp_x265", methods=["PUT"])
@token_required
def worker_update_pp_x265(current_user):
    #Function that updates worker pp_x265 parameter
    data = request.get_json(silent=True)
    if not data or not data['id'] or not data['pp_x265']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    pp_x265 = data['pp_x265']
    worker = db.session.query(Worker).filter(Worker.id == id).first()

    try:
        worker.pp_x265 = pp_x265
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying worker pp_x265 in database."), 409

    # Return success message
    return jsonify("Worker pp_x265 updated."), 200

@app.route("/api/worker/pp_vp9", methods=["PUT"])
@token_required
def worker_update_pp_vp9(current_user):
    #Function that updates worker pp_vp9 parameter
    data = request.get_json(silent=True)
    if not data or not data['id'] or not data['pp_vp9']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    pp_vp9 = data['pp_vp9']
    worker = db.session.query(Worker).filter(Worker.id == id).first()

    try:
        worker.pp_vp9 = pp_vp9
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying worker pp_vp9 in database."), 409

    # Return success message
    return jsonify("Worker pp_vp9 updated."), 200

@app.route("/api/worker/pp_av1", methods=["PUT"])
@token_required
def worker_update_pp_av1(current_user):
    #Function that updates worker pp_av1 parameter
    data = request.get_json(silent=True)
    if not data or not data['id'] or not data['pp_av1']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    pp_av1 = data['pp_av1']
    worker = db.session.query(Worker).filter(Worker.id == id).first()

    try:
        worker.pp_av1 = pp_av1
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying worker pp_av1 in database."), 409

    # Return success message
    return jsonify("Worker pp_av1 updated."), 200

@app.route("/api/worker/job", methods=["POST"])
def worker_submit_job_result():
    #Function that inserts job result into db for analytics
    data = request.get_json(silent=True)
    if not data or not data['time_io']:
        # Error handling
        return jsonify("Invalid request."), 400

    codec = data['codec']
    time_io = data['time_io']
    time_transcoding = data['time_transcoding']
    estimated_power = data['estimated_power']
    nr_chunks_total = data['nr_chunks_total']
    nr_chunks_proccessed = data['nr_chunks_proccessed']

    new_job = JobResult(codec=codec, time_io=time_io,\
                    time_transcoding=time_transcoding, estimated_power=estimated_power, \
                    nr_chunks_total=nr_chunks_total, nr_chunks_proccessed=nr_chunks_proccessed)
    try:
        db.session.add(new_job)  
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify("Job result couldn't be added into database."), 409

    # Return success message
    return jsonify("Job result inserted job result into db."), 200    


@app.route("/api/boss/status", methods=["PUT"])
@token_required
def boss_update_status(current_user):
    #Function that updates boss to IDLE status after finishing job
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

@app.route("/api/boss/ip", methods=["PUT"])
@token_required
def boss_update_ip(current_user):
    #Function that updates boss ip address
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400

    id = data['id']
    ip = data['ip']
    boss = db.session.query(Boss).filter(Boss.id == id).first()

    try:
        boss.ip = ip
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        return jsonify("Error while modifying boss status in database."), 409

    # Return success message
    return jsonify("Boss updated to IDLE status."), 200

@app.route("/api/worker/owner", methods=["GET"])
@token_required
def worker_request_boss(current_user):
    data = request.get_json(silent=True)
    if not data or not data['id']:
        # Error handling
        return jsonify("Invalid request."), 400
    
    id = data['id']
    query = db.session.query(Worker).filter(Worker.id == id).first()
    worker = worker_schema.dump(query)

    if worker == None:
            return jsonify("Worker session doesn't exist."), 401

    if worker['boss_id'] == -2147483647:
        return jsonify("Worker session should be IDLE."), 404

    query_boss = db.session.query(Boss).filter(Boss.id == worker['boss_id']).first()
    exists = bool(query_boss)

    if exists is False:
        return jsonify("Worker session is orfan."), 404
    
    boss = boss_schema.dump(query_boss)

    return jsonify({"boss_ip_address": boss['ip_address']}), 200

@app.route("/api/boss/job", methods=["GET"])
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

   
    boss = db.session.query(Boss).filter(Boss.id == id).first()
    #update boss
    try:
        if boss == None:
            return jsonify("Boss session doesn't exist."), 401

        if boss.idle == False:
            return jsonify("Boss session hasn't finished previous job."), 401

        boss.idle = False
        boss.timestamp = db.func.current_timestamp()
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
            worker.timestamp = db.func.current_timestamp()

            new_log = JobEvent(worker_username=worker.username, worker_id=worker.id, \
                            worker_ip_address=worker.ip_address, \
                            worker_port_msg=worker.port_msg, worker_port_file=worker.port_file, \
                            boss_username=boss.username, boss_id=boss.id, \
                            boss_ip_address=boss.ip_address, \
                            boss_port_msg=boss.port_msg, boss_port_file=boss.port_file)
            try:
                db.session.add(new_log)  
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                return jsonify("Log for job couldn't be added into database."), 409
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            return jsonify("Error while modifying worker status in database."), 409

    # Return list of countries
    return jsonify(result), 200


@app.route("/api/cleanup", methods=["DELETE"])
def server_cleanup():
    #Function that cleanes database from hange up sessions (boss or workers)
    time = request.args.get('time', default=None, type = toDate)
    result_bosses = []
    result_workers = []

    try:
        removed_bosses = db.session.query(Boss)\
                     .filter(Boss.timestamp >= time).filter(Boss.idle == False).all()
        result_bosses = bosses_schema.dump(removed_bosses)
        removed_workers = db.session.query(Worker)\
                     .filter(Worker.timestamp >= time).filter(Worker.idle == False).all()
        result_workers = workers_schema.dump(removed_workers)

        for boss in removed_bosses:
            print("boss " + str(boss.id) + " ")
            db.session.query(Boss).filter(Boss.id == boss.id).delete()
            db.session.commit()

        for worker in removed_workers:
            print("worker " + str(worker.id) + " ")
            db.session.query(Worker).filter(Worker.id == worker.id).delete()
            db.session.commit()

    except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify("Error fetching sessions list"), 500

    return jsonify({'removed_bosses' : result_bosses, 'removed_workers': result_workers}), 200


#### Create db ####


def create_db():
    db.create_all()
    db.session.commit()

def main():
    create_db()
    app.run(host="0.0.0.0", debug=False)   

if __name__ == "__main__":
    main()