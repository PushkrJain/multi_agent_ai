import os
import grpc
from concurrent import futures

from agent_pb2_grpc import AgentServiceServicer, add_AgentServiceServicer_to_server
from agent_pb2 import AgentMessage

from mid_agents.intent.parser import IntentParser
from mid_agents.intent.errors import IntentParseError, SecurityViolationError

from task_agents.weather import WeatherAgent
from utils.errors import WeatherAPIError

from task_agents.news import NewsAgent
from mid_agents.intent.errors import NewsAPIError

from task_agents.translation import TranslationAgent
from mid_agents.intent.errors import TranslationAPIError

from prometheus_client import start_http_server
start_http_server(9101) 

class AgentService(AgentServiceServicer):
    def __init__(self):
        self.intent_parser = IntentParser()
        self.weather_agent = WeatherAgent()
        self.news_agent = NewsAgent()
        self.translation_agent = TranslationAgent()

    def SendAgentMessage(self, request, context):
        try:
            decoded_msg = request.payload.decode()
            intent = self.intent_parser.parse(decoded_msg)
            response_msg = self._handle_intent(intent)
            return AgentMessage(
                id=request.id,
                payload=response_msg.encode('utf-8'),
                urgency=AgentMessage.Urgency.NORMAL
            )
        except SecurityViolationError as e:
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details(f"Security violation: {str(e)}")
            return AgentMessage()
        except IntentParseError as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
            return AgentMessage()
        except (WeatherAPIError, NewsAPIError, TranslationAPIError) as e:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details(f"Service error: {str(e)}")
            return AgentMessage()
        except Exception as e:
            print(f"[SERVER ERROR] Unexpected failure: {str(e)}")  # Debug log
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Internal server error: {str(e)}")
            return AgentMessage()

    def _handle_intent(self, intent: dict) -> str:
        intent_type = intent.get('intent')
        try:
            if intent_type == 'weather':
                weather_data = self.weather_agent.get_weather(intent['target'])
                return (
                    f"Weather in {weather_data['location']}:\n"
                    f"Condition: {weather_data['condition']}\n"
                    f"Temperature: {weather_data['temp_c']}°C ({weather_data['temp_f']}°F)\n"
                    f"Humidity: {weather_data['humidity']}%\n"
                    f"Wind: {weather_data['wind']} km/h\n"
                    f"Pressure: {weather_data['pressure']} hPa"
                )
            elif intent_type == 'news':
                news_data = self.news_agent.get_news(
                    query=intent.get('query'),
                    category=intent.get('category'),
                    country=intent.get('country')
                )
                location = f" in {intent['country']}" if intent.get('country') else ""
                headlines = "\n".join(
                    f"{i + 1}. {article['title']} ({article['source']})"
                    for i, article in enumerate(news_data)
                )
                return f"🗞️ Latest News Headlines{location}:\n{headlines}"
            elif intent_type == 'translate':
                translation = self.translation_agent.translate_text(
                    text=intent['text'],
                    target_lang=intent['target_lang'],
                    source_lang=intent.get('source_lang')
                )
                return (
                    f"🌐 Translation ({translation['service']}):\n"
                    f"From {translation['source_lang']} to {translation['target_lang']}:\n"
                    f"{translation['text']}"
                )
            else:
                raise IntentParseError(f"Unsupported intent type: {intent_type}")
        except Exception as e:
            print(f"[SERVER ERROR] while handling '{intent_type}': {str(e)}")  # Debug log
            raise Exception(f"Failed to process {intent_type} request: {str(e)}")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_AgentServiceServicer_to_server(AgentService(), server)

    try:
        with open('shared/config/agent_key.pem', 'rb') as f:
            private_key = f.read()
        with open('shared/config/agent_cert.pem', 'rb') as f:
            certificate = f.read()
    except FileNotFoundError:
        print("❌ SSL certificate or key not found in 'shared/config/'")
        return

    credentials = grpc.ssl_server_credentials(((private_key, certificate),))
    server.add_secure_port('[::]:50051', credentials)

    print("✅ Server running securely on port 50051")
    server.start()
    server.wait_for_termination()

def start_failover_agent(agent_name):
    print(f"[FAILOVER] Starting standby container for {agent_name}")
    os.system(f"sudo lxc-start -n standby_{agent_name}")


if __name__ == '__main__':
    serve()
