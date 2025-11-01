# API Tester

A simple CLI tool for testing APIs, built with Python.

## Features

- HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- Request headers and query parameters
- JSON request bodies
- Basic authentication
- Environment variables with `{{variable}}` syntax
- Save requests to collections
- Request history
- Response assertions
- JSON/YAML import/export

## Installation

```bash
pip install -r requirements.txt
python3 api_tester.py --help
```

## Usage

### Basic request
```bash
python3 api_tester.py request get https://api.example.com/users
```

### POST with JSON
```bash
python3 api_tester.py request post https://api.example.com/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John", "email": "john@example.com"}'
```

### With authentication
```bash
python3 api_tester.py request get https://api.example.com/users \
  -H "Authorization: Bearer TOKEN" \
  --auth "username:password"
```

### Save to collection
```bash
python3 api_tester.py request get https://api.example.com/users --save my-api
```

### Run collection
```bash
python3 api_tester.py run-collection my-api
```

### Environment variables
Create a `.env` file:
```
API_URL=https://api.example.com
TOKEN=your-token
```

Use in requests:
```bash
python3 api_tester.py request get "{{API_URL}}/users" \
  -H "Authorization: Bearer {{TOKEN}}"
```

## Assertions

```bash
python3 api_tester.py request get https://api.example.com/user/1 \
  --test "status_code==200" \
  --test "body.name==John"
```

## Collections

```bash
# List collections
python3 api_tester.py list

# Export collection
python3 api_tester.py export my-api --format json

# Import collection
python3 api_tester.py import-collection my-api.json
```

## Requirements

- Python 3.7+
- requests
- click
- rich
- pyyaml
- python-dotenv

## License

MIT