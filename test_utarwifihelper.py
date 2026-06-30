import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure the script directory is in the path so we can import utarwifihelper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import utarwifihelper

class TestUtarWifiHelper(unittest.TestCase):

    def test_rc4_encrypt(self):
        """Test RC4 encryption logic against known output format."""
        key = "test_key"
        plaintext = "secret_password"
        encrypted = utarwifihelper.rc4_encrypt(key, plaintext)
        
        # Output should be a hex string of the same length as plaintext * 2
        self.assertEqual(len(encrypted), len(plaintext) * 2)
        # Should contain only hex characters
        self.assertTrue(all(c in "0123456789abcdefABCDEF" for c in encrypted))

    @patch('utarwifihelper.requests.get')
    def test_check_internet_success(self, mock_get):
        """Test internet check when 204 is returned."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_get.return_value = mock_response
        
        self.assertTrue(utarwifihelper.check_internet())

    @patch('utarwifihelper.requests.get')
    def test_check_internet_fail(self, mock_get):
        """Test internet check when exception occurs."""
        mock_get.side_effect = Exception("Connection refused")
        self.assertFalse(utarwifihelper.check_internet())

    @patch('utarwifihelper.requests.Session')
    def test_detect_portal_url_redirect(self, mock_session_class):
        """Test portal detection via 302 redirect."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_response.headers = {"Location": "http://example.com/ac_portal/login.php"}
        
        mock_session.get.return_value = mock_response
        
        url = utarwifihelper.detect_portal_url()
        self.assertEqual(url, "http://example.com/ac_portal/login.php")

    @patch('utarwifihelper.requests.Session')
    def test_login_success(self, mock_session_class):
        """Test login success path."""
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_post_response
        
        result = utarwifihelper.login("http://portal.com/ac_portal/", "user", "pass")
        self.assertTrue(result)

    @patch('utarwifihelper.subprocess.run')
    @patch('utarwifihelper.get_current_ssid')
    def test_scan_and_connect_netsh_fallback_fail(self, mock_get_ssid, mock_run):
        """Test netsh fallback aborts properly when out of range."""
        # Mock PyWiFi to fail and fallback to netsh
        utarwifihelper.pywifi.PyWiFi = MagicMock(side_effect=Exception("No pywifi"))
        
        # Mock get_current_ssid to return nothing (meaning netsh failed to connect)
        mock_get_ssid.return_value = None
        
        # Should return False because verification failed
        result = utarwifihelper.scan_and_connect("utarwifi", log_callback=lambda x: None)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
