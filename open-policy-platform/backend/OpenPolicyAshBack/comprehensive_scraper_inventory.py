#!/usr/bin/env python3
"""
Comprehensive Scraper Inventory System
=====================================

This script performs a complete inventory of all scrapers in the codebase,
categorizes them by type and schedule, and identifies testing gaps.

Following AI Agent Guidance System and TDD Process.
"""

import os
import sys
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# Add scrapers path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../scrapers/scrapers-ca'))

class ScraperType(Enum):
    FEDERAL = "federal"
    PROVINCIAL = "provincial"
    MUNICIPAL = "municipal"
    CIVIC = "civic"
    UPDATE = "update"
    UNKNOWN = "unknown"

class ScraperSchedule(Enum):
    ONE_TIME = "one_time"
    LONG_RUNNING = "long_running"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    UNKNOWN = "unknown"

class ScraperPriority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ScraperInfo:
    name: str
    path: str
    type: ScraperType
    schedule: ScraperSchedule
    priority: ScraperPriority
    has_people_py: bool
    has_init_py: bool
    has_requirements: bool
    estimated_size: str  # small, medium, large
    dependencies: List[str]
    last_modified: Optional[str]
    is_tested: bool = False
    test_status: str = "not_tested"
    records_collected: int = 0
    error_count: int = 0

