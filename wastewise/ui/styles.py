"""Custom CSS design system for WasteWise with luxury dark aesthetics and glassmorphism."""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Reset & Typography */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e2e8f0;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

/* App Background Gradient */
.stApp {
    background: radial-gradient(circle at 10% 15%, rgba(30, 41, 59, 0.45) 0%, rgba(10, 14, 23, 0.98) 55%),
                radial-gradient(circle at 85% 80%, rgba(99, 102, 241, 0.08) 0%, rgba(10, 14, 23, 0.98) 60%),
                #070a12;
    background-attachment: fixed;
}

/* Header Banner */
.ww-hero-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 18px;
    padding: 24px 30px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.ww-hero-title {
    font-size: 28px;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #ffffff 30%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.ww-hero-subtitle {
    font-size: 14px;
    color: #94a3b8;
    margin-top: 4px;
}

/* Glassmorphism Metric Cards */
.ww-metric-card {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0.6) 100%);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
    padding: 20px;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.25);
    position: relative;
    overflow: hidden;
}

.ww-metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(99, 102, 241, 0.3);
    box-shadow: 0 12px 30px -5px rgba(99, 102, 241, 0.15);
}

.ww-metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #6366f1, #06b6d4);
    opacity: 0.8;
}

.ww-metric-label {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 8px;
}

.ww-metric-value {
    font-family: 'Outfit', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: #f8fafc;
    margin: 8px 0 4px 0;
    line-height: 1.1;
}

.ww-metric-subtext {
    font-size: 12px;
    color: #64748b;
}

/* Pills & Badges */
.ww-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.ww-badge-critical {
    background: rgba(244, 63, 94, 0.15);
    color: #fb7185;
    border: 1px solid rgba(244, 63, 94, 0.3);
}

.ww-badge-high {
    background: rgba(245, 158, 11, 0.15);
    color: #fcd34d;
    border: 1px solid rgba(245, 158, 11, 0.3);
}

.ww-badge-safe {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}

.ww-badge-info {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
}

/* Recommendation Item Cards */
.ww-rec-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.75) 100%);
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    padding: 20px;
    margin-bottom: 16px;
    transition: all 0.2s ease;
}

.ww-rec-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.4);
}

.ww-rec-title {
    font-size: 18px;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.ww-action-box {
    background: rgba(15, 23, 42, 0.6);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 12px 0;
    font-size: 13.5px;
    color: #cbd5e1;
    line-height: 1.5;
}

.ww-data-table {
    width: 100%;
    margin-top: 10px;
    border-collapse: collapse;
}

.ww-data-table th, .ww-data-table td {
    padding: 6px 10px;
    font-size: 12px;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.ww-data-table th {
    color: #94a3b8;
    font-weight: 600;
}

.ww-data-table td {
    color: #e2e8f0;
}

/* Streamlit Native Widget overrides */
div[data-testid="stSidebar"] {
    background-color: #0b111e;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.stButton>button {
    border-radius: 10px;
    font-weight: 600;
    padding: 0.5rem 1.25rem;
    transition: all 0.2s ease;
}

.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    border: none;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.4);
}

.stButton>button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.6);
}

/* Custom Alert / Notice Box */
.ww-notice {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 13px;
    color: #cbd5e1;
    margin-bottom: 16px;
}
</style>
"""
