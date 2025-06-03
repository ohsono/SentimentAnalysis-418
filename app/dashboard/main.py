#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import os
import json
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title="UCLA Sentiment Analysis",
    page_icon="🐻",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv('API_URL', 'http://gateway-api:8080')

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "sentiment_db"),
    "username": os.getenv("DB_USER", "sentiment_user"),
    "password": os.getenv("DB_PASSWORD", "sentiment_password")
}

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "sentiment_redis")

# Initialize Redis
redis_client = None
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    # Check connection
    redis_client.ping()
    logger.info("✅ Connected to Redis successfully")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")
    redis_client = None

def call_api(endpoint: str, method: str = 'GET', data: dict = None):
    """Call API endpoint"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        if method == 'GET':
            response = requests.get(url, timeout=10)
        elif method == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            return None
            
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None

def get_tasks_from_redis(limit=10):
    """Get tasks from Redis"""
    if not redis_client:
        return []
    
    try:
        # Get all active task IDs
        task_ids = redis_client.smembers("active_tasks")
        tasks = []
        
        if task_ids:
            for task_id in list(task_ids)[:limit]:
                task_info = redis_client.hgetall(f"task:{task_id}")
                if task_info:
                    # Parse JSON data if available
                    if 'data' in task_info:
                        try:
                            task_info['data'] = json.loads(task_info['data'])
                        except:
                            pass
                    
                    if 'result' in task_info:
                        try:
                            task_info['result'] = json.loads(task_info['result'])
                        except:
                            pass
                            
                    tasks.append(task_info)
        
        return tasks
    except Exception as e:
        logger.error(f"Error getting tasks from Redis: {e}")
        return []

def main():
    """Main dashboard application"""
    
    # Header
    st.title("🐻 UCLA Social Sentiment Analysis")
    st.markdown("### Real-time monitoring of campus sentiment across Reddit communities")
    
    # Sidebar
    st.sidebar.header("🎛️ Dashboard Controls")
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)")
    if auto_refresh:
        st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.rerun()
    
    # Date range selector
    date_range = st.sidebar.selectbox(
        "📅 Time Range",
        options=[1, 3, 7, 14, 30],
        index=2,
        format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
    )
    
    # Connection status
    st.sidebar.subheader("Connection Status")
    
    # Test API connection
    health_data = call_api('/health')
    if health_data:
        st.sidebar.success("✅ API Connected")
        st.sidebar.text(f"Status: {health_data.get('status', 'unknown')}")
    else:
        st.sidebar.error("❌ API Disconnected")
        st.sidebar.text("Using demo data")
    
    # Test Redis connection
    if redis_client and redis_client.ping():
        st.sidebar.success("✅ Redis Connected")
        active_tasks = len(redis_client.smembers("active_tasks") or [])
        st.sidebar.text(f"Active tasks: {active_tasks}")
    else:
        st.sidebar.error("❌ Redis Disconnected")
    
    # Test database connection via API
    if health_data and health_data.get('services', {}).get('database') == 'operational':
        st.sidebar.success("✅ Database Connected")
    else:
        st.sidebar.error("❌ Database Disconnected")
    
    # Get analytics data
    analytics_data = call_api('/analytics')
    if not analytics_data:
        # Demo data fallback
        analytics_data = {
            "overview": {
                "total_posts": 1234,
                "total_comments": 4567,
                "avg_sentiment": 0.234,
                "data_source": "demo",
                "last_updated": datetime.now().isoformat(),
                "posts_today": 87,
                "active_users": 342,
                "database_connected": False
            },
            "sentiment_distribution": {
                "positive": 45.2,
                "neutral": 38.1,
                "negative": 16.7
            },
            "category_breakdown": {
                "academic_departments": {
                    "count": 420,
                    "avg_sentiment": 0.15,
                    "trending": "up"
                },
                "campus_life": {
                    "count": 380,
                    "avg_sentiment": 0.22,
                    "trending": "stable"
                },
                "sports": {
                    "count": 250,
                    "avg_sentiment": 0.45,
                    "trending": "up"
                },
                "administrative": {
                    "count": 200,
                    "avg_sentiment": -0.05
                }
            }
        }
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📝 Total Posts", 
            f"{analytics_data['overview'].get('total_posts', 0):,}",
            delta="+5.2%"
        )
    
    with col2:
        st.metric(
            "💬 Total Comments", 
            f"{analytics_data['overview'].get('total_comments', 0):,}",
            delta="+12.1%"
        )
        
    with col3:
        sentiment_value = analytics_data['overview'].get('avg_sentiment', 0)
        sentiment_emoji = "😊" if sentiment_value > 0.1 else "😐" if sentiment_value > -0.1 else "😞"
        st.metric(
            f"{sentiment_emoji} Avg Sentiment", 
            f"{sentiment_value:.3f}",
            delta="+0.045"
        )
        
    with col4:
        # Get alerts data
        alerts_data = call_api('/alerts')
        active_alerts = len(alerts_data.get('active_alerts', [])) if alerts_data else 3
        st.metric(
            "🚨 Active Alerts", 
            active_alerts,
            delta="-2"
        )
    
    st.divider()
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Overview", "🎯 Categories", "🚨 Alerts", "🔄 Tasks", "🔧 Tools"])
    
    with tab1:
        st.subheader("📈 Sentiment Trends")
        
        # Generate sample trend data
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=date_range),
            end=datetime.now(),
            freq='D'
        )
        
        trend_data = pd.DataFrame({
            'date': dates,
            'sentiment': [analytics_data['overview'].get('avg_sentiment', 0) + 0.1 * (i % 3 - 1) for i in range(len(dates))],
            'volume': [50 + 20 * (i % 4) for i in range(len(dates))]
        })
        
        # Sentiment trend chart
        fig1 = px.line(
            trend_data, 
            x='date', 
            y='sentiment', 
            title='Daily Sentiment Trends',
            labels={'sentiment': 'Average Sentiment', 'date': 'Date'}
        )
        fig1.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Neutral")
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
        
        # Volume chart
        fig2 = px.bar(
            trend_data,
            x='date',
            y='volume',
            title='Daily Post Volume',
            labels={'volume': 'Number of Posts', 'date': 'Date'}
        )
        fig2.update_layout(height=300)
        st.plotly_chart(fig2, use_container_width=True)
        
        # Sentiment distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Sentiment Distribution")
            dist_data = analytics_data['sentiment_distribution']
            
            fig3 = px.pie(
                values=list(dist_data.values()),
                names=list(dist_data.keys()),
                title="Overall Sentiment Distribution",
                color_discrete_map={
                    'positive': '#4CAF50',
                    'neutral': '#FFC107', 
                    'negative': '#F44336'
                }
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        with col2:
            st.subheader("🏷️ Category Activity")
            categories = analytics_data.get('category_breakdown', {})
            
            cat_df = pd.DataFrame([
                {'category': cat.replace('_', ' ').title(), 'count': data['count'], 'sentiment': data['avg_sentiment']}
                for cat, data in categories.items()
            ])
            
            fig4 = px.bar(
                cat_df,
                x='category',
                y='count',
                color='sentiment',
                title="Posts by Category",
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    with tab2:
        st.subheader("🎯 Category Analysis")
        
        # Category selector
        categories = list(analytics_data.get('category_breakdown', {}).keys())
        selected_category = st.selectbox(
            "Select Category",
            options=categories,
            format_func=lambda x: x.replace('_', ' ').title()
        )
        
        if selected_category:
            cat_data = analytics_data['category_breakdown'][selected_category]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📊 Total Posts", cat_data['count'])
            with col2:
                st.metric("😊 Avg Sentiment", f"{cat_data['avg_sentiment']:.3f}")
            with col3:
                trend = "📈" if cat_data['avg_sentiment'] > 0 else "📉"
                st.metric("📈 Trend", f"{trend} Trending")
            
            # Sample subcategory data
            st.subheader(f"📋 {selected_category.replace('_', ' ').title()} Details")
            
            subcategory_data = {
                'academic_departments': ['Computer Science', 'Engineering', 'Business', 'Pre-Med'],
                'campus_life': ['Housing', 'Dining', 'Events', 'Facilities'],
                'sports': ['Football', 'Basketball', 'General Sports'],
                'administrative': ['Admissions', 'Financial Aid', 'Academics']
            }
            
            if selected_category in subcategory_data:
                subcats = subcategory_data[selected_category]
                subcat_df = pd.DataFrame({
                    'subcategory': subcats,
                    'posts': [cat_data['count'] // len(subcats) + (i % 3) * 10 for i in range(len(subcats))],
                    'sentiment': [cat_data['avg_sentiment'] + 0.1 * (i % 3 - 1) for i in range(len(subcats))]
                })
                
                fig = px.scatter(
                    subcat_df,
                    x='posts',
                    y='sentiment',
                    text='subcategory',
                    title=f"{selected_category.replace('_', ' ').title()} Subcategories",
                    size='posts',
                    color='sentiment',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(textposition="top center")
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("🚨 Alert Monitoring")
        
        alerts_data = call_api('/alerts')
        if alerts_data:
            stats = alerts_data.get('stats', {})
            active_alerts = alerts_data.get('active_alerts', [])
            
            # Alert statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🚨 Total Active", stats.get('total_active', 0))
            with col2:
                st.metric("⚡ Recent (1h)", stats.get('recent_count', 0))
            with col3:
                critical_count = stats.get('by_severity', {}).get('critical', 0)
                st.metric("🔴 Critical", critical_count)
            
            # Severity distribution
            if stats.get('by_severity'):
                severity_data = stats['by_severity']
                
                fig = px.pie(
                    values=list(severity_data.values()),
                    names=list(severity_data.keys()),
                    title="Alert Severity Distribution",
                    color_discrete_map={
                        'critical': '#f44336',
                        'high': '#ff9800',
                        'medium': '#9c27b0',
                        'low': '#4caf50'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Recent alerts
            st.subheader("📋 Recent Alerts")
            
            if active_alerts:
                for alert in active_alerts[:5]:  # Show last 5
                    severity = alert.get('severity', 'medium')
                    alert_type = alert.get('alert_type', 'unknown')
                    timestamp = alert.get('timestamp', 'unknown')
                    
                    if severity == 'critical':
                        st.error(f"🔴 **{alert_type.title()}** - {timestamp}")
                    elif severity == 'high':
                        st.warning(f"🟠 **{alert_type.title()}** - {timestamp}")
                    else:
                        st.info(f"🟡 **{alert_type.title()}** - {timestamp}")
                    
                    st.text(f"Content: {alert.get('content_text', '')[:100]}...")
                    st.text(f"Author: {alert.get('author', 'unknown')} | Subreddit: r/{alert.get('subreddit', 'unknown')}")
                    st.divider()
            else:
                st.success("✅ No active alerts")
        else:
            st.warning("⚠️ Could not load alerts data")
    
    with tab4:
        st.subheader("🔄 Task Management")
        
        # First try to get tasks from Redis
        redis_tasks = get_tasks_from_redis(10)
        
        # If no Redis tasks, try to get tasks from API
        if not redis_tasks:
            api_tasks = call_api('/tasks')
            tasks = api_tasks.get('tasks', []) if api_tasks else []
        else:
            tasks = redis_tasks
        
        if tasks:
            st.info(f"Showing {len(tasks)} active tasks")
            
            # Create task summary
            task_types = {}
            task_statuses = {}
            
            for task in tasks:
                task_type = task.get('type', 'unknown')
                status = task.get('status', 'unknown')
                
                if task_type not in task_types:
                    task_types[task_type] = 0
                task_types[task_type] += 1
                
                if status not in task_statuses:
                    task_statuses[status] = 0
                task_statuses[status] += 1
            
            # Display task summary
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Task Types")
                fig1 = px.pie(
                    values=list(task_types.values()),
                    names=list(task_types.keys()),
                    title="Task Types Distribution"
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.subheader("Task Statuses")
                fig2 = px.pie(
                    values=list(task_statuses.values()),
                    names=list(task_statuses.keys()),
                    title="Task Statuses Distribution",
                    color_discrete_map={
                        'completed': '#4CAF50',
                        'processing': '#2196F3',
                        'queued': '#FFC107',
                        'error': '#F44336',
                        'submitted': '#9C27B0',
                        'unknown': '#9E9E9E'
                    }
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            # Display task details
            st.subheader("Task Details")
            for task in tasks:
                task_id = task.get('task_id', '')
                task_type = task.get('type', 'unknown')
                status = task.get('status', 'unknown')
                submitted_at = task.get('submitted_at', '')
                
                if status == 'completed':
                    st.success(f"✅ {task_type.upper()} - {task_id}")
                elif status == 'processing':
                    st.info(f"⏳ {task_type.upper()} - {task_id}")
                elif status == 'error':
                    st.error(f"❌ {task_type.upper()} - {task_id}")
                else:
                    st.warning(f"⏳ {task_type.upper()} - {task_id}")
                
                st.text(f"Submitted: {submitted_at}")
                
                # Show task data if available
                if 'data' in task:
                    data = task['data']
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except:
                            pass
                    
                    if isinstance(data, dict):
                        for key, value in data.items():
                            st.text(f"{key}: {value}")
                    else:
                        st.text(f"Data: {data}")
                
                st.divider()
        else:
            st.warning("No active tasks found")
        
        # Add refresh button
        if st.button("🔄 Refresh Tasks"):
            st.rerun()
    
    with tab5:
        st.subheader("🔧 Analysis Tools")
        
        # Manual sentiment analysis
        st.subheader("🎯 Test Sentiment Analysis")
        
        test_text = st.text_area(
            "Enter text to analyze:",
            placeholder="Type some text related to UCLA to test sentiment analysis...",
            height=100
        )
        
        if st.button("🔍 Analyze Sentiment") and test_text:
            with st.spinner("Analyzing..."):
                result = call_api('/predict', 'POST', {'text': test_text, 'include_probabilities': True})
                
                if result:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        sentiment = result.get('sentiment', 'neutral')
                        emoji = {"positive": "😊", "negative": "😞", "neutral": "😐"}[sentiment]
                        st.metric(f"{emoji} Sentiment", sentiment.title())
                    
                    with col2:
                        confidence = result.get('confidence', 0)
                        st.metric("🎯 Confidence", f"{confidence:.1%}")
                    
                    with col3:
                        compound = result.get('compound_score', 0)
                        st.metric("📊 Score", f"{compound:.3f}")
                    
                    # Probabilities
                    if result.get('probabilities'):
                        probs = result['probabilities']
                        prob_df = pd.DataFrame([
                            {'Sentiment': k.title(), 'Probability': v}
                            for k, v in probs.items()
                        ])
                        
                        fig = px.bar(
                            prob_df,
                            x='Sentiment',
                            y='Probability',
                            title="Sentiment Probabilities",
                            color='Sentiment',
                            color_discrete_map={
                                'Positive': '#4CAF50',
                                'Neutral': '#FFC107',
                                'Negative': '#F44336'
                            }
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("❌ Could not analyze text")
        
        # Reddit scraping tool
        st.subheader("📡 Reddit Data Collection")
        
        col1, col2 = st.columns(2)
        
        with col1:
            scrape_subreddit = st.text_input("Subreddit", value="UCLA")
        
        with col2:
            scrape_limit = st.number_input("Post Limit", min_value=1, max_value=50, value=5)
        
        if st.button("🔄 Scrape Reddit Data"):
            with st.spinner("Submitting scraping task..."):
                scrape_result = call_api('/scrape', 'POST', {
                    'subreddit': scrape_subreddit,
                    'post_limit': scrape_limit
                })
                
                if scrape_result and "task_id" in scrape_result:
                    st.success(f"✅ Scraping task submitted. Task ID: {scrape_result['task_id']}")
                    
                    # Show task details
                    st.subheader("Task Details")
                    st.json(scrape_result)
                    
                    # Add instructions for checking task status
                    st.info("Check the Tasks tab for task status and results")
                    
                else:
                    st.error("❌ Could not submit scraping task")
        
        # System status
        st.subheader("🔧 System Status")
        
        if health_data:
            st.success("✅ All systems operational")
            
            with st.expander("📊 System Details"):
                st.json(health_data)
        else:
            st.error("❌ System health check failed")
    
    # Footer
    st.divider()
    st.markdown("**Built with ❤️ for the UCLA Community** 🐻")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

if __name__ == "__main__":
    main()
