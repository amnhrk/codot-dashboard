"""
KPI (Key Performance Indicators) Module
Calculate and track important metrics for code development and store analytics
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import logging
import sqlite3
from sqlite_utils import Database

logger = logging.getLogger(__name__)

class KPICalculator:
    """Calculate various KPIs for development metrics"""
    
    def __init__(self, data: pd.DataFrame):
        self.data = data.copy()
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
    
    def developer_productivity(self) -> Dict[str, float]:
        """Calculate developer productivity metrics"""
        if self.data.empty:
            return {}
        
        # Average commits per developer per day
        daily_commits = self.data.groupby(['user_id', 'date'])['commits'].sum().reset_index()
        avg_commits_per_day = daily_commits.groupby('user_id')['commits'].mean().mean()
        
        # Average lines of code per developer
        if 'lines_added' in self.data.columns:
            avg_lines_per_developer = self.data.groupby('user_id')['lines_added'].mean().mean()
        else:
            avg_lines_per_developer = 0
        
        # Code churn rate (lines deleted / lines added)
        if 'lines_added' in self.data.columns and 'lines_deleted' in self.data.columns:
            total_added = self.data['lines_added'].sum()
            total_deleted = self.data['lines_deleted'].sum()
            churn_rate = (total_deleted / total_added * 100) if total_added > 0 else 0
        else:
            churn_rate = 0
        
        return {
            'avg_commits_per_day': round(avg_commits_per_day, 2),
            'avg_lines_per_developer': round(avg_lines_per_developer, 2),
            'code_churn_rate': round(churn_rate, 2)
        }
    
    def project_health(self) -> Dict[str, float]:
        """Calculate project health metrics"""
        if self.data.empty:
            return {}
        
        # Number of active developers
        active_developers = self.data['user_id'].nunique()
        
        # Number of active projects
        active_projects = self.data['project_id'].nunique() if 'project_id' in self.data.columns else 1
        
        # Commit frequency (commits per day)
        if 'date' in self.data.columns:
            date_range = (self.data['date'].max() - self.data['date'].min()).days
            total_commits = self.data['commits'].sum()
            commit_frequency = total_commits / max(date_range, 1)
        else:
            commit_frequency = 0
        
        return {
            'active_developers': active_developers,
            'active_projects': active_projects,
            'commits_per_day': round(commit_frequency, 2)
        }
    
    def velocity_metrics(self) -> Dict[str, float]:
        """Calculate development velocity metrics"""
        if self.data.empty or 'date' not in self.data.columns:
            return {}
        
        # Weekly velocity (commits per week)
        self.data['week'] = self.data['date'].dt.isocalendar().week
        weekly_commits = self.data.groupby('week')['commits'].sum()
        avg_weekly_velocity = weekly_commits.mean()
        
        # Velocity trend (comparing last 2 weeks)
        if len(weekly_commits) >= 2:
            recent_weeks = weekly_commits.tail(2)
            velocity_trend = ((recent_weeks.iloc[-1] - recent_weeks.iloc[-2]) / recent_weeks.iloc[-2] * 100) if recent_weeks.iloc[-2] > 0 else 0
        else:
            velocity_trend = 0
        
        # Story points per sprint (mock calculation)
        story_points_per_sprint = avg_weekly_velocity * 2  # Assuming 2-week sprints
        
        return {
            'avg_weekly_velocity': round(avg_weekly_velocity, 2),
            'velocity_trend': round(velocity_trend, 2),
            'story_points_per_sprint': round(story_points_per_sprint, 2)
        }
    
    def quality_metrics(self) -> Dict[str, float]:
        """Calculate code quality metrics"""
        if self.data.empty:
            return {}
        
        # Mock quality metrics (in real scenario, these would come from code analysis tools)
        
        # Bug density (bugs per 1000 lines of code)
        if 'lines_added' in self.data.columns:
            total_lines = self.data['lines_added'].sum()
            # Mock bug count (in real scenario, this would come from bug tracking system)
            estimated_bugs = np.random.randint(10, 50)
            bug_density = (estimated_bugs / max(total_lines, 1)) * 1000
        else:
            bug_density = 0
        
        # Code review coverage (percentage of commits that went through review)
        # Mock calculation - in reality, this would come from your code review system
        review_coverage = np.random.uniform(75, 95)
        
        # Technical debt ratio (mock calculation)
        technical_debt_ratio = np.random.uniform(10, 25)
        
        return {
            'bug_density': round(bug_density, 2),
            'review_coverage': round(review_coverage, 2),
            'technical_debt_ratio': round(technical_debt_ratio, 2)
        }

def calculate_kpis(data: pd.DataFrame = None) -> Dict[str, Any]:
    """Main function to calculate all KPIs"""
    
    # If no data provided, create sample data
    if data is None:
        data = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=30),
            'user_id': np.random.choice(range(1, 6), 30),
            'project_id': np.random.choice(range(1, 4), 30),
            'commits': np.random.randint(1, 8, 30),
            'lines_added': np.random.randint(50, 300, 30),
            'lines_deleted': np.random.randint(10, 100, 30)
        })
    
    calculator = KPICalculator(data)
    
    try:
        kpis = {
            'Developer Productivity': calculator.developer_productivity(),
            'Project Health': calculator.project_health(),
            'Velocity Metrics': calculator.velocity_metrics(),
            'Quality Metrics': calculator.quality_metrics()
        }
        
        # Flatten the nested dictionary for easier display
        flattened_kpis = {}
        for category, metrics in kpis.items():
            for metric_name, value in metrics.items():
                flattened_kpis[f"{category} - {metric_name.title().replace('_', ' ')}"] = value
        
        return flattened_kpis
        
    except Exception as e:
        logger.error(f"Error calculating KPIs: {e}")
        return {"Error": "Failed to calculate KPIs"}

def get_kpi_insights(kpis: Dict[str, Any]) -> List[str]:
    """Generate insights based on calculated KPIs"""
    insights = []
    
    for kpi_name, value in kpis.items():
        if isinstance(value, (int, float)):
            if "commits_per_day" in kpi_name.lower() and value > 5:
                insights.append(f"High commit frequency detected: {value} commits/day")
            elif "churn_rate" in kpi_name.lower() and value > 30:
                insights.append(f"High code churn rate: {value}% - consider code review improvements")
            elif "bug_density" in kpi_name.lower() and value > 10:
                insights.append(f"High bug density: {value} bugs/1000 lines - focus on quality")
            elif "review_coverage" in kpi_name.lower() and value < 80:
                insights.append(f"Low code review coverage: {value}% - improve review process")
    
    if not insights:
        insights.append("All metrics are within normal ranges")
    
    return insights

# Store Analytics Functions

def _fetch_df(sql: str, params: tuple = (), db_path: str = "codot.db") -> pd.DataFrame:
    """
    Internal helper function to fetch data from SQLite database
    
    Args:
        sql: SQL query string
        params: Query parameters tuple
        db_path: Path to SQLite database
        
    Returns:
        DataFrame with query results
    """
    try:
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql_query(sql, conn, params=params)
            return df
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def get_store_list(db_path: str = "codot.db") -> List[str]:
    """
    Get distinct store_id list from SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        List of unique store IDs
    """
    sql = """
    SELECT DISTINCT store_id 
    FROM (
        SELECT store_id FROM sales_daily WHERE store_id IS NOT NULL
        UNION
        SELECT store_id FROM customers_daily WHERE store_id IS NOT NULL
        UNION  
        SELECT store_id FROM spend_daily WHERE store_id IS NOT NULL
        UNION
        SELECT store_id FROM labor_daily WHERE store_id IS NOT NULL
    ) 
    ORDER BY store_id
    """
    
    try:
        df = _fetch_df(sql, db_path=db_path)
        return df['store_id'].tolist() if not df.empty else []
    except Exception as e:
        logger.error(f"Error getting store list: {e}")
        return []


def plot_customer_trend(store_id: str, months: int = 3, db_path: str = "codot.db") -> go.Figure:
    """
    Plot customer count trend for specified store
    
    Args:
        store_id: Store identifier
        months: Number of months to display
        db_path: Path to SQLite database
        
    Returns:
        Plotly figure object
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    prev_year_start = start_date - timedelta(days=365)
    prev_year_end = end_date - timedelta(days=365)
    
    # Current year data
    sql_current = """
    SELECT 
        sales_date,
        customer_count
    FROM customers_daily 
    WHERE store_id = ? 
        AND sales_date >= ? 
        AND sales_date <= ?
    ORDER BY sales_date
    """
    
    current_df = _fetch_df(
        sql_current, 
        (store_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Previous year data
    prev_df = _fetch_df(
        sql_current,
        (store_id, prev_year_start.strftime('%Y-%m-%d'), prev_year_end.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Process current year data
    if not current_df.empty:
        current_df['sales_date'] = pd.to_datetime(current_df['sales_date'])
        current_df['month'] = current_df['sales_date'].dt.to_period('M').astype(str)
        current_monthly = current_df.groupby('month')['customer_count'].sum().reset_index()
    else:
        current_monthly = pd.DataFrame(columns=['month', 'customer_count'])
    
    # Process previous year data
    if not prev_df.empty:
        prev_df['sales_date'] = pd.to_datetime(prev_df['sales_date'])
        prev_df['month'] = (prev_df['sales_date'] + pd.DateOffset(years=1)).dt.to_period('M').astype(str)
        prev_monthly = prev_df.groupby('month')['customer_count'].sum().reset_index()
    else:
        prev_monthly = pd.DataFrame(columns=['month', 'customer_count'])
    
    # Create figure
    fig = go.Figure()
    
    # Add current year line
    if not current_monthly.empty:
        fig.add_trace(go.Scatter(
            x=current_monthly['month'],
            y=current_monthly['customer_count'],
            mode='lines+markers',
            name='今年',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
    
    # Add previous year line (dashed)
    if not prev_monthly.empty:
        fig.add_trace(go.Scatter(
            x=prev_monthly['month'],
            y=prev_monthly['customer_count'],
            mode='lines+markers',
            name='前年同期',
            line=dict(color='#A23B72', width=2, dash='dash'),
            marker=dict(size=6)
        ))
    
    # Update layout
    fig.update_layout(
        title=f'顧客数推移 - {store_id}',
        xaxis_title='月',
        yaxis_title='顧客数',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Format Y-axis for auto units (K, M)
    fig.update_yaxes(tickformat='.2s')
    
    return fig


def plot_spend_trend(store_id: str, months: int = 3, db_path: str = "codot.db") -> go.Figure:
    """
    Plot average spend trend for specified store
    
    Args:
        store_id: Store identifier
        months: Number of months to display
        db_path: Path to SQLite database
        
    Returns:
        Plotly figure object
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    prev_year_start = start_date - timedelta(days=365)
    prev_year_end = end_date - timedelta(days=365)
    
    # Current year data
    sql_current = """
    SELECT 
        sales_date,
        average_spend
    FROM spend_daily 
    WHERE store_id = ? 
        AND sales_date >= ? 
        AND sales_date <= ?
    ORDER BY sales_date
    """
    
    current_df = _fetch_df(
        sql_current, 
        (store_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Previous year data
    prev_df = _fetch_df(
        sql_current,
        (store_id, prev_year_start.strftime('%Y-%m-%d'), prev_year_end.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Process current year data
    if not current_df.empty:
        current_df['sales_date'] = pd.to_datetime(current_df['sales_date'])
        current_df['month'] = current_df['sales_date'].dt.to_period('M').astype(str)
        current_monthly = current_df.groupby('month')['average_spend'].mean().reset_index()
    else:
        current_monthly = pd.DataFrame(columns=['month', 'average_spend'])
    
    # Process previous year data
    if not prev_df.empty:
        prev_df['sales_date'] = pd.to_datetime(prev_df['sales_date'])
        prev_df['month'] = (prev_df['sales_date'] + pd.DateOffset(years=1)).dt.to_period('M').astype(str)
        prev_monthly = prev_df.groupby('month')['average_spend'].mean().reset_index()
    else:
        prev_monthly = pd.DataFrame(columns=['month', 'average_spend'])
    
    # Create figure
    fig = go.Figure()
    
    # Add current year line
    if not current_monthly.empty:
        fig.add_trace(go.Scatter(
            x=current_monthly['month'],
            y=current_monthly['average_spend'],
            mode='lines+markers',
            name='今年',
            line=dict(color='#F18F01', width=3),
            marker=dict(size=8)
        ))
    
    # Add previous year line (dashed)
    if not prev_monthly.empty:
        fig.add_trace(go.Scatter(
            x=prev_monthly['month'],
            y=prev_monthly['average_spend'],
            mode='lines+markers',
            name='前年同期',
            line=dict(color='#C73E1D', width=2, dash='dash'),
            marker=dict(size=6)
        ))
    
    # Update layout
    fig.update_layout(
        title=f'客単価推移 - {store_id}',
        xaxis_title='月',
        yaxis_title='客単価 (円)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Format Y-axis for auto units (K, M)
    fig.update_yaxes(tickformat='.2s')
    
    return fig


def plot_productivity(store_id: str, months: int = 3, db_path: str = "codot.db") -> go.Figure:
    """
    Plot productivity metrics (sales per work hour) for specified store
    
    Args:
        store_id: Store identifier
        months: Number of months to display
        db_path: Path to SQLite database
        
    Returns:
        Plotly figure object
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    prev_year_start = start_date - timedelta(days=365)
    prev_year_end = end_date - timedelta(days=365)
    
    # Current year data - join sales and labor data
    sql_current = """
    SELECT 
        s.sales_date,
        s.sales_amount,
        l.work_hours
    FROM sales_daily s
    LEFT JOIN labor_daily l ON s.sales_date = l.sales_date AND s.store_id = l.store_id
    WHERE s.store_id = ? 
        AND s.sales_date >= ? 
        AND s.sales_date <= ?
        AND l.work_hours > 0
    ORDER BY s.sales_date
    """
    
    current_df = _fetch_df(
        sql_current, 
        (store_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Previous year data
    prev_df = _fetch_df(
        sql_current,
        (store_id, prev_year_start.strftime('%Y-%m-%d'), prev_year_end.strftime('%Y-%m-%d')),
        db_path
    )
    
    # Process current year data
    if not current_df.empty:
        current_df['sales_date'] = pd.to_datetime(current_df['sales_date'])
        current_df['productivity'] = current_df['sales_amount'] / current_df['work_hours']
        current_df['month'] = current_df['sales_date'].dt.to_period('M').astype(str)
        current_monthly = current_df.groupby('month')['productivity'].mean().reset_index()
    else:
        current_monthly = pd.DataFrame(columns=['month', 'productivity'])
    
    # Process previous year data
    if not prev_df.empty:
        prev_df['sales_date'] = pd.to_datetime(prev_df['sales_date'])
        prev_df['productivity'] = prev_df['sales_amount'] / prev_df['work_hours']
        prev_df['month'] = (prev_df['sales_date'] + pd.DateOffset(years=1)).dt.to_period('M').astype(str)
        prev_monthly = prev_df.groupby('month')['productivity'].mean().reset_index()
    else:
        prev_monthly = pd.DataFrame(columns=['month', 'productivity'])
    
    # Create figure
    fig = go.Figure()
    
    # Add current year line
    if not current_monthly.empty:
        fig.add_trace(go.Scatter(
            x=current_monthly['month'],
            y=current_monthly['productivity'],
            mode='lines+markers',
            name='今年',
            line=dict(color='#3D5A80', width=3),
            marker=dict(size=8)
        ))
    
    # Add previous year line (dashed)
    if not prev_monthly.empty:
        fig.add_trace(go.Scatter(
            x=prev_monthly['month'],
            y=prev_monthly['productivity'],
            mode='lines+markers',
            name='前年同期',
            line=dict(color='#98C1D9', width=2, dash='dash'),
            marker=dict(size=6)
        ))
    
    # Update layout
    fig.update_layout(
        title=f'生産性推移 (売上/労働時間) - {store_id}',
        xaxis_title='月',
        yaxis_title='生産性 (円/時)',
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Format Y-axis for auto units (K, M)
    fig.update_yaxes(tickformat='.2s')
    
    return fig


if __name__ == "__main__":
    # Test the KPI calculations
    kpis = calculate_kpis()
    print("Calculated KPIs:")
    for name, value in kpis.items():
        print(f"  {name}: {value}")
    
    print("\nInsights:")
    insights = get_kpi_insights(kpis)
    for insight in insights:
        print(f"  - {insight}")
    
    # Test store analytics functions
    print("\nTesting Store Analytics:")
    stores = get_store_list()
    print(f"Available stores: {stores}")
    
    if stores:
        print(f"Testing plots for store: {stores[0]}")
        customer_fig = plot_customer_trend(stores[0])
        spend_fig = plot_spend_trend(stores[0])
        productivity_fig = plot_productivity(stores[0])
        print("Plot functions executed successfully") 