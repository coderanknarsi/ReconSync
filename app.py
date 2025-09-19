#!/usr/bin/env python3
import http.server
import socketserver
import urllib.parse
import json
from datetime import datetime
import os
import html

# Fake data for demonstration purposes
VEHICLE_DATA = {
    "123": {
        "vin": "123",
        "year": 2018,
        "make": "Ford",
        "model": "F-150",
        "customer": "Jane Smith",
        "phone": "(555) 123-4567",
        "email": "jane.smith@email.com",
    },
}

CUSTOMER_DATA = {
    "john doe": {
        "vin": "ABC123",
        "year": 2020,
        "make": "Toyota",
        "model": "Camry",
        "customer": "John Doe",
        "phone": "(555) 987-6543",
        "email": "john.doe@email.com",
    },
}

# Store repair orders in memory
REPAIR_ORDERS = {}
_ticket_counter = 0

def get_next_ticket_number():
    global _ticket_counter
    _ticket_counter += 1
    return _ticket_counter

def load_template(template_name):
    """Load HTML template from templates directory"""
    try:
        with open(f'templates/{template_name}', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"<html><body><h1>Template {template_name} not found</h1></body></html>"

def render_template(template_name, **kwargs):
    """Simple template rendering with variable substitution"""
    template = load_template(template_name)
    
    # Simple variable substitution
    for key, value in kwargs.items():
        if isinstance(value, dict):
            # Handle nested dictionaries
            for nested_key, nested_value in value.items():
                template = template.replace(f'{{{{{key}.{nested_key}}}}}', str(nested_value))
        elif isinstance(value, list):
            # Handle lists (for repair orders)
            if key == 'repair_orders':
                rows = ""
                for ticket, order in value.items():
                    rows += f"""
                    <tr>
                        <td>{ticket}</td>
                        <td>{order.get('vin', '')}</td>
                        <td>{order.get('customer', '')}</td>
                        <td>{order.get('work_description', '')[:50]}...</td>
                        <td>${order.get('total', 0):.2f}</td>
                        <td>{order.get('status', 'Open')}</td>
                        <td>{order.get('created_at', '')[:10]}</td>
                    </tr>
                    """
                template = template.replace('{{repair_orders_rows}}', rows)
        else:
            template = template.replace(f'{{{{{key}}}}}', str(value))
    
    return template

class ShopHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)
        
        if path == '/' or path == '/search':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = render_template('search.html')
            self.wfile.write(html_content.encode())
            
        elif path == '/repair-order':
            vin = query.get('vin', [''])[0]
            ticket_number = query.get('ticket', [''])[0]
            
            vehicle = VEHICLE_DATA.get(vin)
            if not vehicle:
                vehicle = next((data for data in CUSTOMER_DATA.values() if data["vin"] == vin), None)
            
            if not vehicle:
                vehicle = {
                    "vin": vin or "Unknown",
                    "year": "-",
                    "make": "-",
                    "model": "-",
                    "customer": "Unknown",
                    "phone": "-",
                    "email": "-",
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = render_template('repair_order.html', vehicle=vehicle, ticket_number=ticket_number)
            self.wfile.write(html_content.encode())
            
        elif path == '/repair-orders':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html_content = render_template('repair_orders_list.html', repair_orders=REPAIR_ORDERS)
            self.wfile.write(html_content.encode())
            
        elif path.startswith('/static/'):
            # Serve static files
            file_path = path[1:]  # Remove leading slash
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                    if path.endswith('.css'):
                        content_type = 'text/css'
                    elif path.endswith('.js'):
                        content_type = 'application/javascript'
                    else:
                        content_type = 'application/octet-stream'
                    
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'File not found')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Page not found')
    
    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/search':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            form_data = urllib.parse.parse_qs(post_data)
            
            query = form_data.get('query', [''])[0].strip()
            
            if not query:
                # Redirect back to search with error
                self.send_response(302)
                self.send_header('Location', '/')
                self.end_headers()
                return
            
            vehicle = None
            
            # VIN lookup
            if query in VEHICLE_DATA:
                vehicle = VEHICLE_DATA[query]
            else:
                # Customer lookup (case-insensitive)
                vehicle = CUSTOMER_DATA.get(query.lower())
            
            if not vehicle:
                vehicle = {
                    "vin": "DEMO123",
                    "year": 2022,
                    "make": "Demo",
                    "model": "Vehicle",
                    "customer": "Demo Customer",
                    "phone": "(555) 000-0000",
                    "email": "demo@example.com",
                }
            
            ticket_number = get_next_ticket_number()
            redirect_url = f'/repair-order?ticket={ticket_number}&vin={vehicle["vin"]}'
            
            self.send_response(302)
            self.send_header('Location', redirect_url)
            self.end_headers()
            
        elif path == '/save-repair-order':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(post_data)
                ticket_number = data.get("ticket_number")
                
                # Create repair order record
                repair_order = {
                    "ticket_number": ticket_number,
                    "vin": data.get("vin"),
                    "customer": data.get("customer"),
                    "work_description": data.get("work_description"),
                    "payer_type": data.get("payer_type"),
                    "line_items": data.get("line_items", []),
                    "subtotal": data.get("subtotal", 0),
                    "tax": data.get("tax", 0),
                    "total": data.get("total", 0),
                    "created_at": datetime.now().isoformat(),
                    "status": "Open"
                }
                
                REPAIR_ORDERS[ticket_number] = repair_order
                
                response = {"success": True, "message": "Repair order saved successfully"}
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                response = {"success": False, "message": str(e)}
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

def run_server(port=8000):
    with socketserver.TCPServer(("", port), ShopHandler) as httpd:
        print(f"Shop Management System running at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == "__main__":
    run_server()