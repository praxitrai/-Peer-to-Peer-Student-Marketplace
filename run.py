from app import create_app

app = create_app()

if __name__ == '__main__':
    # Debug mode activated for instant server reloads during your development cycle
    app.run(debug=True, port=5000)
