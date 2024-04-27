import asyncio
import os
import time

from consts import IMAGE_DIRECTORY

async def delete_old_images(age_limit=60):
    while True:
        try:
            now = time.time()
            for filename in os.listdir(IMAGE_DIRECTORY):
                file_path = os.path.join(IMAGE_DIRECTORY, filename)
                if os.stat(file_path).st_mtime < now - age_limit:
                    os.remove(file_path)
                    print(f"Deleted {file_path}")
        except Exception as e:
            print(f"Error deleting files: {e}")
        await asyncio.sleep(60)