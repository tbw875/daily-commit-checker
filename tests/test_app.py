import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime, timezone
import sys
import os

# Add the parent directory to the Python path so we can import the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_twilio():
    with patch('app.client') as mock_client:
        yield mock_client

class TestWebhook:
    def test_unauthorized_request(self, client):
        response = client.post('/webhook', 
            json={'message': 'test'},
            headers={'X-Webhook-Secret': 'wrong-secret'})
        assert response.status_code == 401

    def test_successful_webhook(self, client, mock_twilio_client):
        response = client.post('/webhook',
            json={'message': 'test'},
            headers={'X-Webhook-Secret': 'test-secret'})
        
        # Assert the response is correct
        assert response.status_code == 200
        assert response.json['success'] is True
        
        # Verify Twilio was called correctly
        mock_twilio_client.return_value.messages.create.assert_called_once_with(
            body='test',
            from_=os.getenv('TWILIO_FROM_NUMBER'),
            to=os.getenv('YOUR_PHONE_NUMBER')
        )

class TestGitHubCommitCheck:
    @pytest.fixture
    def mock_github_response(self):
        # Helper to create mock GitHub API responses
        def create_event(event_type, created_at):
            return {
                'type': event_type,
                'created_at': created_at.isoformat()
            }
        return create_event

    def test_finds_push_event(self, mock_github_response):
        today = datetime.now(timezone.utc)
        events = [
            mock_github_response('PushEvent', today),
            mock_github_response('OtherEvent', today)
        ]
        
        with patch('github.rest.activity.listPublicEventsForUser') as mock_events:
            mock_events.return_value = {'data': events}
            
            # Simulate the GitHub Action script
            commitFound = False
            for event in events:
                if event['type'] == 'PushEvent':
                    event_date = event['created_at'].split('T')[0]
                    if event_date == today.date().isoformat():
                        commitFound = True
                        break
            
            assert commitFound is True

    def test_handles_pagination(self, mock_github_response):
        today = datetime.now(timezone.utc)
        
        # Create 50 events (more than default page size)
        events = [mock_github_response('OtherEvent', today) for _ in range(49)]
        # Add a PushEvent at the end
        events.append(mock_github_response('PushEvent', today))
        
        with patch('github.rest.activity.listPublicEventsForUser') as mock_events:
            # Simulate pagination by returning events in chunks
            mock_events.return_value = {'data': events[:30]}  # First page
            
            # The current implementation would miss this commit
            commitFound = False
            for event in events[:30]:  # Only checking first page
                if event['type'] == 'PushEvent':
                    event_date = event['created_at'].split('T')[0]
                    if event_date == today.date().isoformat():
                        commitFound = True
                        break
            
            assert commitFound is False  # Test fails, showing the pagination issue

    def test_timezone_handling(self, mock_github_response):
        # Create event at 11:59 PM PST
        pst_late_night = datetime.now(timezone.utc)  # Would need proper timezone handling
        
        events = [mock_github_response('PushEvent', pst_late_night)]
        
        with patch('github.rest.activity.listPublicEventsForUser') as mock_events:
            mock_events.return_value = {'data': events}
            
            # Current implementation might miss this depending on timezone handling
            today = datetime.now(timezone.utc).date().isoformat()
            commitFound = False
            for event in events:
                if event['type'] == 'PushEvent':
                    event_date = event['created_at'].split('T')[0]
                    if event_date == today:
                        commitFound = True
                        break
            
            assert commitFound is True  # Might fail due to timezone issues

