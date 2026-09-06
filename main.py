from exporter.server import app, config

if __name__ == "__main__":
    host = config["server"]["host"]
    port = config["server"]["port"]
    app.run(host=host, port=port)
