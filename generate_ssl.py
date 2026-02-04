#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for HTTPS support.
This is required for camera access on mobile devices over the network.
"""

import os
import subprocess
import sys

def generate_certificates():
    """Generate self-signed SSL certificates using OpenSSL"""
    
    certs_dir = os.path.join(os.path.dirname(__file__), 'certs')
    os.makedirs(certs_dir, exist_ok=True)
    
    cert_file = os.path.join(certs_dir, 'cert.pem')
    key_file = os.path.join(certs_dir, 'key.pem')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✓ SSL certificates already exist in ./certs/")
        print(f"  - {cert_file}")
        print(f"  - {key_file}")
        
        response = input("\nRegenerate certificates? (y/N): ").strip().lower()
        if response != 'y':
            print("Keeping existing certificates.")
            return True
    
    print("\n🔐 Generating self-signed SSL certificates...")
    print("   (Valid for 365 days)\n")
    
    # Get local IP for Subject Alternative Name
    local_ip = get_local_ip()
    
    # OpenSSL command to generate self-signed certificate
    # Using Subject Alternative Names (SAN) for IP access
    openssl_cmd = [
        'openssl', 'req', '-x509',
        '-newkey', 'rsa:4096',
        '-keyout', key_file,
        '-out', cert_file,
        '-days', '365',
        '-nodes',  # No password
        '-subj', '/CN=localhost/O=CampusConnect/C=IN',
        '-addext', f'subjectAltName=DNS:localhost,IP:127.0.0.1,IP:{local_ip}'
    ]
    
    try:
        result = subprocess.run(openssl_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ SSL certificates generated successfully!")
            print(f"\n   Certificate: {cert_file}")
            print(f"   Private Key: {key_file}")
            print(f"\n📱 Your local IP: {local_ip}")
            print(f"\n🌐 Access your app at:")
            print(f"   https://localhost:5000")
            print(f"   https://{local_ip}:5000")
            print("\n⚠️  Note: Browsers will show a security warning for self-signed certificates.")
            print("   Click 'Advanced' → 'Proceed to site' to continue.")
            return True
        else:
            print(f"❌ Failed to generate certificates:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL not found. Please install OpenSSL:")
        print("   Ubuntu/Debian: sudo apt install openssl")
        print("   macOS: brew install openssl")
        print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        return False
    except Exception as e:
        print(f"❌ Error generating certificates: {e}")
        return False


def get_local_ip():
    """Get the local IP address of this machine"""
    import socket
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def install_pyopenssl():
    """Install pyopenssl for adhoc SSL support"""
    print("\n📦 Installing pyopenssl for adhoc SSL support...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyopenssl'], check=True)
        print("✅ pyopenssl installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install pyopenssl")
        return False


if __name__ == '__main__':
    print("=" * 50)
    print("  Campus Connect - SSL Certificate Generator")
    print("=" * 50)
    
    # Try to generate certificates with OpenSSL
    success = generate_certificates()
    
    if not success:
        print("\n🔄 Attempting alternative: Installing pyopenssl for adhoc SSL...")
        install_pyopenssl()
        print("\n✓ You can now use USE_HTTPS=1 with adhoc SSL certificates")
    
    print("\n" + "=" * 50)
    print("  Next Steps:")
    print("=" * 50)
    print("1. Set USE_HTTPS=1 in your .env file")
    print("2. Run: python app.py")
    print("3. Access via HTTPS on your mobile device")
    print("4. Accept the security warning in your browser")
    print("=" * 50)
