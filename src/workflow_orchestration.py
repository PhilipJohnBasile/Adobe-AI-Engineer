"""
Free Workflow Orchestration System
Visual pipeline designer with step-by-step execution and rollback capabilities
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import logging
import asyncio
from pathlib import Path
import time


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepType(Enum):
    # Core pipeline steps
    VALIDATE_BRIEF = "validate_brief"
    CHECK_COMPLIANCE = "check_compliance"
    MODERATE_CONTENT = "moderate_content"
    GENERATE_ASSETS = "generate_assets"
    COMPOSE_CREATIVES = "compose_creatives"
    
    # Advanced steps
    LOCALIZE_CAMPAIGN = "localize_campaign"
    AB_TEST_SETUP = "ab_test_setup"
    BATCH_PROCESS = "batch_process"
    SEND_NOTIFICATIONS = "send_notifications"
    
    # Control flow
    CONDITIONAL = "conditional"
    PARALLEL = "parallel"
    DELAY = "delay"
    
    # Custom
    CUSTOM = "custom"


@dataclass
class StepCondition:
    """Condition for conditional execution"""
    field: str
    operator: str  # eq, ne, gt, lt, contains, exists
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context"""
        try:
            field_value = self._get_nested_value(context, self.field)
            
            if self.operator == "eq":
                return field_value == self.value
            elif self.operator == "ne":
                return field_value != self.value
            elif self.operator == "gt":
                return float(field_value) > float(self.value)
            elif self.operator == "lt":
                return float(field_value) < float(self.value)
            elif self.operator == "contains":
                return str(self.value).lower() in str(field_value).lower()
            elif self.operator == "exists":
                return field_value is not None
            else:
                return False
        except:
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current


@dataclass
class WorkflowStep:
    """Individual step in a workflow"""
    step_id: str
    name: str
    step_type: StepType
    description: str
    config: Dict[str, Any]
    dependencies: List[str]  # step_ids that must complete first
    conditions: List[StepCondition]  # conditions for execution
    rollback_config: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300
    retry_count: int = 0
    max_retries: int = 2
    
    # Runtime state
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def can_execute(self, workflow_context: Dict[str, Any], completed_steps: Set[str]) -> bool:
        """Check if step can be executed"""
        # Check dependencies
        for dep in self.dependencies:
            if dep not in completed_steps:
                return False
        
        # Check conditions
        for condition in self.conditions:
            if not condition.evaluate(workflow_context):
                return False
        
        return True
    
    def should_retry(self) -> bool:
        """Check if step should be retried"""
        return self.status == StepStatus.FAILED and self.retry_count < self.max_retries


@dataclass
class Workflow:
    """Complete workflow definition"""
    workflow_id: str
    name: str
    description: str
    version: str
    steps: Dict[str, WorkflowStep]
    global_config: Dict[str, Any]
    
    # Runtime state
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    context: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.context:
            self.context = {}
    
    def get_executable_steps(self) -> List[WorkflowStep]:
        """Get steps that can be executed now"""
        completed_steps = {step_id for step_id, step in self.steps.items() 
                          if step.status == StepStatus.COMPLETED}
        
        executable = []
        for step in self.steps.values():
            if (step.status == StepStatus.PENDING and 
                step.can_execute(self.context, completed_steps)):
                executable.append(step)
        
        return executable
    
    def get_failed_steps(self) -> List[WorkflowStep]:
        """Get failed steps that can be retried"""
        return [step for step in self.steps.values() if step.should_retry()]
    
    def get_execution_graph(self) -> Dict[str, Any]:
        """Get visual representation of workflow execution"""
        nodes = []
        edges = []
        
        for step in self.steps.values():
            # Create node
            node = {
                "id": step.step_id,
                "name": step.name,
                "type": step.step_type.value,
                "status": step.status.value,
                "duration": step.duration_seconds,
                "description": step.description
            }
            nodes.append(node)
            
            # Create edges for dependencies
            for dep in step.dependencies:
                edges.append({
                    "source": dep,
                    "target": step.step_id,
                    "type": "dependency"
                })
        
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "nodes": nodes,
            "edges": edges,
            "progress": self._calculate_progress()
        }
    
    def _calculate_progress(self) -> Dict[str, Any]:
        """Calculate workflow progress statistics"""
        total_steps = len(self.steps)
        if total_steps == 0:
            return {"percentage": 100, "completed": 0, "total": 0}
        
        completed = sum(1 for step in self.steps.values() if step.status == StepStatus.COMPLETED)
        failed = sum(1 for step in self.steps.values() if step.status == StepStatus.FAILED)
        running = sum(1 for step in self.steps.values() if step.status == StepStatus.RUNNING)
        
        return {
            "percentage": (completed / total_steps) * 100,
            "completed": completed,
            "failed": failed,
            "running": running,
            "total": total_steps
        }


