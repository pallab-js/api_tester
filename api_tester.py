#!/usr/bin/env python3
"""
Powerful CLI-based API testing tool inspired by Postman
"""

import os
import json
import yaml
import click
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich.panel import Panel
from rich.syntax import Syntax
from dotenv import load_dotenv

console = Console()

class APITester:
    """Main API testing tool class"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or '.env'
        self.collections_dir = Path.home() / '.api_tester' / 'collections'
        self.history_file = Path.home() / '.api_tester' / 'history.json'
        self.env_dir = Path.home() / '.api_tester' / 'environments'
        
        # Create directories
        self.collections_dir.mkdir(parents=True, exist_ok=True)
        self.env_dir.mkdir(parents=True, exist_ok=True)
        
        # Load environment variables
        self.environments = {}
        self.current_env = None
        self.load_environment()
    
    def load_environment(self, env_name: Optional[str] = None):
        """Load environment variables"""
        if env_name:
            env_path = self.env_dir / f"{env_name}.env"
            if env_path.exists():
                load_dotenv(env_path)
                self.current_env = env_name
        else:
            # Load default .env file
            if Path(self.env_file).exists():
                load_dotenv(self.env_file)
    
    def substitute_vars(self, text: str) -> str:
        """Substitute {{variable}} with environment variables"""
        import re
        pattern = r'\{\{(\w+)\}\}'
        
        def replace(match):
            var_name = match.group(1)
            value = os.getenv(var_name, match.group(0))
            return value
        
        return re.sub(pattern, replace, text)
    
    def send_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        body: Optional[Any] = None,
        auth: Optional[tuple] = None,
        timeout: int = 30,
        verify: bool = True
    ) -> requests.Response:
        """Send HTTP request"""
        # Substitute variables in URL and headers
        url = self.substitute_vars(url)
        
        if headers:
            headers = {k: self.substitute_vars(str(v)) for k, v in headers.items()}
        
        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                headers=headers,
                params=params,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) else None,
                auth=auth,
                timeout=timeout,
                verify=verify
            )
            return response
        except requests.exceptions.RequestException as e:
            console.print(f"[red]Request failed: {e}[/red]")
            raise
    
    def format_response(self, response: requests.Response, show_headers: bool = False) -> str:
        """Format response for display"""
        output = []
        
        # Status
        status_color = "green" if response.status_code < 400 else "red"
        output.append(f"[{status_color}]Status: {response.status_code} {response.reason}[/{status_color}]\n")
        
        # Headers
        if show_headers:
            headers_table = Table(show_header=True, header_style="bold magenta")
            headers_table.add_column("Header")
            headers_table.add_column("Value")
            for key, value in response.headers.items():
                headers_table.add_row(key, value)
            output.append(headers_table)
            output.append("\n")
        
        # Body
        try:
            body = response.json()
            syntax = Syntax(json.dumps(body, indent=2), "json", theme="monokai")
            output.append(Panel(syntax, title="Response Body", border_style="blue"))
        except:
            body = response.text
            syntax = Syntax(body, "text", theme="monokai")
            output.append(Panel(syntax, title="Response Body", border_style="blue"))
        
        # Timing
        output.append(f"\n[dim]Time: {response.elapsed.total_seconds():.2f}s[/dim]")
        
        return "\n".join(str(o) for o in output)
    
    def save_to_history(self, method: str, url: str, response: requests.Response):
        """Save request to history"""
        history = []
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                history = json.load(f)
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "url": url,
            "status_code": response.status_code,
            "status_text": response.reason
        }
        
        history.insert(0, entry)
        # Keep only last 100 entries
        history = history[:100]
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def save_collection(self, name: str, requests: List[Dict]):
        """Save a collection of requests"""
        collection_file = self.collections_dir / f"{name}.json"
        with open(collection_file, 'w') as f:
            json.dump({"name": name, "requests": requests}, f, indent=2)
        console.print(f"[green]Collection '{name}' saved successfully![/green]")
    
    def load_collection(self, name: str) -> Dict:
        """Load a collection"""
        collection_file = self.collections_dir / f"{name}.json"
        if not collection_file.exists():
            console.print(f"[red]Collection '{name}' not found![/red]")
            return None
        
        with open(collection_file, 'r') as f:
            return json.load(f)
    
    def run_test(self, response: requests.Response, assertions: List[str]) -> Dict:
        """Run assertions on response"""
        results = {"passed": [], "failed": []}
        
        for assertion in assertions:
            try:
                # Parse assertion (e.g., "status_code == 200", "body.key == 'value'")
                if assertion.startswith("status_code"):
                    expected = int(assertion.split("==")[1].strip())
                    if response.status_code == expected:
                        results["passed"].append(assertion)
                    else:
                        results["failed"].append(f"{assertion} (got {response.status_code})")
                elif assertion.startswith("body."):
                    # Simple JSON path assertion
                    path = assertion.split("==")[0].strip().replace("body.", "")
                    expected = assertion.split("==")[1].strip().strip("'\"")
                    try:
                        body = response.json()
                        keys = path.split(".")
                        value = body
                        for key in keys:
                            value = value[key]
                        if str(value) == expected:
                            results["passed"].append(assertion)
                        else:
                            results["failed"].append(f"{assertion} (got {value})")
                    except:
                        results["failed"].append(f"{assertion} (invalid path or response not JSON)")
            except Exception as e:
                results["failed"].append(f"{assertion} (error: {e})")
        
        return results


# CLI Commands
tester = APITester()

@click.group()
@click.option('--env', help='Environment file to use')
def cli(env):
    """Powerful CLI-based API testing tool"""
    global tester
    if env:
        tester.load_environment(env)

@cli.command()
@click.argument('method', type=click.Choice(['get', 'post', 'put', 'delete', 'patch', 'head', 'options']))
@click.argument('url')
@click.option('--header', '-H', multiple=True, help='HTTP headers (format: Key:Value)')
@click.option('--param', '-p', multiple=True, help='Query parameters (format: key=value)')
@click.option('--body', '-d', help='Request body (JSON string or file path)')
@click.option('--file', '-f', type=click.File('r'), help='Load request body from file')
@click.option('--auth', help='Basic auth (format: username:password)')
@click.option('--timeout', default=30, type=int, help='Request timeout in seconds')
@click.option('--no-verify', is_flag=True, help='Disable SSL verification')
@click.option('--show-headers', is_flag=True, help='Show response headers')
@click.option('--test', multiple=True, help='Assertions (e.g., status_code==200, body.id==123)')
@click.option('--save', help='Save request to collection')
def request(method, url, header, param, body, file, auth, timeout, no_verify, show_headers, test, save):
    """Send HTTP request"""
    # Parse headers
    headers = {}
    for h in header:
        if ':' in h:
            key, value = h.split(':', 1)
            headers[key.strip()] = value.strip()
    
    # Parse params
    params = {}
    for p in param:
        if '=' in p:
            key, value = p.split('=', 1)
            params[key.strip()] = value.strip()
    
    # Parse body
    body_data = None
    if file:
        body_data = file.read()
        try:
            body_data = json.loads(body_data)
        except:
            pass
    elif body:
        if Path(body).exists():
            with open(body, 'r') as f:
                body_data = f.read()
                try:
                    body_data = json.loads(body_data)
                except:
                    pass
        else:
            try:
                body_data = json.loads(body)
            except:
                body_data = body
    
    # Parse auth
    auth_tuple = None
    if auth:
        if ':' in auth:
            username, password = auth.split(':', 1)
            auth_tuple = (username, password)
    
    # Send request
    try:
        console.print(f"[bold blue]→ {method.upper()} {url}[/bold blue]\n")
        
        response = tester.send_request(
            method=method,
            url=url,
            headers=headers if headers else None,
            params=params if params else None,
            body=body_data,
            auth=auth_tuple,
            timeout=timeout,
            verify=not no_verify
        )
        
        # Display response
        console.print(tester.format_response(response, show_headers))
        
        # Run tests
        if test:
            console.print("\n[bold]Running Tests:[/bold]")
            results = tester.run_test(response, list(test))
            for passed in results["passed"]:
                console.print(f"[green]✓ {passed}[/green]")
            for failed in results["failed"]:
                console.print(f"[red]✗ {failed}[/red]")
            
            if not results["failed"]:
                console.print("\n[bold green]All tests passed![/bold green]")
            else:
                console.print(f"\n[bold red]{len(results['failed'])} test(s) failed![/bold red]")
        
        # Save to history
        tester.save_to_history(method, url, response)
        
        # Save to collection if requested
        if save:
            request_data = {
                "method": method,
                "url": url,
                "headers": headers,
                "params": params,
                "body": body_data
            }
            # Load existing collection or create new
            collection = tester.load_collection(save)
            requests_list = collection["requests"] if collection else []
            requests_list.append(request_data)
            tester.save_collection(save, requests_list)
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise click.Abort()

@cli.command('list')
def list_collections():
    """List all saved collections"""
    collections = list(tester.collections_dir.glob("*.json"))
    if not collections:
        console.print("[yellow]No collections found[/yellow]")
        return
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Collection Name")
    table.add_column("Requests")
    
    for collection_file in collections:
        collection = tester.load_collection(collection_file.stem)
        if collection:
            table.add_row(collection["name"], str(len(collection.get("requests", []))))
    
    console.print(table)

@cli.command()
@click.argument('name')
@click.option('--format', type=click.Choice(['json', 'yaml']), default='json', help='Export format')
@click.option('--output', '-o', help='Output file path')
def export(name, format, output):
    """Export a collection"""
    collection = tester.load_collection(name)
    if not collection:
        return
    
    if not output:
        output = f"{name}.{format}"
    
    if format == 'json':
        with open(output, 'w') as f:
            json.dump(collection, f, indent=2)
    else:
        with open(output, 'w') as f:
            yaml.dump(collection, f, default_flow_style=False)
    
    console.print(f"[green]Collection exported to {output}[/green]")

@cli.command()
@click.argument('file', type=click.Path(exists=True))
@click.option('--name', help='Collection name (defaults to filename)')
def import_collection(file, name):
    """Import a collection from file"""
    file_path = Path(file)
    if not name:
        name = file_path.stem
    
    if file_path.suffix == '.json':
        with open(file_path, 'r') as f:
            collection = json.load(f)
    elif file_path.suffix in ['.yaml', '.yml']:
        with open(file_path, 'r') as f:
            collection = yaml.safe_load(f)
    else:
        console.print("[red]Unsupported file format[/red]")
        return
    
    tester.save_collection(name, collection.get("requests", []))

@cli.command()
def history():
    """Show request history"""
    if not tester.history_file.exists():
        console.print("[yellow]No history found[/yellow]")
        return
    
    with open(tester.history_file, 'r') as f:
        history_data = json.load(f)
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Time")
    table.add_column("Method")
    table.add_column("URL")
    table.add_column("Status")
    
    for entry in history_data[:20]:  # Show last 20
        status_color = "green" if entry["status_code"] < 400 else "red"
        table.add_row(
            entry["timestamp"][:19],  # Format timestamp
            entry["method"].upper(),
            entry["url"][:50] + "..." if len(entry["url"]) > 50 else entry["url"],
            f"[{status_color}]{entry['status_code']}[/{status_color}]"
        )
    
    console.print(table)

@cli.command()
@click.argument('name')
def run_collection(name):
    """Run all requests in a collection"""
    collection = tester.load_collection(name)
    if not collection:
        return
    
    console.print(f"[bold]Running collection: {name}[/bold]\n")
    
    results = {"passed": 0, "failed": 0, "total": len(collection.get("requests", []))}
    
    for i, req in enumerate(collection.get("requests", []), 1):
        console.print(f"[bold cyan]Request {i}/{results['total']}[/bold cyan]")
        
        try:
            response = tester.send_request(
                method=req.get("method", "GET"),
                url=req.get("url", ""),
                headers=req.get("headers"),
                params=req.get("params"),
                body=req.get("body")
            )
            
            status_color = "green" if response.status_code < 400 else "red"
            console.print(f"  [{status_color}]{req.get('method', 'GET')} {req.get('url', '')} → {response.status_code}[/{status_color}]")
            
            if response.status_code < 400:
                results["passed"] += 1
            else:
                results["failed"] += 1
            
            tester.save_to_history(req.get("method", "GET"), req.get("url", ""), response)
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
            results["failed"] += 1
        
        console.print()
    
    console.print(f"[bold]Results: {results['passed']}/{results['total']} passed, {results['failed']} failed[/bold]")

@cli.command()
@click.argument('name')
@click.argument('file', type=click.Path(exists=True))
def save_env(name, file):
    """Save environment variables from file"""
    env_file = tester.env_dir / f"{name}.env"
    if Path(file).exists():
        import shutil
        shutil.copy(file, env_file)
        console.print(f"[green]Environment '{name}' saved![/green]")
    else:
        console.print(f"[red]File '{file}' not found![/red]")

@cli.command()
@click.argument('name')
def use_env(name):
    """Switch to a different environment"""
    tester.load_environment(name)
    console.print(f"[green]Switched to environment: {name}[/green]")

if __name__ == '__main__':
    cli()
