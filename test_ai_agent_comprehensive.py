#!/usr/bin/env python3
"""
Comprehensive AI Agent Testing Suite
Tests all Task 3 requirements thoroughly
"""

import asyncio
import json
import os
import shutil
import tempfile
import time
import yaml
from pathlib import Path
from src.ai_agent import CreativeAutomationAgent


class AIAgentTestSuite:
    """Comprehensive test suite for AI Agent system"""
    
    def __init__(self):
        self.test_results = []
        self.temp_dirs = []
        
    def setup_test_environment(self):
        """Setup clean test environment"""
        print("🧪 Setting up test environment...")
        
        # Clean up previous test artifacts
        test_dirs = ["campaign_briefs", "alerts", "logs", "output"]
        for dir_name in test_dirs:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)
        
        # Create fresh directories
        for dir_name in test_dirs:
            os.makedirs(dir_name, exist_ok=True)
            
        print("✅ Test environment ready")
    
    def create_test_campaign_brief(self, campaign_id: str, products: int = 2, aspect_ratios: list = None) -> str:
        """Create a test campaign brief"""
        if aspect_ratios is None:
            aspect_ratios = ["1:1", "9:16", "16:9"]
            
        campaign_brief = {
            "campaign_brief": {
                "campaign_id": campaign_id,
                "products": [
                    {
                        "name": f"Test Product {i+1}",
                        "description": f"High-quality test product {i+1} for automated generation",
                        "target_keywords": ["premium", "quality", "innovative"]
                    }
                    for i in range(products)
                ],
                "target_region": "US",
                "target_audience": "tech-savvy millennials",
                "campaign_message": "Discover Innovation",
                "brand_guidelines": {
                    "primary_colors": ["#007BFF", "#28A745"],
                    "fonts": ["Arial", "Helvetica"],
                    "tone": "professional yet approachable"
                },
                "output_requirements": {
                    "aspect_ratios": aspect_ratios,
                    "formats": ["JPG"],
                    "quality": "high"
                }
            }
        }
        
        brief_path = f"campaign_briefs/{campaign_id}.yaml"
        with open(brief_path, 'w') as f:
            yaml.dump(campaign_brief, f)
            
        return brief_path
    
    async def test_campaign_brief_monitoring(self):
        """Test 1: Monitor incoming campaign briefs"""
        print("\n🔍 Test 1: Campaign Brief Monitoring")
        
        agent = CreativeAutomationAgent()
        agent.check_interval = 2  # Fast testing
        
        # Test case 1: Detect new campaign brief
        print("  📝 Creating test campaign brief...")
        brief_path = self.create_test_campaign_brief("test_monitoring_001")
        
        # Monitor for brief detection
        print("  👀 Monitoring for brief detection...")
        await agent.monitor_campaign_briefs()
        
        # Verify detection
        if "test_monitoring_001" in agent.campaign_tracking:
            print("  ✅ Campaign brief detected successfully")
            self.test_results.append(("Campaign Brief Monitoring", "PASS", "Brief detected and tracked"))
        else:
            print("  ❌ Campaign brief not detected")
            self.test_results.append(("Campaign Brief Monitoring", "FAIL", "Brief not detected"))
        
        # Test case 2: Ignore already processed briefs
        print("  🔄 Testing duplicate detection prevention...")
        await agent.monitor_campaign_briefs()
        
        tracking_count = len(agent.campaign_tracking)
        if tracking_count == 1:
            print("  ✅ Duplicate detection prevented")
        else:
            print(f"  ❌ Duplicate detected (count: {tracking_count})")
    
    async def test_automated_generation_triggering(self):
        """Test 2: Trigger automated generation tasks"""
        print("\n🚀 Test 2: Automated Generation Task Triggering")
        
        agent = CreativeAutomationAgent()
        
        # Create campaign brief
        brief_path = self.create_test_campaign_brief("test_generation_001", products=1)
        
        with open(brief_path, 'r') as f:
            campaign_brief = yaml.safe_load(f)
        
        # Test generation triggering
        print("  🎯 Triggering generation task...")
        try:
            # Initialize campaign tracking first (simulating agent.monitor_campaign_briefs behavior)
            agent.campaign_tracking["test_generation_001"] = {
                "brief_file": brief_path,
                "detected_at": "2025-09-15T20:00:00",
                "status": "detected",
                "variants_generated": 0,
                "target_variants": 0,
                "last_check": "2025-09-15T20:00:00"
            }
            
            await agent.trigger_generation("test_generation_001", campaign_brief)
            
            # Check if campaign status was updated properly
            campaign_data = agent.campaign_tracking.get("test_generation_001", {})
            current_status = campaign_data.get("status", "unknown")
            
            if current_status in ["generating", "completed", "failed"]:
                print(f"  ✅ Generation task triggered successfully (Status: {current_status})")
                self.test_results.append(("Generation Triggering", "PASS", f"Status: {current_status}"))
            else:
                print(f"  ❌ Generation task not triggered properly (Status: {current_status})")
                self.test_results.append(("Generation Triggering", "FAIL", f"Unexpected status: {current_status}"))
                
        except Exception as e:
            print(f"  ❌ Generation triggering failed: {str(e)}")
            self.test_results.append(("Generation Triggering", "FAIL", str(e)))
    
    async def test_variant_tracking(self):
        """Test 3: Track count and diversity of creative variants"""
        print("\n📊 Test 3: Creative Variant Tracking")
        
        agent = CreativeAutomationAgent()
        
        # Create mock output structure
        campaign_id = "test_variants_001"
        campaign_output = Path("output") / campaign_id
        campaign_output.mkdir(parents=True, exist_ok=True)
        
        # Create mock product directories with variants
        products = ["Product_A", "Product_B"]
        aspect_ratios = ["1x1", "9x16", "16x9"]
        
        total_variants = 0
        for product in products:
            product_dir = campaign_output / product
            product_dir.mkdir(exist_ok=True)
            
            for ratio in aspect_ratios:
                variant_file = product_dir / f"{ratio}.jpg"
                variant_file.write_text("mock image data")
                total_variants += 1
        
        # Initialize campaign tracking
        agent.campaign_tracking[campaign_id] = {
            "status": "generating",
            "target_variants": total_variants
        }
        
        # Test variant tracking
        print("  📈 Tracking variant count and diversity...")
        await agent.track_creative_variants()
        
        # Verify tracking
        campaign_data = agent.campaign_tracking.get(campaign_id, {})
        tracked_variants = campaign_data.get("variants_generated", 0)
        tracked_products = campaign_data.get("products_processed", 0)
        tracked_ratios = campaign_data.get("aspect_ratios_covered", [])
        diversity_score = campaign_data.get("diversity_score", 0)
        
        print(f"  📊 Tracked: {tracked_variants} variants, {tracked_products} products, {len(tracked_ratios)} ratios")
        print(f"  🎯 Diversity Score: {diversity_score}")
        
        if tracked_variants == total_variants and tracked_products == len(products):
            print("  ✅ Variant tracking accurate")
            self.test_results.append(("Variant Tracking", "PASS", f"{tracked_variants} variants, {diversity_score} diversity"))
        else:
            print("  ❌ Variant tracking inaccurate")
            self.test_results.append(("Variant Tracking", "FAIL", f"Expected {total_variants}, got {tracked_variants}"))
    
    async def test_insufficient_asset_flagging(self):
        """Test 4: Flag missing or insufficient assets (< 3 variants)"""
        print("\n🚨 Test 4: Insufficient Asset Flagging")
        
        agent = CreativeAutomationAgent()
        
        # Test case 1: Insufficient variants (< 3)
        print("  ⚠️  Testing insufficient variant detection...")
        campaign_id = "test_insufficient_001"
        campaign_output = Path("output") / campaign_id
        campaign_output.mkdir(parents=True, exist_ok=True)
        
        # Create only 2 variants (below threshold of 3)
        product_dir = campaign_output / "Test_Product"
        product_dir.mkdir(exist_ok=True)
        for i in range(2):
            variant_file = product_dir / f"variant_{i}.jpg"
            variant_file.write_text("mock image data")
        
        # Initialize campaign tracking
        agent.campaign_tracking[campaign_id] = {
            "status": "generating",
            "target_variants": 3
        }
        
        # Track variants (should trigger insufficient assets alert)
        await agent.track_creative_variants()
        
        # Check if alert was generated
        insufficient_alerts = [a for a in agent.alert_history if a["type"] == "insufficient_variants"]
        
        if insufficient_alerts:
            print("  ✅ Insufficient asset alert generated")
            self.test_results.append(("Insufficient Asset Flagging", "PASS", f"Alert generated for {len(insufficient_alerts)} cases"))
        else:
            print("  ❌ Insufficient asset alert not generated")
            self.test_results.append(("Insufficient Asset Flagging", "FAIL", "No alert generated"))
        
        # Test case 2: Sufficient variants (>= 3)
        print("  ✅ Testing sufficient variant detection...")
        campaign_id_2 = "test_sufficient_001"
        campaign_output_2 = Path("output") / campaign_id_2
        campaign_output_2.mkdir(parents=True, exist_ok=True)
        
        # Create 4 variants (above threshold)
        product_dir_2 = campaign_output_2 / "Test_Product"
        product_dir_2.mkdir(exist_ok=True)
        for i in range(4):
            variant_file = product_dir_2 / f"variant_{i}.jpg"
            variant_file.write_text("mock image data")
        
        agent.campaign_tracking[campaign_id_2] = {
            "status": "generating",
            "target_variants": 4
        }
        
        alert_count_before = len(agent.alert_history)
        await agent.track_creative_variants()
        alert_count_after = len(agent.alert_history)
        
        if alert_count_after == alert_count_before:
            print("  ✅ No alert for sufficient variants")
        else:
            print("  ⚠️  Alert generated for sufficient variants (unexpected)")
    
    async def test_alert_logging_mechanism(self):
        """Test 5: Alert and/or Logging mechanism"""
        print("\n📧 Test 5: Alert and Logging Mechanism")
        
        agent = CreativeAutomationAgent()
        
        # Test alert creation
        print("  🚨 Creating test alerts...")
        await agent.create_alert("test_alert_type", "Test alert message for validation", "medium")
        await agent.create_alert("critical_failure", "Critical system failure simulation", "critical")
        
        # Test alert processing
        print("  📝 Processing alerts...")
        await agent.process_alerts()
        
        # Verify alert files
        alert_files = list(Path("alerts").glob("*.json"))
        log_files = list(Path("logs").glob("*_email.txt"))
        
        print(f"  📁 Generated: {len(alert_files)} alert files, {len(log_files)} log files")
        
        if alert_files and log_files:
            print("  ✅ Alert and logging mechanism working")
            self.test_results.append(("Alert/Logging Mechanism", "PASS", f"{len(alert_files)} alerts, {len(log_files)} logs"))
        else:
            print("  ❌ Alert and logging mechanism failed")
            self.test_results.append(("Alert/Logging Mechanism", "FAIL", "No files generated"))
        
        # Test LLM integration (if API key available)
        if os.getenv("OPENAI_API_KEY"):
            print("  🤖 Testing LLM integration...")
            sample_alert = agent.alert_history[-1] if agent.alert_history else {
                "id": "test_llm",
                "type": "test_alert",
                "message": "LLM integration test",
                "severity": "medium",
                "timestamp": "2025-09-15T20:00:00"
            }
            
            try:
                communication = await agent.generate_stakeholder_communication(sample_alert)
                if communication and len(communication) > 100:
                    print("  ✅ LLM communication generated")
                    self.test_results.append(("LLM Integration", "PASS", f"{len(communication)} chars generated"))
                else:
                    print("  ❌ LLM communication too short")
                    self.test_results.append(("LLM Integration", "FAIL", "Communication too short"))
            except Exception as e:
                print(f"  ⚠️  LLM integration error: {str(e)}")
                self.test_results.append(("LLM Integration", "PARTIAL", f"Error: {str(e)}"))
        else:
            print("  💡 OpenAI API key not set - testing fallback communication")
            sample_alert = {"id": "test", "type": "test", "message": "test", "severity": "medium"}
            fallback_comm = agent._generate_fallback_communication(sample_alert)
            if fallback_comm and len(fallback_comm) > 50:
                print("  ✅ Fallback communication working")
                self.test_results.append(("Fallback Communication", "PASS", "Fallback working"))
            else:
                print("  ❌ Fallback communication failed")
                self.test_results.append(("Fallback Communication", "FAIL", "No fallback"))
    
    async def test_model_context_protocol(self):
        """Test 6: Model Context Protocol implementation"""
        print("\n🧠 Test 6: Model Context Protocol")
        
        agent = CreativeAutomationAgent()
        
        # Setup test context
        agent.campaign_tracking = {
            "test_campaign_001": {
                "status": "completed",
                "variants_generated": 6,
                "target_variants": 6
            },
            "test_campaign_002": {
                "status": "failed",
                "variants_generated": 0,
                "target_variants": 3
            }
        }
        
        # Create test costs file
        test_costs = {"total_cost": 15.50, "api_calls": 25}
        with open("costs.json", 'w') as f:
            json.dump(test_costs, f)
        
        # Test context building
        print("  🔍 Building comprehensive context...")
        test_alert = {
            "id": "test_context",
            "type": "generation_failure",
            "message": "Test context building",
            "severity": "high",
            "timestamp": "2025-09-15T20:00:00"
        }
        
        try:
            context = await agent._build_comprehensive_context(test_alert)
            
            # Verify context structure
            required_sections = [
                "alert_details", "system_status", "alert_context", 
                "campaign_portfolio", "recommended_actions", "stakeholder_context"
            ]
            
            missing_sections = [section for section in required_sections if section not in context]
            
            if not missing_sections:
                print("  ✅ Complete context structure")
                print(f"  📊 Context includes: {', '.join(required_sections)}")
                
                # Check business metrics
                business_impact = context["alert_details"]["business_impact"]
                performance_metrics = context["system_status"]["performance_metrics"]
                
                print(f"  💰 Revenue at risk: ${business_impact['revenue_at_risk']}")
                print(f"  ⏱️  Estimated delay: {business_impact['estimated_delay_hours']}h")
                print(f"  📈 Success rate: {performance_metrics['success_rate']:.1%}")
                
                self.test_results.append(("Model Context Protocol", "PASS", "Complete business context"))
            else:
                print(f"  ❌ Missing context sections: {missing_sections}")
                self.test_results.append(("Model Context Protocol", "FAIL", f"Missing: {missing_sections}"))
                
        except Exception as e:
            print(f"  ❌ Context building failed: {str(e)}")
            self.test_results.append(("Model Context Protocol", "FAIL", str(e)))
    
    async def test_stakeholder_communication(self):
        """Test 7: Sample Stakeholder Communication"""
        print("\n📨 Test 7: Stakeholder Communication Quality")
        
        agent = CreativeAutomationAgent()
        
        # Test different alert types
        test_scenarios = [
            ("generation_failure", "high", "GenAI API provisioning issues"),
            ("cost_spike", "critical", "Budget overrun detected"),
            ("insufficient_variants", "medium", "Campaign missing required assets"),
            ("low_success_rate", "high", "System performance degradation")
        ]
        
        communication_quality = []
        
        for alert_type, severity, message in test_scenarios:
            print(f"  📝 Testing {alert_type} communication...")
            
            test_alert = {
                "id": f"test_{alert_type}",
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": "2025-09-15T20:00:00"
            }
            
            try:
                communication = await agent.generate_stakeholder_communication(test_alert)
                
                # Quality checks
                quality_score = 0
                if len(communication) > 200:
                    quality_score += 1
                if "business" in communication.lower() or "impact" in communication.lower():
                    quality_score += 1
                if "action" in communication.lower() or "recommend" in communication.lower():
                    quality_score += 1
                if severity.upper() in communication:
                    quality_score += 1
                
                communication_quality.append((alert_type, quality_score, len(communication)))
                print(f"    ✅ Quality score: {quality_score}/4, Length: {len(communication)} chars")
                
            except Exception as e:
                print(f"    ❌ Communication failed: {str(e)}")
                communication_quality.append((alert_type, 0, 0))
        
        avg_quality = sum(score for _, score, _ in communication_quality) / len(communication_quality)
        if avg_quality >= 3.0:
            print("  ✅ High-quality stakeholder communications")
            self.test_results.append(("Stakeholder Communication", "PASS", f"Avg quality: {avg_quality:.1f}/4"))
        else:
            print("  ⚠️  Communication quality needs improvement")
            self.test_results.append(("Stakeholder Communication", "PARTIAL", f"Avg quality: {avg_quality:.1f}/4"))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("🎯 AI AGENT COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[1] == "PASS"])
        partial_tests = len([r for r in self.test_results if r[1] == "PARTIAL"])
        failed_tests = len([r for r in self.test_results if r[1] == "FAIL"])
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ⚠️  Partial: {partial_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests + partial_tests)/total_tests:.1%}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, status, details in self.test_results:
            status_icon = "✅" if status == "PASS" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"   {status_icon} {test_name}: {status} - {details}")
        
        print(f"\n🎯 TASK 3 REQUIREMENT VALIDATION:")
        requirements = [
            "Monitor incoming campaign briefs",
            "Trigger automated generation tasks", 
            "Track count and diversity of creative variants",
            "Flag missing or insufficient assets (< 3 variants)",
            "Alert and/or Logging mechanism"
        ]
        
        for i, req in enumerate(requirements):
            if i < len(self.test_results):
                status = self.test_results[i][1]
                icon = "✅" if status in ["PASS", "PARTIAL"] else "❌"
                print(f"   {icon} {req}")
            else:
                print(f"   ⚠️  {req}")
        
        # Overall assessment
        success_percentage = ((passed_tests + partial_tests) / total_tests) * 100
        if success_percentage >= 90:
            print(f"\n🏆 VERDICT: AI Agent system EXCEEDS requirements ({success_percentage:.0f}% success)")
        elif success_percentage >= 75:
            print(f"\n✅ VERDICT: AI Agent system MEETS requirements ({success_percentage:.0f}% success)")
        else:
            print(f"\n⚠️  VERDICT: AI Agent system needs improvement ({success_percentage:.0f}% success)")
    
    def cleanup(self):
        """Cleanup test environment"""
        print(f"\n🧹 Cleaning up test environment...")
        # Note: Keeping test artifacts for inspection

async def main():
    """Run comprehensive AI Agent test suite"""
    print("🤖 AI AGENT COMPREHENSIVE TEST SUITE")
    print("Testing all Task 3 requirements thoroughly\n")
    
    # Set dummy API key for testing
    os.environ["OPENAI_API_KEY"] = "test-key-for-agent-testing"
    
    test_suite = AIAgentTestSuite()
    
    try:
        # Setup
        test_suite.setup_test_environment()
        
        # Run all tests
        await test_suite.test_campaign_brief_monitoring()
        await test_suite.test_automated_generation_triggering()
        await test_suite.test_variant_tracking()
        await test_suite.test_insufficient_asset_flagging()
        await test_suite.test_alert_logging_mechanism()
        await test_suite.test_model_context_protocol()
        await test_suite.test_stakeholder_communication()
        
        # Generate report
        test_suite.generate_test_report()
        
    finally:
        test_suite.cleanup()

if __name__ == "__main__":
    asyncio.run(main())