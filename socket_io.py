from flask_socketio import SocketIO, emit,ConnectionRefusedError, Namespace , join_room, leave_room , send , emit

from app import app

socketio = SocketIO(app)

class Chat(Namespace):
    def on_connect(self):
        print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')
    def on_disconnect(self):
        print('zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz')

    def on_join(self,data):
        room = data['room']
        join_room(room)
        print(room + ' a user entered')

class GroupChat(Namespace):
    def on_connect(self):
        print('user Connected')
    def on_disconnect(self):
        print('A User Disconnected')
    def on_test(self):
        print('123123123')
    def on_join(self,data):
        print("Joined")
        room = data['room']
        join_room(room)
        send('ZZZZZZZZZz has entered the room.', room=room)  
    
    def on_send_message(self,data):
        print("on send message")
        room = data['room']
        message = data['message']
        emit('send_message',message,room=room)




    


