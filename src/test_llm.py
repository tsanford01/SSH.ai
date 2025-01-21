import asyncio
from app.core.llm_manager import LLMManager

async def test_llm_queries():
    llm = LLMManager()
    
    print("\nInitializing LLM server...")
    if llm.start_server():
        print("\nTesting basic command queries...")
        
        test_cases = [
            "list files",  # Simple command
            "show current directory",  # Basic navigation
            "create a new folder",  # File operation
        ]
        
        for query in test_cases:
            print("\n" + "="*50)
            print(f"Testing: {query}")
            try:
                response = await llm.get_command_suggestion(query)
                print(f"Response:\n{response}")
            except Exception as e:
                print(f"Error: {e}")
            await asyncio.sleep(2)
        
        print("\nTests completed. Shutting down server...")
        llm.stop_server()
    else:
        print("Server failed to start!")

if __name__ == "__main__":
    asyncio.run(test_llm_queries()) 