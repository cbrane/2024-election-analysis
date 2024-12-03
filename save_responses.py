"""
Script to save NYT election data responses for all states and DC.
"""
import json
import os
import requests
from typing import Dict


def get_all_state_urls() -> Dict[str, str]:
    """
    Generate URLs for all 50 states and DC.

    Returns:
        Dict[str, str]: Dictionary mapping state names to their NYT JSON URLs
    """
    base_url = "https://static01.nyt.com/elections-assets/pages/data/2024-11-05/results-{}-president.json"
    
    states = {
        "Alabama": "alabama", "Alaska": "alaska", "Arizona": "arizona",
        "Arkansas": "arkansas", "California": "california", "Colorado": "colorado",
        "Connecticut": "connecticut", "Delaware": "delaware", 
        "District of Columbia": "washington-dc", "Florida": "florida",
        "Georgia": "georgia", "Hawaii": "hawaii", "Idaho": "idaho",
        "Illinois": "illinois", "Indiana": "indiana", "Iowa": "iowa",
        "Kansas": "kansas", "Kentucky": "kentucky", "Louisiana": "louisiana",
        "Maine": "maine", "Maryland": "maryland", "Massachusetts": "massachusetts",
        "Michigan": "michigan", "Minnesota": "minnesota", "Mississippi": "mississippi",
        "Missouri": "missouri", "Montana": "montana", "Nebraska": "nebraska",
        "Nevada": "nevada", "New Hampshire": "new-hampshire", "New Jersey": "new-jersey",
        "New Mexico": "new-mexico", "New York": "new-york", 
        "North Carolina": "north-carolina", "North Dakota": "north-dakota",
        "Ohio": "ohio", "Oklahoma": "oklahoma", "Oregon": "oregon",
        "Pennsylvania": "pennsylvania", "Rhode Island": "rhode-island",
        "South Carolina": "south-carolina", "South Dakota": "south-dakota",
        "Tennessee": "tennessee", "Texas": "texas", "Utah": "utah",
        "Vermont": "vermont", "Virginia": "virginia", "Washington": "washington",
        "West Virginia": "west-virginia", "Wisconsin": "wisconsin", 
        "Wyoming": "wyoming"
    }
    
    return {state: base_url.format(url_name) for state, url_name in states.items()}


def save_state_responses(output_dir: str = "state_responses"):
    """
    Fetch and save JSON responses for all states.

    Args:
        output_dir (str): Directory to save the JSON responses
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    state_urls = get_all_state_urls()
    total_states = len(state_urls)
    processed = 0
    failed = []
    
    print(f"Saving responses for {total_states} states to {output_dir}/")
    
    for state_name, url in state_urls.items():
        processed += 1
        file_name = state_name.lower().replace(" ", "_") + ".json"
        file_path = os.path.join(output_dir, file_name)
        
        print(f"\nProcessing {state_name} ({processed}/{total_states})")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Saved response to {file_path}")
            
        except Exception as e:
            print(f"✗ Error saving {state_name}: {str(e)}")
            failed.append(state_name)
    
    # Print summary
    print("\nDownload Complete")
    print("=" * 50)
    print(f"Total States: {total_states}")
    print(f"Successfully saved: {total_states - len(failed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed States:")
        for state in failed:
            print(f"- {state}")


if __name__ == "__main__":
    save_state_responses() 