# 2024 Election Analysis Tool

A comprehensive Python tool for analyzing and visualizing U.S. election data, comparing 2020 and 2024 results at county and township levels.

## Overview

This tool fetches, processes, and analyzes election data from the New York Times election endpoints, creating detailed visualizations and analyses of voting patterns, shifts, and demographic trends. It supports analysis of all 50 U.S. states and the District of Columbia. Some states have partial data available, and some may not work as NYT endpoints are updated/ deleted.

## Features

- **Data Collection**
  - Automated fetching from NYT election data endpoints
  - Support for both county and township-level data
  - Historical comparison with 2020 election results

- **Analysis Capabilities**
  - Vote share calculations and comparisons
  - Democratic/Republican shift analysis
  - Urban vs. Rural voting pattern analysis
  - County-size categorization
  - Demographic trend identification

- **Visualizations**
  - FiveThirtyEight-style shift visualizations
  - County-level vote share shifts
  - Size-based boxplots
  - Additional geographic visualizations (where applicable)

- **Output Formats**
  - Detailed Markdown analysis reports
  - CSV data exports
  - High-resolution visualizations
  - Comprehensive state-by-state summaries

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/cbrane/election-analysis-tool.git
   cd election-analysis-tool
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```python
from electionthings import analyze_election_data

# Analyze a single state
url = "https://static01.nyt.com/elections-assets/pages/data/2024-11-05/results-new-york-president.json"
df = analyze_election_data(url, "New York")
```

### Analyzing All States

```python
from electionthings import analyze_all_states

# Analyze all states
results = analyze_all_states()
```

## Directory Structure

The tool creates the following directory structure for results:
```
election_results/
├── state_name/
│   ├── analysis.md        # Detailed analysis report
│   ├── results.csv        # Raw data and calculations
│   ├── county_shifts.png  # Visualization of county-level shifts
│   └── shifts_by_size.png # Analysis by county size
```

## Analysis Output Details

### Analysis Report (analysis.md)
Each state's analysis includes:
- Overall vote totals and turnout comparison
- Vote share analysis between elections
- Detailed shift analysis at county level
- Urban vs. Rural voting patterns
- Most competitive counties
- Largest demographic shifts
- County control statistics

### Data Export (results.csv)
Contains detailed county-level data including:
- Raw vote totals
- Vote share percentages
- Historical comparisons
- Demographic categorizations
- Calculated shifts and trends

## Required Dependencies

- Python 3.7+
- pandas
- matplotlib
- requests
- numpy
- typing-extensions

## Data Sources

This tool relies on election data from the New York Times API. Please note:
- Data availability may vary by state
- Historical comparisons require 2020 data
- Some regions may only have partial data available
- Township-level data is included where available

## Limitations

- Requires active internet connection for data fetching
- Analysis depends on NYT API availability
- Historical comparisons may not be available for all locations
- Some visualizations require minimum data thresholds

## Future Enhancements

Planned features include:
- Interactive visualization options
- Additional demographic analysis capabilities
- Enhanced geographic visualizations
- Data caching and rate limiting
- Support for additional historical elections
- Custom analysis parameters

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

Please ensure your code follows the project's style guidelines and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- New York Times for election data access
- FiveThirtyEight for visualization inspiration
- Contributors and maintainers

## Support

For support, please:
- Open an issue in the GitHub repository
- Check existing documentation
- Review closed issues for similar problems

## Author

Connor Raney
connor@connorraney.com

---

**Note**: This project is under active development. Features and capabilities may change.