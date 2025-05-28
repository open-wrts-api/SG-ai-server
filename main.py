from fastapi import FastAPI
from SQLite import sqlite_commands as SQLite
import time


async def cleanup():
    try:
        current_time = time.time()
        for user in db.get_all_items_sorted("users", "removeAt"):
            if user["removeAt"] < current_time:
                db.delete_item("users", "id", user["id"])
    except Exception as error:
        print(f"Error during cleanup: {error}")


db = SQLite()
try:
    db.set_database("main.db")
    db.insert_into_table("users", {"id": 1, "password": "IGNORE", "email": "IGNORE", "removeAt": time.time(), "banned": True})
    db.delete_item("users", "email", "IGNORE")
except Exception as e:
    print("ERROR tijdens het test schrijven naar de database nieuwe tabel word gemaakt.\nen oja hier is de error: ", e)
    db.create_table("users", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "password": "TEXT", "email": "TEXT", "removeAt": "INTEGER", "banned": "BOOLEAN", "botId": "INTEGER UNIQUE"})
    db.create_table("webhooks", {"id": "INTEGER PRIMARY KEY AUTOINCREMENT", "url": "TEXT", "botId": "INTEGER NOT NULL UNIQUE"})
app = FastAPI(title="Bot Management API", version="0.1")

@app.get("/setup/{email}/{password}")
async def setup(email: str, password: str):
    """
    Setup endpoint to create a user with email and password.
    :param email:
    :param password:
    :return:
    """
    await cleanup()
    try:
        db.insert_into_table(
            "users",
            {
                "email": email,
                "password": password,
                "banned": False,
                "removeAt": time.time() + 60 * 30,  # 30 minutes from now
                "botId": find_lowest_available_botid()
            }
        )
        return {"staat": "OK"}
    except Exception as error:
        return {"error": str(error), "staat": "ERROR"}

@app.get("/getbot/{email}")
async def getbot(email: str):
    """
    Get the bot information for a user by email.
    :param email:
    :return:
    """
    await cleanup()
    try:
        user = db.get_item("users", "email", email)
        if user:
            return {"password": user[1], "email": user[2], "banned": user[4], "removeAt": user[3], "staat": "OK", "botId": user[5], "webhook": db.get_item("webhooks", "botId", user[5])}
        else:
            return {"error": "User not found", "staat": "ERROR"}
    except Exception as error:
        return {"error": str(error), "staat": "ERROR"}

@app.get("/dump/")
async def dump():
    """
    Dump all users in the database.
    :return:
    """
    await cleanup()
    try:
        users = db.get_all_items_sorted("users", "id", descending=True)
        return {"users": users, "staat": "OK"}
    except Exception as error:
        return {"error": str(error), "staat": "ERROR"}

@app.get("/ik_leef/{email}")
async def ik_leef(email: str):
    """
    Endpoint to check if a user is alive and update their removeAt timestamp.
    :param email:
    :return:
    """
    await cleanup()
    try:
        db.edit_item("users", "removeAt", time.time() + 60 * 30, "email", email)
        return {"staat": "OK"}
    except Exception as error:
        return {"error": str(error), "staat": "ERROR"}

@app.get("/cleanup/")
async def manual_cleanup():
    await cleanup()
    return {"staat": "Cleanup triggered manually"}


def find_lowest_available_botid():
    """Find the lowest available botId that is not already in use."""
    try:
        # Get all existing botIds
        users = db.get_all_items_sorted("users", "id")
        used_ids = set()

        # Extract botIds from users
        for user in users:
            if isinstance(user, dict) and "botId" in user:
                used_ids.add(user["botId"])
            elif isinstance(user, tuple) and len(user) > 5 and user[5] is not None:
                used_ids.add(user[5])

        # Find the lowest available id
        next_id = 0
        while next_id in used_ids:
            next_id += 1

        return next_id
    except Exception as error:
        print(f"Error finding lowest botId: {error}")
        return 1  # Default to 1 if there's an error

@app.get("/reportBan/{email}")
async def report_ban(email: str):
    """
    Report a user as banned.
    :param email:
    :return:
    """
    await cleanup()
    try:
        db.edit_item("users", "banned", True, "email", email)
        return {"staat": "OK"}
    except Exception as error:
        return {"error": str(error), "staat": "ERROR"}