from transitions import Machine
from .schemas import Receipt, ReceiptStatus

class ReceiptStateMachine:
    states = [status.value for status in ReceiptStatus]

    def __init__(self, receipt: Receipt):
        self.receipt = receipt
        self.machine = Machine(model=self, states=ReceiptStateMachine.states, initial=self.receipt.status)

        self.machine.add_transition(trigger='queue', source='CREATED', dest='WAITING')
        self.machine.add_transition(trigger='select', source='WAITING', dest='PROCESSING')
        self.machine.add_transition(trigger='complete', source='PROCESSING', dest='COMPLETED')
        self.machine.add_transition(trigger='fail', source='PROCESSING', dest='FAILED')
        self.machine.add_transition(trigger='cancel', source='WAITING', dest='CANCELED')
        self.machine.add_transition(trigger='fail', source='CREATED', dest='FAILED')
        self.machine.add_transition(trigger='fail', source='WAITING', dest='FAILED')