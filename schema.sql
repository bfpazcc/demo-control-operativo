services:
  - type: web
    name: demo-control-operativo
    env: python
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
