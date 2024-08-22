from fiubaftp_vals.constants import MAX_SHORT


class Protocol():

    def __init__(self, max_seq_number: int = MAX_SHORT):
        self.max_seq_number = max_seq_number
        self.package_number = 0

    def set_package_number(self, package_number):
        self.package_number = package_number
    
    def update_package_number(self):
        self.package_number = self.package_number + 1 % (self.max_seq_number + 1)

    def get_package_number(self):
        return self.package_number
