"""
Quality Value Stock Screener - Streamlit Dashboard
A comprehensive tool for finding undervalued, high-quality companies with strong fundamentals,
ethical management, and sustainable competitive advantages.

Run with: streamlit run stock_screener.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import requests
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import time
import json

# Page configuration
st.set_page_config(
    page_title="Quality Value Stock Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1e3c72;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7f8c8d;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .score-excellent {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .score-good {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .score-fair {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .score-poor {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.75rem;
        border-radius: 8px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(30, 60, 114, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# API DATA FETCHERS
# ============================================================================

class StockDataFetcher:
    """Handles fetching stock data from multiple sources"""
    
    def __init__(self, alpha_key: str = None, fmp_key: str = None):
        self.alpha_key = alpha_key
        self.fmp_key = fmp_key
        self.cache = {}
        self.cache_duration = 3600  # 1 hour cache
        
    def get_stock_list(self, market: str = "us") -> List[str]:
        """Get list of stock symbols based on market"""
        try:
            if market == "us":
                # Get S&P 500 stocks as a starting point
                url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
                tables = pd.read_html(url)
                symbols = tables[0]['Symbol'].tolist()
                return [s.replace('.', '-') for s in symbols[:100]]  # Limit to 100 for demo
            else:
                # For other markets, return a smaller sample
                return ['MSFT', 'AAPL', 'JNJ', 'V', 'PG', 'KO', 'WMT', 'JPM', 'BAC', 'DIS']
        except Exception as e:
            st.warning(f"Could not fetch stock list: {e}. Using default symbols.")
            return ['MSFT', 'AAPL', 'JNJ', 'V', 'PG', 'KO', 'WMT', 'JPM', 'BAC', 'DIS']
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Fetch comprehensive stock data using yfinance"""
        try:
            # Check cache
            cache_key = f"{symbol}_{datetime.now().hour}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get financial data
            balance_sheet = ticker.balance_sheet
            income_stmt = ticker.income_stmt
            cash_flow = ticker.cashflow
            
            # Extract key metrics with error handling
            data = {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                'market_cap': info.get('marketCap', 0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                
                # Valuation metrics
                'pe_ratio': info.get('trailingPE', info.get('forwardPE', 0)),
                'pb_ratio': info.get('priceToBook', 0),
                'ps_ratio': info.get('priceToSalesTrailing12Months', 0),
                'peg_ratio': info.get('pegRatio', 0),
                
                # Profitability metrics
                'roe': info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0,
                'roa': info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0,
                'profit_margin': info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0,
                'operating_margin': info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0,
                'gross_margin': info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0,
                
                # Financial health
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'interest_coverage': self._calculate_interest_coverage(income_stmt),
                
                # Growth metrics
                'revenue_growth': info.get('revenueGrowth', 0) * 100 if info.get('revenueGrowth') else 0,
                'earnings_growth': info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0,
                'earnings_quarterly_growth': info.get('earningsQuarterlyGrowth', 0) * 100 if info.get('earningsQuarterlyGrowth') else 0,
                
                # Dividend metrics
                'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'payout_ratio': info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0,
                'dividend_rate': info.get('dividendRate', 0),
                'five_year_avg_dividend_yield': info.get('fiveYearAvgDividendYield', 0),
                
                # Management metrics
                'insider_ownership': info.get('heldPercentInsiders', 0) * 100 if info.get('heldPercentInsiders') else 0,
                'institutional_ownership': info.get('heldPercentInstitutions', 0) * 100 if info.get('heldPercentInstitutions') else 0,
                
                # Additional data
                'beta': info.get('beta', 1.0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'avg_volume': info.get('averageVolume', 0),
                
                # ESG scores (if available)
                'esg_score': info.get('esgScores', {}).get('totalEsg', 50) if info.get('esgScores') else 50,
                'governance_score': info.get('esgScores', {}).get('governanceScore', 50) if info.get('esgScores') else 50,
            }
            
            # Calculate additional metrics
            data['roic'] = self._calculate_roic(data, balance_sheet, income_stmt)
            data['free_cash_flow'] = self._get_free_cash_flow(cash_flow)
            data['intrinsic_value'] = self._calculate_intrinsic_value(data, cash_flow)
            
            # Cache the result
            self.cache[cache_key] = data
            return data
            
        except Exception as e:
            st.warning(f"Error fetching data for {symbol}: {e}")
            return None
    
    def _calculate_interest_coverage(self, income_stmt) -> float:
        """Calculate interest coverage ratio"""
        try:
            if income_stmt is None or income_stmt.empty:
                return 0
            ebit = income_stmt.loc['EBIT'].iloc[0] if 'EBIT' in income_stmt.index else 0
            interest = income_stmt.loc['Interest Expense'].iloc[0] if 'Interest Expense' in income_stmt.index else 1
            return abs(ebit / interest) if interest != 0 else 0
        except:
            return 0
    
    def _calculate_roic(self, data: Dict, balance_sheet, income_stmt) -> float:
        """Calculate Return on Invested Capital"""
        try:
            if income_stmt is None or income_stmt.empty or balance_sheet is None or balance_sheet.empty:
                return data.get('roe', 0) * 0.8  # Estimate from ROE
            
            nopat = income_stmt.loc['Net Income'].iloc[0] if 'Net Income' in income_stmt.index else 0
            total_assets = balance_sheet.loc['Total Assets'].iloc[0] if 'Total Assets' in balance_sheet.index else 1
            current_liab = balance_sheet.loc['Current Liabilities'].iloc[0] if 'Current Liabilities' in balance_sheet.index else 0
            
            invested_capital = total_assets - current_liab
            roic = (nopat / invested_capital * 100) if invested_capital > 0 else 0
            return roic
        except:
            return data.get('roe', 0) * 0.8
    
    def _get_free_cash_flow(self, cash_flow) -> float:
        """Get free cash flow"""
        try:
            if cash_flow is None or cash_flow.empty:
                return 0
            fcf = cash_flow.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cash_flow.index else 0
            return fcf
        except:
            return 0
    
    def _calculate_intrinsic_value(self, data: Dict, cash_flow) -> float:
        """Simple DCF-based intrinsic value calculation"""
        try:
            fcf = self._get_free_cash_flow(cash_flow)
            if fcf <= 0:
                # Use earnings-based valuation as fallback
                eps = data['price'] / data['pe_ratio'] if data['pe_ratio'] > 0 else 0
                growth_rate = min(data['earnings_growth'] / 100, 0.15)
                return eps * (1 + growth_rate) * 15  # Simple PE-based valuation
            
            growth_rate = min(data['earnings_growth'] / 100, 0.15)
            discount_rate = 0.10
            terminal_growth = 0.03
            projection_years = 5
            
            # Project future cash flows
            pv_fcf = 0
            for year in range(1, projection_years + 1):
                future_fcf = fcf * ((1 + growth_rate) ** year)
                pv_fcf += future_fcf / ((1 + discount_rate) ** year)
            
            # Terminal value
            terminal_fcf = fcf * ((1 + growth_rate) ** projection_years) * (1 + terminal_growth)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth)
            pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
            
            enterprise_value = pv_fcf + pv_terminal
            shares_outstanding = data['market_cap'] / data['price'] if data['price'] > 0 else 1
            intrinsic_value = enterprise_value / shares_outstanding if shares_outstanding > 0 else data['price']
            
            return max(intrinsic_value, data['price'] * 0.5)  # Floor at 50% of current price
            
        except:
            return data['price']
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Get historical price data"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except:
            return pd.DataFrame()


# ============================================================================
# SCORING ENGINE
# ============================================================================

class StockScorer:
    """Calculate comprehensive quality scores for stocks"""
    
    @staticmethod
    def calculate_valuation_score(data: Dict) -> Tuple[float, Dict]:
        """Score based on valuation metrics"""
        score = 0
        details = {}
        
        # P/E Ratio (20 points)
        pe = data.get('pe_ratio', 0)
        if 0 < pe <= 15:
            score += 20
            details['pe'] = 'Excellent'
        elif 15 < pe <= 20:
            score += 15
            details['pe'] = 'Good'
        elif 20 < pe <= 25:
            score += 10
            details['pe'] = 'Fair'
        elif pe > 25:
            score += 5
            details['pe'] = 'High'
        
        # P/B Ratio (15 points)
        pb = data.get('pb_ratio', 0)
        if 0 < pb <= 1.5:
            score += 15
            details['pb'] = 'Excellent'
        elif 1.5 < pb <= 3:
            score += 12
            details['pb'] = 'Good'
        elif 3 < pb <= 5:
            score += 8
            details['pb'] = 'Fair'
        else:
            score += 4
            details['pb'] = 'High'
        
        # P/S Ratio (15 points)
        ps = data.get('ps_ratio', 0)
        if 0 < ps <= 1:
            score += 15
            details['ps'] = 'Excellent'
        elif 1 < ps <= 2:
            score += 12
            details['ps'] = 'Good'
        elif 2 < ps <= 3:
            score += 8
            details['ps'] = 'Fair'
        else:
            score += 4
            details['ps'] = 'High'
        
        # Intrinsic Value vs Price (30 points)
        price = data.get('price', 0)
        intrinsic = data.get('intrinsic_value', 0)
        if price > 0 and intrinsic > 0:
            discount = (intrinsic - price) / intrinsic
            if discount >= 0.30:
                score += 30
                details['valuation'] = f'Undervalued by {discount*100:.1f}%'
            elif discount >= 0.15:
                score += 20
                details['valuation'] = f'Undervalued by {discount*100:.1f}%'
            elif discount >= 0:
                score += 10
                details['valuation'] = 'Fair value'
            else:
                score += 5
                details['valuation'] = f'Overvalued by {abs(discount)*100:.1f}%'
        
        # PEG Ratio (20 points)
        peg = data.get('peg_ratio', 0)
        if 0 < peg <= 1:
            score += 20
            details['peg'] = 'Excellent growth value'
        elif 1 < peg <= 1.5:
            score += 15
            details['peg'] = 'Good growth value'
        elif 1.5 < peg <= 2:
            score += 10
            details['peg'] = 'Fair growth value'
        else:
            score += 5
            details['peg'] = 'Expensive growth'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_financial_score(data: Dict) -> Tuple[float, Dict]:
        """Score based on financial health"""
        score = 0
        details = {}
        
        # Current Ratio (25 points)
        current_ratio = data.get('current_ratio', 0)
        if current_ratio >= 2:
            score += 25
            details['liquidity'] = 'Excellent'
        elif current_ratio >= 1.5:
            score += 20
            details['liquidity'] = 'Good'
        elif current_ratio >= 1:
            score += 15
            details['liquidity'] = 'Adequate'
        else:
            score += 5
            details['liquidity'] = 'Weak'
        
        # Quick Ratio (20 points)
        quick_ratio = data.get('quick_ratio', 0)
        if quick_ratio >= 1.5:
            score += 20
            details['quick_liquidity'] = 'Strong'
        elif quick_ratio >= 1:
            score += 15
            details['quick_liquidity'] = 'Good'
        elif quick_ratio >= 0.5:
            score += 10
            details['quick_liquidity'] = 'Fair'
        else:
            score += 5
            details['quick_liquidity'] = 'Weak'
        
        # Debt-to-Equity (30 points)
        de = data.get('debt_to_equity', 0)
        if de <= 0.5:
            score += 30
            details['leverage'] = 'Conservative'
        elif de <= 1:
            score += 25
            details['leverage'] = 'Moderate'
        elif de <= 2:
            score += 15
            details['leverage'] = 'Elevated'
        else:
            score += 5
            details['leverage'] = 'High risk'
        
        # Interest Coverage (25 points)
        coverage = data.get('interest_coverage', 0)
        if coverage >= 10:
            score += 25
            details['interest_coverage'] = 'Excellent'
        elif coverage >= 5:
            score += 20
            details['interest_coverage'] = 'Good'
        elif coverage >= 2:
            score += 10
            details['interest_coverage'] = 'Adequate'
        else:
            score += 5
            details['interest_coverage'] = 'Weak'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_profitability_score(data: Dict) -> Tuple[float, Dict]:
        """Score based on profitability metrics"""
        score = 0
        details = {}
        
        # ROE (25 points)
        roe = data.get('roe', 0)
        if roe >= 20:
            score += 25
            details['roe'] = 'Excellent'
        elif roe >= 15:
            score += 20
            details['roe'] = 'Good'
        elif roe >= 10:
            score += 15
            details['roe'] = 'Fair'
        else:
            score += 5
            details['roe'] = 'Weak'
        
        # ROIC (25 points)
        roic = data.get('roic', 0)
        if roic >= 15:
            score += 25
            details['roic'] = 'Excellent'
        elif roic >= 12:
            score += 20
            details['roic'] = 'Good'
        elif roic >= 8:
            score += 15
            details['roic'] = 'Fair'
        else:
            score += 5
            details['roic'] = 'Weak'
        
        # Operating Margin (25 points)
        op_margin = data.get('operating_margin', 0)
        if op_margin >= 20:
            score += 25
            details['op_margin'] = 'Excellent'
        elif op_margin >= 15:
            score += 20
            details['op_margin'] = 'Good'
        elif op_margin >= 10:
            score += 15
            details['op_margin'] = 'Fair'
        else:
            score += 5
            details['op_margin'] = 'Weak'
        
        # Net Margin (25 points)
        net_margin = data.get('profit_margin', 0)
        if net_margin >= 15:
            score += 25
            details['net_margin'] = 'Excellent'
        elif net_margin >= 10:
            score += 20
            details['net_margin'] = 'Good'
        elif net_margin >= 5:
            score += 15
            details['net_margin'] = 'Fair'
        else:
            score += 5
            details['net_margin'] = 'Weak'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_growth_score(data: Dict) -> Tuple[float, Dict]:
        """Score based on growth metrics"""
        score = 0
        details = {}
        
        # Earnings Growth (40 points)
        earnings_growth = data.get('earnings_growth', 0)
        if earnings_growth >= 15:
            score += 40
            details['earnings_growth'] = 'Excellent'
        elif earnings_growth >= 10:
            score += 30
            details['earnings_growth'] = 'Good'
        elif earnings_growth >= 5:
            score += 20
            details['earnings_growth'] = 'Moderate'
        elif earnings_growth >= 0:
            score += 10
            details['earnings_growth'] = 'Slow'
        else:
            score += 5
            details['earnings_growth'] = 'Declining'
        
        # Revenue Growth (40 points)
        revenue_growth = data.get('revenue_growth', 0)
        if revenue_growth >= 15:
            score += 40
            details['revenue_growth'] = 'Excellent'
        elif revenue_growth >= 10:
            score += 30
            details['revenue_growth'] = 'Good'
        elif revenue_growth >= 5:
            score += 20
            details['revenue_growth'] = 'Moderate'
        elif revenue_growth >= 0:
            score += 10
            details['revenue_growth'] = 'Slow'
        else:
            score += 5
            details['revenue_growth'] = 'Declining'
        
        # Quarterly Growth (20 points)
        q_growth = data.get('earnings_quarterly_growth', 0)
        if q_growth >= 15:
            score += 20
            details['quarterly_momentum'] = 'Strong'
        elif q_growth >= 5:
            score += 15
            details['quarterly_momentum'] = 'Positive'
        elif q_growth >= 0:
            score += 10
            details['quarterly_momentum'] = 'Stable'
        else:
            score += 5
            details['quarterly_momentum'] = 'Weak'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_management_score(data: Dict) -> Tuple[float, Dict]:
        """Score based on management quality"""
        score = 0
        details = {}
        
        # Insider Ownership (40 points)
        insider = data.get('insider_ownership', 0)
        if insider >= 10:
            score += 40
            details['insider_alignment'] = 'Excellent'
        elif insider >= 5:
            score += 30
            details['insider_alignment'] = 'Good'
        elif insider >= 2:
            score += 20
            details['insider_alignment'] = 'Moderate'
        else:
            score += 10
            details['insider_alignment'] = 'Low'
        
        # Institutional Ownership (30 points)
        institutional = data.get('institutional_ownership', 0)
        if 40 <= institutional <= 80:
            score += 30
            details['institutional'] = 'Optimal range'
        elif 20 <= institutional <= 90:
            score += 20
            details['institutional'] = 'Good'
        else:
            score += 10
            details['institutional'] = 'Suboptimal'
        
        # ROE as proxy for management efficiency (30 points)
        roe = data.get('roe', 0)
        if roe >= 20:
            score += 30
            details['efficiency'] = 'Excellent'
        elif roe >= 15:
            score += 20
            details['efficiency'] = 'Good'
        else:
            score += 10
            details['efficiency'] = 'Fair'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_ethics_score(data: Dict, ethical_profile: str) -> Tuple[float, Dict]:
        """Score based on ethics and governance"""
        score = 50  # Base score
        details = {}
        
        # ESG Score (50 points)
        esg = data.get('esg_score', 50)
        if esg >= 70:
            score += 50
            details['esg'] = 'Leader'
        elif esg >= 50:
            score += 35
            details['esg'] = 'Average'
        elif esg >= 30:
            score += 20
            details['esg'] = 'Below average'
        else:
            score += 10
            details['esg'] = 'Laggard'
        
        # Governance Score (30 points)
        gov = data.get('governance_score', 50)
        if gov >= 70:
            score += 30
            details['governance'] = 'Strong'
        elif gov >= 50:
            score += 20
            details['governance'] = 'Adequate'
        else:
            score += 10
            details['governance'] = 'Weak'
        
        # Adjust based on ethical profile
        if ethical_profile == 'conservative':
            score *= 0.9  # Stricter standards
        elif ethical_profile == 'flexible':
            score *= 1.1  # More lenient
        
        # Controversy check (simulated - would need real API)
        details['controversy'] = 'Low risk'
        
        return min(score, 100), details
    
    @staticmethod
    def calculate_overall_score(scores: Dict) -> float:
        """Calculate weighted overall score"""
        weights = {
            'valuation': 0.25,
            'financial': 0.20,
            'profitability': 0.20,
            'growth': 0.15,
            'management': 0.10,
            'ethics': 0.10
        }
        
        overall = sum(scores[key] * weights[key] for key in weights)
        return round(overall, 1)


# ============================================================================
# STREAMLIT UI
# ============================================================================

def main():
    # Header
    st.markdown('<div class="main-header">🎯 Quality Value Stock Screener</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Discover undervalued, high-quality companies with strong fundamentals and ethical management</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'comparison_list' not in st.session_state:
        st.session_state.comparison_list = []
    if 'fetcher' not in st.session_state:
        st.session_state.fetcher = StockDataFetcher()
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Keys (collapsible)
        with st.expander("🔑 API Keys (Optional)", expanded=False):
            st.info("Free tier available:\n- Alpha Vantage: alphavantage.co\n- FMP: financialmodelingprep.com")
            alpha_key = st.text_input("Alpha Vantage API Key", type="password", help="Optional - provides additional fundamental data")
            fmp_key = st.text_input("FMP API Key", type="password", help="Optional - provides additional screening data")
            
            if alpha_key or fmp_key:
                st.session_state.fetcher = StockDataFetcher(alpha_key, fmp_key)
                st.success("API keys configured!")
        
        st.divider()
        
        # Market Selection
        st.subheader("🌍 Market Selection")
        market = st.selectbox(
            "Primary Market",
            ["us", "uk", "eu", "global"],
            format_func=lambda x: {
                "us": "🇺🇸 United States",
                "uk": "🇬🇧 United Kingdom",
                "eu": "🇪🇺 European Union",
                "global": "🌍 Global Markets"
            }[x]
        )
        
        include_emerging = st.checkbox("Include Emerging Markets", value=False)
        
        st.divider()
        
        # Screening Criteria
        st.subheader("📊 Valuation Criteria")
        max_pe = st.slider("Maximum P/E Ratio", 5, 50, 25)
        max_pb = st.slider("Maximum P/B Ratio", 0.5, 5.0, 3.0, 0.1)
        min_discount = st.slider("Minimum Discount to Intrinsic Value (%)", 0, 50, 15)
        
        st.divider()
        
        st.subheader("💪 Financial Strength")
        min_current_ratio = st.slider("Minimum Current Ratio", 1.0, 3.0, 1.5, 0.1)
        max_debt_equity = st.slider("Maximum Debt-to-Equity", 0.0, 3.0, 1.0, 0.1)
        min_interest_cov = st.slider("Minimum Interest Coverage", 2, 20, 5)
        
        st.divider()
        
        st.subheader("📈 Profitability")
        min_roe = st.slider("Minimum ROE (%)", 5, 40, 15)
        min_roic = st.slider("Minimum ROIC (%)", 5, 35, 12)
        min_op_margin = st.slider("Minimum Operating Margin (%)", 0, 40, 10)
        
        st.divider()
        
        st.subheader("🚀 Growth")
        min_earnings_growth = st.slider("Minimum Earnings Growth (%)", -10, 30, 5)
        min_revenue_growth = st.slider("Minimum Revenue Growth (%)", -10, 25, 3)
        
        st.divider()
        
        st.subheader("🌟 Ethics & Governance")
        ethical_profile = st.selectbox(
            "Ethical Profile",
            ["moderate", "conservative", "flexible"],
            format_func=lambda x: {
                "moderate": "⚖️ Moderate (Recommended)",
                "conservative": "🛡️ Conservative",
                "flexible": "🎯 Flexible"
            }[x]
        )
        
        st.divider()
        
        st.subheader("💰 Dividend Preferences")
        dividend_req = st.selectbox(
            "Dividend Requirement",
            ["any", "paying", "growing"],
            format_func=lambda x: {
                "any": "No Requirement",
                "paying": "Must Pay Dividends",
                "growing": "Must Have Dividend Growth"
            }[x]
        )
        
        if dividend_req != "any":
            min_div_yield = st.slider("Minimum Dividend Yield (%)", 0.0, 8.0, 1.0, 0.1)
        else:
            min_div_yield = 0
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Screening", "📊 Results", "🔄 Comparison", "📈 Stock Details"])
    
    with tab1:
        st.header("Run Stock Screening")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Market", market.upper())
        with col2:
            st.metric("Max P/E", max_pe)
        with col3:
            st.metric("Min ROE", f"{min_roe}%")
        
        st.info("""
        **How it works:**
        1. We'll fetch real-time data for top stocks in your selected market
        2. Apply your custom screening criteria
        3. Calculate comprehensive quality scores across 6 categories
        4. Rank stocks by overall quality score
        
        Note: This may take 1-2 minutes depending on the number of stocks analyzed.
        """)
        
        if st.button("🚀 Run Screening", type="primary"):
            run_screening(
                st.session_state.fetcher,
                market,
                {
                    'max_pe': max_pe,
                    'max_pb': max_pb,
                    'min_discount': min_discount,
                    'min_current_ratio': min_current_ratio,
                    'max_debt_equity': max_debt_equity,
                    'min_interest_cov': min_interest_cov,
                    'min_roe': min_roe,
                    'min_roic': min_roic,
                    'min_op_margin': min_op_margin,
                    'min_earnings_growth': min_earnings_growth,
                    'min_revenue_growth': min_revenue_growth,
                    'ethical_profile': ethical_profile,
                    'dividend_req': dividend_req,
                    'min_div_yield': min_div_yield
                }
            )
    
    with tab2:
        if st.session_state.results is not None:
            display_results(st.session_state.results)
        else:
            st.info("Run a screening to see results here.")
    
    with tab3:
        if len(st.session_state.comparison_list) > 0:
            display_comparison(st.session_state.comparison_list)
        else:
            st.info("Select stocks from the Results tab to compare them here.")
    
    with tab4:
        if st.session_state.results is not None:
            display_stock_details(st.session_state.results, st.session_state.fetcher)
        else:
            st.info("Run a screening first to view detailed stock analysis.")


def run_screening(fetcher: StockDataFetcher, market: str, criteria: Dict):
    """Execute the stock screening process"""
    
    with st.spinner("🔍 Fetching stock list..."):
        symbols = fetcher.get_stock_list(market)
        st.info(f"Analyzing {len(symbols)} stocks...")
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(symbols):
        status_text.text(f"Analyzing {symbol}... ({i+1}/{len(symbols)})")
        progress_bar.progress((i + 1) / len(symbols))
        
        # Fetch data
        data = fetcher.get_stock_data(symbol)
        if data is None:
            continue
        
        # Apply filters
        if not passes_filters(data, criteria):
            continue
        
        # Calculate scores
        scorer = StockScorer()
        valuation_score, val_details = scorer.calculate_valuation_score(data)
        financial_score, fin_details = scorer.calculate_financial_score(data)
        profit_score, prof_details = scorer.calculate_profitability_score(data)
        growth_score, growth_details = scorer.calculate_growth_score(data)
        mgmt_score, mgmt_details = scorer.calculate_management_score(data)
        ethics_score, eth_details = scorer.calculate_ethics_score(data, criteria['ethical_profile'])
        
        scores = {
            'valuation': valuation_score,
            'financial': financial_score,
            'profitability': profit_score,
            'growth': growth_score,
            'management': mgmt_score,
            'ethics': ethics_score
        }
        
        overall_score = scorer.calculate_overall_score(scores)
        
        # Store result
        result = {
            **data,
            'overall_score': overall_score,
            'valuation_score': valuation_score,
            'financial_score': financial_score,
            'profitability_score': profit_score,
            'growth_score': growth_score,
            'management_score': mgmt_score,
            'ethics_score': ethics_score,
            'score_details': {
                'valuation': val_details,
                'financial': fin_details,
                'profitability': prof_details,
                'growth': growth_details,
                'management': mgmt_details,
                'ethics': eth_details
            }
        }
        
        results.append(result)
        
        # Rate limiting
        time.sleep(0.1)
    
    progress_bar.empty()
    status_text.empty()
    
    if len(results) > 0:
        # Sort by overall score
        results.sort(key=lambda x: x['overall_score'], reverse=True)
        st.session_state.results = results
        st.success(f"✅ Found {len(results)} high-quality stocks matching your criteria!")
        st.balloons()
    else:
        st.warning("No stocks found matching your criteria. Try adjusting the filters.")


def passes_filters(data: Dict, criteria: Dict) -> bool:
    """Check if stock passes all screening criteria"""
    
    # Valuation filters
    if data.get('pe_ratio', 0) > criteria['max_pe'] and data.get('pe_ratio', 0) > 0:
        return False
    if data.get('pb_ratio', 0) > criteria['max_pb'] and data.get('pb_ratio', 0) > 0:
        return False
    
    # Discount to intrinsic value
    price = data.get('price', 0)
    intrinsic = data.get('intrinsic_value', 0)
    if price > 0 and intrinsic > 0:
        discount = (intrinsic - price) / intrinsic * 100
        if discount < criteria['min_discount']:
            return False
    
    # Financial health
    if data.get('current_ratio', 0) < criteria['min_current_ratio']:
        return False
    if data.get('debt_to_equity', 999) > criteria['max_debt_equity']:
        return False
    if data.get('interest_coverage', 0) < criteria['min_interest_cov']:
        return False
    
    # Profitability
    if data.get('roe', 0) < criteria['min_roe']:
        return False
    if data.get('roic', 0) < criteria['min_roic']:
        return False
    if data.get('operating_margin', 0) < criteria['min_op_margin']:
        return False
    
    # Growth
    if data.get('earnings_growth', -999) < criteria['min_earnings_growth']:
        return False
    if data.get('revenue_growth', -999) < criteria['min_revenue_growth']:
        return False
    
    # Dividend
    if criteria['dividend_req'] == 'paying':
        if data.get('dividend_yield', 0) < criteria['min_div_yield']:
            return False
    elif criteria['dividend_req'] == 'growing':
        if data.get('dividend_yield', 0) < criteria['min_div_yield']:
            return False
        if data.get('five_year_avg_dividend_yield', 0) == 0:
            return False
    
    return True


def display_results(results: List[Dict]):
    """Display screening results in a nice table"""
    
    st.header(f"📊 Screening Results ({len(results)} stocks)")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_score = np.mean([r['overall_score'] for r in results])
        st.metric("Average Quality Score", f"{avg_score:.1f}")
    with col2:
        excellent = len([r for r in results if r['overall_score'] >= 80])
        st.metric("Excellent Stocks (80+)", excellent)
    with col3:
        avg_pe = np.mean([r['pe_ratio'] for r in results if r['pe_ratio'] > 0])
        st.metric("Average P/E", f"{avg_pe:.1f}")
    with col4:
        avg_div = np.mean([r['dividend_yield'] for r in results if r['dividend_yield'] > 0])
        st.metric("Average Div Yield", f"{avg_div:.2f}%")
    
    st.divider()
    
    # Create DataFrame for display
    df_display = pd.DataFrame([
        {
            'Symbol': r['symbol'],
            'Company': r['name'][:30] + '...' if len(r['name']) > 30 else r['name'],
            'Overall': r['overall_score'],
            'Valuation': r['valuation_score'],
            'Financial': r['financial_score'],
            'Profit': r['profitability_score'],
            'Growth': r['growth_score'],
            'Mgmt': r['management_score'],
            'Ethics': r['ethics_score'],
            'Price': f"${r['price']:.2f}",
            'P/E': f"{r['pe_ratio']:.1f}" if r['pe_ratio'] > 0 else 'N/A',
            'Div Yield': f"{r['dividend_yield']:.2f}%" if r['dividend_yield'] > 0 else 'N/A',
            'Market Cap': f"${r['market_cap']/1e9:.1f}B" if r['market_cap'] > 0 else 'N/A'
        }
        for r in results
    ])
    
    # Display with formatting
    st.dataframe(
        df_display,
        column_config={
            'Overall': st.column_config.ProgressColumn(
                'Overall',
                help='Overall quality score (0-100)',
                format='%d',
                min_value=0,
                max_value=100
            ),
            'Valuation': st.column_config.ProgressColumn('Val', min_value=0, max_value=100),
            'Financial': st.column_config.ProgressColumn('Fin', min_value=0, max_value=100),
            'Profit': st.column_config.ProgressColumn('Prof', min_value=0, max_value=100),
            'Growth': st.column_config.ProgressColumn('Grow', min_value=0, max_value=100),
            'Mgmt': st.column_config.ProgressColumn('Mgmt', min_value=0, max_value=100),
            'Ethics': st.column_config.ProgressColumn('Eth', min_value=0, max_value=100),
        },
        hide_index=True,
        use_container_width=True,
        height=500
    )
    
    st.divider()
    
    # Export options
    col1, col2 = st.columns(2)
    with col1:
        csv = df_display.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"stock_screening_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
            key='download-csv'
        )
    
    with col2:
        # Add to comparison
        selected_symbols = st.multiselect(
            "Select stocks to compare:",
            [r['symbol'] for r in results],
            key='select_compare'
        )
        if st.button("Add to Comparison"):
            st.session_state.comparison_list = selected_symbols
            st.success(f"Added {len(selected_symbols)} stocks to comparison!")


def display_comparison(symbols: List[str]):
    """Display side-by-side comparison of selected stocks"""
    
    if st.session_state.results is None:
        st.warning("No results available for comparison")
        return
    
    stocks = [r for r in st.session_state.results if r['symbol'] in symbols]
    
    if len(stocks) == 0:
        st.warning("Selected stocks not found in results")
        return
    
    st.header(f"🔄 Stock Comparison ({len(stocks)} stocks)")
    
    # Create comparison table
    comparison_data = {
        'Metric': [
            'Overall Score',
            'Current Price',
            'P/E Ratio',
            'Dividend Yield',
            'ROE',
            'ROIC',
            'Debt/Equity',
            'Earnings Growth',
            'Revenue Growth',
            'Market Cap'
        ]
    }
    
    for stock in stocks:
        comparison_data[stock['symbol']] = [
            f"{stock['overall_score']:.1f}",
            f"${stock['price']:.2f}",
            f"{stock['pe_ratio']:.1f}" if stock['pe_ratio'] > 0 else 'N/A',
            f"{stock['dividend_yield']:.2f}%" if stock['dividend_yield'] > 0 else 'N/A',
            f"{stock['roe']:.1f}%",
            f"{stock['roic']:.1f}%",
            f"{stock['debt_to_equity']:.2f}",
            f"{stock['earnings_growth']:.1f}%",
            f"{stock['revenue_growth']:.1f}%",
            f"${stock['market_cap']/1e9:.1f}B"
        ]
    
    df_comparison = pd.DataFrame(comparison_data)
    st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Radar chart comparison
    st.subheader("📊 Score Comparison")
    
    fig = go.Figure()
    
    categories = ['Valuation', 'Financial', 'Profitability', 'Growth', 'Management', 'Ethics']
    
    for stock in stocks:
        fig.add_trace(go.Scatterpolar(
            r=[
                stock['valuation_score'],
                stock['financial_score'],
                stock['profitability_score'],
                stock['growth_score'],
                stock['management_score'],
                stock['ethics_score']
            ],
            theta=categories,
            fill='toself',
            name=stock['symbol']
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Clear comparison button
    if st.button("🗑️ Clear Comparison"):
        st.session_state.comparison_list = []
        st.rerun()


def display_stock_details(results: List[Dict], fetcher: StockDataFetcher):
    """Display detailed analysis for a selected stock"""
    
    st.header("📈 Detailed Stock Analysis")
    
    # Stock selector
    stock_symbols = [r['symbol'] for r in results]
    selected_symbol = st.selectbox("Select a stock:", stock_symbols)
    
    stock = next((r for r in results if r['symbol'] == selected_symbol), None)
    
    if stock is None:
        st.error("Stock not found")
        return
    
    # Header with key info
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score_class = (
            "score-excellent" if stock['overall_score'] >= 90 else
            "score-good" if stock['overall_score'] >= 80 else
            "score-fair" if stock['overall_score'] >= 70 else
            "score-poor"
        )
        st.markdown(f"""
        <div class="{score_class}">
            <h2>{stock['overall_score']:.1f}</h2>
            <p>Overall Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.metric("Current Price", f"${stock['price']:.2f}")
        st.metric("52W Range", f"${stock['fifty_two_week_low']:.0f} - ${stock['fifty_two_week_high']:.0f}")
    
    with col3:
        st.metric("Market Cap", f"${stock['market_cap']/1e9:.1f}B")
        st.metric("Sector", stock['sector'])
    
    with col4:
        div_change = stock['dividend_yield'] - stock.get('five_year_avg_dividend_yield', stock['dividend_yield'])
        st.metric(
            "Dividend Yield",
            f"{stock['dividend_yield']:.2f}%" if stock['dividend_yield'] > 0 else "N/A",
            f"{div_change:.2f}%" if stock['dividend_yield'] > 0 else None
        )
        st.metric("Payout Ratio", f"{stock['payout_ratio']:.1f}%" if stock['payout_ratio'] > 0 else "N/A")
    
    st.divider()
    
    # Category scores
    st.subheader("📊 Category Scores")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    scores = [
        ('Valuation', stock['valuation_score'], col1),
        ('Financial', stock['financial_score'], col2),
        ('Profit', stock['profitability_score'], col3),
        ('Growth', stock['growth_score'], col4),
        ('Mgmt', stock['management_score'], col5),
        ('Ethics', stock['ethics_score'], col6),
    ]
    
    for label, score, col in scores:
        with col:
            grade = 'A' if score >= 90 else 'B' if score >= 80 else 'C' if score >= 70 else 'D'
            st.metric(label, f"{score:.0f}", f"Grade: {grade}")
    
    st.divider()
    
    # Detailed metrics
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Valuation", "💪 Financial Health", "📈 Profitability", "🚀 Growth", "📊 Charts"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Valuation Metrics")
            metrics_df = pd.DataFrame({
                'Metric': ['P/E Ratio', 'P/B Ratio', 'P/S Ratio', 'PEG Ratio', 'Price', 'Intrinsic Value', 'Discount'],
                'Value': [
                    f"{stock['pe_ratio']:.2f}" if stock['pe_ratio'] > 0 else 'N/A',
                    f"{stock['pb_ratio']:.2f}" if stock['pb_ratio'] > 0 else 'N/A',
                    f"{stock['ps_ratio']:.2f}" if stock['ps_ratio'] > 0 else 'N/A',
                    f"{stock['peg_ratio']:.2f}" if stock['peg_ratio'] > 0 else 'N/A',
                    f"${stock['price']:.2f}",
                    f"${stock['intrinsic_value']:.2f}",
                    f"{((stock['intrinsic_value'] - stock['price'])/stock['intrinsic_value']*100):.1f}%"
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Valuation Analysis")
            details = stock['score_details']['valuation']
            for key, value in details.items():
                st.info(f"**{key.upper()}**: {value}")
            
            # Scenario analysis
            st.subheader("📊 Valuation Scenarios")
            scenarios = {
                'Bull Case': stock['intrinsic_value'] * 1.2,
                'Base Case': stock['intrinsic_value'],
                'Bear Case': stock['intrinsic_value'] * 0.8
            }
            
            for scenario, value in scenarios.items():
                upside = (value - stock['price']) / stock['price'] * 100
                st.metric(scenario, f"${value:.2f}", f"{upside:+.1f}%")
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Financial Health Metrics")
            metrics_df = pd.DataFrame({
                'Metric': ['Current Ratio', 'Quick Ratio', 'Debt/Equity', 'Interest Coverage', 'Beta'],
                'Value': [
                    f"{stock['current_ratio']:.2f}",
                    f"{stock['quick_ratio']:.2f}",
                    f"{stock['debt_to_equity']:.2f}",
                    f"{stock['interest_coverage']:.2f}x",
                    f"{stock['beta']:.2f}"
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Financial Analysis")
            details = stock['score_details']['financial']
            for key, value in details.items():
                st.info(f"**{key.replace('_', ' ').title()}**: {value}")
    
    with tab3:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Profitability Metrics")
            metrics_df = pd.DataFrame({
                'Metric': ['ROE', 'ROIC', 'ROA', 'Operating Margin', 'Net Margin', 'Gross Margin'],
                'Value': [
                    f"{stock['roe']:.2f}%",
                    f"{stock['roic']:.2f}%",
                    f"{stock['roa']:.2f}%",
                    f"{stock['operating_margin']:.2f}%",
                    f"{stock['profit_margin']:.2f}%",
                    f"{stock['gross_margin']:.2f}%"
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Profitability Analysis")
            details = stock['score_details']['profitability']
            for key, value in details.items():
                st.info(f"**{key.upper()}**: {value}")
    
    with tab4:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Growth Metrics")
            metrics_df = pd.DataFrame({
                'Metric': ['Earnings Growth', 'Revenue Growth', 'Quarterly Growth'],
                'Value': [
                    f"{stock['earnings_growth']:.2f}%",
                    f"{stock['revenue_growth']:.2f}%",
                    f"{stock['earnings_quarterly_growth']:.2f}%"
                ]
            })
            st.dataframe(metrics_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.subheader("Growth Analysis")
            details = stock['score_details']['growth']
            for key, value in details.items():
                st.info(f"**{key.replace('_', ' ').title()}**: {value}")
    
    with tab5:
        # Price history chart
        st.subheader("📈 Price History (1 Year)")
        hist_data = fetcher.get_historical_data(selected_symbol, "1y")
        
        if not hist_data.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist_data.index,
                y=hist_data['Close'],
                mode='lines',
                name='Price',
                line=dict(color='#1e3c72', width=2)
            ))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Historical data not available")
        
        # Volume chart
        if not hist_data.empty:
            st.subheader("📊 Volume History")
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=hist_data.index,
                y=hist_data['Volume'],
                name='Volume',
                marker_color='#2a5298'
            ))
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Volume",
                height=300
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Investment thesis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 Investment Thesis")
        st.success("""
        **Key Strengths:**
        - Strong competitive position with sustainable moat
        - Consistent earnings and revenue growth
        - Healthy balance sheet with manageable debt
        - Quality management with shareholder alignment
        - Trading below intrinsic value
        """)
    
    with col2:
        st.subheader("⚠️ Key Risks")
        st.warning("""
        **Considerations:**
        - Market volatility and economic uncertainty
        - Competitive pressure in core markets
        - Regulatory changes affecting operations
        - Technology disruption risks
        - Cyclical industry dynamics
        """)
    
    st.divider()
    
    # External links
    st.subheader("🔗 External Research")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.link_button("📊 Yahoo Finance", f"https://finance.yahoo.com/quote/{selected_symbol}")
    with col2:
        st.link_button("📈 Finviz", f"https://finviz.com/quote.ashx?t={selected_symbol}")
    with col3:
        st.link_button("💹 MarketBeat", f"https://www.marketbeat.com/stocks/NYSE/{selected_symbol}/")
    with col4:
        st.link_button("🌍 Investing.com", f"https://www.investing.com/search/?q={selected_symbol}")
    with col5:
        st.link_button("🔍 Seeking Alpha", f"https://seekingalpha.com/symbol/{selected_symbol}")


# ============================================================================
# RUN APP
# ============================================================================

if __name__ == "__main__":
    main()
