import shutil

def cleanFake():
	try:
		shutil.rmtree('templates/fake')
	except (OSError, FileNotFoundError) as e:
		print(f'[-] Directory not found or cannot be removed: {str(e)}')