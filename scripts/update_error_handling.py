#!/usr/bin/env python3
"""
Update all services to use standardized error handling.

This script adds error handling middleware to all microservices.
"""
import os
import re
from pathlib import Path


def update_service_file(service_path: str, service_name: str):
    """Update a service file to include error handling."""
    main_py = os.path.join(service_path, "main.py")
    
    if not os.path.exists(main_py):
        print(f"⚠️  {service_name}: main.py not found")
        return
    
    with open(main_py, 'r') as f:
        content = f.read()
    
    # Check if already updated
    if "setup_error_handling" in content:
        print(f"✅ {service_name}: Already has error handling")
        return
    
    # Add import
    import_pattern = r"(from core\.middleware\.\w+ import \w+)"
    if "from core.middleware.error_handling import setup_error_handling" not in content:
        # Find the last import line
        lines = content.split('\n')
        import_end = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_end = i
        
        # Insert error handling import
        lines.insert(import_end + 1, "from core.middleware.error_handling import setup_error_handling")
        content = '\n'.join(lines)
    
    # Add setup_error_handling call
    create_app_pattern = r"(def create_app\([^)]*\) -> web\.Application:.*?app = web\.Application\(\))"
    
    if re.search(create_app_pattern, content, re.DOTALL):
        # Find create_app function and add setup_error_handling
        content = re.sub(
            r"(def create_app\([^)]*\) -> web\.Application:.*?app = web\.Application\(\))",
            r"\1\n    \n    # Setup error handling\n    setup_error_handling(app, \"" + service_name + "\")",
            content,
            flags=re.DOTALL
        )
    
    # Write back
    with open(main_py, 'w') as f:
        f.write(content)
    
    print(f"✅ {service_name}: Updated with error handling")


def main():
    """Update all services."""
    services_dir = Path("services")
    
    if not services_dir.exists():
        print("❌ Services directory not found")
        return
    
    services = [
        "auth", "profile", "discovery", "chat", "media", 
        "admin", "notification", "data"
    ]
    
    for service in services:
        service_path = services_dir / service
        if service_path.exists():
            update_service_file(str(service_path), f"{service}-service")
        else:
            print(f"⚠️  {service}-service: Directory not found")
    
    print("\n🎉 Error handling update complete!")


if __name__ == "__main__":
    main()
