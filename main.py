from website import create_app

app = create_app()

if __name__ == '__main__':
    # Temporarily disable SSL for testing - uncomment next line to re-enable HTTPS
    # app.run(debug=True, port=5000, ssl_context=('ssl/cert.pem', 'ssl/key.pem'))
    app.run(debug=True, port=5000)