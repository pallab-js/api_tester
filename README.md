# API Tester

A powerful CLI tool for testing APIs, built with Python.

## Features

- HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
- Request headers and query parameters
- JSON request bodies
- Basic authentication
- Environment variables with `{{variable}}` syntax
- Save requests to collections
- Request history
- Response assertions (status, body, headers, time, size)
- JSON/YAML import/export
- Retry logic with exponential backoff
- Parallel collection execution
- Request chaining (use response data in subsequent requests)
- Response export to files
- GraphQL support
- Interactive mode
- Response diff tool

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
  -d '{"name": "Pallab", "email": "sonowalpallabjyoti@gmail.com"}'
```

### With authentication
```bash
python3 api_tester.py request get https://api.example.com/users \
  -H "Authorization: Bearer TOKEN" \
  --auth "username:password"
```

### With retry
```bash
python3 api_tester.py request get https://api.example.com/users --retry 3 --retry-delay 2
```

### GraphQL request
```bash
python3 api_tester.py request post https://api.example.com/graphql \
  --graphql \
  -d 'query { users { id name } }'
```

### Save to collection
```bash
python3 api_tester.py request get https://api.example.com/users --save my-api
```

### Run collection
```bash
python3 api_tester.py run-collection my-api
python3 api_tester.py run-collection my-api --parallel
```

### Interactive mode
```bash
python3 api_tester.py interactive
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
  --test "body.name==John" \
  --test "response_time<1000" \
  --test "header.Content-Type==application/json" \
  --test "response_size>0"
```

Supported operators: ==, !=, >, <, >=, <=

Fields: status_code, body.*, header.*, response_time (ms), response_size (bytes)

## Collections

```bash
# List collections
python3 api_tester.py list

# Export collection
python3 api_tester.py export my-api --format json

# Import collection
python3 api_tester.py import-collection my-api.json

# Run in parallel
python3 api_tester.py run-collection my-api --parallel
```

## Request Chaining

Use response data from previous requests in collections:

```bash
# In collection, use {{response0.id}} in URL or body of next request
```

## Diff Responses

```bash
python3 api_tester.py diff response1.json response2.json
```

## Requirements

- Python 3.7+
- requests
- click
- rich
- pyyaml
- python-dotenv

## License

MIT License - see LICENSE file for details