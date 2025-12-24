from app import create_app

# This is the entry point for the application.
# It creates the Flask app instance using the function from our app package.
app = create_app()

if __name__ == '__main__':
    # This condition ensures that the app runs only when this script is executed directly.
    # Debug mode is controlled by FLASK_DEBUG environment variable (defaults to False for safety).
    # To enable debug mode for development, set FLASK_DEBUG=True in your .env file.
    debug_mode = app.config.get('DEBUG', False)

    if debug_mode:
        print("⚠️  WARNING: Running in DEBUG mode - this should ONLY be used in development!")
        print("   Debug mode exposes source code and allows interactive debugging via browser.")
    else:
        print("✓ Running in production mode (debug=False)")

    app.run(debug=debug_mode)