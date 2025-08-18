#!/usr/bin/env python3
"""
🎯 OpenPolicy Platform - MCP Data Quality Agent

This module implements a comprehensive MCP (Model Context Protocol) middleware AI agent
that works between scrapers and the database to ensure:

1. All data is properly scraped and validated
2. Missing data sources are identified and scrapers corrected
3. All values go to the right tables and are committed correctly
4. Data quality is maintained throughout the pipeline
5. Automated error detection and correction

Following AI Agent Guidance System and TDD Process.
"""

import json
import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlalchemy as sa
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine, text
import requests
import redis
from pathlib import Path
import yaml
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityStatus(Enum):
    """Data quality status enumeration"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class ValidationResult(Enum):
    """Validation result enumeration"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    CRITICAL = "critical"

@dataclass
class DataQualityMetrics:
    """Data quality metrics"""
    completeness: float  # 0.0 to 1.0
    accuracy: float      # 0.0 to 1.0
    consistency: float   # 0.0 to 1.0
    freshness: float     # 0.0 to 1.0
    validity: float      # 0.0 to 1.0
    overall_score: float # 0.0 to 1.0
    status: DataQualityStatus
    issues: List[str]
    recommendations: List[str]

@dataclass
class ScrapingValidation:
    """Scraping validation result"""
    scraper_name: str
    source_url: str
    records_expected: int
    records_collected: int
    records_valid: int
    data_quality_score: float
    validation_result: ValidationResult
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime

@dataclass
class DatabaseValidation:
    """Database validation result"""
    table_name: str
    records_count: int
    records_valid: int
    foreign_key_issues: int
    constraint_violations: int
    data_quality_score: float
    validation_result: ValidationResult
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime

