import requests
import re

# trace GEO IP -------------------------------------------------------------------------------------------------

def tracegeoIp(ip):
    """Trace geolocation of IP address with validation"""
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$|^127\.0\.0\.1$|^::1$|^[a-f0-9:]+$'
    
    if not re.match(ip_pattern, ip):
        return {'error': 'Invalid IP format'}
    
    try:
        if '127.0.0.1' == ip or '::1' == ip:
            url = 'https://geoip-db.com/json/'
        else:
            url = 'https://geoip-db.com/jsonp/' + ip
        
        # Use timeout and verify SSL
        result = requests.get(url, timeout=10, verify=True).json()
    except requests.exceptions.Timeout:
        result = {'error': 'Request timeout. Check your network connection.'}
    except requests.exceptions.ConnectionError:
        result = {'error': 'Connection failed. Verify your network connection.'}
    except (ValueError, requests.exceptions.JSONDecodeError):
        result = {'error': 'Invalid response format from GeoIP service'}
    except Exception as e:
        print(f'[-] GeoIP trace error: {str(e)}')
        result = {'error': 'Trace failed. Verify your network connection.'}
    
    return result
# --------------------------------------------------------------------------------------------------------------