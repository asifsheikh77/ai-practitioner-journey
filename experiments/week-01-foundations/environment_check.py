
import platform
import sys
import urllib.request
import urllib.error

print("Python:", sys.version.split()[0])
print("Operating system:", platform.platform())
print("Python executable:", sys.executable)

try:
    with urllib.request.urlopen(
        "http://localhost:11434/api/tags",
        timeout=5
    ) as response:
        print("Ollama status:", response.status)
        print("Ollama API: reachable")

except (urllib.error.URLError, TimeoutError) as error:
    print("Ollama API: not reachable")
    print("Details:", error)
