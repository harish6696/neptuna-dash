import app

if __name__ == '__main__':
    print("Open the webapp on this port: localhost:5121")
    # We use app.app.run instead of app.run_server if we want to customize the output
    # but app.run_server is the standard Dash way.
    # To match the requirement exactly:
    app.app.run(host='0.0.0.0', port=5121, debug=False)
