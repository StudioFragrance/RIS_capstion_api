import importlib
import traceback
from multiprocessing import Process

from kafka.errors import NoBrokersAvailable
from rich.console import Console
from rich.prompt import Prompt
from rpc.message_broker import MessageBroker


def main():
    console = Console()
    print = console.print

    print("[ RPC CLI ]")

    while True:
        broker_url = Prompt.ask("broker_url", default="localhost:9092")
        try:
            broker = MessageBroker(broker_url)
            break
        except NoBrokersAvailable:
            print("NoBrokersAvailable")


    processes = []
    alias = {
        "q": [". sys.exit()"],
        "!!": [
            "! rpc.data.data2 main",
        ]
    }

    def run(cmd):
        if len(cmd.strip()) == 0:
            # Blank command
            return
        elif cmd in alias:
            # Alias commands
            for line in alias[cmd]:
                run(line)
        elif cmd.startswith("."):
            # Run python code
            exec(cmd[1:].strip())
        elif cmd.startswith("!"):
            # Run python module
            try:
                cmds = cmd[1:].strip().split()
                module = importlib.import_module(cmds[0])
                p = Process(target=getattr(module, cmds[1]))
                p.start()
                processes.append(p)
            except:
                print("\n───────────────────────────────")
                traceback.print_exc()
                print("───────────────────────────────\n")
        else:
            # Call RPC method
            try:
                i_topic = cmd.index(" ")
                i_method = cmd.index(" ", i_topic + 1)

                result = broker.rpc(
                    cmd[:i_topic],
                    cmd[i_topic+1:i_method],
                    eval(cmd[i_method+1:])
                )
                print(result)
            except:
                print("\n───────────────────────────────")
                traceback.print_exc()
                print("───────────────────────────────\n")

    try:
        while True:
            run(input("-] "))
    except KeyboardInterrupt:
        pass
    finally:
        for p in processes:
            print("\n───────────── JOIN ────────────")
            print(p)
            p.terminate()
        print("──────────── EXITED ───────────")


if __name__ == "__main__":
    main()
