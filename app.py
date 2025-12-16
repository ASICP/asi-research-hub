"""
Entry point for ARA v2 deployment.
This file imports and runs the ARA v2 application.
"""
import os
import sys

# Add ara_v2 to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the ARA v2 application factory
from ara_v2.app import create_app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
