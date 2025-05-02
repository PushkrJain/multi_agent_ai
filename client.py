import grpc
import agent_pb2
import agent_pb2_grpc
from task_agents.translation import TranslationAgent

def display_welcome_message():
    try:
        translator = TranslationAgent()
        supported_langs = translator.get_supported_languages()
        print("\n╔════════════════════════════════════════╗")
        print("║ Multi-Agent System Client               ║")
        print("╚════════════════════════════════════════╝")
        print("\n🌍 Supported Translation Languages (use 2-letter codes):")
        print("──────────────────────────────────────")
        for i, (name, code) in enumerate(supported_langs.items(), 1):
            print(f"{name.title():<12} ({code})", end=" | " if i % 3 else "\n")
        print("\n\n📝 Query Examples:")
        print("──────────────────────────────────────")
        print("- Weather: 'weather in Tokyo'")
        print("- News: 'US technology news', 'business headlines in india'")
        print("- Translation: 'translate Hello to es' (use codes)")
        print("\nType 'quit' or 'exit' to end session\n")
    except Exception as e:
        print(f"⚠️ Warning: Could not load translation support - {str(e)}")

def run():
    try:
        with open('shared/config/agent_cert.pem', 'rb') as f:
            cert = f.read()
    except FileNotFoundError:
        print("⚠️ Error: SSL certificate not found at 'shared/config/agent_cert.pem'")
        return

    channel = grpc.secure_channel(
        'localhost:50051',
        grpc.ssl_channel_credentials(root_certificates=cert),
        options=[('grpc.ssl_target_name_override', 'localhost')]
    )
    stub = agent_pb2_grpc.AgentServiceStub(channel)
    display_welcome_message()

    while True:
        try:
            message = input("\n🔍 Enter your query: ").strip()
            if message.lower() in ('quit', 'exit'):
                print("\n🛑 Session ended. Goodbye!\n")
                break
            if not message:
                print("⚠️ Please enter a query")
                continue

            response = stub.SendAgentMessage(
                agent_pb2.AgentMessage(
                    id="cli",
                    payload=message.encode(),
                    urgency=agent_pb2.AgentMessage.Urgency.NORMAL
                )
            )
            print("\n" + "═" * 50)
            print("💬 Response:")
            print(response.payload.decode())
            print("═" * 50)

        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                print(f"\n⚠️ Input Error: {e.details()}")
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                print("\n⚠️ Service Unavailable: Please check:")
                print("- Server is running (python server.py)")
                print("- Your internet connection")
            elif e.code() == grpc.StatusCode.FAILED_PRECONDITION:
                print(f"\n⚠️ Service Error: {e.details()}")
            elif e.code() == grpc.StatusCode.INTERNAL:
                error_msg = e.details()
                if "Failed to process" in error_msg:
                    print(f"\n⚠️ Processing Error: {error_msg.split(':')[-1].strip()}")
                else:
                    print("\n⚠️ Server Error: Please check server logs")
            else:
                print(f"\n⚠️ Server Error [{e.code()}]: {e.details()}")

        except KeyboardInterrupt:
            print("\n🛑 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n⚠️ Unexpected Error: {str(e)}")

if __name__ == '__main__':
    run()

