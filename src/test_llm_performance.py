#!/usr/bin/env python3
"""
Test script for benchmarking LLM performance with different configurations.
"""

import asyncio
import time
from pathlib import Path
import psutil
import logging
from typing import Dict, Any

from app.core.llm_manager import LLMManager, LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_configuration(config: LLMConfig) -> Dict[str, Any]:
    """Test LLM performance with given configuration."""
    logger.info(f"\nTesting configuration:\n{config}")
    
    # Initialize manager with config
    manager = LLMManager()
    manager.config = config
    
    # Track metrics
    metrics = {
        "startup_time": 0,
        "first_response_time": 0,
        "avg_response_time": 0,
        "peak_memory_mb": 0,
        "peak_cpu_percent": 0,
        "success_rate": 0
    }
    
    try:
        # Measure startup time
        start_time = time.time()
        if not manager.start_server(no_browser=True):
            logger.error("Failed to start server")
            return metrics
        metrics["startup_time"] = time.time() - start_time
        
        # Wait for server to be fully ready
        await asyncio.sleep(5)
        
        # Test connection
        if not await manager.test_connection():
            logger.error("Server connection test failed")
            return metrics
        
        # Test queries
        test_queries = [
            "list files in current directory",
            "show system status",
            "create a new directory",
            "check disk space",
            "show network connections"
        ]
        
        response_times = []
        successes = 0
        peak_memory = 0
        peak_cpu = 0
        
        # First query (cold start)
        start_time = time.time()
        response = await manager.get_command_suggestion(test_queries[0])
        metrics["first_response_time"] = time.time() - start_time
        if response:
            successes += 1
        
        # Test remaining queries
        for query in test_queries[1:]:
            # Track resource usage
            memory = psutil.Process().memory_info().rss / (1024 * 1024)
            cpu = psutil.Process().cpu_percent()
            peak_memory = max(peak_memory, memory)
            peak_cpu = max(peak_cpu, cpu)
            
            # Measure response time
            start_time = time.time()
            response = await manager.get_command_suggestion(query)
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            if response:
                successes += 1
            
            # Small delay between queries
            await asyncio.sleep(1)
        
        # Calculate metrics
        metrics.update({
            "avg_response_time": sum(response_times) / len(response_times),
            "peak_memory_mb": peak_memory,
            "peak_cpu_percent": peak_cpu,
            "success_rate": successes / len(test_queries)
        })
        
    finally:
        # Cleanup
        manager.stop_server()
    
    return metrics

async def main():
    """Run performance tests with different configurations."""
    # Test configurations
    configs = [
        # GPU with larger batch size
        LLMConfig(
            max_memory_mb=4096,
            max_cpu_percent=50,
            context_length=2048,
            temperature=0.7,
            use_gpu=True,
            gpu_layers=9999,
            batch_size=1024,  # Increased batch size
            threads=max(1, (psutil.cpu_count() or 2) - 1)
        ),
        
        # GPU with larger context window
        LLMConfig(
            max_memory_mb=4096,
            max_cpu_percent=50,
            context_length=4096,  # Increased context length
            temperature=0.7,
            use_gpu=True,
            gpu_layers=9999,
            batch_size=512,
            threads=max(1, (psutil.cpu_count() or 2) - 1)
        ),
        
        # GPU with more aggressive threading
        LLMConfig(
            max_memory_mb=4096,
            max_cpu_percent=90,  # Increased CPU usage
            context_length=2048,
            temperature=0.7,
            use_gpu=True,
            gpu_layers=9999,
            batch_size=512,
            threads=psutil.cpu_count()  # Using all cores
        ),
        
        # Previous best configuration (baseline)
        LLMConfig(
            max_memory_mb=4096,
            max_cpu_percent=50,
            context_length=2048,
            temperature=0.7,
            use_gpu=True,
            gpu_layers=9999,
            batch_size=512,
            threads=max(1, (psutil.cpu_count() or 2) - 1)
        )
    ]
    
    # Run tests
    results = []
    for i, config in enumerate(configs, 1):
        logger.info(f"\nRunning test configuration {i}/{len(configs)}")
        metrics = await test_configuration(config)
        results.append((config, metrics))
        
        # Print results
        logger.info("\nResults:")
        logger.info(f"Startup Time: {metrics['startup_time']:.2f}s")
        logger.info(f"First Response Time: {metrics['first_response_time']:.2f}s")
        logger.info(f"Average Response Time: {metrics['avg_response_time']:.2f}s")
        logger.info(f"Peak Memory Usage: {metrics['peak_memory_mb']:.0f}MB")
        logger.info(f"Peak CPU Usage: {metrics['peak_cpu_percent']:.0f}%")
        logger.info(f"Success Rate: {metrics['success_rate']*100:.0f}%")
        
        # Wait between tests
        await asyncio.sleep(5)
    
    # Compare results
    logger.info("\nPerformance Comparison:")
    for config, metrics in results:
        logger.info(f"\nConfiguration:")
        logger.info(f"  GPU: {'Enabled' if config.use_gpu else 'Disabled'}")
        logger.info(f"  Threads: {config.threads}")
        logger.info(f"  Batch Size: {config.batch_size}")
        logger.info(f"  Context Length: {config.context_length}")
        logger.info(f"Performance:")
        logger.info(f"  Avg Response Time: {metrics['avg_response_time']:.2f}s")
        logger.info(f"  Memory Usage: {metrics['peak_memory_mb']:.0f}MB")
        logger.info(f"  Success Rate: {metrics['success_rate']*100:.0f}%")

if __name__ == "__main__":
    asyncio.run(main()) 