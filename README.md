# Quality Value Stock Screener - Streamlit Dashboard

A comprehensive web-based tool for finding undervalued, high-quality companies with strong fundamentals, ethical management, and sustainable competitive advantages.

## Features

- **Real-time Data**: Fetches live stock data using yfinance (Yahoo Finance)
- **Comprehensive Analysis**: 6 category scoring system
  - Valuation (P/E, P/B, DCF, Intrinsic Value)
  - Financial Health (Liquidity, Debt, Coverage Ratios)
  - Profitability (ROE, ROIC, Margins)
  - Growth (Earnings, Revenue)
  - Management Quality (Insider Ownership, Efficiency)
  - Ethics & Governance (ESG Scores)
- **Customizable Filters**: Adjust all screening criteria via sliders
- **Stock Comparison**: Compare up to 10 stocks side-by-side
- **Detailed Analysis**: Full investment thesis with charts and scenarios
- **Multiple Markets**: US, UK, EU, Global coverage
- **Dividend Screening**: Filter by dividend requirements

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Python Dependencies

Open your terminal/command prompt and run:

```bash
pip install -r requirements.txt
```

This will install:
- streamlit (Web dashboard framework)
- pandas (Data manipulation)
- numpy (Numerical computing)
- yfinance (Yahoo Finance data)
- plotly (Interactive charts)
- requests (HTTP library)

### Step 2: Verify Installation

```bash
streamlit --version
```

You should see the Streamlit version number.

## Usage

### Running the Dashboard

1. Open terminal/command prompt in the folder containing `stock_screener.py`

2. Run the app:
```bash
streamlit run stock_screener.py
```

3. Your web browser will automatically open to `http://localhost:8501`

4. If it doesn't open automatically, copy this URL into your browser

### Using the Dashboard

1. **Configure Settings** (Left Sidebar):
   - Optional: Add API keys for enhanced data (Alpha Vantage, FMP)
   - Select your market (US, UK, EU, Global)
   - Adjust screening criteria using sliders:
     - Valuation thresholds
     - Financial strength requirements
     - Profitability minimums
     - Growth expectations
     - Management quality
     - Ethical profile
     - Dividend preferences

2. **Run Screening**:
   - Click "🚀 Run Screening" button
   - Wait 1-2 minutes for analysis (fetches real-time data)
   - View results ranked by quality score

3. **Analyze Results**:
   - Browse the results table with all key metrics
   - Click on any stock for detailed analysis
   - Add stocks to comparison list
   - Export results to CSV

4. **Compare Stocks**:
   - Select multiple stocks from results
   - View side-by-side comparison
   - See radar chart of category scores

5. **View Details**:
   - Select a stock from the dropdown
   - See comprehensive analysis including:
     - Category scores and grades
     - Valuation scenarios (Bull/Base/Bear)
     - Financial health breakdown
     - Profitability metrics
     - Growth analysis
     - Historical price charts
     - Investment thesis and risks
     - Links to external research

## Data Sources

### Primary (No API Key Required)
- **Yahoo Finance**: Real-time quotes, fundamentals, historical data
- Access via yfinance library

### Optional (Free Tier Available)
- **Alpha Vantage**: Enhanced fundamental data
  - Get free key: https://www.alphavantage.co/support/#api-key
  - 500 calls/day free tier
  
- **Financial Modeling Prep (FMP)**: Additional ratios and screening
  - Get free key: https://site.financialmodelingprep.com/developer/docs/
  - 250 calls/day free tier

## Understanding the Scores

### Overall Score (0-100)
Weighted composite of all category scores:
- 90-100: Excellent (A grade)
- 80-89: Good (B grade)
- 70-79: Fair (C grade)
- Below 70: Poor (D grade)

### Category Scores

1. **Valuation Score** (25% weight)
   - P/E, P/B, P/S ratios
   - Discount to intrinsic value
   - PEG ratio

2. **Financial Health Score** (20% weight)
   - Current & quick ratios
   - Debt-to-equity
   - Interest coverage

3. **Profitability Score** (20% weight)
   - ROE, ROIC, ROA
   - Operating & net margins

4. **Growth Score** (15% weight)
   - Earnings & revenue growth
   - Quarterly momentum

5. **Management Score** (10% weight)
   - Insider ownership
   - Institutional ownership
   - Management efficiency

6. **Ethics Score** (10% weight)
   - ESG scores
   - Governance quality
   - Controversy checks

## Screening Workflow

1. **Stock Universe**: Fetches list of stocks from selected market
2. **Data Collection**: Downloads real-time data for each stock
3. **Filter Application**: Applies your custom criteria
4. **Score Calculation**: Computes 6 category scores + overall
5. **Ranking**: Sorts by overall quality score
6. **Results Display**: Shows top-scoring stocks

## Tips for Best Results

### Finding Undervalued Quality Stocks
- Set max P/E around 20-25
- Require minimum 15% discount to intrinsic value
- Look for ROE above 15%
- Ensure current ratio above 1.5
- Focus on consistent growth (5-10% minimum)

### Conservative Screening
- Tighter debt requirements (max D/E of 0.5)
- Higher interest coverage (10x+)
- Stronger profitability (ROE 20%+)
- Conservative ethical profile

### Growth Focus
- Lower P/E requirements (up to 30-35)
- Higher growth minimums (15%+)
- Accept higher valuations for quality growth
- Look at PEG ratio under 2

### Dividend Income
- Set dividend requirement to "Must Pay"
- Minimum yield 2-4%
- Check payout ratio under 70%
- Look for dividend growth history

## Troubleshooting

### "No stocks found matching criteria"
- Your filters may be too strict
- Try relaxing one criterion at a time
- Start with default settings and adjust gradually

### "Error fetching data for [SYMBOL]"
- Stock may be delisted or ticker changed
- Data temporarily unavailable from Yahoo Finance
- Try again in a few minutes

### Slow Performance
- Analyzing 100+ stocks takes time
- Each stock requires multiple API calls
- Be patient during screening (1-2 minutes is normal)
- Consider screening smaller lists for faster results

### Missing Historical Data
- Some stocks may not have full history
- Recently IPO'd companies have limited data
- International stocks may have gaps

## Limitations

1. **Data Accuracy**: 
   - Free data sources may have delays
   - Always verify critical data before investing

2. **Coverage**:
   - Best coverage for US stocks
   - International data may be limited

3. **Rate Limits**:
   - Yahoo Finance has informal limits
   - Too many requests too fast may be blocked temporarily

4. **Calculations**:
   - Intrinsic value is estimated (multiple methods exist)
   - Scores are relative, not absolute

## Legal Disclaimer

**This tool is for educational and research purposes only.**

- Not financial advice
- Do your own due diligence
- Past performance doesn't guarantee future results
- Consult a financial advisor before investing
- No warranties or guarantees provided

## Support & Updates

For issues or questions:
1. Check this README
2. Verify all dependencies are installed
3. Ensure you have internet connection for data fetching
4. Try running with default settings first

## Version

Current Version: 1.0.0
Last Updated: February 2026

## License

This tool is provided as-is for personal use.
