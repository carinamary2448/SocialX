import shutil
from pathlib import Path

def cleanFake():
	"""Remove the `templates/fake` directory if it exists.

	This is a best-effort cleanup used at startup. Missing directory is
	expected on first run and will be ignored silently.
	"""
	fake_dir = Path('templates') / 'fake'
	if not fake_dir.exists():
		return

	try:
		shutil.rmtree(fake_dir)
		print('[+] Removed templates/fake')
	except OSError as e:
		print(f'[-] Could not remove templates/fake: {e}')