"""
Dependency injection container.
Creates and wires all agent components.

This is the ONLY place where singletons are created.
All other code receives dependencies via __init__ parameters.

Testing: create a Container with mock dependencies.
Web UI: create a Container per request (or share where safe).
"""
import asyncio
from config.settings import Settings
from agent.intent import IntentClassifier
from agent.date_resolver import DateResolver
from agent.context_manager import ContextManager
from agent.prompt_builder import PromptBuilder
from agent.nutrition_pipeline import NutritionPipeline
from agent.orchestrator import AgentOrchestrator
from agent.events import EventBus
from agent.llm import LLMClient
from vault.reader import VaultReader
from vault.writer import VaultWriter
from git_manager.commits import GitManager
from memory.database import Database
from memory.vector_store import VectorStore


class Container:
    """
    Dependency injection container.
    
    Creates all instances once and wires them together.
    Pass this container to main.py and the CLI — they 
    pull what they need from it.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        
        # Infrastructure layer (unchanged from current)
        self.llm_client = LLMClient(settings)
        self.vault_reader = VaultReader(settings)
        self.git_manager = GitManager(settings)
        
        # Memory layer (intelligence system)
        self.memory_db = Database(str(settings.get_memory_db_path()))
        self.vector_store = VectorStore(str(settings.get_vector_store_path()))
        
        # Initialize memory systems asynchronously
        asyncio.run(self._initialize_memory())
        
        # Create vault_writer with initialized memory components
        self.vault_writer = VaultWriter(settings, self.vault_reader)
        self.vault_writer.memory_db = self.memory_db
        self.vault_writer.vector_store = self.vector_store
        
        # Agent layer (new)
        self.event_bus = EventBus()
        self.prompt_builder = PromptBuilder()
        self.intent_classifier = IntentClassifier(self.llm_client)
        self.date_resolver = DateResolver(self.llm_client)
        self.context_manager = ContextManager(
            vault_reader=self.vault_reader,
            prompt_builder=self.prompt_builder,
            context_days=settings.agent_context_days
        )
        self.nutrition_pipeline = NutritionPipeline(self.llm_client)
        
        # Wire cache invalidation:
        # When writer writes a file, context cache is invalidated
        # This is the event system in action — writer doesn't know
        # about context_manager; the container wires them together
        original_write = self.vault_writer.write_daily_log
        def write_and_invalidate(*args, **kwargs):
            result = original_write(*args, **kwargs)
            self.context_manager.invalidate()
            return result
        self.vault_writer.write_daily_log = write_and_invalidate
        
        # Orchestrator gets everything injected
        self.orchestrator = AgentOrchestrator(
            intent_classifier=self.intent_classifier,
            date_resolver=self.date_resolver,
            context_manager=self.context_manager,
            nutrition_pipeline=self.nutrition_pipeline,
            vault_writer=self.vault_writer,
            git_manager=self.git_manager,
            settings=settings,
            on_event=self.event_bus.emit
        )
    
    async def _initialize_memory(self):
        """Initialize memory database and vector store."""
        try:
            await self.memory_db.initialize()
            await self.vector_store.initialize()
        except Exception as e:
            import logging
            logging.warning(f"Failed to initialize memory systems: {e}")
            # Continue without memory - graceful degradation


def create_container() -> Container:
    """Create the production container. Called once from main.py."""
    from config.settings import get_settings
    return Container(get_settings())


# Made with Bob