class ComprehensiveScraperInventory:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent
        self.scrapers_path = self.base_path / "scrapers"
        self.backend_scrapers_path = self.base_path / "backend" / "scrapers"
        self.inventory: List[ScraperInfo] = []
        self.federal_scrapers: List[ScraperInfo] = []
        self.provincial_scrapers: List[ScraperInfo] = []
        self.municipal_scrapers: List[ScraperInfo] = []
        self.civic_scrapers: List[ScraperInfo] = []
        self.update_scrapers: List[ScraperInfo] = []
        
        # Currently tested scrapers (from existing framework)
        self.tested_scrapers = {
            "scrapers/openparliament",
            "scrapers/scrapers-ca/ca",
            "scrapers/scrapers-ca/ca_on",
            "scrapers/scrapers-ca/ca_bc",
            "scrapers/scrapers-ca/ca_ab",
            "scrapers/scrapers-ca/ca_sk",
            "scrapers/scrapers-ca/ca_mb",
            "scrapers/scrapers-ca/ca_ns",
            "scrapers/scrapers-ca/ca_nb",
            "scrapers/scrapers-ca/ca_pe",
            "scrapers/scrapers-ca/ca_nl",
            "scrapers/scrapers-ca/ca_nt",
            "scrapers/scrapers-ca/ca_nu",
            "scrapers/scrapers-ca/ca_yt",
            "scrapers/scrapers-ca/ca_qc",
            "scrapers/scrapers-ca/ca_on_toronto",
            "scrapers/scrapers-ca/ca_ab_calgary",
            "scrapers/scrapers-ca/ca_ab_edmonton",
            "scrapers/scrapers-ca/ca_on_mississauga",
            "scrapers/scrapers-ca/ca_on_windsor",
            "scrapers/scrapers-ca/ca_bc_surrey",
            "scrapers/scrapers-ca/ca_on_hamilton",
            "scrapers/scrapers-ca/ca_qc_quebec",
            "scrapers/scrapers-ca/ca_bc_victoria",
            "scrapers/scrapers-ca/ca_bc_abbotsford",
            "scrapers/scrapers-ca/ca_sk_regina",
            "scrapers/scrapers-ca/ca_mb_winnipeg",
            "scrapers/scrapers-ca/ca_bc_richmond",
            "scrapers/scrapers-ca/ca_qc_gatineau",
            "scrapers/scrapers-ca/ca_ab_lethbridge",
            "scrapers/scrapers-ca/ca_sk_saskatoon",
            "scrapers/scrapers-ca/ca_nb_moncton",
            "scrapers/scrapers-ca/ca_pe_charlottetown",
            "scrapers/scrapers-ca/ca_bc_burnaby",
            "scrapers/scrapers-ca/ca_ns_halifax",
            "scrapers/scrapers-ca/ca_nb_fredericton",
            "scrapers/scrapers-ca/ca_nl_st_john_s",
            "scrapers/scrapers-ca/ca_on_burlington",
            "scrapers/scrapers-ca/ca_on_brampton",
            "scrapers/scrapers-ca/ca_on_kitchener",
            "scrapers/scrapers-ca/ca_on_london",
            "scrapers/scrapers-ca/ca_on_ottawa",
            "scrapers/scrapers-ca/ca_qc_montreal",
            "scrapers/scrapers-ca/ca_on_ajax",
            "scrapers/scrapers-ca/ca_on_belleville",
            "scrapers/scrapers-ca/ca_on_brantford",
            "scrapers/scrapers-ca/ca_on_cambridge",
            "scrapers/scrapers-ca/ca_on_chatham_kent",
            "scrapers/scrapers-ca/ca_on_clarington",
            "scrapers/scrapers-ca/ca_on_caledon",
            "scrapers/scrapers-ca/ca_on_georgina",
            "scrapers/scrapers-ca/ca_on_haldimand_county",
            "scrapers/scrapers-ca/ca_on_kawartha_lakes",
            "scrapers/scrapers-ca/ca_on_king",
            "scrapers/scrapers-ca/ca_on_kingston",
            "scrapers/scrapers-ca/ca_on_lambton",
            "scrapers/scrapers-ca/ca_on_niagara_on_the_lake",
            "scrapers/scrapers-ca/ca_on_oakville",
            "scrapers/scrapers-ca/ca_on_pickering",
            "scrapers/scrapers-ca/ca_on_richmond_hill",
            "scrapers/scrapers-ca/ca_on_st_catharines",
            "scrapers/scrapers-ca/ca_on_waterloo",
            "scrapers/scrapers-ca/ca_on_waterloo_region",
            "scrapers/scrapers-ca/ca_on_welland",
            "scrapers/scrapers-ca/ca_on_whitby",
            "scrapers/scrapers-ca/ca_on_whitchurch_stouffville",
            "scrapers/scrapers-ca/ca_on_woolwich",
            "scrapers/scrapers-ca/ca_ab_grande_prairie",
            "scrapers/scrapers-ca/ca_ab_strathcona_county",
            "scrapers/scrapers-ca/ca_ab_wood_buffalo",
            "scrapers/scrapers-ca/ca_bc_coquitlam",
            "scrapers/scrapers-ca/ca_bc_kelowna",
            "scrapers/scrapers-ca/ca_bc_langley",
            "scrapers/scrapers-ca/ca_bc_langley_city",
            "scrapers/scrapers-ca/ca_bc_new_westminster",
            "scrapers/scrapers-ca/ca_bc_saanich",
            "scrapers/scrapers-ca/ca_bc_vancouver",
            "scrapers/scrapers-ca/ca_ns_cape_breton",
            "scrapers/scrapers-ca/ca_nb_saint_john",
            "scrapers/scrapers-ca/ca_pe_stratford",
            "scrapers/scrapers-ca/ca_pe_summerside",
            "scrapers/scrapers-ca/ca_qc_beaconsfield",
            "scrapers/scrapers-ca/ca_qc_dollard_des_ormeaux",
            "scrapers/scrapers-ca/ca_qc_dorval",
            "scrapers/scrapers-ca/ca_qc_laval",
            "scrapers/scrapers-ca/ca_qc_longueuil",
            "scrapers/scrapers-ca/ca_qc_mercier",
            "scrapers/scrapers-ca/ca_qc_montreal_est",
            "scrapers/scrapers-ca/ca_qc_pointe_claire",
            "scrapers/scrapers-ca/ca_qc_saguenay",
            "scrapers/scrapers-ca/ca_qc_sainte_anne_de_bellevue",
            "scrapers/scrapers-ca/ca_qc_saint_jean_sur_richelieu",
            "scrapers/scrapers-ca/ca_qc_saint_jerome",
            "scrapers/scrapers-ca/ca_qc_senneville",
            "scrapers/scrapers-ca/ca_qc_sherbrooke",
            "scrapers/scrapers-ca/ca_qc_trois_rivieres",
            "scrapers/scrapers-ca/ca_qc_westmount",
            "scrapers/scrapers-ca/ca_on_greater_sudbury",
            "scrapers/scrapers-ca/ca_on_grimsby",
            "scrapers/scrapers-ca/ca_on_huron",
            "scrapers/scrapers-ca/ca_on_lincoln",
            "scrapers/scrapers-ca/ca_on_peel",
            "backend/scrapers/federal_parliament_scraper"
        }

    def classify_scraper_type(self, path: str) -> ScraperType:
        """Classify scraper by type based on path and name."""
        path_lower = path.lower()
        
        # Federal scrapers
        if any(keyword in path_lower for keyword in ['openparliament', 'federal_parliament', 'parliament_of_canada']):
            return ScraperType.FEDERAL
        
        # Municipal scrapers (cities) - check this first
        if any(keyword in path_lower for keyword in ['ca_on_', 'ca_bc_', 'ca_ab_', 'ca_qc_', 'ca_sk_', 'ca_mb_', 'ca_ns_', 'ca_nb_', 'ca_pe_', 'ca_nl_']):
            # Check if it's a specific city (not just a province)
            if any(city in path_lower for city in ['toronto', 'vancouver', 'calgary', 'edmonton', 'montreal', 'ottawa', 'quebec', 'winnipeg', 'halifax', 'victoria', 'regina', 'saskatoon', 'fredericton', 'charlottetown', 'st_john', 'mississauga', 'brampton', 'surrey', 'hamilton', 'kitchener', 'london', 'burnaby', 'richmond', 'gatineau', 'lethbridge', 'moncton', 'charlottetown', 'fredericton']):
                return ScraperType.MUNICIPAL
        
        # Provincial scrapers (main provinces)
        if any(keyword in path_lower for keyword in ['ca_on', 'ca_bc', 'ca_ab', 'ca_qc', 'ca_sk', 'ca_mb', 'ca_ns', 'ca_nb', 'ca_pe', 'ca_nl', 'ca_nt', 'ca_nu', 'ca_yt']):
            # Check if it's a main provincial scraper (not municipal)
            if not any(city in path_lower for city in ['toronto', 'vancouver', 'calgary', 'edmonton', 'montreal', 'ottawa', 'quebec', 'winnipeg', 'halifax', 'victoria', 'regina', 'saskatoon', 'fredericton', 'charlottetown', 'st_john']):
                return ScraperType.PROVINCIAL
        
        # Civic scrapers
        if any(keyword in path_lower for keyword in ['represent', 'opennorth', 'civic']):
            return ScraperType.CIVIC
        
        # Update scrapers
        if any(keyword in path_lower for keyword in ['update', 'daily', 'weekly', 'monthly']):
            return ScraperType.UPDATE
        
        return ScraperType.UNKNOWN

    def classify_schedule(self, scraper_info: ScraperInfo) -> ScraperSchedule:
        """Classify scraper by schedule based on type and name."""
        name_lower = scraper_info.name.lower()
        path_lower = scraper_info.path.lower()
        
        # Daily scrapers (parliamentary transcripts, daily votes)
        if any(keyword in name_lower or keyword in path_lower for keyword in ['transcript', 'daily', 'vote', 'session']):
            return ScraperSchedule.DAILY
        
        # Weekly scrapers (committee reports, weekly updates)
        if any(keyword in name_lower or keyword in path_lower for keyword in ['committee', 'weekly', 'report']):
            return ScraperSchedule.WEEKLY
        
        # Monthly scrapers (budget updates, monthly reports)
        if any(keyword in name_lower or keyword in path_lower for keyword in ['budget', 'monthly', 'financial']):
            return ScraperSchedule.MONTHLY
        
        # Long-running scrapers (real-time data)
        if any(keyword in name_lower or keyword in path_lower for keyword in ['realtime', 'continuous', 'stream']):
            return ScraperSchedule.LONG_RUNNING
        
        # One-time scrapers (historical data, initial setup)
        if any(keyword in name_lower or keyword in path_lower for keyword in ['historical', 'initial', 'setup', 'migration']):
            return ScraperSchedule.ONE_TIME
        
        # Default based on type
        if scraper_info.type == ScraperType.FEDERAL:
            return ScraperSchedule.DAILY  # Federal data is usually updated daily
        elif scraper_info.type == ScraperType.PROVINCIAL:
            return ScraperSchedule.WEEKLY  # Provincial data is usually updated weekly
        elif scraper_info.type == ScraperType.MUNICIPAL:
            return ScraperSchedule.MONTHLY  # Municipal data is usually updated monthly
        
        return ScraperSchedule.UNKNOWN

    def classify_priority(self, scraper_info: ScraperInfo) -> ScraperPriority:
        """Classify scraper by priority based on type and importance."""
        if scraper_info.type == ScraperType.FEDERAL:
            return ScraperPriority.HIGH
        
        # Major cities (population > 500,000)
        major_cities = ['toronto', 'montreal', 'vancouver', 'calgary', 'edmonton', 'ottawa', 'winnipeg', 'quebec']
        if any(city in scraper_info.name.lower() for city in major_cities):
            return ScraperPriority.HIGH
        
        if scraper_info.type == ScraperType.PROVINCIAL:
            return ScraperPriority.HIGH
        
        # Medium cities (population 100,000 - 500,000)
        medium_cities = ['mississauga', 'brampton', 'surrey', 'hamilton', 'kitchener', 'london', 'victoria', 'halifax', 'regina', 'saskatoon']
        if any(city in scraper_info.name.lower() for city in medium_cities):
            return ScraperPriority.MEDIUM
        
        if scraper_info.type == ScraperType.MUNICIPAL:
            return ScraperPriority.MEDIUM
        
        return ScraperPriority.LOW

    def estimate_size(self, path: str) -> str:
        """Estimate scraper size based on file count and complexity."""
        try:
            scraper_dir = Path(path)
            if not scraper_dir.exists():
                return "unknown"
            
            # Count Python files
            py_files = list(scraper_dir.rglob("*.py"))
            
            if len(py_files) <= 2:
                return "small"
            elif len(py_files) <= 5:
                return "medium"
            else:
                return "large"
        except:
            return "unknown"

    def scan_scrapers(self):
        """Scan all scrapers in the codebase."""
        print("🔍 Scanning all scrapers in the codebase...")
        
        # Scan main scrapers directory
        if self.scrapers_path.exists():
            print(f"📁 Scanning {self.scrapers_path}")
            self.scan_directory(self.scrapers_path, "scrapers")
        
        # Scan backend scrapers directory
        if self.backend_scrapers_path.exists():
            print(f"📁 Scanning {self.backend_scrapers_path}")
            self.scan_directory(self.backend_scrapers_path, "backend/scrapers")
        
        # Direct scan of scrapers-ca city directories
        scrapers_ca_path = self.scrapers_path / "scrapers-ca"
        if scrapers_ca_path.exists():
            print(f"📁 Direct scanning of scrapers-ca city directories")
            self.scan_scrapers_ca_directly(scrapers_ca_path)
        
        print(f"✅ Found {len(self.inventory)} scrapers total")

    def scan_scrapers_ca_directly(self, scrapers_ca_path: Path):
        """Directly scan scrapers-ca for city directories."""
        for item in scrapers_ca_path.iterdir():
            if item.is_dir() and item.name.startswith('ca_') and not item.name.startswith('ca_candidates'):
                print(f"    📁 Found city directory: {item.name}")
                if self.is_scraper_directory(item):
                    print(f"      ✅ Processing city scraper: {item.name}")
                    self.process_scraper_directory(item, "scrapers/scrapers-ca")

    def scan_directory(self, directory: Path, base_prefix: str):
        """Scan a directory for scrapers."""
        print(f"  🔍 Scanning directory: {directory.name}")
        for item in directory.iterdir():
            if item.is_dir():
                print(f"    📁 Found directory: {item.name}")
                
                # Special case: scrapers-ca directory - scan all its subdirectories
                if directory.name == "scrapers-ca":
                    print(f"      🔍 Recursively scanning scrapers-ca subdirectory: {item.name}")
                    self.scan_directory(item, base_prefix)
                # Check if this is a scraper directory
                elif self.is_scraper_directory(item):
                    print(f"      ✅ Processing scraper: {item.name}")
                    self.process_scraper_directory(item, base_prefix)
                else:
                    # Recursively scan subdirectories
                    self.scan_directory(item, base_prefix)

    def is_scraper_directory(self, directory: Path) -> bool:
        """Check if a directory contains a scraper."""
        # Special case: don't treat scrapers-ca itself as a scraper
        if directory.name == "scrapers-ca":
            return False
        
        # Check for people.py (main scraper file)
        if (directory / "people.py").exists():
            return True
        
        # Check for __init__.py with scraper class
        if (directory / "__init__.py").exists():
            try:
                with open(directory / "__init__.py", 'r') as f:
                    content = f.read()
                    if any(keyword in content for keyword in ['class', 'Scraper', 'pupa']):
                        return True
            except:
                pass
        
        # Check for other Python files that might be scrapers
        py_files = list(directory.glob("*.py"))
        if len(py_files) > 0:
            return True
        
        # Special case for scrapers-ca: any directory starting with ca_ is likely a scraper
        if directory.name.startswith('ca_'):
            return True
        
        return False

    def process_scraper_directory(self, directory: Path, base_prefix: str):
        """Process a scraper directory and extract information."""
        try:
            # Get relative path
            relative_path = str(directory.relative_to(self.base_path))
            
            # Check if already tested
            is_tested = relative_path in self.tested_scrapers
            
            # Get scraper name
            name = directory.name.replace('_', ' ').title()
            
            # Check for files
            has_people_py = (directory / "people.py").exists()
            has_init_py = (directory / "__init__.py").exists()
            has_requirements = (directory / "requirements.txt").exists() or (directory / "requirements.in").exists()
            
            # Get last modified time
            try:
                last_modified = datetime.fromtimestamp(directory.stat().st_mtime).isoformat()
            except:
                last_modified = None
            
            # Create scraper info
            scraper_info = ScraperInfo(
                name=name,
                path=relative_path,
                type=ScraperType.UNKNOWN,
                schedule=ScraperSchedule.UNKNOWN,
                priority=ScraperPriority.LOW,
                has_people_py=has_people_py,
                has_init_py=has_init_py,
                has_requirements=has_requirements,
                estimated_size=self.estimate_size(str(directory)),
                dependencies=[],
                last_modified=last_modified,
                is_tested=is_tested,
                test_status="working" if is_tested else "not_tested"
            )
            
            # Classify scraper
            scraper_info.type = self.classify_scraper_type(relative_path)
            scraper_info.schedule = self.classify_schedule(scraper_info)
            scraper_info.priority = self.classify_priority(scraper_info)
            
            # Add to inventory
            self.inventory.append(scraper_info)
            
            # Categorize
            if scraper_info.type == ScraperType.FEDERAL:
                self.federal_scrapers.append(scraper_info)
            elif scraper_info.type == ScraperType.PROVINCIAL:
                self.provincial_scrapers.append(scraper_info)
            elif scraper_info.type == ScraperType.MUNICIPAL:
                self.municipal_scrapers.append(scraper_info)
            elif scraper_info.type == ScraperType.CIVIC:
                self.civic_scrapers.append(scraper_info)
            elif scraper_info.type == ScraperType.UPDATE:
                self.update_scrapers.append(scraper_info)
            
        except Exception as e:
            print(f"❌ Error processing {directory}: {e}")

    def generate_reports(self):
        """Generate comprehensive reports."""
        print("📊 Generating comprehensive reports...")
        
        # Create reports directory
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Generate summary report
        self.generate_summary_report(reports_dir)
        
        # Generate detailed CSV reports
        self.generate_csv_reports(reports_dir)
        
        # Generate JSON inventory
        self.generate_json_inventory(reports_dir)
        
        # Generate dashboard data
        self.generate_dashboard_data(reports_dir)
        
        print(f"✅ Reports generated in {reports_dir}")

    def generate_summary_report(self, reports_dir: Path):
        """Generate a summary report."""
        report_path = reports_dir / "scraper_inventory_summary.md"
        
        with open(report_path, 'w') as f:
            f.write("# 📊 COMPREHENSIVE SCRAPER INVENTORY SUMMARY\n\n")
            f.write(f"**Generated**: {datetime.now().isoformat()}\n\n")
            
            f.write("## 🎯 **EXECUTIVE SUMMARY**\n\n")
            f.write(f"- **Total Scrapers Found**: {len(self.inventory)}\n")
            f.write(f"- **Federal Scrapers**: {len(self.federal_scrapers)}\n")
            f.write(f"- **Provincial Scrapers**: {len(self.provincial_scrapers)}\n")
            f.write(f"- **Municipal Scrapers**: {len(self.municipal_scrapers)}\n")
            f.write(f"- **Civic Scrapers**: {len(self.civic_scrapers)}\n")
            f.write(f"- **Update Scrapers**: {len(self.update_scrapers)}\n")
            f.write(f"- **Currently Tested**: {len([s for s in self.inventory if s.is_tested])}\n")
            f.write(f"- **Testing Coverage**: {len([s for s in self.inventory if s.is_tested]) / len(self.inventory) * 100:.1f}%\n\n")
            
            f.write("## 📋 **DETAILED BREAKDOWN**\n\n")
            
            # Federal scrapers
            f.write("### 🏛️ **FEDERAL SCRAPERS**\n")
            for scraper in self.federal_scrapers:
                f.write(f"- **{scraper.name}** (`{scraper.path}`) - {scraper.schedule.value} - {scraper.priority.value}\n")
            f.write("\n")
            
            # Provincial scrapers
            f.write("### 🏛️ **PROVINCIAL SCRAPERS**\n")
            for scraper in self.provincial_scrapers:
                f.write(f"- **{scraper.name}** (`{scraper.path}`) - {scraper.schedule.value} - {scraper.priority.value}\n")
            f.write("\n")
            
            # Municipal scrapers (show first 20)
            f.write("### 🏙️ **MUNICIPAL SCRAPERS** (showing first 20)\n")
            for scraper in self.municipal_scrapers[:20]:
                f.write(f"- **{scraper.name}** (`{scraper.path}`) - {scraper.schedule.value} - {scraper.priority.value}\n")
            if len(self.municipal_scrapers) > 20:
                f.write(f"- ... and {len(self.municipal_scrapers) - 20} more\n")
            f.write("\n")
            
            # Civic scrapers
            f.write("### 🏛️ **CIVIC SCRAPERS**\n")
            for scraper in self.civic_scrapers:
                f.write(f"- **{scraper.name}** (`{scraper.path}`) - {scraper.schedule.value} - {scraper.priority.value}\n")
            f.write("\n")
            
            # Update scrapers
            f.write("### 🔄 **UPDATE SCRAPERS**\n")
            for scraper in self.update_scrapers:
                f.write(f"- **{scraper.name}** (`{scraper.path}`) - {scraper.schedule.value} - {scraper.priority.value}\n")
            f.write("\n")
            
            f.write("## 🚨 **CRITICAL FINDINGS**\n\n")
            f.write(f"1. **Major Testing Gap**: Only {len([s for s in self.inventory if s.is_tested])} out of {len(self.inventory)} scrapers tested!\n")
            f.write(f"2. **Municipal Coverage**: {len(self.municipal_scrapers)} municipal scrapers need testing\n")
            f.write(f"3. **Federal Coverage**: {len(self.federal_scrapers)} federal scrapers need testing\n")
            f.write(f"4. **Provincial Coverage**: {len(self.provincial_scrapers)} provincial scrapers need testing\n")
            f.write("\n")
            
            f.write("## 🎯 **NEXT STEPS**\n\n")
            f.write("1. **Expand Testing Framework** to test all scrapers\n")
            f.write("2. **Implement Parallel Testing** for 50+ scrapers simultaneously\n")
            f.write("3. **Create Monitoring System** for different schedule types\n")
            f.write("4. **Start Background Execution** of working scrapers\n")
            f.write("5. **Implement Schedule-Based Execution** (daily, weekly, monthly)\n")

    def generate_csv_reports(self, reports_dir: Path):
        """Generate CSV reports for each category."""
        # All scrapers
        with open(reports_dir / "all_scrapers.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Path', 'Type', 'Schedule', 'Priority', 'Has People.py', 'Has Init.py', 'Has Requirements', 'Size', 'Tested', 'Status'])
            for scraper in self.inventory:
                writer.writerow([
                    scraper.name,
                    scraper.path,
                    scraper.type.value,
                    scraper.schedule.value,
                    scraper.priority.value,
                    scraper.has_people_py,
                    scraper.has_init_py,
                    scraper.has_requirements,
                    scraper.estimated_size,
                    scraper.is_tested,
                    scraper.test_status
                ])
        
        # Municipal scrapers
        with open(reports_dir / "municipal_scrapers.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Name', 'Path', 'Schedule', 'Priority', 'Tested', 'Status'])
            for scraper in self.municipal_scrapers:
                writer.writerow([
                    scraper.name,
                    scraper.path,
                    scraper.schedule.value,
                    scraper.priority.value,
                    scraper.is_tested,
                    scraper.test_status
                ])

    def generate_json_inventory(self, reports_dir: Path):
        """Generate JSON inventory file."""
        # Convert enum values to strings for JSON serialization
        def convert_enum(obj):
            if isinstance(obj, (ScraperType, ScraperSchedule, ScraperPriority)):
                return obj.value
            return obj
        
        inventory_data = {
            'generated': datetime.now().isoformat(),
            'summary': {
                'total_scrapers': len(self.inventory),
                'federal_scrapers': len(self.federal_scrapers),
                'provincial_scrapers': len(self.provincial_scrapers),
                'municipal_scrapers': len(self.municipal_scrapers),
                'civic_scrapers': len(self.civic_scrapers),
                'update_scrapers': len(self.update_scrapers),
                'tested_scrapers': len([s for s in self.inventory if s.is_tested]),
                'testing_coverage': len([s for s in self.inventory if s.is_tested]) / len(self.inventory) * 100 if self.inventory else 0
            },
            'scrapers': []
        }
        
        # Convert scraper data manually to handle enums
        for scraper in self.inventory:
            scraper_dict = {
                'name': scraper.name,
                'path': scraper.path,
                'type': scraper.type.value,
                'schedule': scraper.schedule.value,
                'priority': scraper.priority.value,
                'has_people_py': scraper.has_people_py,
                'has_init_py': scraper.has_init_py,
                'has_requirements': scraper.has_requirements,
                'estimated_size': scraper.estimated_size,
                'dependencies': scraper.dependencies,
                'last_modified': scraper.last_modified,
                'is_tested': scraper.is_tested,
                'test_status': scraper.test_status,
                'records_collected': scraper.records_collected,
                'error_count': scraper.error_count
            }
            inventory_data['scrapers'].append(scraper_dict)
        
        with open(reports_dir / "scraper_inventory.json", 'w') as f:
            json.dump(inventory_data, f, indent=2)

    def generate_dashboard_data(self, reports_dir: Path):
        """Generate data for the dashboard."""
        dashboard_data = {
            'last_updated': datetime.now().isoformat(),
            'statistics': {
                'total_scrapers': len(self.inventory),
                'tested_scrapers': len([s for s in self.inventory if s.is_tested]),
                'working_scrapers': len([s for s in self.inventory if s.test_status == 'working']),
                'failed_scrapers': len([s for s in self.inventory if s.test_status == 'failed']),
                'untested_scrapers': len([s for s in self.inventory if not s.is_tested])
            },
            'categories': {
                'federal': {
                    'total': len(self.federal_scrapers),
                    'tested': len([s for s in self.federal_scrapers if s.is_tested]),
                    'working': len([s for s in self.federal_scrapers if s.test_status == 'working'])
                },
                'provincial': {
                    'total': len(self.provincial_scrapers),
                    'tested': len([s for s in self.provincial_scrapers if s.is_tested]),
                    'working': len([s for s in self.provincial_scrapers if s.test_status == 'working'])
                },
                'municipal': {
                    'total': len(self.municipal_scrapers),
                    'tested': len([s for s in self.municipal_scrapers if s.is_tested]),
                    'working': len([s for s in self.municipal_scrapers if s.test_status == 'working'])
                },
                'civic': {
                    'total': len(self.civic_scrapers),
                    'tested': len([s for s in self.civic_scrapers if s.is_tested]),
                    'working': len([s for s in self.civic_scrapers if s.test_status == 'working'])
                },
                'update': {
                    'total': len(self.update_scrapers),
                    'tested': len([s for s in self.update_scrapers if s.is_tested]),
                    'working': len([s for s in self.update_scrapers if s.test_status == 'working'])
                }
            },
            'schedules': {
                'daily': len([s for s in self.inventory if s.schedule == ScraperSchedule.DAILY]),
                'weekly': len([s for s in self.inventory if s.schedule == ScraperSchedule.WEEKLY]),
                'monthly': len([s for s in self.inventory if s.schedule == ScraperSchedule.MONTHLY]),
                'long_running': len([s for s in self.inventory if s.schedule == ScraperSchedule.LONG_RUNNING]),
                'one_time': len([s for s in self.inventory if s.schedule == ScraperSchedule.ONE_TIME])
            }
        }
        
        with open(reports_dir / "dashboard_data.json", 'w') as f:
            json.dump(dashboard_data, f, indent=2)

    def run(self):
        """Run the comprehensive inventory."""
        print("🚀 Starting Comprehensive Scraper Inventory...")
        print("=" * 60)
        
        # Scan all scrapers
        self.scan_scrapers()
        
        # Generate reports
        self.generate_reports()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 INVENTORY COMPLETE!")
        print("=" * 60)
        print(f"Total Scrapers Found: {len(self.inventory)}")
        print(f"Federal Scrapers: {len(self.federal_scrapers)}")
        print(f"Provincial Scrapers: {len(self.provincial_scrapers)}")
        print(f"Municipal Scrapers: {len(self.municipal_scrapers)}")
        print(f"Civic Scrapers: {len(self.civic_scrapers)}")
        print(f"Update Scrapers: {len(self.update_scrapers)}")
        print(f"Currently Tested: {len([s for s in self.inventory if s.is_tested])}")
        print(f"Testing Coverage: {len([s for s in self.inventory if s.is_tested]) / len(self.inventory) * 100:.1f}%")
        print("\n📁 Reports generated in: backend/OpenPolicyAshBack/reports/")
        print("📋 Check scraper_inventory_summary.md for detailed breakdown")

if __name__ == "__main__":
    inventory = ComprehensiveScraperInventory()
    inventory.run()
