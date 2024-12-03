import json
import pandas as pd
import requests
import matplotlib.pyplot as plt
from typing import Dict, List
import os


def fetch_nyt_election_data(url: str) -> Dict:
    """
    Fetch election data from NYT API endpoint.

    Args:
        url (str): URL of the NYT election data endpoint

    Returns:
        Dict: JSON response containing election data
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch data: {str(e)}")


def process_reporting_units(
    reporting_units: List[Dict], dem_candidate_id: str, rep_candidate_id: str
) -> pd.DataFrame:
    """
    Process reporting units data into a pandas DataFrame with combined county data.
    """
    rows = []
    has_historical = False

    for unit in reporting_units:
        # Accept both county and township levels
        if unit["level"] not in ["county", "township"]:
            continue

        total_votes = unit.get("total_votes", unit.get("votes", 0))

        base_data = {
            "name": unit["name"],
            "total_votes": total_votes,
        }

        # Get 2024 data
        for candidate in unit["candidates"]:
            votes = candidate["votes"].get("total", 0)
            base_data[f"{candidate['nyt_id']}_votes"] = votes

        # Only calculate percentages if we have votes
        if total_votes > 0:
            # Calculate 2024 percentages
            base_data[f"{dem_candidate_id}_pct"] = (
                base_data[f"{dem_candidate_id}_votes"] / base_data["total_votes"] * 100
            )
            base_data[f"{rep_candidate_id}_pct"] = (
                base_data[f"{rep_candidate_id}_votes"] / base_data["total_votes"] * 100
            )

        # Get 2020 data if available at the same level
        if "historical_2020_pres" in unit:
            hist = unit["historical_2020_pres"]
            base_data.update({
                "votes_2020": hist.get("votes", 0),
                "dem_pct_2020": hist.get("pct_dem", 0),
                "rep_pct_2020": hist.get("pct_rep", 0),
                "margin_2020": hist.get("margin", 0),
            })
            has_historical = True

        rows.append(base_data)

    df = pd.DataFrame(rows)
    
    # Only calculate shifts if we have historical data
    if has_historical:
        df["dem_shift"] = df[f"{dem_candidate_id}_pct"] - df["dem_pct_2020"]
    else:
        # Create empty shift column if no historical data
        df["dem_shift"] = None
        print("No historical data available at this geographic level")

    # Only create size categories if we have more than one unique total_votes value
    if len(df) > 0 and len(df["total_votes"].unique()) > 1:
        try:
            df["size_category"] = pd.qcut(
                df["total_votes"],
                q=4,
                labels=["Rural", "Small", "Medium", "Urban"],
                duplicates="drop",
            )
        except ValueError:
            df["size_category"] = "Equal Size"
    else:
        df["size_category"] = "Equal Size"

    return df


def create_shift_visualization(
    df: pd.DataFrame, dem_candidate_id: str, state_name: str, results_dir: str
):
    """
    Create a visualization showing the shift in voting patterns between
    2020 and 2024 elections, using FiveThirtyEight style.

    Args:
        df (pd.DataFrame): DataFrame containing both 2024 and 2020 results
        dem_candidate_id (str): NYT ID for Democratic candidate
        state_name (str): Name of the state being analyzed
        results_dir (str): Directory to save results
    """
    # Set style parameters
    plt.style.use("fivethirtyeight")
    dem_blue = "#3572C6"
    rep_red = "#DA4453"
    background_color = "#FFFFFF"
    text_color = "#000000"

    # Calculate the Democratic shift
    df["dem_shift"] = df[f"{dem_candidate_id}_pct"] - df["dem_pct_2020"]
    df_sorted = df.sort_values("dem_shift")

    # Create the figure with style - increased height
    fig, ax = plt.subplots(figsize=(15, 20))
    fig.patch.set_facecolor(background_color)
    ax.set_facecolor(background_color)

    # Create bars
    dem_mask = df_sorted["dem_shift"] >= 0
    rep_mask = df_sorted["dem_shift"] < 0

    # Plot Democratic shifts
    dem_bars = ax.barh(
        df_sorted[dem_mask]["name"],
        df_sorted[dem_mask]["dem_shift"],
        color=dem_blue,
        label="Democratic Shift",
    )

    # Plot Republican shifts
    rep_bars = ax.barh(
        df_sorted[rep_mask]["name"],
        df_sorted[rep_mask]["dem_shift"],
        color=rep_red,
        label="Republican Shift",
    )

    # Get the maximum absolute shift for label positioning
    max_abs_shift = max(
        abs(df_sorted["dem_shift"].max()), abs(df_sorted["dem_shift"].min())
    )
    label_offset = max_abs_shift * 0.05  # 5% of max shift for offset

    # Add percentage labels for all counties
    for i, (name, row) in enumerate(df_sorted.iterrows()):
        shift = row["dem_shift"]
        if shift >= 0:
            label = f"D+{abs(shift):.1f}"
            color = dem_blue
            xpos = shift + label_offset
            ha = "left"
        else:
            label = f"R+{abs(shift):.1f}"
            color = rep_red
            xpos = shift - label_offset
            ha = "right"

        ax.text(
            xpos,
            row["name"],
            label,
            va="center",
            ha=ha,
            color=color,
            fontsize=8,
            fontweight="bold",
        )

    # Styling
    ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5, zorder=1)
    ax.set_title(
        f"{state_name} - County-Level Vote Share Shifts\n2020 to 2024",
        pad=20,
        fontsize=14,
        fontweight="bold",
        color=text_color,
    )
    ax.set_xlabel("Percentage Point Shift", fontsize=10, color=text_color)
    ax.set_ylabel("County", fontsize=10, color=text_color)

    # Customize grid
    ax.grid(True, axis="x", linestyle="--", alpha=0.3, zorder=0)
    ax.grid(False, axis="y")

    # Add legend with custom styling
    legend = ax.legend(
        title="Vote Share Shifts",
        loc="center right",
        bbox_to_anchor=(1.15, 0.5),
        frameon=True,
        facecolor=background_color,
        edgecolor="lightgray",
    )
    legend.get_title().set_fontweight("bold")

    # Customize spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("lightgray")
    ax.spines["bottom"].set_color("lightgray")

    # Adjust tick colors
    ax.tick_params(axis="both", colors=text_color)

    # Add more padding between county names
    ax.margins(y=0.01)

    # Set x-axis limits to accommodate labels
    current_xlim = ax.get_xlim()
    ax.set_xlim(current_xlim[0] * 1.2, current_xlim[1] * 1.2)

    # Adjust layout
    plt.tight_layout()

    # Save the plot with high resolution in results directory
    output_path = os.path.join(results_dir, "county_shifts.png")
    plt.savefig(output_path, bbox_inches="tight", dpi=300, facecolor=background_color)
    plt.close()


def create_additional_visualizations(
    df: pd.DataFrame, dem_candidate_id: str, state_name: str, results_dir: str
):
    """Create additional visualizations for deeper analysis."""

    # Only create size category boxplot if we have the column
    if "size_category" in df.columns:
        plt.figure(figsize=(12, 8))
        df.boxplot(column="dem_shift", by="size_category")
        plt.axhline(y=0, color="black", linestyle="--")
        plt.title(f"{state_name} - Shifts by County Size")
        plt.suptitle("")  # Remove automatic suptitle
        plt.ylabel("Democratic Shift (%)")
        plt.savefig(
            os.path.join(results_dir, "shifts_by_size.png"),
            bbox_inches="tight",
            dpi=300,
        )
        plt.close()


def analyze_election_data(
    url: str,
    state_name: str,
    results_dir: str = "election_results",
    dem_candidate_id: str = "harris-k",
    rep_candidate_id: str = "trump-d",
) -> pd.DataFrame:
    """
    Analyze election data for a given state.

    Args:
        url (str): URL to the NYT JSON data
        state_name (str): Name of the state being analyzed
        results_dir (str): Directory to save results
        dem_candidate_id (str): NYT ID for Democratic candidate
        rep_candidate_id (str): NYT ID for Republican candidate

    Returns:
        pd.DataFrame: Processed election data
    """
    # Create directories
    os.makedirs(results_dir, exist_ok=True)
    state_dir = os.path.join(results_dir, state_name.lower().replace(" ", "_"))
    os.makedirs(state_dir, exist_ok=True)

    # Fetch and process data
    data = fetch_nyt_election_data(url)
    df = process_reporting_units(
        data["races"][0]["reporting_units"], dem_candidate_id, rep_candidate_id
    )

    # Skip shift analysis if we don't have historical data
    if 'dem_shift' not in df.columns or df['dem_shift'].isna().all():
        print(f"No historical comparison data available for {state_name}")
        
        # Save current results without historical comparisons
        csv_path = os.path.join(state_dir, "results.csv")
        df.to_csv(csv_path, index=False)
        
        # Save basic analysis
        analysis_path = os.path.join(state_dir, "analysis.md")
        with open(analysis_path, "w") as f:
            f.write(f"# Vote Analysis for {state_name}\n\n")
            f.write("Note: Historical comparison data not available at this geographic level\n\n")
            
            # Current vote totals
            total_votes = df["total_votes"].sum()
            dem_votes = df[f"{dem_candidate_id}_votes"].sum()
            rep_votes = df[f"{rep_candidate_id}_votes"].sum()
            
            dem_pct = (dem_votes / total_votes) * 100
            rep_pct = (rep_votes / total_votes) * 100
            
            f.write("## Current Vote Totals\n\n")
            f.write(f"* Total Votes: {total_votes:,}\n")
            f.write(f"* Democratic Votes: {dem_votes:,} ({dem_pct:.1f}%)\n")
            f.write(f"* Republican Votes: {rep_votes:,} ({rep_pct:.1f}%)\n")
        
        return df

    # Create visualizations after all calculations
    create_shift_visualization(df, dem_candidate_id, state_name, state_dir)
    create_additional_visualizations(df, dem_candidate_id, state_name, state_dir)

    # Remove any existing county shift map if it exists
    shift_map_path = os.path.join(state_dir, "county_shift_map.html")
    if os.path.exists(shift_map_path):
        os.remove(shift_map_path)

    # Calculate additional statistics
    total_votes_2024 = df["total_votes"].sum()
    total_votes_2020 = df["votes_2020"].sum()

    dem_votes_2024 = df[f"{dem_candidate_id}_votes"].sum()
    rep_votes_2024 = df[f"{rep_candidate_id}_votes"].sum()

    dem_pct_2024 = (dem_votes_2024 / total_votes_2024) * 100
    rep_pct_2024 = (rep_votes_2024 / total_votes_2024) * 100

    weighted_dem_shift = df["dem_shift"].mean()

    # Calculate county-level statistics
    total_counties = len(df)
    dem_counties_2024 = len(
        df[df[f"{dem_candidate_id}_pct"] > df[f"{rep_candidate_id}_pct"]]
    )
    rep_counties_2024 = total_counties - dem_counties_2024

    counties_shifted_dem = len(df[df["dem_shift"] > 0])
    counties_shifted_rep = len(df[df["dem_shift"] < 0])

    # Additional calculations
    # Urban vs Rural Analysis (using vote totals as proxy)
    urban_shift = df[df["size_category"] == "Urban"]["dem_shift"].mean()
    rural_shift = df[df["size_category"] == "Rural"]["dem_shift"].mean()

    # Swing Analysis
    df["swing_severity"] = abs(df["dem_shift"])
    biggest_swings = df.nlargest(10, "swing_severity")

    # Competitiveness Analysis
    df["margin_2024"] = abs(
        df[f"{dem_candidate_id}_pct"] - df[f"{rep_candidate_id}_pct"]
    )
    close_races = df[df["margin_2024"] < 5]  # Counties decided by less than 5%

    # Regional Patterns (if we have region/geographic data)
    # We could group counties by region and analyze patterns

    # Calculate state-level 2020 percentages and margins
    total_votes_2020 = df["votes_2020"].sum()
    dem_votes_2020 = sum(df["votes_2020"] * df["dem_pct_2020"] / 100)
    rep_votes_2020 = sum(df["votes_2020"] * df["rep_pct_2020"] / 100)

    dem_pct_2020 = (dem_votes_2020 / total_votes_2020) * 100
    rep_pct_2020 = (rep_votes_2020 / total_votes_2020) * 100

    margin_2020 = dem_pct_2020 - rep_pct_2020
    margin_prefix_2020 = "D+" if margin_2020 > 0 else "R+"

    # Calculate total shift
    total_shift = (dem_pct_2024 - rep_pct_2024) - (dem_pct_2020 - rep_pct_2020)
    shift_prefix = "D+" if total_shift > 0 else "R+"

    # Get largest shifts
    dem_shifts = df.nlargest(5, "dem_shift")[["name", "dem_shift"]]
    rep_shifts = df.nsmallest(5, "dem_shift")[["name", "dem_shift"]]
    top_counties = df.nlargest(5, "total_votes")

    # Save enhanced analysis results to text file in markdown format
    analysis_path = os.path.join(state_dir, "analysis.md")
    with open(analysis_path, "w") as f:
        f.write(f"# Detailed Vote Analysis for {state_name}\n\n")

        # Overall Vote Totals
        f.write("## Overall Vote Totals\n\n")
        f.write(f"* 2024 Total Votes: {total_votes_2024:,}\n")
        f.write(f"* 2020 Total Votes: {total_votes_2020:,}\n")
        f.write(
            f"* Turnout Change: {((total_votes_2024/total_votes_2020) - 1)*100:.1f}%\n\n"
        )

        # Vote Share Analysis
        f.write("## Vote Share Analysis\n\n")
        f.write(f"* 2024 Democratic Vote Share: {dem_pct_2024:.1f}%\n")
        f.write(f"* 2024 Republican Vote Share: {rep_pct_2024:.1f}%\n")
        margin_2024 = abs(dem_pct_2024 - rep_pct_2024)
        margin_prefix_2024 = "D+" if dem_pct_2024 > rep_pct_2024 else "R+"
        f.write(f"* 2024 Margin: {margin_prefix_2024}{margin_2024:.1f}%\n")
        f.write(f"* 2020 Margin: {margin_prefix_2020}{abs(margin_2020):.1f}%\n")
        f.write(f"* Shift from 2020: {shift_prefix}{abs(total_shift):.1f}%\n\n")

        # Shift Analysis
        f.write("## Shift Analysis\n\n")
        shift_prefix = "D+" if weighted_dem_shift > 0 else "R+"
        f.write(f"* Average Shift: {shift_prefix}{abs(weighted_dem_shift):.1f}%\n\n")

        # County Control
        f.write("## County Control\n\n")
        f.write(f"* Democratic Counties: {dem_counties_2024} of {total_counties} ")
        f.write(f"({dem_counties_2024/total_counties*100:.1f}%)\n")
        f.write(f"* Republican Counties: {rep_counties_2024} of {total_counties} ")
        f.write(f"({rep_counties_2024/total_counties*100:.1f}%)\n\n")

        # Most Significant County Shifts
        f.write("## Most Significant County Shifts\n\n")
        f.write("### Largest Democratic Shifts:\n")
        for _, row in dem_shifts.iterrows():
            f.write(f"* {row['name']}: D+{row['dem_shift']:.1f}%\n")

        f.write("\n### Largest Republican Shifts:\n")
        for i, (_, row) in enumerate(rep_shifts.iterrows()):
            f.write(f"* {row['name']}: R+{abs(row['dem_shift']):.1f}%")
            if i < len(rep_shifts) - 1:  # If not the last row
                f.write("\n")
        f.write("\n\n")

        # Population Centers
        f.write("## Largest Counties by Vote Total\n\n")
        for _, row in top_counties.iterrows():
            dem_pct = row[f"{dem_candidate_id}_pct"]
            rep_pct = row[f"{rep_candidate_id}_pct"]
            shift_prefix = "D+" if row["dem_shift"] > 0 else "R+"
            f.write(f"* {row['name']}: {row['total_votes']:,} votes ")
            f.write(f"(D: {dem_pct:.1f}%, R: {rep_pct:.1f}%, ")
            f.write(f"Shift: {shift_prefix}{abs(row['dem_shift']):.1f}%)\n")

        # Urban-Rural Analysis
        f.write("\n## Urban-Rural Analysis\n\n")
        f.write(
            f"* Urban County Average Shift: {'D+' if urban_shift > 0 else 'R+'}{abs(urban_shift):.1f}%\n"
        )
        f.write(
            f"* Rural County Average Shift: {'D+' if rural_shift > 0 else 'R+'}{abs(rural_shift):.1f}%\n"
        )
        f.write(f"* Urban-Rural Gap: {abs(urban_shift - rural_shift):.1f} points\n\n")

        # Competitive Races Analysis
        f.write("## Competitive Races Analysis\n\n")
        f.write(f"Counties decided by <5%: {len(close_races)} of {total_counties} ")
        f.write(f"({len(close_races)/total_counties*100:.1f}%)\n\n")
        f.write("### Most Competitive Counties:\n")
        for _, row in close_races.nsmallest(5, "margin_2024").iterrows():
            margin_prefix = (
                "D+"
                if row[f"{dem_candidate_id}_pct"] > row[f"{rep_candidate_id}_pct"]
                else "R+"
            )
            f.write(f"* {row['name']}: {margin_prefix}{row['margin_2024']:.1f}%\n")

        # Swing Analysis
        f.write("\n## Swing Analysis\n\n")
        f.write("### Counties with Largest Swings:\n")
        for _, row in biggest_swings.head().iterrows():
            shift_prefix = "D+" if row["dem_shift"] > 0 else "R+"
            f.write(f"* {row['name']}: {shift_prefix}{abs(row['dem_shift']):.1f}%\n")

    # Save DataFrame to CSV
    csv_path = os.path.join(state_dir, "results.csv")
    df.to_csv(csv_path, index=False)

    # Display analysis
    print(f"\nShift Analysis for {state_name}:")
    print("-" * 50)
    print(f"Average Democratic shift: {df['dem_shift'].mean():.2f}")
    print("\nLargest shifts toward Democrats:")
    print(df.nlargest(5, "dem_shift")[["name", "dem_shift"]])
    print("\nLargest shifts toward Republicans:")
    print(df.nsmallest(5, "dem_shift")[["name", "dem_shift"]])

    return df


def get_all_state_urls():
    """
    Generate URLs for all 50 states and DC.

    Returns:
        Dict[str, str]: Dictionary mapping state names to their NYT JSON URLs
    """
    base_url = "https://static01.nyt.com/elections-assets/pages/data/2024-11-05/results-{}-president.json"

    states = {
        "Alabama": "alabama",
        "Alaska": "alaska",
        "Arizona": "arizona",
        "Arkansas": "arkansas",
        "California": "california",
        "Colorado": "colorado",
        "Connecticut": "connecticut",
        "Delaware": "delaware",
        "District of Columbia": "washington-dc",
        "Florida": "florida",
        "Georgia": "georgia",
        "Hawaii": "hawaii",
        "Idaho": "idaho",
        "Illinois": "illinois",
        "Indiana": "indiana",
        "Iowa": "iowa",
        "Kansas": "kansas",
        "Kentucky": "kentucky",
        "Louisiana": "louisiana",
        "Maine": "maine",
        "Maryland": "maryland",
        "Massachusetts": "massachusetts",
        "Michigan": "michigan",
        "Minnesota": "minnesota",
        "Mississippi": "mississippi",
        "Missouri": "missouri",
        "Montana": "montana",
        "Nebraska": "nebraska",
        "Nevada": "nevada",
        "New Hampshire": "new-hampshire",
        "New Jersey": "new-jersey",
        "New Mexico": "new-mexico",
        "New York": "new-york",
        "North Carolina": "north-carolina",
        "North Dakota": "north-dakota",
        "Ohio": "ohio",
        "Oklahoma": "oklahoma",
        "Oregon": "oregon",
        "Pennsylvania": "pennsylvania",
        "Rhode Island": "rhode-island",
        "South Carolina": "south-carolina",
        "South Dakota": "south-dakota",
        "Tennessee": "tennessee",
        "Texas": "texas",
        "Utah": "utah",
        "Vermont": "vermont",
        "Virginia": "virginia",
        "Washington": "washington",
        "West Virginia": "west-virginia",
        "Wisconsin": "wisconsin",
        "Wyoming": "wyoming",
    }

    return {state: base_url.format(url_name) for state, url_name in states.items()}


def analyze_all_states(results_dir: str = "election_results") -> dict:
    """
    Analyze election data for all 50 states and DC.

    Args:
        results_dir (str): Base directory for saving results

    Returns:
        Dict[str, pd.DataFrame]: Dictionary mapping state names to their analysis DataFrames
    """
    state_urls = get_all_state_urls()
    results = {}

    total_states = len(state_urls)
    processed = 0

    for state_name, url in state_urls.items():
        processed += 1
        print(f"\nAnalyzing {state_name}... ({processed}/{total_states})")

        try:
            df = analyze_election_data(url, state_name, results_dir)
            results[state_name] = df
            print(f"✓ Analysis complete for {state_name}")
        except Exception as e:
            print(f"✗ Error analyzing {state_name}: {str(e)}")

    # Print summary
    successful = len(results)
    failed = total_states - successful
    print("\nAnalysis Complete")
    print("=" * 50)
    print(f"Total States Processed: {total_states}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if failed > 0:
        print("\nFailed States:")
        for state in state_urls.keys():
            if state not in results:
                print(f"- {state}")

    return results
