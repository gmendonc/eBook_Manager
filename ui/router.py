import streamlit as st
from ui.pages.home_page import render_home_page
from ui.pages.setup_page import render_setup_page
from ui.pages.scan_page import render_scan_page
from ui.pages.view_page import render_view_page
from ui.pages.dashboard_page import render_dashboard_page
from ui.pages.workflow_page import render_workflow_page

# Page routing dictionary
page_routes = {
    "home": render_home_page,
    "setup": render_setup_page,
    "scan": render_scan_page,
    "view": render_view_page,
    "dashboard": render_dashboard_page,
    "workflow": render_workflow_page
}

def render_page(page_name, library_service, app_state):
    """
    Renders a page based on its name.
    
    Args:
        page_name: Name of the page to render
        library_service: Service for managing the library
        app_state: Application state manager
    """
    render_func = page_routes.get(page_name)
    
    if render_func:
        render_func(library_service, app_state)
    else:
        st.error(f"Page '{page_name}' not found")
        # Fallback to home page
        render_home_page(library_service, app_state)