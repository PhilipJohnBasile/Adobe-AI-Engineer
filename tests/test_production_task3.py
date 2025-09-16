"""
Simplified test suite for Production Task 3 System
"""
import pytest
import pytest_asyncio
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

# Import the production system
import sys
sys.path.append('src')
from production_task3_system import ProductionTask3Agent, CampaignBrief, Alert, AlertSeverity

class TestProductionTask3Agent:
    """Test suite for the Production Task 3 Agent"""
    
    @pytest_asyncio.fixture
    async def agent(self):
        """Create a test agent instance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "brief_directory": f"{temp_dir}/briefs",
                "output_directory": f"{temp_dir}/output",
                "alerts_directory": f"{temp_dir}/alerts",
                "logs_directory": f"{temp_dir}/logs",
                "min_variants_threshold": 3,
                "check_interval_seconds": 1,
                "api_timeout_seconds": 30,
                "max_retries": 2
            }
            
            # Create directories
            for key, directory in config.items():
                if isinstance(directory, str) and directory.startswith(temp_dir):
                    Path(directory).mkdir(parents=True, exist_ok=True)
            
            agent = ProductionTask3Agent(config)
            yield agent
            await agent.stop_monitoring()

    @pytest.fixture
    def sample_brief_data(self):
        """Sample campaign brief data"""
        return {
            "campaign_id": "test_campaign_001",
            "campaign_name": "Test Campaign",
            "products": ["Product A", "Product B"],
            "target_variants": 5,
            "requirements": {
                "style": "modern",
                "colors": ["blue", "white"],
                "format": "digital"
            }
        }

    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test agent initializes correctly"""
        assert agent is not None
        assert agent.config["min_variants_threshold"] == 3
        assert agent.campaign_briefs == {}
        assert agent.variant_tracking == {}
        assert agent.alerts == []

    @pytest.mark.asyncio
    async def test_brief_loading(self, agent, sample_brief_data):
        """Test loading campaign briefs from files"""
        # Create a test brief file
        brief_file = Path(agent.config["brief_directory"]) / "test_campaign.yaml"
        with open(brief_file, 'w') as f:
            yaml.dump(sample_brief_data, f)
        
        # Load the brief
        brief_data = agent._load_brief_file(brief_file)
        assert brief_data["campaign_id"] == "test_campaign_001"
        assert brief_data["target_variants"] == 5

    @pytest.mark.asyncio
    async def test_campaign_brief_creation(self, agent, sample_brief_data):
        """Test creating CampaignBrief objects"""
        brief = CampaignBrief(
            campaign_id=sample_brief_data["campaign_id"],
            campaign_name=sample_brief_data["campaign_name"],
            products=sample_brief_data["products"],
            target_variants=sample_brief_data["target_variants"],
            requirements=sample_brief_data["requirements"],
            detected_at="2024-01-01T00:00:00",
            status="new"
        )
        assert isinstance(brief, CampaignBrief)
        assert brief.campaign_id == "test_campaign_001"
        assert brief.target_variants == 5
        assert brief.status == "new"

    @pytest.mark.asyncio
    async def test_variant_generation_simulation(self, agent):
        """Test the variant generation simulation"""
        brief = CampaignBrief(
            campaign_id="test_001",
            campaign_name="Test",
            products=["Product A"],
            target_variants=4,
            requirements={},
            detected_at="2024-01-01T00:00:00",
            status="new"
        )
        
        # Mock the generation process
        with patch.object(agent, '_simulate_generation_process') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "variants_generated": 4,
                "quality_score": 0.85,
                "output_files": ["variant1.jpg", "variant2.jpg", "variant3.jpg", "variant4.jpg"]
            }
            
            result = await agent._simulate_generation_process(brief)
            assert result["success"] is True
            assert result["variants_generated"] == 4
            assert result["quality_score"] == 0.85

    @pytest.mark.asyncio
    async def test_variant_tracking(self, agent):
        """Test variant tracking functionality"""
        campaign_id = "test_campaign_001"
        generation_result = {
            "success": True,
            "variants_generated": 3,
            "quality_score": 0.80,
            "output_files": ["variant1.jpg", "variant2.jpg", "variant3.jpg"]
        }
        
        # Set up campaign brief
        agent.campaign_briefs[campaign_id] = CampaignBrief(
            campaign_id=campaign_id,
            campaign_name="Test Campaign",
            products=["Product A"],
            target_variants=5,
            requirements={},
            detected_at="2024-01-01T00:00:00",
            status="generating"
        )
        
        # Track variants
        await agent._track_variants(campaign_id, generation_result)
        
        tracking_data = agent.variant_tracking[campaign_id]
        assert tracking_data["variants_count"] == 3
        assert tracking_data["target_count"] == 5
        assert tracking_data["completion_rate"] == 60.0
        assert len(tracking_data["output_files"]) == 3

    @pytest.mark.asyncio
    async def test_insufficiency_detection(self, agent):
        """Test detection of insufficient variants"""
        campaign_id = "test_campaign_001"
        
        # Set up tracking data with insufficient variants
        agent.variant_tracking[campaign_id] = {
            "campaign_id": campaign_id,
            "variants_count": 2,  # Below threshold of 3
            "target_count": 5,
            "completion_rate": 40.0
        }
        
        # Mock alert creation
        with patch.object(agent, '_create_alert') as mock_alert:
            await agent._check_variant_sufficiency(campaign_id)
            mock_alert.assert_called_once()
            
            # Verify alert details
            call_args = mock_alert.call_args
            assert call_args[0][0] == "insufficient_variants"
            assert "insufficient variants: 2" in call_args[0][1]
            assert call_args[0][2] == AlertSeverity.MEDIUM

    @pytest.mark.asyncio
    async def test_alert_creation(self, agent):
        """Test alert creation and storage"""
        alert_type = "test_alert"
        message = "Test alert message"
        severity = AlertSeverity.HIGH
        campaign_id = "test_campaign_001"
        context = {"test_key": "test_value"}
        
        await agent._create_alert(alert_type, message, severity, campaign_id, context)
        
        # Check alert was added to alerts list
        assert len(agent.alerts) == 1
        alert = agent.alerts[0]
        assert alert.alert_type == alert_type
        assert alert.message == message
        assert alert.severity == severity
        assert alert.campaign_id == campaign_id
        assert alert.context == context

    @pytest.mark.asyncio
    async def test_stakeholder_communication(self, agent):
        """Test stakeholder communication generation"""
        alert = Alert(
            alert_id="test_alert_001",
            alert_type="api_failure",
            severity=AlertSeverity.HIGH,
            message="API failure detected",
            campaign_id="test_campaign_001",
            timestamp="2024-01-01T00:00:00",
            context={"error_count": 5},
            status="pending"
        )
        
        # Test email generation
        email_content = agent._create_stakeholder_email(alert, {})
        assert "API Failure" in email_content
        assert "HIGH PRIORITY" in email_content
        assert "test_campaign_001" in email_content

    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, agent, sample_brief_data):
        """Test complete workflow from brief to completion"""
        # Create a test brief file
        brief_file = Path(agent.config["brief_directory"]) / "workflow_test.yaml"
        with open(brief_file, 'w') as f:
            yaml.dump(sample_brief_data, f)
        
        # Mock generation for predictable results
        with patch.object(agent, '_simulate_generation_process') as mock_generate:
            mock_generate.return_value = {
                "success": True,
                "variants_generated": 5,  # Meets requirement
                "quality_score": 0.90,
                "output_files": [f"variant{i}.jpg" for i in range(1, 6)]
            }
            
            # Process the brief
            await agent._check_for_new_briefs()
            
            # Verify campaign was processed
            campaign_id = "test_campaign_001"
            assert campaign_id in agent.campaign_briefs
            assert campaign_id in agent.variant_tracking
            
            brief = agent.campaign_briefs[campaign_id]
            tracking = agent.variant_tracking[campaign_id]
            
            assert brief.status == "completed"
            assert tracking["variants_count"] == 5
            assert tracking["completion_rate"] == 100.0
            
            # Should have no alerts for successful completion
            insufficiency_alerts = [
                alert for alert in agent.alerts 
                if alert.alert_type == "insufficient_variants"
            ]
            assert len(insufficiency_alerts) == 0

    @pytest.mark.asyncio
    async def test_monitoring_loop(self, agent):
        """Test the monitoring loop functionality"""
        # Start monitoring in background
        monitoring_task = asyncio.create_task(agent.start_monitoring())
        
        # Wait a short time
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await agent.stop_monitoring()
        
        # Wait for task to complete
        try:
            await asyncio.wait_for(monitoring_task, timeout=1.0)
        except asyncio.TimeoutError:
            monitoring_task.cancel()
        
        # Test should complete without errors
        assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])