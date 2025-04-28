from datetime import datetime
import os

class OutputLogger:
    def __init__(self, base_filename):
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename, ext = os.path.splitext(base_filename)
        self.filename = f"{filename}_{timestamp}{ext}"
        self.file = open(self.filename, 'w')

    def log(self, message):
        print(message)  # Still print to terminal
        self.file.write(str(message) + '\n')  # Write to file
        self.file.flush()  # Ensure immediate writing

    def close(self):
        self.file.close()