
class config():
    def __init__(self, filename):
        self.file = open(filename, "r")
        self.settings = dict()

        for line in self.file:
            if len(line) > 1:
                values = line.split("=")
                self.settings[values[0]] = values[1]

    def get_setting(self, setting_name):
        rtn_string = self.settings[setting_name]
        if rtn_string[-1] == '\n':
            rtn_string = rtn_string[:-1]
        if rtn_string[0] == '"' and rtn_string[-1] == '"':
            rtn_string = rtn_string[1:-1]
        elif rtn_string[0] == "'" and rtn_string[-1] == "'":
            rtn_string = rtn_string[1:-1]
        return str(rtn_string)