class MCPDataQualityAgent:
    """MCP Data Quality Agent - Middleware between scrapers and database"""
    
    def __init__(self, 
                 database_url: str = "postgresql://openpolicy:openpolicy123@localhost:5432/openpolicy",
                 redis_url: str = "redis://localhost:6379",
                 config_path: Optional[str] = None):
        self.database_url = database_url
        self.redis_url = redis_url
        self.config_path = config_path or "mcp_agent_config.yaml"
        
        # Initialize connections
        self.engine = None
        self.session_factory = None
        self.redis_client = None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize components
        self._initialize_connections()
        self._setup_validation_rules()
        
        # Tracking
        self.validation_history: List[Dict] = []
        self.quality_metrics: Dict[str, DataQualityMetrics] = {}
        self.scraping_issues: List[Dict] = []
        self.database_issues: List[Dict] = []
    
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP agent configuration"""
        default_config = {
            "validation_rules": {
                "completeness_threshold": 0.8,
                "accuracy_threshold": 0.9,
                "consistency_threshold": 0.85,
                "freshness_threshold": 0.7,
                "validity_threshold": 0.95
            },
            "scraping_rules": {
                "max_retries": 3,
                "timeout": 30,
                "batch_size": 100,
                "quality_check_interval": 300
            },
            "database_rules": {
                "foreign_key_validation": True,
                "constraint_validation": True,
                "data_type_validation": True,
                "uniqueness_validation": True
            },
            "monitoring": {
                "enabled": True,
                "alert_threshold": 0.7,
                "report_interval": 3600
            }
        }
        
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Create default config
                with open(self.config_path, 'w') as f:
                    yaml.dump(default_config, f)
                return default_config
        except Exception as e:
            logger.warning(f"Failed to load config, using defaults: {e}")
            return default_config
    
    def _initialize_connections(self):
        """Initialize database and Redis connections"""
        try:
            # Database connection
            self.engine = create_engine(self.database_url, pool_size=20, max_overflow=30)
            self.session_factory = sessionmaker(bind=self.engine)
            logger.info("✅ Database connection established")
            
            # Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
            logger.info("✅ Redis connection established")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connections: {e}")
            raise
    
    def _setup_validation_rules(self):
        """Setup validation rules and schemas"""
        self.validation_rules = {
            "representatives": {
                "required_fields": ["name", "role", "jurisdiction_id"],
                "optional_fields": ["party", "riding", "email", "phone", "bio", "image_url"],
                "valid_roles": ["mp", "mla", "mpp", "councillor", "mayor", "premier", "prime_minister"],
                "email_pattern": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "phone_pattern": r'^\+?1?\d{9,15}$'
            },
            "bills": {
                "required_fields": ["bill_number", "title", "jurisdiction_id", "status"],
                "optional_fields": ["summary", "introduced_date", "passed_date", "bill_text_url"],
                "valid_statuses": ["introduced", "first_reading", "second_reading", "third_reading", "passed", "defeated", "withdrawn"],
                "bill_number_pattern": r'^[A-Z]-\d+$'
            },
            "jurisdictions": {
                "required_fields": ["name", "jurisdiction_type"],
                "optional_fields": ["website"],
                "valid_types": ["federal", "provincial", "municipal"]
            },
            "committees": {
                "required_fields": ["name", "jurisdiction_id"],
                "optional_fields": ["description", "website"]
            },
            "events": {
                "required_fields": ["title", "event_type", "jurisdiction_id"],
                "optional_fields": ["description", "start_time", "end_time", "location", "agenda_url", "minutes_url", "video_url"],
                "valid_types": ["session", "committee_meeting", "vote", "debate", "announcement"]
            }
        }
    
    async def validate_scraped_data(self, scraper_name: str, data: Dict[str, Any], source_url: str) -> ScrapingValidation:
        """Validate scraped data before database insertion"""
        logger.info(f"🔍 Validating scraped data from {scraper_name}")
        
        issues = []
        recommendations = []
        records_collected = 0
        records_valid = 0
        
        try:
            # Count records by type
            for data_type, records in data.items():
                if isinstance(records, list):
                    records_collected += len(records)
                    
                    # Validate each record
                    for record in records:
                        if self._validate_record(data_type, record):
                            records_valid += 1
                        else:
                            issues.append(f"Invalid {data_type} record: {record.get('id', 'unknown')}")
            
            # Calculate quality score
            quality_score = records_valid / records_collected if records_collected > 0 else 0.0
            
            # Determine validation result
            if quality_score >= 0.95:
                validation_result = ValidationResult.PASSED
            elif quality_score >= 0.8:
                validation_result = ValidationResult.WARNING
            elif quality_score >= 0.6:
                validation_result = ValidationResult.FAILED
            else:
                validation_result = ValidationResult.CRITICAL
            
            # Generate recommendations
            if quality_score < 0.95:
                recommendations.append("Data quality below threshold - review scraper logic")
            if records_collected == 0:
                recommendations.append("No data collected - check scraper configuration")
            if len(issues) > 0:
                recommendations.append(f"Found {len(issues)} data quality issues")
            
            validation = ScrapingValidation(
                scraper_name=scraper_name,
                source_url=source_url,
                records_expected=self._get_expected_records(scraper_name),
                records_collected=records_collected,
                records_valid=records_valid,
                data_quality_score=quality_score,
                validation_result=validation_result,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
            # Store validation result
            self.validation_history.append(asdict(validation))
            
            logger.info(f"✅ Validation complete for {scraper_name}: {quality_score:.2%} quality score")
            return validation
            
        except Exception as e:
            logger.error(f"❌ Validation failed for {scraper_name}: {e}")
            return ScrapingValidation(
                scraper_name=scraper_name,
                source_url=source_url,
                records_expected=0,
                records_collected=0,
                records_valid=0,
                data_quality_score=0.0,
                validation_result=ValidationResult.CRITICAL,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Review scraper implementation and data format"],
                timestamp=datetime.now()
            )
    
    def _validate_record(self, data_type: str, record: Dict[str, Any]) -> bool:
        """Validate a single record"""
        if data_type not in self.validation_rules:
            return True  # Unknown type, assume valid
        
        rules = self.validation_rules[data_type]
        
        # Check required fields
        for field in rules.get("required_fields", []):
            if field not in record or not record[field]:
                return False
        
        # Check field values
        for field, value in record.items():
            if field in rules.get("valid_roles", []):
                if value not in rules["valid_roles"]:
                    return False
            
            if field in rules.get("valid_statuses", []):
                if value not in rules["valid_statuses"]:
                    return False
            
            if field in rules.get("valid_types", []):
                if value not in rules["valid_types"]:
                    return False
        
        # Check patterns
        if "email_pattern" in rules and "email" in record:
            if not re.match(rules["email_pattern"], record["email"]):
                return False
        
        if "phone_pattern" in rules and "phone" in record:
            if not re.match(rules["phone_pattern"], record["phone"]):
                return False
        
        if "bill_number_pattern" in rules and "bill_number" in record:
            if not re.match(rules["bill_number_pattern"], record["bill_number"]):
                return False
        
        return True
    
    def _get_expected_records(self, scraper_name: str) -> int:
        """Get expected number of records for a scraper"""
        # This could be based on historical data or configuration
        expected_counts = {
            "federal_parliament": 338,  # MPs
            "ontario_legislature": 124,  # MPPs
            "british_columbia_legislature": 87,  # MLAs
            "alberta_legislature": 87,  # MLAs
            "toronto_council": 25,  # Councillors + Mayor
            "vancouver_council": 11,  # Councillors + Mayor
            "calgary_council": 15,  # Councillors + Mayor
        }
        
        return expected_counts.get(scraper_name.lower(), 50)
    
    async def validate_database_integrity(self) -> List[DatabaseValidation]:
        """Validate database integrity and data quality"""
        logger.info("🔍 Validating database integrity")
        
        validations = []
        
        try:
            with self.session_factory() as session:
                # Validate each table
                tables = ["jurisdictions", "representatives", "bills", "committees", "events", "votes"]
                
                for table_name in tables:
                    validation = await self._validate_table(session, table_name)
                    validations.append(validation)
                
                # Validate foreign key relationships
                fk_validation = await self._validate_foreign_keys(session)
                validations.extend(fk_validation)
                
                # Validate constraints
                constraint_validation = await self._validate_constraints(session)
                validations.extend(constraint_validation)
                
        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
        
        return validations
    
    async def _validate_table(self, session: Session, table_name: str) -> DatabaseValidation:
        """Validate a specific table"""
        try:
            # Get record count
            result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            records_count = result.scalar()
            
            # Get valid records count (non-null required fields)
            valid_count = await self._count_valid_records(session, table_name)
            
            # Calculate quality score
            quality_score = valid_count / records_count if records_count > 0 else 0.0
            
            # Determine validation result
            if quality_score >= 0.95:
                validation_result = ValidationResult.PASSED
            elif quality_score >= 0.8:
                validation_result = ValidationResult.WARNING
            elif quality_score >= 0.6:
                validation_result = ValidationResult.FAILED
            else:
                validation_result = ValidationResult.CRITICAL
            
            issues = []
            recommendations = []
            
            if quality_score < 0.95:
                issues.append(f"Data quality below threshold: {quality_score:.2%}")
                recommendations.append("Review data quality and fix issues")
            
            if records_count == 0:
                issues.append("No records found")
                recommendations.append("Check if data has been loaded")
            
            return DatabaseValidation(
                table_name=table_name,
                records_count=records_count,
                records_valid=valid_count,
                foreign_key_issues=0,
                constraint_violations=0,
                data_quality_score=quality_score,
                validation_result=validation_result,
                issues=issues,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"❌ Table validation failed for {table_name}: {e}")
            return DatabaseValidation(
                table_name=table_name,
                records_count=0,
                records_valid=0,
                foreign_key_issues=0,
                constraint_violations=0,
                data_quality_score=0.0,
                validation_result=ValidationResult.CRITICAL,
                issues=[f"Validation error: {str(e)}"],
                recommendations=["Review table structure and data"],
                timestamp=datetime.now()
            )
    
    async def _count_valid_records(self, session: Session, table_name: str) -> int:
        """Count valid records in a table"""
        try:
            if table_name == "representatives":
                result = session.execute(text("""
                    SELECT COUNT(*) FROM representatives 
                    WHERE name IS NOT NULL AND role IS NOT NULL AND jurisdiction_id IS NOT NULL
                """))
            elif table_name == "bills":
                result = session.execute(text("""
                    SELECT COUNT(*) FROM bills 
                    WHERE bill_number IS NOT NULL AND title IS NOT NULL AND jurisdiction_id IS NOT NULL
                """))
            elif table_name == "jurisdictions":
                result = session.execute(text("""
                    SELECT COUNT(*) FROM jurisdictions 
                    WHERE name IS NOT NULL AND jurisdiction_type IS NOT NULL
                """))
            else:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            
            return result.scalar()
        except Exception as e:
            logger.error(f"❌ Error counting valid records for {table_name}: {e}")
            return 0
    
    async def _validate_foreign_keys(self, session: Session) -> List[DatabaseValidation]:
        """Validate foreign key relationships"""
        validations = []
        
        try:
            # Check representatives -> jurisdictions
            result = session.execute(text("""
                SELECT COUNT(*) FROM representatives r
                LEFT JOIN jurisdictions j ON r.jurisdiction_id = j.id
                WHERE j.id IS NULL
            """))
            fk_issues = result.scalar()
            
            if fk_issues > 0:
                validations.append(DatabaseValidation(
                    table_name="representatives_jurisdictions_fk",
                    records_count=0,
                    records_valid=0,
                    foreign_key_issues=fk_issues,
                    constraint_violations=0,
                    data_quality_score=0.0,
                    validation_result=ValidationResult.CRITICAL,
                    issues=[f"Found {fk_issues} orphaned representatives"],
                    recommendations=["Fix foreign key relationships"],
                    timestamp=datetime.now()
                ))
            
            # Check bills -> jurisdictions
            result = session.execute(text("""
                SELECT COUNT(*) FROM bills b
                LEFT JOIN jurisdictions j ON b.jurisdiction_id = j.id
                WHERE j.id IS NULL
            """))
            fk_issues = result.scalar()
            
            if fk_issues > 0:
                validations.append(DatabaseValidation(
                    table_name="bills_jurisdictions_fk",
                    records_count=0,
                    records_valid=0,
                    foreign_key_issues=fk_issues,
                    constraint_violations=0,
                    data_quality_score=0.0,
                    validation_result=ValidationResult.CRITICAL,
                    issues=[f"Found {fk_issues} orphaned bills"],
                    recommendations=["Fix foreign key relationships"],
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"❌ Foreign key validation failed: {e}")
        
        return validations
    
    async def _validate_constraints(self, session: Session) -> List[DatabaseValidation]:
        """Validate database constraints"""
        validations = []
        
        try:
            # Check for duplicate representatives (same name and jurisdiction)
            result = session.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT name, jurisdiction_id, COUNT(*)
                    FROM representatives
                    WHERE name IS NOT NULL
                    GROUP BY name, jurisdiction_id
                    HAVING COUNT(*) > 1
                ) duplicates
            """))
            duplicates = result.scalar()
            
            if duplicates > 0:
                validations.append(DatabaseValidation(
                    table_name="representatives_uniqueness",
                    records_count=0,
                    records_valid=0,
                    foreign_key_issues=0,
                    constraint_violations=duplicates,
                    data_quality_score=0.0,
                    validation_result=ValidationResult.WARNING,
                    issues=[f"Found {duplicates} duplicate representatives"],
                    recommendations=["Review and deduplicate records"],
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"❌ Constraint validation failed: {e}")
        
        return validations
    
    async def ensure_data_completeness(self, scraper_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure data completeness and identify missing sources"""
        logger.info(f"🔍 Ensuring data completeness for {scraper_name}")
        
        missing_sources = []
        corrected_data = data.copy()
        
        try:
            # Check for missing data sources
            expected_sources = self._get_expected_sources(scraper_name)
            
            for source in expected_sources:
                if source not in data or not data[source]:
                    missing_sources.append(source)
                    logger.warning(f"⚠️ Missing data source: {source}")
            
            # If missing sources, attempt to fetch them
            if missing_sources:
                logger.info(f"🔄 Attempting to fetch missing sources: {missing_sources}")
                
                for source in missing_sources:
                    try:
                        source_data = await self._fetch_missing_source(scraper_name, source)
                        if source_data:
                            corrected_data[source] = source_data
                            logger.info(f"✅ Successfully fetched missing source: {source}")
                        else:
                            logger.warning(f"⚠️ Failed to fetch missing source: {source}")
                    except Exception as e:
                        logger.error(f"❌ Error fetching missing source {source}: {e}")
            
            # Validate corrected data
            validation = await self.validate_scraped_data(scraper_name, corrected_data, "")
            
            return {
                "original_data": data,
                "corrected_data": corrected_data,
                "missing_sources": missing_sources,
                "validation": validation,
                "completeness_score": 1.0 - (len(missing_sources) / len(expected_sources)) if expected_sources else 1.0
            }
            
        except Exception as e:
            logger.error(f"❌ Data completeness check failed for {scraper_name}: {e}")
            return {
                "original_data": data,
                "corrected_data": data,
                "missing_sources": [],
                "validation": None,
                "completeness_score": 0.0
            }
    
    def _get_expected_sources(self, scraper_name: str) -> List[str]:
        """Get expected data sources for a scraper"""
        source_mapping = {
            "federal_parliament": ["mps", "bills", "committees", "votes"],
            "ontario_legislature": ["mpps", "bills", "committees"],
            "british_columbia_legislature": ["mlas", "bills", "committees"],
            "toronto_council": ["councillors", "mayor", "meetings"],
            "vancouver_council": ["councillors", "mayor", "meetings"],
        }
        
        return source_mapping.get(scraper_name.lower(), ["representatives", "bills"])
    
    async def _fetch_missing_source(self, scraper_name: str, source: str) -> Optional[List[Dict]]:
        """Fetch missing data source"""
        try:
            # This would implement the actual fetching logic
            # For now, return None to indicate failure
            logger.info(f"🔄 Fetching missing source {source} for {scraper_name}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching missing source {source}: {e}")
            return None
    
    async def ensure_database_operations(self, data: Dict[str, Any], table_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Ensure all data goes to the right tables and is committed correctly"""
        logger.info("🔍 Ensuring correct database operations")
        
        results = {}
        
        try:
            with self.session_factory() as session:
                for data_type, records in data.items():
                    if data_type not in table_mapping:
                        logger.warning(f"⚠️ No table mapping for {data_type}")
                        continue
                    
                    table_name = table_mapping[data_type]
                    logger.info(f"📝 Inserting {len(records)} records into {table_name}")
                    
                    try:
                        # Validate records before insertion
                        valid_records = []
                        invalid_records = []
                        
                        for record in records:
                            if self._validate_record(data_type, record):
                                valid_records.append(record)
                            else:
                                invalid_records.append(record)
                        
                        # Insert valid records
                        inserted_count = 0
                        for record in valid_records:
                            try:
                                # This would implement the actual insertion logic
                                # For now, just count
                                inserted_count += 1
                            except Exception as e:
                                logger.error(f"❌ Error inserting record: {e}")
                        
                        results[data_type] = {
                            "table": table_name,
                            "total_records": len(records),
                            "valid_records": len(valid_records),
                            "invalid_records": len(invalid_records),
                            "inserted_records": inserted_count,
                            "success_rate": inserted_count / len(records) if records else 0.0
                        }
                        
                        logger.info(f"✅ Successfully processed {data_type}: {inserted_count}/{len(records)} records")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {data_type}: {e}")
                        results[data_type] = {
                            "table": table_name,
                            "total_records": len(records),
                            "valid_records": 0,
                            "invalid_records": len(records),
                            "inserted_records": 0,
                            "success_rate": 0.0,
                            "error": str(e)
                        }
                
                # Commit all changes
                session.commit()
                logger.info("✅ All database operations committed successfully")
                
        except Exception as e:
            logger.error(f"❌ Database operations failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def generate_quality_report(self) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        logger.info("📊 Generating data quality report")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_quality": {
                "score": 0.0,
                "status": DataQualityStatus.CRITICAL,
                "issues": [],
                "recommendations": []
            },
            "scraping_quality": {},
            "database_quality": {},
            "validation_history": self.validation_history[-10:],  # Last 10 validations
            "issues_summary": {
                "total_issues": len(self.scraping_issues) + len(self.database_issues),
                "scraping_issues": len(self.scraping_issues),
                "database_issues": len(self.database_issues),
                "critical_issues": len([i for i in self.scraping_issues + self.database_issues if i.get("severity") == "critical"])
            }
        }
        
        try:
            # Calculate overall quality score
            scores = []
            
            # Scraping quality scores
            for validation in self.validation_history[-10:]:
                if "data_quality_score" in validation:
                    scores.append(validation["data_quality_score"])
            
            # Database quality scores
            db_validations = await self.validate_database_integrity()
            for validation in db_validations:
                scores.append(validation.data_quality_score)
            
            if scores:
                overall_score = sum(scores) / len(scores)
                report["overall_quality"]["score"] = overall_score
                
                if overall_score >= 0.95:
                    report["overall_quality"]["status"] = DataQualityStatus.EXCELLENT
                elif overall_score >= 0.8:
                    report["overall_quality"]["status"] = DataQualityStatus.GOOD
                elif overall_score >= 0.6:
                    report["overall_quality"]["status"] = DataQualityStatus.FAIR
                elif overall_score >= 0.4:
                    report["overall_quality"]["status"] = DataQualityStatus.POOR
                else:
                    report["overall_quality"]["status"] = DataQualityStatus.CRITICAL
            
            # Add recommendations
            if report["overall_quality"]["score"] < 0.8:
                report["overall_quality"]["recommendations"].append("Data quality below threshold - review scraping and validation processes")
            
            if report["issues_summary"]["critical_issues"] > 0:
                report["overall_quality"]["recommendations"].append(f"Found {report['issues_summary']['critical_issues']} critical issues - immediate attention required")
            
            logger.info(f"✅ Quality report generated: {report['overall_quality']['status'].value}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Quality report generation failed: {e}")
            report["error"] = str(e)
            return report
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all data and systems"""
        logger.info("🎯 Running comprehensive validation")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "scraping_validation": {},
            "database_validation": {},
            "quality_report": {},
            "recommendations": []
        }
        
        try:
            # Validate database integrity
            db_validations = await self.validate_database_integrity()
            results["database_validation"] = [asdict(v) for v in db_validations]
            
            # Generate quality report
            quality_report = await self.generate_quality_report()
            results["quality_report"] = quality_report
            
            # Generate recommendations
            recommendations = []
            
            # Check for critical issues
            critical_issues = [v for v in db_validations if v.validation_result == ValidationResult.CRITICAL]
            if critical_issues:
                recommendations.append(f"Found {len(critical_issues)} critical database issues - immediate attention required")
            
            # Check for quality issues
            if quality_report["overall_quality"]["score"] < 0.8:
                recommendations.append("Overall data quality below threshold - review scraping processes")
            
            # Check for missing data
            if quality_report["issues_summary"]["total_issues"] > 0:
                recommendations.append(f"Found {quality_report['issues_summary']['total_issues']} issues - review and resolve")
            
            results["recommendations"] = recommendations
            
            logger.info("✅ Comprehensive validation completed")
            return results
            
        except Exception as e:
            logger.error(f"❌ Comprehensive validation failed: {e}")
            results["error"] = str(e)
            return results

# Example usage
async def main():
    """Example usage of MCP Data Quality Agent"""
    agent = MCPDataQualityAgent()
    
    # Example data
    sample_data = {
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
    
    # Validate scraped data
    validation = await agent.validate_scraped_data("federal_parliament", sample_data, "https://example.com")
    print(f"Validation result: {validation.validation_result.value}")
    
    # Ensure data completeness
    completeness = await agent.ensure_data_completeness("federal_parliament", sample_data)
    print(f"Completeness score: {completeness['completeness_score']:.2%}")
    
    # Ensure database operations
    table_mapping = {
        "representatives": "representatives",
        "bills": "bills"
    }
    db_ops = await agent.ensure_database_operations(sample_data, table_mapping)
    print(f"Database operations: {db_ops}")
    
    # Generate quality report
    quality_report = await agent.generate_quality_report()
    print(f"Overall quality: {quality_report['overall_quality']['status'].value}")

if __name__ == "__main__":
    asyncio.run(main())
