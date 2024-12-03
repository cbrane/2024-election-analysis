from electionthings import analyze_all_states

def main():
    """
    Main function to analyze election data for all states and DC.
    """
    try:
        state_results = analyze_all_states()
        return state_results
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        return None

if __name__ == "__main__":
    state_results = main()