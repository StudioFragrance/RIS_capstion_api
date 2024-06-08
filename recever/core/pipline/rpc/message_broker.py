import asyncio
import time
import traceback

import msgpack
from kafka import KafkaProducer, KafkaConsumer, TopicPartition

ERROR_CODE_MESSAGES = {
    -32700: "Parse error",
    -32600: "Invalid Request",
    -32601: "Method not found",
    -32602: "Invalid params",
    -32603: "Internal error",
}


class MessageBroker:
    def __init__(self, *bootstrap_servers):
        if len(bootstrap_servers) == 0:
            bootstrap_servers = ["localhost:9092"]

        self.protocol_version = "2.0"
        self.bootstrap_servers = bootstrap_servers
        self.request_ids = {}

        self.producer = KafkaProducer(
            compression_type=None,
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: msgpack.packb(x, use_bin_type=True),
        )

        self.consumers = {}

    async def __send_method_request__(
        self,
        topic_name,
        name,
        id,
        *args,
        **kwargs,
    ):
        assert (
            len(args) * len(kwargs) == 0
        ), "JSON RPC 2.0 specification: You must use either args or kwargs"

        body = {
            "jsonrpc": self.protocol_version,
            "method": name,
            "params": kwargs if len(kwargs) != 0 else args,
        }

        if id:
            body["id"] = str(int(time.time() * 10_000_000))

        check = self.producer.send(f"{topic_name}_method_requests", value=body)
        self.producer.flush()
        check.get()

        if id:
            message = await self.__recv_message__(
                "method_results",
                key=body["id"].encode(),
            )
            response = message.value

            if "result" in response:
                return response["result"]
            elif "error" in response:
                raise Exception(f"get error on json rpc: {response['error']}")
            else:
                raise Exception(f"response message format error: {message}")

    def __get_error__(self, error_code):
        error_message = "Server error"
        if error_code in ERROR_CODE_MESSAGES:
            error_message = ERROR_CODE_MESSAGES[error_code]
        return {
            "code": error_code,
            "message": error_message,
        }

    async def __recv_method_request__(self, methods, message):
        request = message.value
        body = {
            "jsonrpc": self.protocol_version,
            "id": request["id"],
        }
        method = lambda x: x

        try:
            # FIXME: 임시로 주석처리함
            # if request["method"].startswith("_"):
            #     # Private prefix method
            #     raise AttributeError  # Method not found

            method = getattr(methods, request["method"])
        except AttributeError:
            traceback.print_exc()
            body["error"] = self.__get_error__(-32601)  # Method not found

        try:
            params = request["params"]
            if type(params) is list:
                body["result"] = method(*params)
            else:
                body["result"] = method(**params)
        except TypeError:
            traceback.print_exc()
            body["error"] = self.__get_error__(-32602)  # Invalid params
        except Exception:
            traceback.print_exc()
            body["error"] = self.__get_error__(-32603)  # Internal error
        finally:
            if request["id"]:
                self.producer.send(
                    "method_results", key=request["id"].encode(), value=body
                )

    async def __recv_message__(
        self, topic_name, group_id="default", key=None, partition=0
    ):
        name = f"{topic_name}.{group_id}"

        if name not in self.consumers:
            self.consumers[name] = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                group_id=group_id,
                value_deserializer=lambda x: msgpack.unpackb(x, raw=False),
                consumer_timeout_ms=100,
            )

            if partition is not None:
                self.consumers[name].assign(
                    [
                        TopicPartition(topic_name, partition),
                    ]
                )
            else:
                self.consumers[name].subscribe(topic_name)

        while True:
            for message in self.consumers[name]:
                if message.key != key:
                    continue

                self.consumers[name].commit()
                return message

    async def serve_async(self, methods, topic_name, group_id="default"):
        while True:
            message = await self.__recv_message__(
                f"{topic_name}_method_requests",
                group_id,
            )
            await self.__recv_method_request__(methods, message)

    def serve(self, methods, topic_name, group_id="default"):
        try:
            future = self.serve_async(methods, topic_name, group_id)
            asyncio.run(future)
        except KeyboardInterrupt:
            print("KeyboardInterrupt")

    async def rpc_async(self, topic_name, name, *args, **kwargs):
        return await self.__send_method_request__(
            topic_name,
            name,
            True,
            *args,
            **kwargs,
        )

    async def rpc_print_async(self, topic_name, name, *args, **kwargs):
        print(await self.rpc_async(topic_name, name, *args, **kwargs))

    async def rpc_oneway_async(self, topic_name, name, *args, **kwargs):
        return await self.__send_method_request__(
            topic_name,
            name,
            False,
            *args,
            **kwargs,
        )

    def rpc(self, topic_name, name, *args, **kwargs):
        future = self.rpc_async(topic_name, name, *args, **kwargs)
        return asyncio.run(future)

    def rpc_print(self, topic_name, name, *args, **kwargs):
        future = self.rpc_print_async(topic_name, name, *args, **kwargs)
        return asyncio.run(future)

    def rpc_oneway(self, topic_name, name, *args, **kwargs):
        future = self.rpc_oneway_async(topic_name, name, *args, **kwargs)
        return asyncio.run(future)
