
class Pipeline:
    # Note(Matthew): if methods in this class access the dict, we need to restructure

    def __init__(self, inbox, outbox, stages):
        self.inbox = inbox
        self.outbox = outbox
        self.stages = stages

    @staticmethod
    def from_dict(pipeline):
        pipeline_inbox = None
        if 'inbox' in pipeline:
            pipeline_inbox = pipeline['inbox']

        pipeline_outbox = None
        if 'outbox' in pipeline:
            pipeline_outbox = pipeline['outbox']

        pipeline_stages = None
        if 'stages' in pipeline:
            pipeline_stages = pipeline['stages']

        return Pipeline(
            inbox=pipeline_inbox,
            outbox=pipeline_outbox,
            stages=pipeline_stages
        )
