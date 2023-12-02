from pydantic import BaseModel, field_validator
import socket

class NetworkInput(BaseModel):
    host: str
    protocol: str = "icmp"
    port: int = 0
    tos: int = 0

    @field_validator('host')
    def validate_host(cls, v):
        try:
            socket.inet_pton(socket.AF_INET, v)
            return v, "inet"
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, v)
                return v, "inet6"
            except socket.error:
                raise ValueError("Invalid host address provided")

    @field_validator('protocol')
    def validate_protocol(cls, v):
        if v.lower() not in ['tcp', 'udp', 'icmp']:
            raise ValueError("Protocol must be either TCP, UDP, or ICMP")
        return v.lower()

    @field_validator('port')
    def validate_port(cls, v):
        if v < 0 or v > 65535:
            raise ValueError("Port must be a number between 0 and 65535")
        return v

    @field_validator('tos')
    def validate_tos(cls, v):
        if v < 0 or v > 255:
            raise ValueError("Tos must be a number between 0 and 255")
        return v

    def __str__(self):
        return f"Host: {self.host[0]} ({self.host[1]})\nProtocol: {self.protocol}\nPort: {self.port}\nTos: {self.tos}"

        """
        if self.protocol == 'icmp':
            return f"Host: {self.host[0]} ({self.validate_host()[1]})\nProtocol: {self.protocol}\nTos: {self.tos}"
        elif self.protocol == 'tcp':
            return f"Host: {self.host} ({self.validate_host()[1]})\nProtocol: {self.protocol}\nPort: {self.port}\nTos: {self.tos}"
        elif self.protocol == 'udp':
            return f"Host: {self.host} ({self.validate_host()[1]})\nProtocol: {self.protocol}\nPort: {self.port}\nTos: {self.tos}"
        else:
            raise ValueError("Invalid protocol provided")
        """

if __name__ == "__main__":
    # Get destination address and TOS value from user
    #dest_addr = input("Enter destination address: ")
    #tos = int(input("Enter TOS value: "))
    dest_addr = "127.0.0.1"
    protocol = "icmp"
    port = 0
    tos = 0

    test = NetworkInput(host=dest_addr, tos=tos, protocol=protocol, port=port)
    print(test)