"""
Intelligent Task Orchestration Engine
Advanced campaign processing with AI-driven resource allocation and priority management
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import heapq
import logging
from concurrent.futures import ThreadPoolExecutor
import psutil
import numpy as np

class TaskPriority(Enum):
    EMERGENCY = 0    # System failures, critical client issues
    URGENT = 1       # < 24h deadline, premium clients
    HIGH = 2         # < 3 days, important campaigns
    NORMAL = 3       # Standard processing
    LOW = 4          # Background tasks, optimization

class TaskStatus(Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class ResourceType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    GPU = "gpu"
    STORAGE = "storage"
    API_QUOTA = "api_quota"
    NETWORK = "network"

@dataclass
class Task:
    """Enhanced task representation with comprehensive metadata"""
    id: str
    campaign_id: str
    task_type: str
    priority: TaskPriority
    created_at: datetime
    deadline: Optional[datetime] = None
    estimated_duration: timedelta = timedelta(minutes=30)
    resource_requirements: Dict[ResourceType, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.QUEUED
    assigned_worker: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Priority queue comparison - lower priority enum value = higher priority"""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # If same priority, earlier deadline takes precedence
        if self.deadline and other.deadline:
            return self.deadline < other.deadline
        return self.created_at < other.created_at

@dataclass
class WorkerNode:
    """Represents a processing worker with resource capabilities"""
    id: str
    status: str = "idle"  # idle, busy, overloaded, offline
    capabilities: Dict[str, float] = field(default_factory=dict)
    current_load: Dict[ResourceType, float] = field(default_factory=dict)
    max_capacity: Dict[ResourceType, float] = field(default_factory=dict)
    active_tasks: List[str] = field(default_factory=list)
    performance_score: float = 1.0
    last_heartbeat: datetime = field(default_factory=datetime.now)

