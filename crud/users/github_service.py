import requests
from django.conf import settings

class GitHubService:
    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.repo = settings.GITHUB_REPO
        self.api_url = f'https://api.github.com/repos/{self.repo}'

    def _get_headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
        }

    def upload_file(self, path, content, message='Upload file'):
        url = f'{self.api_url}/contents/{path}'
        data = {
            'message': message,
            'content': content.encode('base64')  # Encode content in base64
        }
        response = requests.put(url, json=data, headers=self._get_headers())
        return response.json()

    def get_file(self, path):
        url = f'{self.api_url}/contents/{path}'
        response = requests.get(url, headers=self._get_headers())
        return response.json()

    def list_files(self, path=''):
        url = f'{self.api_url}/contents/{path}'
        response = requests.get(url, headers=self._get_headers())
        return response.json()
