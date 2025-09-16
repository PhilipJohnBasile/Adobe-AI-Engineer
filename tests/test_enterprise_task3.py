"""
Comprehensive test suite for Enterprise Task 3 System
"""
import pytest
import pytest_asyncio
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import yaml

# Import the enterprise system
import sys
sys.path.append('src')
from enterprise_task3_system import (
    EnterpriseTask3Agent, CampaignBrief, Alert, AlertSeverity, 
    APIProvider, GenerationResult, EnhancedModelContextProtocol
)

class TestEnterpriseTask3Agent:
    """Test suite for the Enterprise Task 3 Agent"""
    
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
            for directory in config.values():
                if isinstance(directory, str) and directory.startswith(temp_dir):
                    Path(directory).mkdir(parents=True, exist_ok=True)
            
            agent = EnterpriseTask3Agent(config)
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
        brief = agent._create_campaign_brief(sample_brief_data, "test_campaign")
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
        
        # Mock the API call
        with patch.object(agent, 'generate_variants') as mock_generate:
            mock_generate.return_value = GenerationResult(
                success=True,
                variants_generated=4,
                quality_score=0.85,
                cost_estimate=0.25,
                output_files=["variant1.jpg", "variant2.jpg", "variant3.jpg", "variant4.jpg"],
                provider_used=APIProvider.OPENAI,
                processing_time=2.5,
                metadata={}
            )
            
            result = await agent.generate_variants(brief)
            assert result.success is True
            assert result.variants_generated == 4
            assert result.quality_score == 0.85

    @pytest.mark.asyncio
    async def test_variant_tracking(self, agent):
        """Test variant tracking functionality"""
        campaign_id = "test_campaign_001"
        generation_result = GenerationResult(
            success=True,
            variants_generated=3,
            quality_score=0.80,
            cost_estimate=0.30,
            output_files=["variant1.jpg", "variant2.jpg", "variant3.jpg"],
            provider_used=APIProvider.OPENAI,
            processing_time=2.0,
            metadata={}
        )
        
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
        await agent._track_variants(campaign_id, generation_result.__dict__)
        
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
    async def test_model_context_protocol(self, agent):
        """Test Model Context Protocol implementation"""
        alert = Alert(
            alert_id="test_alert_001",
            alert_type="insufficient_variants",
            severity=AlertSeverity.HIGH,
            message="Test alert message",
            campaign_id="test_campaign_001",
            timestamp="2024-01-01T00:00:00",
            context={"variants_generated": 2, "minimum_required": 3},
            status="pending"
        )
        
        system_data = {
            "active_campaigns": 5,
            "completed_campaigns": 10,
            "success_rate": 0.85,
            "avg_variants": 4.2
        }
        
        context = EnhancedModelContextProtocol.build_alert_context(alert, system_data)
        
        # Verify context structure
        assert "alert_details" in context
        assert "system_status" in context
        assert "performance_metrics" in context
        assert "business_impact" in context
        
        assert context["alert_details"]["alert_id"] == "test_alert_001"
        assert context["system_status"]["active_campaigns"] == 5
        assert context["performance_metrics"]["success_rate"] == 0.85

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
        
        system_data = {
            "active_campaigns": 3,
            "success_rate": 0.75,
            "system_health": "degraded"
        }
        
        # Mock the communication generation
        with patch.object(agent, '_generate_stakeholder_communication') as mock_comm:
            mock_comm.return_value = "Test communication generated"
            
            await agent._generate_stakeholder_communication(alert)
            mock_comm.assert_called_once_with(alert)

    @pytest.mark.asyncio
    async def test_api_failover(self, agent):
        """Test API failover functionality"""
        brief = CampaignBrief(
            campaign_id="test_001",
            campaign_name="Test",
            products=["Product A"],
            target_variants=3,
            requirements={},
            detected_at="2024-01-01T00:00:00",
            status="new"
        )
        
        # Mock primary API failure and secondary success
        with patch.object(agent, '_call_openai_api') as mock_openai, \
             patch.object(agent, '_call_stability_api') as mock_stability:
            
            # Primary fails
            mock_openai.side_effect = Exception("API failure")
            
            # Secondary succeeds
            mock_stability.return_value = GenerationResult(
                success=True,
                variants_generated=3,
                quality_score=0.75,
                cost_estimate=0.20,
                output_files=["variant1.jpg", "variant2.jpg", "variant3.jpg"],
                provider_used=APIProvider.STABILITY_AI,
                processing_time=3.0,
                metadata={}
            )
            
            result = await agent.generate_variants(brief, APIProvider.OPENAI)
            assert result.success is True
            assert result.provider_used == APIProvider.STABILITY_AI

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test system health check"""
        health_status = await agent.get_health_status()
        
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "metrics" in health_status
        assert "components" in health_status
        
        # Should be healthy by default
        assert health_status["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_prometheus_metrics(self, agent):
        """Test Prometheus metrics collection"""
        # Simulate some activity
        agent.system_metrics["campaigns_processed"] = 5
        agent.system_metrics["success_rate"] = 0.90
        agent.system_metrics["total_variants"] = 20
        
        metrics = agent._collect_prometheus_metrics()
        
        assert "task3_campaigns_processed_total 5" in metrics
        assert "task3_success_rate 0.9" in metrics
        assert "task3_variants_generated_total 20" in metrics

    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, agent, sample_brief_data):
        """Test complete workflow from brief to completion"""
        # Create a test brief file
        brief_file = Path(agent.config["brief_directory"]) / "workflow_test.yaml"
        with open(brief_file, 'w') as f:
            yaml.dump(sample_brief_data, f)
        
        # Mock generation for predictable results
        with patch.object(agent, 'generate_variants') as mock_generate:
            mock_generate.return_value = GenerationResult(
                success=True,
                variants_generated=5,  # Meets requirement
                quality_score=0.90,
                cost_estimate=0.40,
                output_files=[f"variant{i}.jpg" for i in range(1, 6)],
                provider_used=APIProvider.OPENAI,
                processing_time=2.8,
                metadata={}
            )
            
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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])