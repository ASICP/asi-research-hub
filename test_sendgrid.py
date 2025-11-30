import os
import ssl
import certifi
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email():
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    
    print(f"Testing SendGrid Configuration...")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    print(f"From Email: {from_email}")
    
    if not api_key or not from_email:
        print("❌ Missing configuration!")
        return

    message = Mail(
        from_email=from_email,
        to_emails=from_email,  # Send to self for testing
        subject='ASI Research Hub - Test Email',
        html_content='<strong>If you see this, SendGrid is configured correctly!</strong>'
    )
    
    try:
        # Create a custom HTTP client with certifi context if needed
        # But usually just setting the env var helps
        os.environ['SSL_CERT_FILE'] = certifi.where()
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        print(f"✅ Email sent successfully!")
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")

if __name__ == "__main__":
    test_email()