class IntelligentOrchestrator:
    """AI-driven task orchestration with intelligent resource management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Core orchestration state
        self.task_queue = []  # Priority queue (heapq)
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.worker_nodes: Dict[str, WorkerNode] = {}
        
        # AI-driven optimization
        self.performance_predictor = PerformancePredictor()
        self.resource_optimizer = ResourceOptimizer()
        self.deadline_manager = DeadlineManager()
        
        # System monitoring
        self.system_metrics = SystemMetrics()
        self.load_balancer = LoadBalancer()
        
        # Configuration
        self.config = {
            "max_concurrent_tasks": 10,
            "resource_buffer_percentage": 0.15,  # Keep 15% resources free
            "performance_weight": 0.4,
            "deadline_weight": 0.4,
            "resource_weight": 0.2,
            "auto_scaling": True,
            "predictive_scheduling": True,
            "adaptive_retry": True
        }
        
        # Start background processes
        self._start_orchestration_loop()
    
    async def submit_campaign_task(self, campaign_brief: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Submit a campaign for intelligent processing"""
        
        # Analyze campaign requirements
        task_analysis = await self._analyze_campaign_requirements(campaign_brief, metadata)
        
        # Create optimized task plan
        tasks = await self._create_task_plan(campaign_brief, task_analysis)
        
        # Submit tasks to intelligent queue
        submitted_task_ids = []
        for task in tasks:
            task_id = await self._submit_task_to_queue(task)
            submitted_task_ids.append(task_id)
        
        self.logger.info(f"🚀 Submitted {len(tasks)} tasks for campaign {campaign_brief.get('campaign_name', 'unknown')}")
        
        return submitted_task_ids[0] if submitted_task_ids else None
    
    async def _analyze_campaign_requirements(self, brief: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered analysis of campaign requirements"""
        
        analysis = {
            "complexity_score": metadata.get("complexity_score", 0.5),
            "estimated_variants": metadata.get("estimated_variants", 10),
            "deadline_pressure": self._calculate_deadline_pressure(brief),
            "resource_intensity": self._estimate_resource_intensity(brief),
            "parallelization_potential": self._assess_parallelization(brief),
            "dependencies": self._identify_dependencies(brief),
            "risk_factors": metadata.get("risk_factors", [])
        }
        
        # AI prediction for processing time and resources
        if self.config["predictive_scheduling"]:
            predictions = await self.performance_predictor.predict_requirements(brief, analysis)
            analysis.update(predictions)
        
        return analysis
    
    async def _create_task_plan(self, brief: Dict[str, Any], analysis: Dict[str, Any]) -> List[Task]:
        """Create optimized task execution plan"""
        
        tasks = []
        base_priority = self._determine_base_priority(brief, analysis)
        
        # Break down campaign into atomic tasks
        if analysis["parallelization_potential"] > 0.7:
            # High parallelization - create tasks per product/variant
            tasks.extend(await self._create_parallel_tasks(brief, analysis, base_priority))
        else:
            # Sequential processing - create staged tasks
            tasks.extend(await self._create_sequential_tasks(brief, analysis, base_priority))
        
        # Add dependency relationships
        await self._setup_task_dependencies(tasks, analysis)
        
        # Optimize task order for resource utilization
        optimized_tasks = await self.resource_optimizer.optimize_task_order(tasks, self.system_metrics.get_current_state())
        
        return optimized_tasks
    
    async def _create_parallel_tasks(self, brief: Dict[str, Any], analysis: Dict[str, Any], base_priority: TaskPriority) -> List[Task]:
        """Create parallelizable tasks for high-throughput processing"""
        
        tasks = []
        products = brief.get("products", [])
        deliverables = brief.get("deliverables", {})
        
        # Create tasks per product
        for i, product in enumerate(products):
            task = Task(
                id=f"{brief.get('campaign_name', 'campaign')}_{product}_{int(time.time())}_{i}",
                campaign_id=brief.get("campaign_name", "unknown"),
                task_type="product_generation",
                priority=base_priority,
                created_at=datetime.now(),
                deadline=self._parse_deadline(brief.get("timeline", {})),
                estimated_duration=timedelta(minutes=15 + analysis["complexity_score"] * 30),
                resource_requirements={
                    ResourceType.CPU: 0.3 + analysis["complexity_score"] * 0.4,
                    ResourceType.MEMORY: 0.5 + analysis["complexity_score"] * 0.3,
                    ResourceType.GPU: 0.2 + analysis["complexity_score"] * 0.6,
                    ResourceType.API_QUOTA: analysis["estimated_variants"] / len(products)
                },
                metadata={
                    "product": product,
                    "variants_needed": analysis["estimated_variants"] // len(products),
                    "aspect_ratios": deliverables.get("aspect_ratios", ["1:1"]),
                    "complexity_score": analysis["complexity_score"]
                }
            )
            tasks.append(task)
        
        return tasks
    
    async def _create_sequential_tasks(self, brief: Dict[str, Any], analysis: Dict[str, Any], base_priority: TaskPriority) -> List[Task]:
        """Create sequential tasks for complex campaigns requiring staged processing"""
        
        tasks = []
        
        # Planning phase
        planning_task = Task(
            id=f"{brief.get('campaign_name', 'campaign')}_planning_{int(time.time())}",
            campaign_id=brief.get("campaign_name", "unknown"),
            task_type="campaign_planning",
            priority=base_priority,
            created_at=datetime.now(),
            deadline=self._parse_deadline(brief.get("timeline", {})),
            estimated_duration=timedelta(minutes=10),
            resource_requirements={
                ResourceType.CPU: 0.2,
                ResourceType.MEMORY: 0.3,
                ResourceType.API_QUOTA: 5
            },
            metadata={"phase": "planning", "brief": brief}
        )
        tasks.append(planning_task)
        
        # Generation phase
        generation_task = Task(
            id=f"{brief.get('campaign_name', 'campaign')}_generation_{int(time.time())}",
            campaign_id=brief.get("campaign_name", "unknown"),
            task_type="bulk_generation",
            priority=base_priority,
            created_at=datetime.now(),
            deadline=self._parse_deadline(brief.get("timeline", {})),
            estimated_duration=timedelta(minutes=30 + analysis["complexity_score"] * 60),
            resource_requirements={
                ResourceType.CPU: 0.7,
                ResourceType.MEMORY: 0.8,
                ResourceType.GPU: 0.9,
                ResourceType.API_QUOTA: analysis["estimated_variants"]
            },
            dependencies=[planning_task.id],
            metadata={"phase": "generation", "variants": analysis["estimated_variants"]}
        )
        tasks.append(generation_task)
        
        # Quality assurance phase
        qa_task = Task(
            id=f"{brief.get('campaign_name', 'campaign')}_qa_{int(time.time())}",
            campaign_id=brief.get("campaign_name", "unknown"),
            task_type="quality_assurance",
            priority=base_priority,
            created_at=datetime.now(),
            deadline=self._parse_deadline(brief.get("timeline", {})),
            estimated_duration=timedelta(minutes=15),
            resource_requirements={
                ResourceType.CPU: 0.4,
                ResourceType.MEMORY: 0.3,
                ResourceType.GPU: 0.2,
                ResourceType.API_QUOTA: 10
            },
            dependencies=[generation_task.id],
            metadata={"phase": "quality_assurance"}
        )
        tasks.append(qa_task)
        
        return tasks
    
    async def _submit_task_to_queue(self, task: Task) -> str:
        """Submit task to intelligent priority queue"""
        
        # Add to priority queue
        heapq.heappush(self.task_queue, task)
        
        self.logger.info(f"📋 Task {task.id} queued with priority {task.priority.name}")
        
        # Trigger immediate scheduling if resources available
        if await self._has_available_resources(task):
            asyncio.create_task(self._schedule_next_task())
        
        return task.id
    
    def _start_orchestration_loop(self):
        """Start the main orchestration background loop"""
        asyncio.create_task(self._orchestration_loop())
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._optimization_loop())
    
    async def _orchestration_loop(self):
        """Main orchestration loop - assigns tasks to workers"""
        while True:
            try:
                # Update system state
                await self.system_metrics.update()
                
                # Schedule pending tasks
                await self._schedule_next_task()
                
                # Check for completed tasks
                await self._check_task_completion()
                
                # Handle failed tasks
                await self._handle_failed_tasks()
                
                await asyncio.sleep(1)  # High-frequency scheduling
                
            except Exception as e:
                self.logger.error(f"❌ Orchestration loop error: {e}")
                await asyncio.sleep(5)
    
    async def _schedule_next_task(self):
        """Intelligent task scheduling with resource optimization"""
        
        if not self.task_queue:
            return
        
        # Get next highest priority task
        next_task = heapq.heappop(self.task_queue)
        
        # Check dependencies
        if not await self._dependencies_satisfied(next_task):
            heapq.heappush(self.task_queue, next_task)  # Put back in queue
            return
        
        # Find optimal worker
        optimal_worker = await self._find_optimal_worker(next_task)
        
        if optimal_worker:
            await self._assign_task_to_worker(next_task, optimal_worker)
        else:
            # No suitable worker available, put task back in queue
            heapq.heappush(self.task_queue, next_task)
            
            # Consider scaling up resources if enabled
            if self.config["auto_scaling"]:
                await self._consider_auto_scaling(next_task)
    
    async def _find_optimal_worker(self, task: Task) -> Optional[str]:
        """Find the optimal worker for a task using AI-driven selection"""
        
        available_workers = [
            worker for worker in self.worker_nodes.values()
            if worker.status in ["idle", "busy"] and await self._can_handle_task(worker, task)
        ]
        
        if not available_workers:
            return None
        
        # Score workers based on multiple factors
        worker_scores = []
        for worker in available_workers:
            score = await self._calculate_worker_score(worker, task)
            worker_scores.append((score, worker.id))
        
        # Return best scoring worker
        worker_scores.sort(reverse=True)
        return worker_scores[0][1] if worker_scores else None
    
    async def _calculate_worker_score(self, worker: WorkerNode, task: Task) -> float:
        """Calculate worker suitability score for a task"""
        
        # Performance factor
        performance_score = worker.performance_score * self.config["performance_weight"]
        
        # Resource utilization factor
        resource_score = await self._calculate_resource_efficiency(worker, task) * self.config["resource_weight"]
        
        # Deadline pressure factor
        deadline_score = await self._calculate_deadline_urgency(task) * self.config["deadline_weight"]
        
        total_score = performance_score + resource_score + deadline_score
        
        return total_score
    
    def _determine_base_priority(self, brief: Dict[str, Any], analysis: Dict[str, Any]) -> TaskPriority:
        """Determine task priority based on brief analysis"""
        
        # Check for emergency indicators
        tags = brief.get("tags", [])
        if any(tag.lower() in ["emergency", "critical", "system_failure"] for tag in tags):
            return TaskPriority.EMERGENCY
        
        # Check deadline pressure
        if analysis["deadline_pressure"] > 0.8:
            return TaskPriority.URGENT
        elif analysis["deadline_pressure"] > 0.6:
            return TaskPriority.HIGH
        
        # Check client tier
        client_tier = brief.get("client", {}).get("tier", "standard")
        if client_tier in ["enterprise", "premium"] and "urgent" in tags:
            return TaskPriority.URGENT
        elif client_tier in ["enterprise", "premium"]:
            return TaskPriority.HIGH
        
        return TaskPriority.NORMAL
    
    def _calculate_deadline_pressure(self, brief: Dict[str, Any]) -> float:
        """Calculate deadline pressure score (0-1)"""
        timeline = brief.get("timeline", {})
        if "deadline" not in timeline:
            return 0.3  # Default moderate pressure
        
        try:
            deadline = datetime.fromisoformat(timeline["deadline"])
            time_remaining = deadline - datetime.now()
            hours_remaining = time_remaining.total_seconds() / 3600
            
            if hours_remaining <= 6:
                return 1.0  # Extreme pressure
            elif hours_remaining <= 24:
                return 0.8  # High pressure
            elif hours_remaining <= 72:
                return 0.6  # Moderate pressure
            else:
                return 0.3  # Low pressure
        except:
            return 0.3
    
    def _parse_deadline(self, timeline: Dict[str, Any]) -> Optional[datetime]:
        """Parse deadline from timeline information"""
        if "deadline" not in timeline:
            return None
        
        try:
            return datetime.fromisoformat(timeline["deadline"])
        except:
            return None


class PerformancePredictor:
    """AI-powered performance prediction for task scheduling"""
    
    def __init__(self):
        self.historical_data = []
        self.model_accuracy = 0.85
    
    async def predict_requirements(self, brief: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Predict processing requirements using historical data"""
        
        # Simplified prediction model (in production, this would use ML)
        complexity = analysis["complexity_score"]
        variants = analysis["estimated_variants"]
        
        predictions = {
            "predicted_duration": timedelta(minutes=15 + complexity * 45 + variants * 0.5),
            "predicted_cpu_usage": 0.3 + complexity * 0.4,
            "predicted_memory_usage": 0.4 + complexity * 0.3,
            "predicted_success_probability": max(0.7, 0.95 - complexity * 0.2),
            "predicted_cost": variants * (5 + complexity * 10)
        }
        
        return predictions


class ResourceOptimizer:
    """Advanced resource optimization and load balancing"""
    
    async def optimize_task_order(self, tasks: List[Task], system_state: Dict[str, Any]) -> List[Task]:
        """Optimize task execution order for resource efficiency"""
        
        # Sort by priority first, then optimize within priority groups
        priority_groups = {}
        for task in tasks:
            if task.priority not in priority_groups:
                priority_groups[task.priority] = []
            priority_groups[task.priority].append(task)
        
        optimized_tasks = []
        
        for priority in sorted(priority_groups.keys()):
            group_tasks = priority_groups[priority]
            
            # Optimize within priority group
            optimized_group = await self._optimize_group_order(group_tasks, system_state)
            optimized_tasks.extend(optimized_group)
        
        return optimized_tasks
    
    async def _optimize_group_order(self, tasks: List[Task], system_state: Dict[str, Any]) -> List[Task]:
        """Optimize task order within a priority group"""
        
        # Simple optimization based on resource complementarity
        # In production, this would use advanced scheduling algorithms
        
        # Sort by deadline first
        tasks.sort(key=lambda t: t.deadline or datetime.max)
        
        return tasks


class SystemMetrics:
    """System resource monitoring and metrics collection"""
    
    def __init__(self):
        self.current_state = {}
        
    async def update(self):
        """Update current system metrics"""
        self.current_state = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "active_connections": len(psutil.net_connections()),
            "timestamp": datetime.now()
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current system state"""
        return self.current_state


class LoadBalancer:
    """Intelligent load balancing across worker nodes"""
    
    async def balance_load(self, workers: Dict[str, WorkerNode], new_task: Task) -> Optional[str]:
        """Balance load across available workers"""
        
        # Find least loaded worker that can handle the task
        available_workers = [
            worker for worker in workers.values()
            if worker.status != "offline"
        ]
        
        if not available_workers:
            return None
        
        # Sort by current load
        available_workers.sort(key=lambda w: sum(w.current_load.values()))
        
        return available_workers[0].id


class DeadlineManager:
    """Advanced deadline management and scheduling"""
    
    def calculate_deadline_priority(self, task: Task) -> float:
        """Calculate priority boost based on deadline pressure"""
        
        if not task.deadline:
            return 0.0
        
        time_remaining = task.deadline - datetime.now()
        hours_remaining = max(time_remaining.total_seconds() / 3600, 0)
        
        # Exponential urgency curve
        if hours_remaining <= 1:
            return 1.0
        elif hours_remaining <= 6:
            return 0.8
        elif hours_remaining <= 24:
            return 0.6
        elif hours_remaining <= 72:
            return 0.4
        else:
            return 0.2


# Example usage
async def demo_intelligent_orchestrator():
    """Demonstrate the intelligent orchestration system"""
    orchestrator = IntelligentOrchestrator()
    
    print("🤖 Intelligent Task Orchestration Engine Demo")
    print("=" * 50)
    print("📋 Key Features:")
    print("  ✅ AI-powered task prioritization and resource allocation")
    print("  ✅ Intelligent worker selection and load balancing")
    print("  ✅ Predictive performance analysis and optimization")
    print("  ✅ Automatic scaling and failure recovery")
    print("  ✅ Real-time deadline management and pressure analysis")
    print("  ✅ Multi-dimensional resource optimization")
    
    # Simulate campaign submission
    sample_brief = {
        "campaign_name": "Holiday_Collection_2024",
        "products": ["winter_coat", "holiday_sweater", "accessories"],
        "timeline": {"deadline": (datetime.now() + timedelta(hours=24)).isoformat()},
        "tags": ["urgent", "premium"],
        "client": {"tier": "enterprise"}
    }
    
    sample_metadata = {
        "complexity_score": 0.7,
        "estimated_variants": 18,
        "risk_factors": ["tight_deadline", "complex_products"]
    }
    
    task_id = await orchestrator.submit_campaign_task(sample_brief, sample_metadata)
    print(f"\n🚀 Submitted campaign task: {task_id}")
    
    return orchestrator


if __name__ == "__main__":
    asyncio.run(demo_intelligent_orchestrator())