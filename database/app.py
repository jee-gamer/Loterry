import connexion

app = connexion.FlaskApp(__name__, specification_dir='openapi/')
app.add_api('swagger.yaml')

if __name__ == "__main__":
    app.run(debug=True)
