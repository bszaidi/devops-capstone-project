"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}

######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_list_all_accounts(self):
        """It should return all accounts from /accounts/all_accounts as a list of dict and HTTP_200_OK"""

        # Step 1: Ensure the database is empty
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])  # Expecting an empty list

        # Step 2: Create some test accounts
        self._create_accounts(3)  # Creating 3 accounts

        # Step 3: Retrieve the list of accounts
        response = self.client.get(BASE_URL)

        # Validate response
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Should always be 200
        data = response.get_json()  # ✅ Fixed variable name from "daa" to "data"

        # Ensure the response is a list
        self.assertIsInstance(data, list)

        # Ensure it contains the correct number of accounts
        self.assertEqual(len(data), 3)  # ✅ Fixed the indentation issue

        # Check that each account contains expected keys
        for account in data:
            self.assertIn("id", account)
            self.assertIn("name", account)
            self.assertIn("email", account)
            self.assertIn("address", account)
            self.assertIn("phone_number", account)
            self.assertIn("date_joined", account)
    
    def test_read_account(self):
        """It should retrieve an account by ID and return HTTP_200_OK, else return HTTP_404_NOT_FOUND"""
        # Step 1: Try to fetch an account that does not exist
        response = self.client.get(f"{BASE_URL}/999999")  # Assuming this ID does not exist
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Step 2: Ensure the response contains an error message
        error_message = response.get_json()
        self.assertIn("error", error_message)
        self.assertEqual(error_message["error"], "Account not found")

        # Step 3: Create a test account
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED) 

        # Extract account ID from response
        new_account = response.get_json()
        account_id = new_account["id"]

        # Step 2: Retrieve the account by ID
        response = self.client.get(f"{BASE_URL}/{account_id}")

        # Validate the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Deserialize the response and compare values
        retrieved_account = response.get_json()
        self.assertEqual(retrieved_account["id"], account_id)
        self.assertEqual(retrieved_account["name"], account.name)
        self.assertEqual(retrieved_account["email"], account.email)
        self.assertEqual(retrieved_account["address"], account.address)
        self.assertEqual(retrieved_account["phone_number"], account.phone_number)
        self.assertEqual(retrieved_account["date_joined"], str(account.date_joined))

    def test_update_account(self): 
        """It should update an existing account and return HTTP_200_OK, return 404 if not found"""
        # Step 1: Attempt to update an account that does not exist
        response = self.client.put(f"{BASE_URL}/999999", json={})

        # Step 2: Validate response (Should return 404 NOT FOUND)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Step 3: Create a test account
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Extract account ID from response
        new_account = response.get_json()
        account_id = new_account["id"]

        # Step 2: Prepare updated data
        updated_data = {
            "name": "Updated Name",
            "email": "updated@example.com",
            "address": "Updated Address",
            "phone_number": "123-456-7890",
            "date_joined": new_account["date_joined"]  # Keep the same date
        }

        # Step 3: Send PUT request to update the account
        response = self.client.put(f"{BASE_URL}/{account_id}", json=updated_data)

        # Step 4: Validate response (Should return 200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Step 5: Fetch the updated account and verify the changes
        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_account = response.get_json()
        self.assertEqual(updated_account["name"], "Updated Name")
        self.assertEqual(updated_account["email"], "updated@example.com")
        self.assertEqual(updated_account["address"], "Updated Address")
        self.assertEqual(updated_account["phone_number"], "123-456-7890")
        self.assertEqual(updated_account["date_joined"], new_account["date_joined"])  # Should not change

    def test_delete_account(self):
        """It should delete an account and return HTTP_204_NO_CONTENT"""

        # Step 1: Create a test account
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Extract account ID from response
        new_account = response.get_json()
        account_id = new_account["id"]

        # Step 2: Delete the account
        response = self.client.delete(f"{BASE_URL}/{account_id}")

        # Step 3: Validate response (Should return 204 NO CONTENT)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data, b"")  # Ensures the body is empty

        # Step 4: Try to retrieve the deleted account
        response = self.client.get(f"{BASE_URL}/{account_id}")

        # Step 5: Validate that the account no longer exists (Should return 404)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)