class StepExecutor:
    """Executes individual workflow steps"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.step_handlers = {
            StepType.VALIDATE_BRIEF: self._validate_brief,
            StepType.CHECK_COMPLIANCE: self._check_compliance,
            StepType.MODERATE_CONTENT: self._moderate_content,
            StepType.GENERATE_ASSETS: self._generate_assets,
            StepType.COMPOSE_CREATIVES: self._compose_creatives,
            StepType.LOCALIZE_CAMPAIGN: self._localize_campaign,
            StepType.AB_TEST_SETUP: self._ab_test_setup,
            StepType.SEND_NOTIFICATIONS: self._send_notifications,
            StepType.CONDITIONAL: self._conditional,
            StepType.DELAY: self._delay,
            StepType.CUSTOM: self._custom
        }
    
    async def execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now().isoformat()
        
        try:
            # Get step handler
            handler = self.step_handlers.get(step.step_type)
            if not handler:
                raise ValueError(f"No handler for step type: {step.step_type}")
            
            # Execute with timeout
            start_time = time.time()
            result = await asyncio.wait_for(
                handler(step, context),
                timeout=step.timeout_seconds
            )
            
            # Update step state
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.now().isoformat()
            step.duration_seconds = time.time() - start_time
            step.output = result
            
            return result
            
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error = f"Step timed out after {step.timeout_seconds} seconds"
            step.completed_at = datetime.now().isoformat()
            step.duration_seconds = time.time() - start_time
            raise
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now().isoformat()
            step.duration_seconds = time.time() - start_time
            self.logger.error(f"Step {step.step_id} failed: {e}")
            raise
    
    async def rollback_step(self, step: WorkflowStep, context: Dict[str, Any]) -> bool:
        """Rollback a completed step"""
        if not step.rollback_config or step.status != StepStatus.COMPLETED:
            return False
        
        try:
            # Execute rollback logic based on step type
            if step.step_type == StepType.GENERATE_ASSETS:
                # Remove generated files
                output_paths = step.output.get("generated_files", [])
                for path in output_paths:
                    if Path(path).exists():
                        Path(path).unlink()
            
            elif step.step_type == StepType.SEND_NOTIFICATIONS:
                # Send rollback notification
                pass  # Would implement notification cancellation
            
            step.status = StepStatus.ROLLED_BACK
            return True
            
        except Exception as e:
            self.logger.error(f"Rollback failed for step {step.step_id}: {e}")
            return False
    
    # Step handler implementations
    async def _validate_brief(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate campaign brief"""
        campaign_brief = context.get("campaign_brief")
        if not campaign_brief:
            raise ValueError("No campaign brief provided")
        
        # Simulate validation
        await asyncio.sleep(1)  # Simulate processing time
        
        # Basic validation
        required_fields = ["campaign_id", "products", "target_region"]
        missing_fields = [field for field in required_fields 
                         if field not in campaign_brief.get("campaign_brief", {})]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        return {
            "valid": True,
            "validation_score": 95,
            "warnings": [],
            "errors": []
        }
    
    async def _check_compliance(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check campaign compliance"""
        from .compliance_checker import ComplianceChecker
        
        checker = ComplianceChecker()
        campaign_brief = context.get("campaign_brief", {})
        
        result = checker.check_campaign_brief(campaign_brief)
        
        if result.get("critical"):
            raise ValueError(f"Critical compliance violations: {result['critical']}")
        
        return {
            "compliant": len(result.get("critical", [])) == 0,
            "score": result.get("score", 0),
            "violations": result.get("critical", []),
            "warnings": result.get("warnings", [])
        }
    
    async def _moderate_content(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Moderate content for safety"""
        from .content_moderation import ComprehensiveContentModerator
        
        moderator = ComprehensiveContentModerator()
        campaign_brief = context.get("campaign_brief", {})
        
        result = moderator.moderate_campaign_content(campaign_brief)
        
        if result["overall_status"] == "blocked":
            raise ValueError(f"Content blocked by moderation: {result['summary']['critical_issues']} critical issues")
        
        return {
            "status": result["overall_status"],
            "risk_level": result["overall_risk"],
            "score": result["summary"].get("moderation_score", 0),
            "issues": result["summary"]["critical_issues"]
        }
    
    async def _generate_assets(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative assets"""
        # This would integrate with the main pipeline
        campaign_brief = context.get("campaign_brief", {})
        config = step.config
        
        # Simulate asset generation
        await asyncio.sleep(3)  # Simulate generation time
        
        products = campaign_brief.get("campaign_brief", {}).get("products", [])
        aspect_ratios = config.get("aspect_ratios", ["1:1", "9:16", "16:9"])
        
        generated_files = []
        for i, product in enumerate(products):
            for ratio in aspect_ratios:
                file_path = f"output/workflow_{step.step_id}/product_{i}_{ratio.replace(':', 'x')}.jpg"
                generated_files.append(file_path)
        
        return {
            "assets_generated": len(generated_files),
            "generated_files": generated_files,
            "products_processed": len(products),
            "aspect_ratios": aspect_ratios
        }
    
    async def _compose_creatives(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compose final creatives"""
        await asyncio.sleep(2)  # Simulate composition time
        
        return {
            "creatives_composed": 6,
            "composition_time": 2.1,
            "output_formats": ["jpg", "png"]
        }
    
    async def _localize_campaign(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Localize campaign for specific market"""
        from .localization import Localizer
        
        localizer = Localizer()
        campaign_brief = context.get("campaign_brief", {})
        target_market = step.config.get("target_market", "US")
        
        localized_brief = localizer.localize_campaign(
            campaign_brief.get("campaign_brief", {}), 
            target_market
        )
        
        # Update context with localized brief
        context["localized_brief"] = localized_brief
        
        return {
            "localized_for": target_market,
            "adaptations_made": len(localized_brief.get("_localization_log", [])),
            "localized_brief": localized_brief
        }
    
    async def _ab_test_setup(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Setup A/B test for campaign"""
        from .ab_testing import ABTestManager
        
        manager = ABTestManager()
        config = step.config
        
        test_id = manager.create_test(
            test_name=config.get("test_name", "Workflow A/B Test"),
            campaign_id=context.get("campaign_brief", {}).get("campaign_brief", {}).get("campaign_id", "unknown"),
            description=config.get("description", "Automated A/B test from workflow")
        )
        
        return {
            "ab_test_id": test_id,
            "test_name": config.get("test_name"),
            "variants_count": config.get("variants_count", 2)
        }
    
    async def _send_notifications(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send workflow notifications"""
        from .webhook_notifications import WebhookNotificationSystem, EventType, Priority
        
        webhook_system = WebhookNotificationSystem()
        config = step.config
        
        event_data = {
            "workflow_id": context.get("workflow_id"),
            "workflow_name": context.get("workflow_name"),
            "step": step.name,
            "message": config.get("message", "Workflow step completed"),
            "context": config.get("include_context", {})
        }
        
        event_id = webhook_system.create_event(
            EventType.CAMPAIGN_COMPLETED,  # Would add workflow-specific events
            event_data,
            Priority.MEDIUM
        )
        
        return {
            "notification_sent": True,
            "event_id": event_id,
            "recipients": config.get("recipients", [])
        }
    
    async def _conditional(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional execution step"""
        conditions = step.config.get("conditions", [])
        
        results = []
        for condition_config in conditions:
            condition = StepCondition(**condition_config)
            result = condition.evaluate(context)
            results.append({
                "condition": condition_config,
                "result": result
            })
        
        # Determine overall result
        logic = step.config.get("logic", "and")  # and, or
        if logic == "and":
            overall_result = all(r["result"] for r in results)
        else:  # or
            overall_result = any(r["result"] for r in results)
        
        return {
            "conditions_evaluated": len(results),
            "overall_result": overall_result,
            "individual_results": results
        }
    
    async def _delay(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Delay execution"""
        delay_seconds = step.config.get("delay_seconds", 5)
        await asyncio.sleep(delay_seconds)
        
        return {
            "delayed_seconds": delay_seconds,
            "completed_at": datetime.now().isoformat()
        }
    
    async def _custom(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Custom step execution"""
        # This would allow users to define custom Python code or external API calls
        custom_code = step.config.get("code", "")
        
        # For security, this would be sandboxed in production
        # For now, just return the config
        return {
            "custom_step": True,
            "config": step.config,
            "message": "Custom step executed"
        }


class WorkflowEngine:
    """Main workflow orchestration engine"""
    
    def __init__(self, storage_path: str = "workflows.json"):
        self.storage_path = storage_path
        self.workflows: Dict[str, Workflow] = {}
        self.executor = StepExecutor()
        self.logger = logging.getLogger(__name__)
        self._load_workflows()
    
    def create_workflow(self, name: str, description: str, steps: List[Dict[str, Any]]) -> str:
        """Create new workflow from step definitions"""
        workflow_id = str(uuid.uuid4())
        
        # Parse steps
        workflow_steps = {}
        for step_def in steps:
            step_id = step_def.get("step_id", str(uuid.uuid4()))
            
            # Parse conditions
            conditions = []
            for cond_def in step_def.get("conditions", []):
                conditions.append(StepCondition(**cond_def))
            
            step = WorkflowStep(
                step_id=step_id,
                name=step_def["name"],
                step_type=StepType(step_def["step_type"]),
                description=step_def.get("description", ""),
                config=step_def.get("config", {}),
                dependencies=step_def.get("dependencies", []),
                conditions=conditions,
                rollback_config=step_def.get("rollback_config"),
                timeout_seconds=step_def.get("timeout_seconds", 300),
                max_retries=step_def.get("max_retries", 2)
            )
            
            workflow_steps[step_id] = step
        
        workflow = Workflow(
            workflow_id=workflow_id,
            name=name,
            description=description,
            version="1.0",
            steps=workflow_steps,
            global_config={}
        )
        
        self.workflows[workflow_id] = workflow
        self._save_workflows()
        
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete workflow"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        workflow.context.update(initial_context)
        workflow.context["workflow_id"] = workflow_id
        workflow.context["workflow_name"] = workflow.name
        
        try:
            while True:
                # Get executable steps
                executable_steps = workflow.get_executable_steps()
                
                if not executable_steps:
                    # Check if there are failed steps to retry
                    failed_steps = workflow.get_failed_steps()
                    if failed_steps:
                        # Retry failed steps
                        for step in failed_steps:
                            step.retry_count += 1
                            step.status = StepStatus.PENDING
                        continue
                    else:
                        # No more steps to execute
                        break
                
                # Execute steps (can be parallel)
                await self._execute_steps_batch(executable_steps, workflow.context)
            
            # Check final status
            failed_steps = [s for s in workflow.steps.values() if s.status == StepStatus.FAILED]
            if failed_steps:
                workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.COMPLETED
            
            workflow.completed_at = datetime.now().isoformat()
            self._save_workflows()
            
            return {
                "workflow_id": workflow_id,
                "status": workflow.status.value,
                "steps_completed": len([s for s in workflow.steps.values() if s.status == StepStatus.COMPLETED]),
                "steps_failed": len(failed_steps),
                "total_steps": len(workflow.steps),
                "duration_seconds": (datetime.fromisoformat(workflow.completed_at) - 
                                   datetime.fromisoformat(workflow.started_at)).total_seconds(),
                "context": workflow.context
            }
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now().isoformat()
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
            raise
    
    async def _execute_steps_batch(self, steps: List[WorkflowStep], context: Dict[str, Any]):
        """Execute a batch of steps (potentially in parallel)"""
        # For now, execute sequentially. In production, would implement parallel execution
        for step in steps:
            try:
                result = await self.executor.execute_step(step, context)
                
                # Update context with step output
                context[f"step_{step.step_id}_output"] = result
                
                self.logger.info(f"Step {step.name} completed successfully")
                
            except Exception as e:
                self.logger.error(f"Step {step.name} failed: {e}")
                # Continue with other steps
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow status"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "progress": workflow._calculate_progress(),
            "created_at": workflow.created_at,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "type": step.step_type.value,
                    "status": step.status.value,
                    "duration": step.duration_seconds,
                    "error": step.error
                }
                for step in workflow.steps.values()
            ]
        }
    
    def get_visual_graph(self, workflow_id: str) -> Dict[str, Any]:
        """Get visual workflow graph for frontend rendering"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}
        
        return workflow.get_execution_graph()
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        return [
            {
                "workflow_id": wf.workflow_id,
                "name": wf.name,
                "description": wf.description,
                "status": wf.status.value,
                "steps_count": len(wf.steps),
                "created_at": wf.created_at,
                "progress": wf._calculate_progress()["percentage"]
            }
            for wf in self.workflows.values()
        ]
    
    def _load_workflows(self):
        """Load workflows from storage"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                
                for wf_data in data.get("workflows", []):
                    # Reconstruct workflow object
                    # This is simplified - would need full serialization/deserialization
                    pass
        except Exception as e:
            self.logger.error(f"Error loading workflows: {e}")
    
    def _save_workflows(self):
        """Save workflows to storage"""
        try:
            # Simplified save - would implement full serialization
            data = {
                "workflows": [],
                "saved_at": datetime.now().isoformat()
            }
            
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving workflows: {e}")


# Predefined workflow templates
class WorkflowTemplates:
    """Predefined workflow templates for common use cases"""
    
    @staticmethod
    def basic_campaign_workflow() -> List[Dict[str, Any]]:
        """Basic campaign generation workflow"""
        return [
            {
                "step_id": "validate_brief",
                "name": "Validate Campaign Brief",
                "step_type": "validate_brief",
                "description": "Validate campaign brief structure and content",
                "config": {},
                "dependencies": [],
                "conditions": []
            },
            {
                "step_id": "check_compliance",
                "name": "Compliance Check",
                "step_type": "check_compliance",
                "description": "Check legal and brand compliance",
                "config": {},
                "dependencies": ["validate_brief"],
                "conditions": []
            },
            {
                "step_id": "moderate_content",
                "name": "Content Moderation",
                "step_type": "moderate_content",
                "description": "Moderate content for safety",
                "config": {},
                "dependencies": ["check_compliance"],
                "conditions": []
            },
            {
                "step_id": "generate_assets",
                "name": "Generate Assets",
                "step_type": "generate_assets",
                "description": "Generate creative assets",
                "config": {
                    "aspect_ratios": ["1:1", "9:16", "16:9"]
                },
                "dependencies": ["moderate_content"],
                "conditions": []
            },
            {
                "step_id": "compose_creatives",
                "name": "Compose Creatives",
                "step_type": "compose_creatives",
                "description": "Compose final creative assets",
                "config": {},
                "dependencies": ["generate_assets"],
                "conditions": []
            }
        ]
    
    @staticmethod
    def enterprise_workflow() -> List[Dict[str, Any]]:
        """Enterprise workflow with advanced features"""
        basic_steps = WorkflowTemplates.basic_campaign_workflow()
        
        # Add enterprise steps
        enterprise_steps = [
            {
                "step_id": "localize_campaign",
                "name": "Localize Campaign",
                "step_type": "localize_campaign",
                "description": "Localize campaign for target market",
                "config": {
                    "target_market": "DE"  # Would be configurable
                },
                "dependencies": ["validate_brief"],
                "conditions": [
                    {
                        "field": "campaign_brief.target_region",
                        "operator": "ne",
                        "value": "US"
                    }
                ]
            },
            {
                "step_id": "ab_test_setup",
                "name": "Setup A/B Test",
                "step_type": "ab_test_setup",
                "description": "Setup A/B testing for campaign",
                "config": {
                    "test_name": "Campaign Performance Test",
                    "variants_count": 2
                },
                "dependencies": ["compose_creatives"],
                "conditions": []
            },
            {
                "step_id": "send_notifications",
                "name": "Send Notifications",
                "step_type": "send_notifications",
                "description": "Notify stakeholders of completion",
                "config": {
                    "message": "Campaign workflow completed successfully",
                    "recipients": ["team@company.com"]
                },
                "dependencies": ["ab_test_setup"],
                "conditions": []
            }
        ]
        
        return basic_steps + enterprise_steps


# Global workflow engine instance
workflow_engine = WorkflowEngine()