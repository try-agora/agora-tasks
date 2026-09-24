# Microapp
A synthetic request pipeline. Middleware instances live for one App instance.
Register middleware with the decorator; lower priorities run first.
Logging wraps the chain. Handlers return (status, body).
Configuration is in src/microapp/config.py.
Run the public smoke tests with python -m unittest discover -s tests.
