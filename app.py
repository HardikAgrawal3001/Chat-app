from flask import *
from flask_socketio import SocketIO,send,emit, join_room, leave_room
from flask_wtf import Form
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy



app = Flask(__name__)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'verySecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    name = db.Column(db.String(255),nullable=False)
    username = db.Column(db.String(255),nullable=False)
    password = db.Column(db.String(255),nullable=False)

class Chat(db.Model):
    __tablename__ = 'chat'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    from_username = db.Column(db.String(255),nullable=False)
    to_username = db.Column(db.String(255),nullable=False)
    message = db.Column(db.Text,nullable=False)
    room = db.Column(db.String(255),nullable=False)

class LoginForm(Form):
    """Accepts a nickname and a room."""
    name = StringField('Name', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])
    submit = SubmitField('Enter Chatroom')

@app.route('/join', methods=['GET', 'POST'])
def join():
    """Login form to enter a room."""
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['room'] = form.room.data
        return redirect(url_for('.chat'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.room.data = session.get('room', '')
    return render_template('join.html', form=form)


@app.route('/register',methods=["POST","GET"])
def register():
    if request.method == 'GET':
        return render_template("register.html")
    else:
        if request.form['Name'].isalnum() is False:
            flash('Please Enter Alphanumeric Name','danger')
            return redirect('/register')
        else:
            if request.form['Username'].isalnum() is False:
                flash('Please Choose Alphanumeric Username','danger')
                return redirect('/register')
            else:
                if request.form['Password'] != request.form['Password1']:
                    flash('Confirmation Password Not Match','danger')
                    return redirect('/register')
                else:
                    if Users.query.filter_by(username=request.form['Username']).first() is not None:
                        flash('Username Already Exists','danger')
                        return redirect('/register')
                    else:
                        user_obj = Users(name=request.form['Name'],username=request.form['Username'],password=request.form['Password'])
                        db.session.add(user_obj)
                        db.session.commit()
                        flash('Registered Successfully, Please Login','success')
                        return redirect('/login')


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method=="GET":
        return render_template("login.html")
    else:
        user_obj = Users.query.filter_by(username=request.form['Username']).first()
        if user_obj is None:
            flash('Username not found','danger')
            return redirect('/login')
        else:
            if user_obj.password != request.form['Password']:
                flash('Invalid Password','danger')
                return redirect('/login')
            else:
                session['userid'] = user_obj.id
                return redirect('/join')


@app.route('/donate')
def donate():
    return render_template("donate.html")


@app.route('/donate_on_this_site_to_get_code')
def get_the_code():
    return render_template("donate_on_this_site_to_get_code.html")


@app.route('/chat')
def chat():
    name = session.get('name', '')
    room = session.get('room', '')
    if name == '' or room == '':
        return redirect(url_for('index'))
    else:
        room_obj = Chat.query.filter_by(room=room).all()
        user_obj = Users.query
        return render_template('chat.html', name=name, room=room,room_obj = room_obj,user_obj=user_obj) 


@socketio.on('joined')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('name') + ' has entered the room.'}, room=room)


@socketio.on('text')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    emit('message', {'msg': session.get('name') + ':' + message['msg']}, room=room)


@socketio.on('left')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('name') + ' has left the room.'}, room=room)


if __name__ == '__main__':
	socketio.run(app,debug=True)
