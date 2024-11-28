import requests
import os
import json

# Your Etherscan API Key

def fetch_source_code(API_KEY, contract_address):
    """
    Fetch the source code or ABI of a smart contract from Etherscan.
    """
    url = f"https://api.etherscan.io/api?module=contract&action=getsourcecode&address={contract_address}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if data["status"] == "1" and len(data["result"]) > 0:
        return data["result"][0]
    else:
        raise Exception(f"Failed to fetch source code or ABI: {data['message']}")

def sanitize_source_code(source_code):
    """
    Sanitize the malformed JSON source code returned by Etherscan.
    """
    sanitized_code = source_code.strip().lstrip("{").rstrip("}")
    sanitized_code = "{" + sanitized_code + "}"  # Re-add a single pair of braces
    return sanitized_code

def save_multi_file(source_code_json, output_dir):
    """
    Save multi-part Solidity source code (e.g., Truffle/Hardhat projects).
    """
    # Sanitize and fix malformed JSON
    sanitized_code = sanitize_source_code(source_code_json)

    try:
        # Attempt to decode the sanitized JSON source code
        sources = json.loads(sanitized_code)
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to decode multi-part source code JSON after sanitization.\nRaw source code:\n{sanitized_code}")

    # Save the files
    for file_name, file_data in sources.get("sources", {}).items():
        # Ensure the full directory structure exists before saving the file
        file_path = os.path.join(output_dir, file_name)
        dir_name = os.path.dirname(file_path)
        
        try:
            # Create directories if they do not exist
            os.makedirs(dir_name, exist_ok=True)
            
            # Get the content of the file (which should be a string)
            file_content = file_data.get("content", "")
            if isinstance(file_content, dict):  # If content is a dictionary, try to access the actual source code
                file_content = json.dumps(file_content)
            
            # Ensure the content is a string before writing to the file
            if not isinstance(file_content, str):
                raise TypeError(f"Expected file content to be a string, but got {type(file_content)}.")
            
            with open(file_path, "w") as file:
                file.write(file_content)
            print(f"Saved {file_name} to {dir_name}")
        except Exception as e:
            print(f"Error saving {file_name} in {dir_name}: {e}")

def main():
    # User-provided contract address
    API_KEY = input("Enter the API key: ").strip()
    contract_address = input("Enter the contract address: ").strip()
    output_dir = "contracts"  # Directory for multi-part source code

    try:
        # Fetch contract data
        
        contract_data = fetch_source_code(API_KEY, contract_address)

        # Check if source code is available
        source_code = contract_data["SourceCode"]
        contract_name = contract_data["ContractName"]
        abi = contract_data["ABI"]

        if not source_code or source_code == "":  # No source code available
            print("Warning: No verified source code found. Returning ABI instead.")
            print(f"ABI for contract {contract_name}:")
            print(abi)  # You can save or use the ABI for other purposes
            return

        # If source code is available, proceed to save it
        if source_code.startswith("{"):  # Likely multi-part
            print("Detected multi-part source code.")
            save_multi_file(source_code, os.path.join(output_dir, contract_name))
        else:  # Single Solidity file
            print("Detected single-file source code.")
            filename = f"{contract_name}.sol"
            with open(filename, "w") as file:
                file.write(source_code)
            print(f"Source code saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
