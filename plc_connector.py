from aphyt import omron


class Connector:
    def __init__(self, address):
        print(self)
        self.eip_instance = omron.NSeries()
        self.address = address

    def __enter__(self):
        self.eip_instance.connect_explicit(self.address)
        self.eip_instance.register_session()
        self.eip_instance.update_variable_dictionary()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.eip_instance.close_explicit()

    def read(self, name):
        try:
            reply = self.eip_instance.read_variable(name)
        except Exception:
            reply = ""
            print("Tag: " + name + " not found")
        return reply

    def write(self, name, value):
        self.eip_instance.write_variable(name, value)
