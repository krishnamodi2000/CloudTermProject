import requests

def lambda_handler(event, context):
    url = "http://10.0.131.134:3080/download"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        print("Request successful. Server response:")
        print(response.text)

        return {
            'statusCode': response.status_code,
            'body': response.text
        }
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {
            'statusCode': 500,
            'body': f"Request failed: {e}"
        }
