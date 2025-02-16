"""
Account Service

This microservice handles the lifecycle of Accounts
"""
# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for   # noqa; F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################
@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
            # paths=url_for("list_accounts", _external=True),
        ),
        status.HTTP_200_OK,
    )


######################################################################
# CREATE A NEW ACCOUNT
######################################################################
@app.route("/accounts", methods=["POST"])
def create_accounts():
    """
    Creates an Account
    This endpoint will create an Account based the data in the body that is posted
    """
    app.logger.info("Request to create an Account")
    check_content_type("application/json")
    account = Account()
    account.deserialize(request.get_json())
    account.create()
    message = account.serialize()
    # Uncomment once get_accounts has been implemented
    # location_url = url_for("get_accounts", account_id=account.id, _external=True)
    location_url = "/"  # Remove once get_accounts has been implemented
    return make_response(
        jsonify(message), status.HTTP_201_CREATED, {"Location": location_url}
    )


######################################################################
# LIST ALL ACCOUNTS
######################################################################


# ... place you code here to LIST accounts ...
@app.route("/accounts", methods=["GET"])
def get_all_accounts_route():
    """Endpoint to fetch all accounts"""
    # Fetch and serialize all accounts
    accounts = [account.serialize() for account in Account.all()]

    # Return response with HTTP_200_OK status code
    return make_response(jsonify(accounts), 200)


######################################################################
# READ AN ACCOUNT
######################################################################


# ... place you code here to READ an account ...
@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    """Retrieve an account by ID"""
    # Use Account.find() to locate the account
    account = Account.find(account_id)

    if not account:
        # If the account is not found, return a 404 response
        return make_response(jsonify({"error": "Account not found"}), 404)

    # If found, serialize the account and return it with a 200 status
    return make_response(jsonify(account.serialize()), 200)


######################################################################
# UPDATE AN EXISTING ACCOUNT
######################################################################


# ... place you code here to UPDATE an account ...
@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """Update an existing account"""
    account = Account.find(account_id)
    if not account:
        return make_response(jsonify({"error": "Account not found"}), 404)

    data = request.get_json()
    account.deserialize(data)
    account.update()

    return make_response(jsonify(account.serialize()), status.HTTP_200_OK)


######################################################################
# DELETE AN ACCOUNT
######################################################################


# ... place you code here to DELETE an account ...
@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """Delete an account by ID"""
    # Step 1: Find the account
    account = Account.find(account_id)

    # Step 2: If the account exists, delete it
    if account:
        account.delete()

    # Step 3: Return an empty response with HTTP_204_NO_CONTENT
    return make_response("", 204)


######################################################################
#  U T I L I T Y   F U N C T I O N S
######################################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    content_type = request.headers.get("Content-Type")
    if content_type and content_type == media_type:
        return
    app.logger.error("Invalid Content-Type: %s", content_type)
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {media_type}",
    )
