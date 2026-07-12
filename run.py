import config
config.Config.SQLALCHEMY_DATABASE_URI = "sqlite:////home/claude/student_marketplace/demo.db"
config.Config.SECRET_KEY = "demo-secret-key-for-screenshots"

from app import create_app
app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
