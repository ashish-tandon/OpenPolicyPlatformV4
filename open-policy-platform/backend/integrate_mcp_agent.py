#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - MCP Agent Integration

This script integrates the MCP Data Quality Agent with the existing scraper system
to ensure data quality, proper scraping, and correct database operations.
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml

# Import the MCP agent
from mcp_data_quality_agent import MCPDataQualityAgent, DataQualityStatus, ValidationResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPAgentIntegration:
    """Integration class for MCP Data Quality Agent"""
    
    def __init__(self, 
                 database_url: str = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                 redis_url: str = "redis://localhost:6379",
                 config_path: Optional[str] = None):
        self.database_url = database_url
        self.redis_url = redis_url
        self.config_path = config_path
        
        # Initialize MCP agent
        self.mcp_agent = MCPDataQualityAgent(database_url, redis_url, config_path)
        
        # Integration tracking
        self.integration_history: List[Dict] = []
        self.scraping_sessions: List[Dict] = []
        self.quality_reports: List[Dict] = []
    
    async def integrate_with_scrapers(self, scraper_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate MCP agent with scraper data"""
        logger.info("🔗 Integrating MCP agent with scraper data")
        
        integration_results = {
            "timestamp": datetime.now().isoformat(),
            "scraper_integrations": {},
            "data_quality_improvements": {},
            "database_operations": {},
            "recommendations": []
        }
        
        try:
            for scraper_name, data in scraper_data.items():
                logger.info(f"🔍 Processing scraper: {scraper_name}")
                
                # Step 1: Validate scraped data
                validation = await self.mcp_agent.validate_scraped_data(scraper_name, data, "")
                integration_results["scraper_integrations"][scraper_name] = {
                    "validation": validation.__dict__,
                    "status": validation.validation_result.value
                }
                
                # Step 2: Ensure data completeness
                completeness = await self.mcp_agent.ensure_data_completeness(scraper_name, data)
                integration_results["data_quality_improvements"][scraper_name] = completeness
                
                # Step 3: Ensure database operations
                table_mapping = self._get_table_mapping(scraper_name)
                db_ops = await self.mcp_agent.ensure_database_operations(data, table_mapping)
                integration_results["database_operations"][scraper_name] = db_ops
                
                # Step 4: Generate recommendations
                recommendations = self._generate_recommendations(validation, completeness, db_ops)
                integration_results["recommendations"].extend(recommendations)
            
            # Store integration results
            self.integration_history.append(integration_results)
            
            logger.info("✅ MCP agent integration completed")
            return integration_results
            
        except Exception as e:
            logger.error(f"❌ MCP agent integration failed: {e}")
            integration_results["error"] = str(e)
            return integration_results
    
    def _get_table_mapping(self, scraper_name: str) -> Dict[str, str]:
        """Get table mapping for a scraper"""
        table_mappings = {
            "federal_parliament": {
                "mps": "representatives",
                "bills": "bills",
                "committees": "committees",
                "votes": "votes"
            },
            "ontario_legislature": {
                "mpps": "representatives",
                "bills": "bills",
                "committees": "committees"
            },
            "british_columbia_legislature": {
                "mlas": "representatives",
                "bills": "bills",
                "committees": "committees"
            },
            "toronto_council": {
                "councillors": "representatives",
                "mayor": "representatives",
                "meetings": "events"
            },
            "vancouver_council": {
                "councillors": "representatives",
                "mayor": "representatives",
                "meetings": "events"
            }
        }
        
        return table_mappings.get(scraper_name.lower(), {
            "representatives": "representatives",
            "bills": "bills",
            "committees": "committees",
            "events": "events",
            "votes": "votes"
        })
    
    def _generate_recommendations(self, validation, completeness, db_ops) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Validation recommendations
        if validation.validation_result == ValidationResult.CRITICAL:
            recommendations.append(f"Critical validation issues for {validation.scraper_name} - immediate attention required")
        elif validation.validation_result == ValidationResult.FAILED:
            recommendations.append(f"Validation failed for {validation.scraper_name} - review scraper logic")
        elif validation.validation_result == ValidationResult.WARNING:
            recommendations.append(f"Validation warnings for {validation.scraper_name} - monitor closely")
        
        # Completeness recommendations
        if completeness["completeness_score"] < 0.8:
            recommendations.append(f"Data completeness below threshold for {validation.scraper_name} - missing sources detected")
        
        # Database operations recommendations
        for data_type, result in db_ops.items():
            if isinstance(result, dict) and result.get("success_rate", 1.0) < 0.8:
                recommendations.append(f"Low success rate for {data_type} in {validation.scraper_name} - review database operations")
        
        return recommendations
    
    async def run_comprehensive_integration(self) -> Dict[str, Any]:
        """Run comprehensive integration with all scrapers"""
        logger.info("🎯 Running comprehensive MCP agent integration")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "integration_status": "completed",
            "scrapers_processed": 0,
            "quality_improvements": 0,
            "issues_found": 0,
            "recommendations": []
        }
        
        try:
            # Get all scrapers
            scrapers = await self._get_all_scrapers()
            results["scrapers_processed"] = len(scrapers)
            
            for scraper in scrapers:
                try:
                    # Process each scraper
                    scraper_data = await self._get_scraper_data(scraper)
                    if scraper_data:
                        integration_result = await self.integrate_with_scrapers({scraper: scraper_data})
                        
                        # Count improvements and issues
                        if integration_result.get("data_quality_improvements"):
                            results["quality_improvements"] += 1
                        
                        if integration_result.get("recommendations"):
                            results["issues_found"] += len(integration_result["recommendations"])
                            results["recommendations"].extend(integration_result["recommendations"])
                
                except Exception as e:
                    logger.error(f"❌ Error processing scraper {scraper}: {e}")
                    results["recommendations"].append(f"Error processing scraper {scraper}: {str(e)}")
            
            # Generate final quality report
            quality_report = await self.mcp_agent.generate_quality_report()
            results["quality_report"] = quality_report
            
            logger.info("✅ Comprehensive integration completed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive integration failed: {e}")
            results["integration_status"] = "failed"
            results["error"] = str(e)
            return results
    
    async def _get_all_scrapers(self) -> List[str]:
        """Get all available scrapers"""
        # This would integrate with the existing scraper system
        # For now, return a list of known scrapers
        return [
            "federal_parliament",
            "ontario_legislature",
            "british_columbia_legislature",
            "alberta_legislature",
            "toronto_council",
            "vancouver_council",
            "calgary_council"
        ]
    
    async def _get_scraper_data(self, scraper_name: str) -> Optional[Dict[str, Any]]:
        """Get data from a specific scraper"""
        try:
            # This would integrate with the existing scraper system
            # For now, return sample data
            sample_data = {
                "representatives": [
                    {
                        "name": f"Sample Representative {scraper_name}",
                        "role": "mp",
                        "jurisdiction_id": "123e4567-e89b-12d3-a456-426614174000",
                        "party": "Sample Party",
                        "riding": "Sample Riding"
                    }
                ]
            }
            return sample_data
        except Exception as e:
            logger.error(f"❌ Error getting scraper data for {scraper_name}: {e}")
            return None
    
    async def monitor_data_quality(self) -> Dict[str, Any]:
        """Monitor data quality continuously"""
        logger.info("📊 Monitoring data quality")
        
        monitoring_results = {
            "timestamp": datetime.now().isoformat(),
            "quality_metrics": {},
            "alerts": [],
            "recommendations": []
        }
        
        try:
            # Run comprehensive validation
            validation_results = await self.mcp_agent.run_comprehensive_validation()
            monitoring_results["quality_metrics"] = validation_results
            
            # Check for critical issues
            if validation_results.get("quality_report", {}).get("overall_quality", {}).get("status") == DataQualityStatus.CRITICAL:
                monitoring_results["alerts"].append("CRITICAL: Overall data quality is critical - immediate attention required")
            
            # Check for quality issues
            if validation_results.get("quality_report", {}).get("overall_quality", {}).get("score", 1.0) < 0.8:
                monitoring_results["alerts"].append("WARNING: Data quality below threshold - review processes")
            
            # Generate recommendations
            if validation_results.get("recommendations"):
                monitoring_results["recommendations"] = validation_results["recommendations"]
            
            logger.info("✅ Data quality monitoring completed")
            return monitoring_results
            
        except Exception as e:
            logger.error(f"❌ Data quality monitoring failed: {e}")
            monitoring_results["error"] = str(e)
            return monitoring_results
    
    async def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        logger.info("📊 Generating integration report")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "integration_summary": {
                "total_integrations": len(self.integration_history),
                "successful_integrations": len([i for i in self.integration_history if "error" not in i]),
                "failed_integrations": len([i for i in self.integration_history if "error" in i]),
                "quality_improvements": len(self.quality_reports)
            },
            "scraping_sessions": self.scraping_sessions[-10:],  # Last 10 sessions
            "quality_reports": self.quality_reports[-10:],  # Last 10 reports
            "integration_history": self.integration_history[-10:],  # Last 10 integrations
            "recommendations": []
        }
        
        try:
            # Generate recommendations based on integration history
            recommendations = []
            
            # Check for common issues
            failed_integrations = [i for i in self.integration_history if "error" in i]
            if failed_integrations:
                recommendations.append(f"Found {len(failed_integrations)} failed integrations - review error logs")
            
            # Check for quality issues
            quality_issues = [r for r in self.quality_reports if r.get("overall_quality", {}).get("status") == DataQualityStatus.CRITICAL]
            if quality_issues:
                recommendations.append(f"Found {len(quality_issues)} critical quality issues - immediate attention required")
            
            # Check for scraping issues
            scraping_issues = [s for s in self.scraping_sessions if s.get("status") == "failed"]
            if scraping_issues:
                recommendations.append(f"Found {len(scraping_issues)} failed scraping sessions - review scraper configuration")
            
            report["recommendations"] = recommendations
            
            logger.info("✅ Integration report generated")
            return report
            
        except Exception as e:
            logger.error(f"❌ Integration report generation failed: {e}")
            report["error"] = str(e)
            return report

# Example usage
async def main():
    """Example usage of MCP Agent Integration"""
    integration = MCPAgentIntegration()
    
    # Example scraper data
    sample_scraper_data = {
        "federal_parliament": {
            "representatives": [
                {
                    "name": "John Doe",
                    "role": "mp",
                    "jurisdiction_id": "123e4567-e89b-12d3-a456-426614174000",
                    "party": "Liberal",
                    "riding": "Toronto Centre"
                }
            ],
            "bills": [
                {
                    "bill_number": "C-123",
                    "title": "An Act to amend the Criminal Code",
                    "jurisdiction_id": "123e4567-e89b-12d3-a456-426614174000",
                    "status": "introduced"
                }
            ]
        }
    }
    
    # Run integration
    integration_result = await integration.integrate_with_scrapers(sample_scraper_data)
    print(f"Integration result: {integration_result}")
    
    # Monitor data quality
    monitoring_result = await integration.monitor_data_quality()
    print(f"Monitoring result: {monitoring_result}")
    
    # Generate integration report
    report = await integration.generate_integration_report()
    print(f"Integration report: {report}")

if __name__ == "__main__":
    asyncio.run(main())
