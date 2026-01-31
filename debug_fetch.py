import requests
import re

try:
    resp = requests.get('http://127.0.0.1:8000/api/summaries/')
    if resp.status_code == 200:
        print("Success! JSON returned.")
        print(resp.text[:200])
    else:
        print(f"Error Code: {resp.status_code}")
        # Search for exception value
        text = resp.text
        # Django standard debug page pattern
        match = re.search(r"<th>Exception Value:</th>\s*<td><pre class=\"exception_value\">(.*?)</pre></td>", text, re.DOTALL)
        if match:
            print("Exception Value:", match.group(1))
        else:
            # Fallback simple search
            match2 = re.search(r"Exception Value: (.*?)<", text)
            if match2:
                print("Exception Value (fallback):", match2.group(1))
            else:
                print("Could not parse exception. Dumping first 1000 chars of text:")
                print(text[:1000])

        match_type = re.search(r"<th>Exception Type:</th>\s*<td>(.*?)\s*</td>", text, re.DOTALL)
        if match_type:
             print("Exception Type:", match_type.group(1))

except Exception as e:
    print(f"Fetch failed: {e}")
