import pickle

class CandidateOutputStream:
    def __init__(self, output_stream):
        self.output_stream = output_stream

    def write(self, data):
        pickle.dump(data, self.output_stream)