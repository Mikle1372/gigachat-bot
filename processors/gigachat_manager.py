import time
import tiktoken
from langchain_gigachat import GigaChat
from langchain.schema import HumanMessage, SystemMessage

class GigaChatManager:
    def __init__(self, config):
        self.llm = GigaChat(
            credentials=config.gigachat_api_key,
            model=config.gigachat_model,
            verify_ssl_certs=False,
            temperature=config.temperature
        )
        self.encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
        self.token_cost = config.token_cost

    def _calculate_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))

    def generate_response(self, system_prompt: str, query: str, context: str) -> tuple:
        start_time = time.time()
        full_input = system_prompt + query + context
        
        response = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)]).content
        
        return response, self._create_metadata(full_input, response, start_time)

    def _create_metadata(self, input_text, response, start_time):
        input_tokens = self._calculate_tokens(input_text)
        output_tokens = self._calculate_tokens(response)
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "cost": (input_tokens + output_tokens) * self.token_cost,
            "response_time": time.time() - start_time
        }