"""
Factory module for creating and registering enrichers.

This module follows the Factory pattern to centralize the creation and registration
of all enrichers in the application. It provides individual factory functions for
each enricher type as well as a convenience function to register all enrichers at once.

The factory pattern used here helps maintain separation of concerns, making the code
more maintainable and testable. It also provides a consistent approach to creating
and configuring enrichers throughout the application.
"""

import logging
from typing import Dict, Any, Optional

from core.services.enrich_service import EnrichService
from adapters.enrichers.basic_enricher import BasicEnricher
from adapters.enrichers.default_enricher import DefaultEnricher
from adapters.enrichers.external_api_enricher import ExternalAPIEnricher
from adapters.enrichers.google_books_enricher import GoogleBooksEnricher

logger = logging.getLogger(__name__)

def register_basic_enricher(enrich_service: EnrichService) -> bool:
    """
    Creates and registers the Basic enricher.
    
    The Basic enricher provides simple metadata extraction from filenames
    without using external services or complex processing.
    
    Args:
        enrich_service: The enrichment service to register with
        
    Returns:
        True if registration was successful
    """
    try:
        enricher = BasicEnricher()
        success = enrich_service.register_enricher('basic', enricher)
        if success:
            logger.info("Basic enricher registered successfully")
        else:
            logger.warning("Failed to register Basic enricher")
        return success
    except Exception as e:
        logger.error(f"Error creating Basic enricher: {str(e)}")
        return False

def register_default_enricher(enrich_service: EnrichService) -> bool:
    """
    Creates and registers the Default enricher.
    
    The Default enricher provides comprehensive metadata extraction and
    theme classification using local processing.
    
    Args:
        enrich_service: The enrichment service to register with
        
    Returns:
        True if registration was successful
    """
    try:
        enricher = DefaultEnricher()
        success = enrich_service.register_enricher('default', enricher)
        if success:
            logger.info("Default enricher registered successfully")
        else:
            logger.warning("Failed to register Default enricher")
        return success
    except Exception as e:
        logger.error(f"Error creating Default enricher: {str(e)}")
        return False

def register_external_api_enricher(enrich_service: EnrichService, api_key: Optional[str] = None) -> bool:
    """
    Creates and registers the External API enricher.
    
    The External API enricher uses the Open Library API to retrieve
    metadata for ebooks. While it can work without an API key,
    providing one may increase the rate limits.
    
    Args:
        enrich_service: The enrichment service to register with
        api_key: Optional API key for the external service
        
    Returns:
        True if registration was successful
    """
    try:
        enricher = ExternalAPIEnricher()
        
        # Configure API key if provided
        if api_key:
            enricher.api_key = api_key
            logger.info("External API enricher created with API key")
        else:
            logger.info("External API enricher created without API key")
            
        success = enrich_service.register_enricher('external_api', enricher)
        if success:
            logger.info("External API enricher registered successfully")
        else:
            logger.warning("Failed to register External API enricher")
        return success
    except Exception as e:
        logger.error(f"Error creating External API enricher: {str(e)}")
        return False

def register_google_books_enricher(enrich_service: EnrichService, api_key: Optional[str] = None) -> bool:
    """
    Creates and registers the Google Books enricher.
    
    The Google Books enricher uses the Google Books API to retrieve
    detailed metadata for ebooks. While it can work without an API key,
    providing one increases the rate limits and quota.
    
    Args:
        enrich_service: The enrichment service to register with
        api_key: Optional API key for the Google Books API
        
    Returns:
        True if registration was successful
    """
    try:
        enricher = GoogleBooksEnricher(api_key=api_key)
        
        if api_key:
            logger.info("Google Books enricher created with API key")
        else:
            logger.info("Google Books enricher created without API key")
            
        success = enrich_service.register_enricher('google_books', enricher)
        if success:
            logger.info("Google Books enricher registered successfully")
        else:
            logger.warning("Failed to register Google Books enricher")
        return success
    except Exception as e:
        logger.error(f"Error creating Google Books enricher: {str(e)}")
        return False

def register_all_enrichers(
    enrich_service: EnrichService, 
    config: Optional[Dict[str, Any]] = None,
    set_default: str = 'default'
) -> bool:
    """
    Registers all available enrichers in a single convenience function.
    
    This function creates and registers all enrichers with the enrichment service,
    applying the provided configuration. It also sets the default enricher
    to be used when no specific enricher is specified.
    
    Args:
        enrich_service: The enrichment service to register with
        config: Optional configuration dictionary containing API keys and other settings
        set_default: Name of the enricher to set as default
        
    Returns:
        True if all registrations were successful
    """
    config = config or {}
    success = True
    
    # Register each enricher
    if not register_basic_enricher(enrich_service):
        success = False
        
    if not register_default_enricher(enrich_service):
        success = False
        
    if not register_external_api_enricher(enrich_service, config.get('external_api_key')):
        success = False
        
    if not register_google_books_enricher(enrich_service, config.get('google_books_api_key')):
        success = False
    
    # Set the default enricher if specified
    if set_default and success:
        if set_default in enrich_service.enricher_registry:
            enrich_service.set_active_enricher(set_default)
            logger.info(f"Set '{set_default}' as the active enricher")
        else:
            logger.warning(f"Could not set '{set_default}' as active: not registered")
            if 'default' in enrich_service.enricher_registry:
                enrich_service.set_active_enricher('default')
                logger.info("Fell back to 'default' as the active enricher")
            success = False
    
    return success