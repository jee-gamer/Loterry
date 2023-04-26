import connexion

application = connexion.FlaskApp(__name__, specification_dir='openapi/')
application.add_api('swagger.yaml')

if __name__ == "__main__":
    application.run(debug=True)
