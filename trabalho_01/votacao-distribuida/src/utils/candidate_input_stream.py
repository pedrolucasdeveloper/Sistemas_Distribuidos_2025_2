import pickle

class CandidateInputStream:
    def __init__(self, input_stream):
        self.input_stream = input_stream

    def read(self):
        return pickle.load(self.input_stream)