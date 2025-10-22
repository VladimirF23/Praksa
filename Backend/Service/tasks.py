# Backend/Service/tasks.py

from gevent import monkey
monkey.patch_all()

from celery_app import celery
import redis, os
from dotenv import load_dotenv

load_dotenv()


from extensions import redis_client
# Connect to Redis
# redis_client = redis.StrictRedis(
#     host="redis-praksa",
#     port=6379,
#     password=redis_password,
#     decode_responses=True
# )
redis_password = os.getenv("REDIS_PASSWORD")

redis_host = os.getenv("REDIS_HOST", "redis-praksa")
redis_port = os.getenv("REDIS_PORT", "6379")
redis_db = os.getenv("REDIS_DB", "0")


redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"


from flask_socketio import SocketIO as SocketIOEmitter
socketio_emitter = SocketIOEmitter(message_queue=redis_url, cors_allowed_origins="*")


@celery.task
def update_all_users_live_data():
    # Lazy import to avoid loading MySQL/Flask at worker start
    try:
        from Backend.Service.LiveMeteringWebSocket import calculate_and_emit_live_data
    except ModuleNotFoundError:
        print("LiveMeteringWebSocket module not found, skipping task.")
        return


    user_keys = redis_client.keys("user:*")
    active_users = [key.split(":")[1] for key in user_keys]

    print(f"Updating {len(active_users)} users' live data...")

    for user_id in active_users:
        try:
            print(f"Updating data for user_id:{int(user_id)}")
            calculate_and_emit_live_data(int(user_id),socketio_emitter)
        except Exception as e:
            print(f"⚠️ Error updating user {user_id}: {e}")

    return "Live data updated successfully"
    # socketio_emitter.emit("test_event", {"ping": "pong"}, namespace="/")
    # print("✅ Test event emitted through Redis SocketIO emitter.")
    # return "Test emit done"
