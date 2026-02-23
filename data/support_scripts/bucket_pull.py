import httpx
import os

bucket_url = "https://ptcd-traces.s3.us-east-2.amazonaws.com/"

def download_file_from_bucket(file_name, save_path):
    url = bucket_url + file_name
    response = httpx.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"File '{file_name}' downloaded successfully to '{save_path}'.")
    else:
        print(f"Failed to download file '{file_name}'. Status code: {response.status_code}")


def main():
    # Example usage: download a file named 'example.csv' from the bucket and save it locally
    #basic request to get xml key list
    response = httpx.get(bucket_url)
    if response.status_code == 200:
        # Parse the XML response to extract file names (keys)
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)
        for contents in root.findall('.//{http://s3.amazonaws.com/doc/2006-03-01/}Contents'):
            key = contents.find('{http://s3.amazonaws.com/doc/2006-03-01/}Key').text
            print(f"Found file in bucket: {key}")
            # Example: download each file to a local directory named 'downloaded_files'
            save_path = os.path.join('downloaded_files', os.path.basename(key))
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            download_file_from_bucket(key, save_path)

if __name__ == "__main__":
    main()