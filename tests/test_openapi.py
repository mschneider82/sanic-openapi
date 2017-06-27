from sanic import Sanic
from sanic_openapi.openapi import blueprint

# ------------------------------------------------------------ #
#  GET
# ------------------------------------------------------------ #

def test_get_docs():
    app = Sanic('test_get')

    app.blueprint(blueprint)

    request, response = app.test_client.get('/openapi/spec.json')
    print(next(response.json()))
    assert response.status == 200

test_get_docs()