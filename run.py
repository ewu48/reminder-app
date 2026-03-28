import os

from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402 — must load .env before importing app

app = create_app(os.environ.get("FLASK_ENV", "default"))

if __name__ == "__main__":
    topic = app.config["NTFY_TOPIC"]
    print("\n" + "=" * 50)
    print("  Reminder App")
    print("=" * 50)
    print(f"  Web UI : http://localhost:5000")
    print(f"  ntfy   : https://ntfy.sh/{topic}")
    print(f"  Topic  : {topic}")
    print("  Subscribe to the topic in the ntfy app")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=5000)
