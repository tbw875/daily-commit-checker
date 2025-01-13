import pytest
import os
from dotenv import load_dotenv

# Load test environment variables
@pytest.fixture(autouse=True)
def load_env():
    load_dotenv('tests/.env.test')

@pytest.fixture(autouse=True)
def mock_twilio_client():
    """Mock Twilio Client initialization and message creation"""
    with patch('twilio.rest.Client') as mock_client:
        # Create a mock messages instance
        mock_messages = mock_client.return_value.messages
        mock_messages.create.return_value.sid = 'TEST_SID'
        yield mock_client
